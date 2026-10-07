"""Offline task accounting: real SQLite, restarts, races and raw questions."""
from concurrent.futures import ThreadPoolExecutor
import importlib
import json

import pytest


def api():
    module = 'scripts.ifc_repair.repair_comparison.ledger'
    from pathlib import Path
    assert (Path(__file__).resolve().parents[3] / module.replace('.', '/')).with_suffix('.py').exists(), 'Task ledger is not implemented'
    return importlib.import_module(module)


def test_ledger_entrypoint_exists():
    assert api().Ledger


def test_formal_mode_keeps_distinct_evidence_label(setup):
    ledger, _, profile = setup
    ledger.create('formal-001-A', case_id='formal-001', arm='A', budget=profile, mode='live_formal')
    assert ledger.snapshot('formal-001-A')['mode'] == 'live_formal'
    assert ledger.events('formal-001-A')[0]['payload']['evidence_class'] == 'live_formal'


@pytest.fixture
def setup(tmp_path):
    clock = [100.0]
    cls = api().Ledger
    ledger = cls(tmp_path / 'control.sqlite', clock=lambda: clock[0])
    profile = {'tokens': 100, 'calls': 10, 'active_seconds': 30, 'tool_seconds': 5,
               'extensions': [{'id': 'after-two', 'min_calls': 2, 'tokens': 50, 'active_seconds': 10}]}
    ledger.create('run-a', case_id='case-001', arm='A', budget=profile)
    ledger.start('run-a')
    return ledger, clock, profile


def test_pause_resume_keeps_usage_and_separates_waiting_time(setup):
    ledger, clock, _ = setup
    ledger.reserve('run-a', 'q1', 40, metadata={'stage': 'root'})
    ledger.settle('run-a', 'q1', usage={'input_tokens': 10, 'output_tokens': 7, 'cached_input_tokens': 4, 'reasoning_output_tokens': 3}, response={'reasoning': 'actually returned'})
    clock[0] = 104
    ledger.ask('run-a', question_id='question-1', text='补在哪一层？')
    clock[0] = 114
    restarted = api().Ledger(ledger.path, clock=lambda: clock[0])
    status = restarted.snapshot('run-a')
    assert status['status'] == 'awaiting_user'
    assert status['active_elapsed_s'] == 4 and status['human_wait_s'] == 10
    assert status['usage']['total_tokens'] == 17
    restarted.answer('run-a', question_id='question-1', text='二层。', requested_fact_ids=['floor'], answered_fact_ids=['floor'], event_id='answer-1')
    clock[0] = 117
    status = restarted.finish('run-a', 'no_output')
    assert status['active_elapsed_s'] == 7 and status['human_wait_s'] == 10 and status['wall_elapsed_s'] == 17
    assert restarted.events('run-a')[-2]['payload']['text'] == '二层。'
    assert restarted.calls('run-a')[0]['response']['reasoning'] == 'actually returned'


def test_unknown_usage_retains_reservation_and_failure(setup):
    ledger, _, _ = setup
    ledger.reserve('run-a', 'retry-1', 70, metadata={'stage': 'summary', 'parent_session': 'root'})
    ledger.settle('run-a', 'retry-1', usage=None, response={'error': 'timeout'}, failed=True)
    status = ledger.snapshot('run-a')
    assert status['usage']['coverage'] == 'unavailable'
    assert status['usage']['total_tokens'] is None
    assert status['usage']['reserved_tokens'] == 70
    with pytest.raises(ValueError, match='TOKEN_BUDGET'):
        ledger.reserve('run-a', 'retry-2', 31)
    ledger.reserve('run-a', 'retry-2', 30)
    ledger.settle('run-a', 'retry-2', usage={'input_tokens': 4, 'output_tokens': 2}, response={})
    assert ledger.snapshot('run-a')['usage']['coverage'] == 'partial'
    assert len(ledger.calls('run-a')) == 2


def test_duplicate_notifications_idempotent_but_conflicts_rejected(setup):
    ledger, _, _ = setup
    ledger.reserve('run-a', 'request', 40)
    for _ in range(2):
        ledger.settle('run-a', 'request', usage={'input_tokens': 10, 'output_tokens': 4}, response={'content': 'ok'})
    assert ledger.snapshot('run-a')['usage']['known_total_tokens'] == 14
    with pytest.raises(ValueError, match='CONFLICT'):
        ledger.settle('run-a', 'request', usage={'input_tokens': 20, 'output_tokens': 4}, response={'content': 'different'})


def test_concurrent_reservations_cannot_double_spend(setup):
    ledger, _, _ = setup
    def reserve(index):
        try:
            api().Ledger(ledger.path, clock=lambda: 100).reserve('run-a', str(index), 60)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(reserve, range(2))) == 1


