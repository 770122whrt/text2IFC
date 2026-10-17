"""Offline SQLite slot policy: races, pending tasks and isolated accounting."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Barrier

import pytest

from scripts.ifc_repair.repair_comparison.ledger import Ledger


STAGE = 'repair-comparison-scalable-live'
BUDGET = {'tokens': 100, 'calls': 10, 'active_seconds': 30,
          'tool_seconds': 5, 'extensions': []}


def create(ledger, index, *, stage=STAGE):
    return ledger.create(f'run-{index}', case_id=f'case-{index}', arm='A',
                         budget=BUDGET, metadata={'runtime': {'stage': stage}})


@pytest.fixture
def scalable(tmp_path):
    ledger = Ledger(tmp_path / 'control.sqlite', clock=lambda: 100)
    for index in range(5):
        create(ledger, index)
    return ledger


def test_concurrent_starts_atomically_respect_persisted_capacity(scalable):
    scalable.configure_concurrency(2)
    barrier = Barrier(5)

    def start(index):
        ledger = Ledger(scalable.path, clock=lambda: 100)
        barrier.wait()
        try:
            ledger.start(f'run-{index}')
            return True
        except ValueError as exc:
            assert str(exc) == 'OTHER_ACTIVE_TASK'
            return False

    with ThreadPoolExecutor(max_workers=5) as pool:
        assert sum(pool.map(start, range(5))) == 2
    statuses = [scalable.snapshot(f'run-{i}')['status'] for i in range(5)]
    assert statuses.count('running') == 2
    assert statuses.count('ready') == 3


def test_pending_task_keeps_slot_and_resume_excludes_self(scalable):
    scalable.configure_concurrency(2)
    scalable.start('run-0')
    scalable.start('run-1')
    scalable.ask('run-0', question_id='q', text='Which floor?')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        scalable.start('run-2')
    assert scalable.answer('run-0', question_id='q', text='Second',
                           event_id='answer')['status'] == 'running'
    scalable.finish('run-1', 'no_output')
    assert scalable.start('run-2')['status'] == 'running'


def test_unconfigured_legacy_pending_task_preserves_original_resume_guard(tmp_path):
    ledger = Ledger(tmp_path / 'control.sqlite')
    create(ledger, 0, stage='repair-comparison-formal-live')
    create(ledger, 1, stage='repair-comparison-formal-live')
    ledger.start('run-0')
    ledger.ask('run-0', question_id='q', text='Which floor?')
    ledger.start('run-1')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        ledger.answer('run-0', question_id='q', text='Second', event_id='answer')
    ledger.finish('run-1', 'no_output')
    ledger.answer('run-0', question_id='q', text='Second', event_id='answer')


def test_policy_idempotent_after_start_and_cannot_change(scalable):
    policy = scalable.configure_concurrency(2)
    scalable.start('run-0')
    restarted = Ledger(scalable.path, clock=lambda: 100)
    assert restarted.configure_concurrency(2) == policy
    with pytest.raises(ValueError, match='CONCURRENCY_POLICY_FROZEN'):
        restarted.configure_concurrency(3)
    with pytest.raises(ValueError, match='CONCURRENCY_POLICY_FROZEN'):
        restarted.configure_concurrency(1, stage='legacy')
    restarted.finish('run-0', 'no_output')
    assert restarted.configure_concurrency(2) == policy


def test_explicit_single_slot_counts_pending_tasks(scalable):
    scalable.configure_concurrency(1)
    scalable.start('run-0')
    scalable.ask('run-0', question_id='q', text='Which floor?')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        scalable.start('run-1')
    scalable.answer('run-0', question_id='q', text='Second', event_id='answer')


@pytest.mark.parametrize('capacity', [0, -1, True, 1.5, '2'])
def test_invalid_capacity_rejected(scalable, capacity):
    with pytest.raises(ValueError, match='INVALID_CONCURRENCY_CAPACITY'):
        scalable.configure_concurrency(capacity)


def test_parallel_policy_rejects_legacy_stage_and_mixed_runs(scalable):
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_NOT_ALLOWED'):
        scalable.configure_concurrency(2, stage='repair-comparison-formal-live')
    create(scalable, 'legacy', stage='repair-comparison-formal-live')
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        scalable.configure_concurrency(2)
    scalable.start('run-0')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        scalable.start('run-1')


def test_parallel_policy_rejects_unstaged_runs(tmp_path):
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('legacy', case_id='legacy', arm='A', budget=BUDGET)
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        ledger.configure_concurrency(2)


@pytest.mark.parametrize('metadata', [{'runtime': None}, {'runtime': []}, ['legacy']])
def test_malformed_runtime_metadata_cannot_opt_in(tmp_path, metadata):
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('legacy', case_id='legacy', arm='A', budget=BUDGET, metadata=metadata)
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        ledger.configure_concurrency(2)


def test_configuration_requires_nonempty_unstarted_batch(scalable, tmp_path):
    empty = Ledger(tmp_path / 'empty.sqlite')
    with pytest.raises(ValueError, match='CONCURRENCY_REQUIRES_READY_BATCH'):
        empty.configure_concurrency(2)
    scalable.start('run-0')
    with pytest.raises(ValueError, match='CONCURRENCY_REQUIRES_READY_BATCH'):
        scalable.configure_concurrency(2)


def test_policy_freezes_updates_and_deletion_in_sqlite(scalable):
    scalable.configure_concurrency(2)
    with sqlite3.connect(scalable.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match='CONCURRENCY_POLICY_FROZEN'):
            db.execute('UPDATE concurrency_policy SET capacity=3')
        with pytest.raises(sqlite3.IntegrityError, match='CONCURRENCY_POLICY_FROZEN'):
            db.execute('DELETE FROM concurrency_policy')
        with pytest.raises(sqlite3.IntegrityError, match='CONCURRENCY_POLICY_FROZEN'):
            db.execute('INSERT OR REPLACE INTO concurrency_policy VALUES(1,3,?)', (STAGE,))
    scalable.start('run-0')
    scalable.start('run-1')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        scalable.start('run-2')


def test_new_runs_and_tampered_stage_cannot_use_parallel_slots(scalable):
    scalable.configure_concurrency(2)
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        create(scalable, 'legacy', stage='repair-comparison-formal-live')
    with scalable.transaction() as db:
        state = scalable._load(db, 'run-0')
        state['metadata']['runtime']['stage'] = 'legacy'
        scalable._save(db, state)
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        scalable.start('run-0')
    with pytest.raises(ValueError, match='CONCURRENCY_STAGE_MISMATCH'):
        scalable.start('run-1')


def test_concurrent_configuration_cannot_change_first_policy(scalable):
    barrier = Barrier(2)

    def configure(capacity):
        ledger = Ledger(scalable.path)
        barrier.wait()
        try:
            return ledger.configure_concurrency(capacity)['capacity']
        except ValueError as exc:
            assert str(exc) == 'CONCURRENCY_POLICY_FROZEN'
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(configure, [2, 3]))
    assert results.count(None) == 1
    winner = next(value for value in results if value is not None)
    assert scalable.configure_concurrency(winner)['capacity'] == winner


def test_reservations_charges_and_unknown_usage_remain_per_task(scalable):
    scalable.configure_concurrency(2)
    scalable.start('run-0')
    scalable.start('run-1')
    scalable.reserve('run-0', 'same-request', 80)
    scalable.reserve('run-1', 'same-request', 80)
    scalable.settle('run-0', 'same-request', usage=None,
                    response={'error': 'timeout'}, failed=True)
    scalable.settle('run-1', 'same-request',
                    usage={'input_tokens': 10, 'output_tokens': 5}, response={})
    assert scalable.snapshot('run-0')['usage']['reserved_tokens'] == 80
    assert scalable.snapshot('run-1')['usage']['known_total_tokens'] == 15
    with pytest.raises(ValueError, match='TOKEN_BUDGET_EXHAUSTED'):
        scalable.reserve('run-0', 'next', 21)
    scalable.reserve('run-1', 'next', 85)
    assert len(scalable.calls('run-0')) == 1
    assert len(scalable.calls('run-1')) == 2
