"""Complete-input batch policy; fake processes, real ledger, no model calls."""
import json

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from tests.ifc_repair.repair_comparison.test_scalable_controller_safety import (
    _batch, _charge, _no_output, _processes,
)
from tests.ifc_repair.repair_comparison.test_property_policy_controller import answer_seam, verified


def pending(tmp_path, monkeypatch, groups=('E', 'B')):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, groups=groups)
    run = order[0]
    _charge(ledger, run)
    ledger.set_native(run, {'session_id': 'original-session'})
    ledger.ask(run, question_id='q1', text='Which public reference is intended?', binding={})
    monkeypatch.setattr(batch, 'docker', lambda *a, **k: '')
    return root, ledger, order


def test_default_wait_preserves_unanswered_question(tmp_path, monkeypatch):
    root, ledger, order = pending(tmp_path, monkeypatch)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root) == 2
    assert not started and ledger.snapshot(order[0])['status'] == 'awaiting_user'


@pytest.mark.parametrize('arm', list('ABCDEFG'))
def test_fail_retains_question_and_cost_then_continues(tmp_path, monkeypatch, arm):
    root, ledger, order = pending(tmp_path, monkeypatch, groups=(arm, 'B'))
    before = ledger.snapshot(order[0])
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root, clarification_policy='fail') == 0
    after = ledger.snapshot(order[0])
    assert after['status'] == 'no_output' and after['artifact'] is None
    for field in ('question', 'usage', 'native', 'limits', 'started', 'metadata'):
        assert after[field] == before[field]
    assert not any(e['kind'] == 'answer' for e in ledger.events(order[0]))
    assert started == [order[1]]
    case, arm = order[0].rsplit('-', 1)
    report = (root/'results'/case/arm/'report.md').read_text(encoding='utf8')
    assert 'UNANSWERED_CLARIFICATION_COMPLETE_INPUT_POLICY' in report
    assert before['question']['text'] in report


def test_verified_property_confirmation_precedes_fail_policy(tmp_path, monkeypatch):
    root, ledger, order = pending(tmp_path, monkeypatch, groups=('E',))
    monkeypatch.setattr(batch, '_verified_property_answer', verified)
    answers = answer_seam(monkeypatch, ledger)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root, confirm_existing_properties=True, clarification_policy='fail') == 0
    assert len(answers) == 1 and started == order
    assert all(e['payload'].get('detail') != 'UNANSWERED_CLARIFICATION_COMPLETE_INPUT_POLICY'
               for e in ledger.events(order[0]) if e['kind'] == 'terminal')


@pytest.mark.parametrize('busy', ['activity', 'inflight', 'container'])
def test_fail_cannot_finish_active_task(tmp_path, monkeypatch, busy):
    root, ledger, order = pending(tmp_path, monkeypatch)
    run = order[0]
    if busy == 'container':
        monkeypatch.setattr(batch, 'docker', lambda *a, **k: 'still-running')
    else:
        # Simulate a recovered inconsistent ledger; a normal ask forbids either.
        with ledger.transaction() as db:
            db.execute("UPDATE runs SET state=json_set(state,'$.status','running') WHERE run_id=?", (run,))
        if busy == 'activity':
            ledger.activity(run, 'background', begin=True)
        else:
            ledger.reserve(run, 'pending-call', 10, {})
        with ledger.transaction() as db:
            db.execute("UPDATE runs SET state=json_set(state,'$.status','awaiting_user') WHERE run_id=?", (run,))
    _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root, clarification_policy='fail') == 2
    assert ledger.snapshot(run)['status'] == 'awaiting_user'
    case, arm = run.rsplit('-', 1)
    assert not (root/'results'/case/arm/'report.md').exists()


def test_pause_resume_preserves_explicit_policy_and_batch_binding(tmp_path, monkeypatch):
    root, ledger, order = pending(tmp_path, monkeypatch)
    _processes(monkeypatch, root, ledger, _no_output)
    batch.pause(root)
    assert batch.run(root, clarification_policy='fail') == 2  # Existing question remains visible.
    assert ledger.snapshot(order[0])['status'] == 'awaiting_user'
    with ledger.transaction() as db:
        policy = json.loads(db.execute("SELECT value FROM batch_control WHERE key='clarification_policy'").fetchone()[0])
    assert policy['policy'] == 'fail' and policy['batch_sha256'] == batch.plan(root)['sha256']
    assert batch.resume(root) == 0
    assert batch.run(root, clarification_policy='wait') == 2
    assert 'CLARIFICATION_POLICY_FROZEN' in batch.brief_status(root)['reason']
    with ledger.transaction() as db:
        db.execute("UPDATE batch_control SET value=json_set(value,'$.batch_sha256','changed') WHERE key='clarification_policy'")
    assert batch.run(root) == 2
    assert 'CLARIFICATION_POLICY_BATCH_CHANGED' in batch.brief_status(root)['reason']


def test_warm_d_stop_waits_for_native_owner_before_completion(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, groups=('D', 'B'))
    requested = []
    monkeypatch.setattr(batch, 'docker', lambda *a, **k: '')
    def stop(root, run, question_id):
        assert ledger.snapshot(run)['status'] == 'awaiting_user'
        requested.append((run, question_id))
    monkeypatch.setattr(batch.carrier, 'request_clarification_stop', stop, raising=False)
    def job(ledger, run, process):
        if run.endswith('-B'):
            return _no_output(ledger, run, process)
        _charge(ledger, run)
        ledger.ask(run, question_id='q-d', text='Need a reference', binding={})
        def poll(_):
            if not requested:
                return None
            ledger.finish(run, 'no_output', detail='UNANSWERED_CLARIFICATION_COMPLETE_INPUT_POLICY')
            return 0
        process.poll_hook = poll
    started, processes = _processes(monkeypatch, root, ledger, job)
    assert batch.run(root, clarification_policy='fail') == 0
    assert started == order and requested == [(order[0], 'q-d')]
    assert all(p.waited for p in processes)


def test_flag_only_valid_for_run_and_resume(tmp_path, capsys):
    assert batch.main(['status', '--root', str(tmp_path), '--clarification-policy', 'fail']) == 2
    assert 'CLARIFICATION_POLICY_EXECUTION_ONLY' in capsys.readouterr().out
