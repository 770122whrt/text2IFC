"""Only whole unstarted case cohorts can receive an explicit lower budget."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile, LEGACY_BUDGET_POLICY_VERSION
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger, encode


def fixture(tmp_path, monkeypatch):
    root = tmp_path/'batch'
    root.mkdir()
    configuration = {'stage': batch.SCALABLE_STAGE, 'case_ids': ['old', 'fresh'],
        'budgets': {case: fixed_budget_profile('S2', policy_version=LEGACY_BUDGET_POLICY_VERSION)
                    for case in ['old', 'fresh']},
        'case_groups': {case: list('ABCDEFG') for case in ['old', 'fresh']},
        'order': [case+'-'+arm for case in ['old', 'fresh'] for arm in 'ABCDEFG']}
    value = {'schema_version': batch.PLAN_SCHEMA, 'budget_policy': batch.TASK_BUDGET_ONLY,
        'fixed_budget_version': LEGACY_BUDGET_POLICY_VERSION, 'configuration': configuration}
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    (root/'admission').mkdir()
    write_json(root/'admission/live.json', {'configuration': configuration})
    write_json(root/'experiment.json', {'mode': 'live', 'configuration': configuration,
        'budgets': configuration['budgets'], 'admission': str(root/'admission/live.json'),
        'routes': {'identity': 'must remain unchanged'}})
    ledger = Ledger(root/'control.sqlite')
    for run in configuration['order']:
        case, arm = run.rsplit('-', 1)
        ledger.create(run, case_id=case, arm=arm, budget=configuration['budgets'][case])
    monkeypatch.setattr(batch, '_source_guard', lambda *args: None)
    return root, ledger


def rows(ledger, table):
    with ledger.transaction() as db:
        return [tuple(row) for row in db.execute('SELECT * FROM '+table)]


def test_budget_revision_preserves_started_cases_and_all_usage(tmp_path, monkeypatch):
    root, ledger = fixture(tmp_path, monkeypatch)
    ledger.start('old-B')
    ledger.reserve('old-B', 'failed-call', 100)
    ledger.settle('old-B', 'failed-call', usage=None, response={'error': 'preserved'}, failed=True)
    ledger.finish('old-B', 'no_output')
    before = {run: raw for run, raw in rows(ledger, 'runs') if run.startswith('old-')}
    calls, events = rows(ledger, 'calls'), rows(ledger, 'events')
    original = (root/'batch.json').read_bytes()
    result = batch.apply_unstarted_budgets(root)
    assert result['updated_cases'] == 1 and result['updated_tasks'] == 7
    value = batch.plan(root)
    assert value['configuration']['budgets']['old']['tokens'] == 2_000_000
    assert value['configuration']['budgets']['fresh']['tokens'] == 1_000_000
    assert value['case_budget_versions']['old'] == LEGACY_BUDGET_POLICY_VERSION
    assert value['case_budget_versions']['fresh'].endswith('/0.2')
    assert before == {run: raw for run, raw in rows(ledger, 'runs') if run in before}
    assert calls == rows(ledger, 'calls') and events == rows(ledger, 'events')
    assert all(ledger.snapshot('fresh-'+a)['budget']['tokens'] == 1_000_000 for a in 'ABCDEFG')
    assert read_json(root/'experiment.json')['configuration'] == value['configuration']
    assert (root/'pause-between-tasks').exists() and (root/'stop-service').exists()
    assert (root/'admission/live.json').is_file()
    assert Path(result['previous_plan']).read_bytes() == original
    assert batch.apply_unstarted_budgets(root)['state'] == 'unchanged'


@pytest.mark.parametrize('unsafe', ['active', 'inflight', 'nonpolicy'])
def test_budget_revision_rejects_unsafe_batch_without_partial_update(tmp_path, monkeypatch, unsafe):
    root, ledger = fixture(tmp_path, monkeypatch)
    if unsafe == 'nonpolicy':
        value = batch.plan(root)
        value['configuration']['budgets']['fresh']['tokens'] = 42
        value.pop('sha256')
        value['sha256'] = batch._digest(value)
        write_json(root/'batch.json', value)
        runtime = read_json(root/'experiment.json')
        runtime['configuration'] = value['configuration']
        runtime['budgets'] = value['configuration']['budgets']
        write_json(root/'experiment.json', runtime)
    else:
        ledger.start('old-B')
        if unsafe == 'inflight':
            ledger.reserve('old-B', 'still-pending', 100)
            with ledger.transaction() as db:
                state = ledger._load(db, 'old-B')
                state['status'] = 'paused'
                ledger._save(db, state)
    before = (root/'batch.json').read_bytes(), rows(ledger, 'runs')
    with pytest.raises(ValueError):
        batch.apply_unstarted_budgets(root)
    assert before == ((root/'batch.json').read_bytes(), rows(ledger, 'runs'))


def test_budget_revision_recovers_interrupted_file_commit_without_resetting_state(tmp_path, monkeypatch):
    root, ledger = fixture(tmp_path, monkeypatch)
    replace = batch._replace_bytes
    def interrupted(path, data):
        if path.name == 'experiment.json':
            raise OSError('injected interruption')
        return replace(path, data)
    monkeypatch.setattr(batch, '_replace_bytes', interrupted)
    with pytest.raises(OSError, match='injected interruption'):
        batch.apply_unstarted_budgets(root)
    assert (root/'pause-between-tasks').exists()
    assert (root/'admission/budget-update.pending.json').exists()
    monkeypatch.setattr(batch, '_replace_bytes', replace)
    assert batch.apply_unstarted_budgets(root)['updated_cases'] == 2
    assert all(s['budget']['tokens'] == 1_000_000 for s in batch._states(root))
    assert not (root/'admission/budget-update.pending.json').exists()
    assert rows(ledger, 'calls') == []


def test_budget_revision_admission_rejects_extra_configuration_drift(tmp_path, monkeypatch):
    root, ledger = fixture(tmp_path, monkeypatch)
    original = batch.plan(root)
    batch.apply_unstarted_budgets(root)
    value = batch.plan(root)
    before = {'files': {}, 'budgets': original['configuration']['budgets'], 'models': {'B': 'same'}}
    after = {'files': {}, 'budgets': value['configuration']['budgets'], 'models': {'B': 'same'}}
    previous = {'configuration': original['configuration'], 'bindings': before}
    batch._verify_budget_revision(root, previous, value, before, after)
    for field in ['models', 'case_groups', 'order']:
        broken = deepcopy(value)
        broken['configuration'][field] = 'unauthorized change'
        with pytest.raises(ValueError, match='BUDGET_REVISION'):
            batch._verify_budget_revision(root, previous, broken, before, after)
    with ledger.transaction() as db:
        state = ledger._load(db, 'fresh-B')
        state['budget']['tokens'] = 42
        ledger._save(db, state)
    with pytest.raises(ValueError, match='BUDGET_REVISION'):
        batch._verify_budget_revision(root, previous, value, before, after)


def test_budget_only_revision_rebinds_existing_delegation_and_clarification_without_changing_scope(tmp_path, monkeypatch):
    root, ledger = fixture(tmp_path, monkeypatch)
    original = batch.plan(root)
    delegated = batch._property_authorization(root, original, grant=True)
    assert batch._clarification_policy(root, original, 'fail') == 'fail'
    batch.apply_unstarted_budgets(root)
    target = batch.plan(root)
    current = batch._property_authorization(root, target)
    assert current == {**delegated, 'batch_sha256': target['sha256']}
    assert batch._clarification_policy(root, target) == 'fail'
    with ledger.transaction() as db:
        old = json.loads(db.execute('SELECT value FROM batch_control WHERE key=?',
            ('property_authorization@'+original['sha256'],)).fetchone()[0])
    assert old == delegated
    with pytest.raises(ValueError, match='CLARIFICATION_POLICY_FROZEN'):
        batch._clarification_policy(root, target, 'wait')


@pytest.mark.parametrize('drift', ['request', 'provider', 'unregistered', 'active'])
def test_policy_rebind_rejects_any_change_beyond_applied_budget(tmp_path, monkeypatch, drift):
    root, ledger = fixture(tmp_path, monkeypatch)
    batch._property_authorization(root, batch.plan(root), grant=True)
    batch.apply_unstarted_budgets(root)
    value = batch.plan(root)
    if drift == 'request': value['request_convention'] = 'different'
    elif drift == 'provider': value['configuration']['models'] = {'B': 'different'}
    elif drift == 'unregistered':
        with ledger.transaction() as db:
            db.execute("DELETE FROM batch_control WHERE key='budget-revision'")
    else: ledger.start('fresh-B')
    with pytest.raises(ValueError):
        batch._property_authorization(root, value)


def test_service_start_can_complete_after_ninety_seconds_without_charging_task_budget(tmp_path, monkeypatch):
    from tests.ifc_repair.repair_comparison.test_parallel_batch import _parallel_batch, _jobs
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, groups=('B',))
    _jobs(monkeypatch, root, ledger, order)
    process = batch._Process
    ticks = [0]
    def clock():
        ticks[0] += 20
        return ticks[0]
    monkeypatch.setattr(batch.time, 'monotonic', clock)
    class DelayedService(process):
        def __init__(self, command):
            super().__init__(command)
            if self.role == 'serve':
                self.ready = read_json(root/'service.json')
                write_json(root/'service.json', {'state': 'starting'})
                self.poll_count = 0
        def poll(self):
            if self.role == 'serve':
                self.poll_count += 1
                if self.poll_count == 7:
                    assert not any(s['started'] for s in batch._states(root))
                    assert not rows(ledger, 'calls')
                    write_json(root/'service.json', self.ready)
            return super().poll()
    monkeypatch.setattr(batch, '_Process', DelayedService)
    assert batch.run(root) == 0
    assert batch.brief_status(root)['state'] == 'complete'
