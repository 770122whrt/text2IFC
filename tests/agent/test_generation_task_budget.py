"""T4 frozen budget/recovery and oscillation family; no real transport."""
import json

import pytest

from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.agent.test_phase6_4_feedback_loop import _issue


def budget(path, **limits):
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits
    return GenerationBudget(path, BudgetLimits(**limits))


def call(provider):
    return provider.generate_live(session_id='test', prompt='json', schema={}, state={'stage':'generator'})


def test_factories_and_resume_share_consumed_calls(tmp_path):
    from text2ifc_agent.generation_budget import BudgetedProvider, GenerationBudgetExceeded
    ledger = budget(tmp_path, max_calls=1, max_tokens=1000)
    raw = SequenceProvider([{}])
    call(BudgetedProvider(raw, ledger, max_output_tokens=100))
    resumed = budget(tmp_path, max_calls=1, max_tokens=1000)
    with pytest.raises(GenerationBudgetExceeded):
        call(BudgetedProvider(raw, resumed, max_output_tokens=100))
    assert len(raw.calls) == 1
    assert resumed.snapshot()['calls_used'] == 1


def test_token_reservation_blocks_before_transport(tmp_path):
    from text2ifc_agent.generation_budget import BudgetedProvider, GenerationBudgetExceeded
    ledger = budget(tmp_path, max_calls=3, max_tokens=50)
    raw = SequenceProvider([{}])
    with pytest.raises(GenerationBudgetExceeded):
        call(BudgetedProvider(raw, ledger, max_output_tokens=100))
    assert raw.calls == []


def test_failed_or_interrupted_calls_are_not_refunded_on_resume(tmp_path):
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    ledger = budget(tmp_path, max_calls=2, max_tokens=100)
    ledger.reserve(stage='generator', reserved_tokens=70)
    resumed = budget(tmp_path, max_calls=2, max_tokens=100)
    with pytest.raises(GenerationBudgetExceeded):
        resumed.reserve(stage='audit', reserved_tokens=40)
    assert resumed.snapshot()['tokens_used_or_reserved'] == 70


def test_reopen_cannot_silently_enlarge_budget(tmp_path):
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    budget(tmp_path, max_calls=1)
    with pytest.raises(GenerationBudgetExceeded):
        budget(tmp_path, max_calls=100)


def test_actual_usage_and_active_time_accumulate(tmp_path):
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    ledger = budget(tmp_path, max_calls=5, max_tokens=1000, max_active_seconds=2)
    token = ledger.reserve(stage='brief', reserved_tokens=500)
    ledger.settle(token, usage={'prompt_tokens':30, 'completion_tokens':20}, elapsed_seconds=2)
    assert ledger.snapshot()['tokens_used_or_reserved'] == 50
    with pytest.raises(GenerationBudgetExceeded):
        ledger.reserve(stage='generator', reserved_tokens=500)


def test_feedback_stops_a_b_a_cycle_but_allows_new_stage(tmp_path):
    from text2ifc_agent.feedback_loop import write_feedback_artifacts
    def write(evidence, stage='audit'):
        return write_feedback_artifacts(tmp_path, source_stage=stage,
            issues=[_issue(evidence=evidence)], previous_issue_count=1, max_feedback_rounds=10)
    write('error A')
    assert write('error B')['retry_allowed']
    repeated = write('error A')
    assert not repeated['retry_allowed']
    assert repeated['terminal_status'] == 'blocked_cycle'
    assert write('error B', 'geometry')['retry_allowed']
    saved = json.loads((tmp_path/'feedback-rounds.json').read_text())
    assert len(saved['rounds']) == 4
