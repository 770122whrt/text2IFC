"""Delegated confirmation uses the existing answer seam; uncertainty still waits."""
import json

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from tests.ifc_repair.repair_comparison.test_scalable_controller_safety import (
    _batch, _charge, _no_output, _processes,
)


def pending(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch, groups=('E',))
    run = order[0]
    _charge(ledger, run)
    ledger.set_native(run, {'session_id': 'same-session'})
    ledger.ask(run, question_id='q1', text='Property confirmation', binding={})
    return root, ledger, run


def answer_seam(monkeypatch, ledger):
    answers = []
    def answer(root, run, value):
        answers.append(value)
        ledger.answer(run, question_id=value['question_id'], text=value['text'],
                      event_id=value['event_id'], native_answer=value['native_answer'])
    monkeypatch.setattr(batch.carrier, 'answer', answer)
    return answers


def verified(state, *_):
    return {'source': 'user_confirmed', 'text': 'User delegated existing-property policy; public evidence verified.',
            'question_id': state['question']['question_id'], 'event_id': 'policy-q1',
            'native_answer': {'kind': 'confirm_property', 'authorized': True, 'preview_hash': 'bound'}}


def test_authorized_resume_keeps_original_session_and_budget(tmp_path, monkeypatch):
    root, ledger, run = pending(tmp_path, monkeypatch)
    before = ledger.snapshot(run)
    monkeypatch.setattr(batch, '_verified_property_answer', verified, raising=False)
    answers = answer_seam(monkeypatch, ledger)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.resume(root, confirm_existing_properties=True) == 0
    after = ledger.snapshot(run)
    assert started == [run] and len(answers) == 1
    for field in ('usage', 'native', 'limits', 'started', 'metadata'):
        assert after[field] == before[field]
    with ledger.transaction() as db:
        policy = json.loads(db.execute("SELECT value FROM batch_control WHERE key='property_authorization'").fetchone()[0])
    assert policy['source'] == 'user_delegated_policy'
    assert policy['batch_sha256'] == batch.plan(root)['sha256']
    assert batch.run(root) == 0  # Idempotent; no re-answer or rerun.
    assert started == [run] and len(answers) == 1


def test_default_never_confirms(tmp_path, monkeypatch):
    root, ledger, run = pending(tmp_path, monkeypatch)
    monkeypatch.setattr(batch, '_verified_property_answer', lambda *a: pytest.fail('No delegation'), raising=False)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root) == 2
    assert not started and ledger.snapshot(run)['status'] == 'awaiting_user'


def test_unverified_question_stays_pending_without_repeated_inspection(tmp_path, monkeypatch):
    root, ledger, run = pending(tmp_path, monkeypatch)
    checked = []
    monkeypatch.setattr(batch, '_verified_property_answer', lambda *a: checked.append(a) or None, raising=False)
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    assert batch.run(root, confirm_existing_properties=True) == 2
    assert batch.run(root) == 2
    assert len(checked) == 1 and not started
    assert ledger.snapshot(run)['status'] == 'awaiting_user'


def test_cooperative_pause_does_not_auto_answer(tmp_path, monkeypatch):
    root, ledger, run = pending(tmp_path, monkeypatch)
    monkeypatch.setattr(batch, '_verified_property_answer', lambda *a: pytest.fail('Paused'), raising=False)
    _processes(monkeypatch, root, ledger, _no_output)
    batch.pause(root)
    batch.run(root, confirm_existing_properties=True)
    assert ledger.snapshot(run)['status'] == 'awaiting_user'


def test_approval_persists_across_restart_but_not_changed_batch(tmp_path, monkeypatch):
    root, ledger, run = pending(tmp_path, monkeypatch)
    _processes(monkeypatch, root, ledger, _no_output)
    batch.pause(root)
    batch.run(root, confirm_existing_properties=True)
    monkeypatch.setattr(batch, '_verified_property_answer', verified, raising=False)
    answers = answer_seam(monkeypatch, ledger)
    assert batch.resume(root) == 0
    assert len(answers) == 1
    with ledger.transaction() as db:
        db.execute("UPDATE batch_control SET value=json_set(value,'$.batch_sha256','different') WHERE key='property_authorization'")
    assert batch.run(root) == 2
    assert 'PROPERTY_AUTHORIZATION_BATCH_CHANGED' in batch.brief_status(root)['reason']


def test_host_policy_is_not_in_isolated_runtime_bundle(tmp_path):
    from scripts.ifc_repair.repair_comparison.isolated_b import build_runtime_bundle
    inventory = build_runtime_bundle(batch.carrier.REPO, tmp_path/'bundle')
    assert not any('property_confirmation.py' in str(p) or 'prompt_check.py' in str(p) for p in inventory)
    key = 'scripts/ifc_repair/repair_comparison/property_confirmation.py'
    production = 'src/text2ifc_ifc_repair/property_intent.py'
    assert batch._runtime_bindings({'files': {key: 'host', production: 'runtime'}})['files'] == {production: 'runtime'}


def test_flag_only_valid_for_execution(tmp_path, capsys):
    assert batch.main(['status', '--root', str(tmp_path), '--confirm-existing-properties']) == 2
    assert 'PROPERTY_AUTHORIZATION_EXECUTION_ONLY' in capsys.readouterr().out
