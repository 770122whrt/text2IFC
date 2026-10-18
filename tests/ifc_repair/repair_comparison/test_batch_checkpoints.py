"""Dataset-row resume is a guard over existing task state, never a reset."""
import json

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.contracts import write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.repair_comparison.test_scalable_controller_safety import (
    _batch, _charge, _no_output, _processes,
)


def test_resume_from_second_case_skips_terminal_and_preserves_usage(tmp_path, monkeypatch):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)
    _charge(ledger, order[0])
    ledger.finish(order[0], 'no_output', detail='Original failure stays terminal.')
    before = ledger.snapshot(order[0])
    _charge(ledger, order[1])
    ledger.set_native(order[1], {'result': {'session_id': 'keep-session'}})
    started, _ = _processes(monkeypatch, root, ledger, _no_output)
    batch.pause(root)
    assert batch.main(['resume', '--root', str(root), '--from-case', '2']) == 0
    assert started == [order[1]]
    after = ledger.snapshot(order[0])
    assert {k: after[k] for k in ('status', 'usage', 'native', 'metadata', 'ended')} == {
        k: before[k] for k in ('status', 'usage', 'native', 'metadata', 'ended')}
    assert ledger.snapshot(order[1])['usage']['known_total_tokens'] == 5
    assert ledger.snapshot(order[1])['native']['result']['session_id'] == 'keep-session'


def test_resume_cannot_skip_unfinished_case_or_remove_pause_marker(tmp_path, monkeypatch, capsys):
    root, ledger, order, _ = _batch(tmp_path, monkeypatch)
    batch.pause(root)
    before = ledger.snapshot(order[0])
    monkeypatch.setattr(batch, 'run', lambda *_: pytest.fail('Invalid resume must not start workers'))
    assert batch.main(['resume', '--root', str(root), '--from-case', '2']) == 2
    assert 'EARLIER_CASE_INCOMPLETE' in capsys.readouterr().out
    assert (root/'pause-between-tasks').is_file()
    after = ledger.snapshot(order[0])
    assert {k: after[k] for k in ('status', 'usage', 'native', 'metadata')} == {
        k: before[k] for k in ('status', 'usage', 'native', 'metadata')}


def test_checkpoint_at_500_handles_partial_groups_and_never_reads_reports(tmp_path, monkeypatch):
    ledger = Ledger(tmp_path/'control.sqlite')
    # The 500th row has one finished group and one pending group.
    with ledger.transaction() as db:
        for i in range(1, 502):
            for arm in 'BE':
                case = f'row-{i:04d}'
                state = {'case_id': case, 'arm': arm,
                         'status': 'no_output' if i < 500 or (i == 500 and arm == 'B') else 'ready'}
                db.execute('INSERT INTO runs(run_id,state) VALUES(?,?)', (case+'-'+arm, json.dumps(state)))
    monkeypatch.setattr(batch, 'export_task', lambda *_: pytest.fail('No result reads'))
    monkeypatch.setattr(Ledger, 'calls', lambda *_: pytest.fail('No call body reads'))
    status = batch.brief_status(tmp_path)
    assert status['cases_total'] == 501
    assert status['cases_completed'] == 499
    assert status['next_case_index'] == 500
    assert status['next_case_id'] == 'row-0500'
    assert status['completed'] == 999
    assert len(json.dumps(status)) < 2048


def test_checkpoint_uses_frozen_order_before_initialization(tmp_path):
    config = {'case_ids': ['z-last-name', 'a-first-name'],
              'order': ['z-last-name-B', 'z-last-name-E', 'a-first-name-B']}
    value = {'schema_version': batch.PLAN_SCHEMA, 'budget_policy': batch.TASK_BUDGET_ONLY,
             'configuration': config}
    value['sha256'] = batch._digest(value)
    write_json(tmp_path/'batch.json', value)
    status = batch.brief_status(tmp_path)
    assert status['next_case_index'] == 1
    assert status['next_case_id'] == 'z-last-name'
    assert status['cases_total'] == 2


def test_completion_summary_includes_checkpoint_without_task_bodies(capsys):
    batch._emit('paused', cases_total=1200, cases_completed=499, next_case_index=500,
                next_case_id='row-0500', format_passed=999, private_body='must stay hidden')
    summary = json.loads(capsys.readouterr().out)
    assert summary['next_case_index'] == 500
    assert summary['cases_completed'] == 499
    assert summary['format_passed'] == 999
    assert 'private_body' not in summary


def test_source_guard_deduplicates_shared_metadata_without_skipping_inputs(tmp_path, monkeypatch):
    calls = []
    def digest(path):
        calls.append(str(path))
        return 'fixed'
    monkeypatch.setattr(batch, 'sha256', digest)
    shared = str(tmp_path/'delivery.json')
    value = {'input_bindings': {case: {'input_digests': {'model.ifc': 'fixed', 'request.txt': 'fixed'},
              'metadata_bindings': {shared: 'fixed'}} for case in ('one', 'two')}}
    batch._source_guard(tmp_path, value)
    assert calls.count(shared) == 1
    assert len(calls) == 5