def test_cannot_pause_or_finish_with_inflight_work(setup):
    ledger, _, _ = setup
    ledger.reserve('run-a', 'request', 10)
    with pytest.raises(ValueError, match='INFLIGHT'):
        ledger.ask('run-a', question_id='q', text='哪里？')
    ledger.settle('run-a', 'request', usage=None, response={})
    ledger.activity('run-a', 'tool', begin=True)
    with pytest.raises(ValueError, match='INFLIGHT'):
        ledger.finish('run-a', 'no_output')
    ledger.activity('run-a', 'tool', begin=False)
    assert ledger.ask('run-a', question_id='q', text='哪里？')['status'] == 'awaiting_user'


def test_answers_need_current_question_and_explicit_fact_subset(setup):
    ledger, _, _ = setup
    ledger.ask('run-a', question_id='q', text='哪层？')
    with pytest.raises(ValueError, match='QUESTION'):
        ledger.answer('run-a', question_id='stale', text='二层', event_id='a')
    with pytest.raises(ValueError, match='UNASKED_FACT'):
        ledger.answer('run-a', question_id='q', text='二层', requested_fact_ids=[], answered_fact_ids=['floor'], event_id='a')
    ledger.answer('run-a', question_id='q', text='二层', event_id='a')
    ledger.answer('run-a', question_id='q', text='二层', event_id='a')
    assert sum(e['kind'] == 'answer' for e in ledger.events('run-a')) == 1


def test_single_active_task_and_same_case_equal_profiles(setup):
    ledger, _, profile = setup
    with pytest.raises(ValueError, match='UNEQUAL_CASE_BUDGET'):
        ledger.create('run-c', case_id='case-001', arm='C', budget={**profile, 'tokens': 200})
    ledger.create('run-c', case_id='case-001', arm='C', budget=profile)
    with pytest.raises(ValueError, match='OTHER_ACTIVE'):
        ledger.start('run-c')


def test_frozen_extension_rule_cannot_be_repeated_or_score_conditioned(setup):
    ledger, _, _ = setup
    with pytest.raises(ValueError, match='EXTENSION_TRIGGER'):
        ledger.extend('run-a', 'after-two')
    for i in range(2):
        ledger.reserve('run-a', str(i), 10)
        ledger.settle('run-a', str(i), usage={'input_tokens': 1, 'output_tokens': 1}, response={})
    ledger.extend('run-a', 'after-two')
    assert ledger.snapshot('run-a')['limits']['tokens'] == 150
    with pytest.raises(ValueError, match='EXTENSION'):
        ledger.extend('run-a', 'after-two')


def test_timeout_overrun_and_terminal_are_not_erased(setup):
    ledger, clock, _ = setup
    ledger.reserve('run-a', 'r', 80)
    clock[0] = 132
    ledger.settle('run-a', 'r', usage={'input_tokens': 70, 'output_tokens': 40}, response={})
    assert ledger.snapshot('run-a')['usage']['token_overrun'] == 10
    with pytest.raises(ValueError, match='TIME_BUDGET'):
        ledger.reserve('run-a', 'r2', 1)
    ledger.finish('run-a', 'budget_exhausted')
    with pytest.raises(ValueError, match='TERMINAL'):
        ledger.ask('run-a', question_id='q', text='继续？')


@pytest.mark.parametrize('usage', [{'input_tokens': -1, 'output_tokens': 1}, {'input_tokens': True, 'output_tokens': 1}, {'input_tokens': 3}, {'input_tokens': 1, 'output_tokens': float('nan')}])
def test_malformed_usage_stays_unknown_not_zero(setup, usage):
    ledger, _, _ = setup
    ledger.reserve('run-a', 'r', 40)
    ledger.settle('run-a', 'r', usage=usage, response={})
    assert ledger.snapshot('run-a')['usage']['total_tokens'] is None
    assert ledger.snapshot('run-a')['usage']['reserved_tokens'] == 40


def test_existing_messages_rows_recompute_without_rewriting_raw_evidence(setup):
    ledger, _, _ = setup
    raw = {'input_tokens': 4, 'cache_read_input_tokens': 30, 'cache_creation_input_tokens': 2,
           'output_tokens': 3}
    ledger.reserve('run-a', 'cached', 50, metadata={'wire_protocol': 'messages'})
    ledger.settle('run-a', 'cached', usage=raw, response={'stream_complete': True})
    reopened = api().Ledger(ledger.path)
    assert reopened.snapshot('run-a')['usage']['total_tokens'] == 39
    assert reopened.calls('run-a')[0]['usage'] == raw
    assert reopened.calls('run-a')[0]['response'] == {'stream_complete': True}


@pytest.mark.parametrize('cached', [-1, True, None, '30'])
def test_invalid_messages_cache_count_stays_unknown(setup, cached):
    ledger, _, _ = setup
    ledger.reserve('run-a', 'cached', 50, metadata={'wire_protocol': 'messages'})
    ledger.settle('run-a', 'cached', usage={'input_tokens': 4, 'cache_read_input_tokens': cached,
                  'output_tokens': 3}, response={'stream_complete': True})
    assert ledger.snapshot('run-a')['usage']['total_tokens'] is None
