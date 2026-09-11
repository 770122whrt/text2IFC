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


def test_legacy_evidence_is_charged_once_without_rewriting_sources(tmp_path):
    raw = tmp_path/'design-brief/response.raw.json'
    raw.parent.mkdir()
    raw.write_text(json.dumps({'id':'old', 'usage':{'input_tokens':11,'output_tokens':17}}))
    before = raw.read_bytes()
    ledger = budget(tmp_path)
    assert ledger.snapshot()['calls_used'] == 1
    assert ledger.snapshot()['tokens_used_or_reserved'] == 28
    assert budget(tmp_path).snapshot()['calls_used'] == 1
    assert raw.read_bytes() == before


def test_actual_usage_and_active_time_accumulate(tmp_path):
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    ledger = budget(tmp_path, max_calls=5, max_tokens=1000, max_active_seconds=2)
    token = ledger.reserve(stage='brief', reserved_tokens=500)
    ledger.settle(token, usage={'prompt_tokens':30, 'completion_tokens':20}, elapsed_seconds=2)
    assert ledger.snapshot()['tokens_used_or_reserved'] == 50
    with pytest.raises(GenerationBudgetExceeded):
        ledger.reserve(stage='generator', reserved_tokens=500)


@pytest.mark.parametrize('usage', [None, {}, {'input_tokens': 11}])
def test_unknown_legacy_usage_blocks_transport_and_preserves_evidence(tmp_path, usage):
    from text2ifc_agent.generation_budget import BudgetedProvider, GenerationBudgetExceeded
    raw = tmp_path / 'design-brief/response.raw.json'
    raw.parent.mkdir()
    raw.write_text(json.dumps({'id': 'old-unknown', 'usage': usage}), encoding='utf-8')
    before = raw.read_bytes()
    provider = SequenceProvider([{}])
    for _ in range(2):
        ledger = budget(tmp_path)
        with pytest.raises(GenerationBudgetExceeded):
            call(BudgetedProvider(provider, ledger, max_output_tokens=100))
        assert ledger.snapshot()['calls_used'] == 1
    assert not provider.calls
    assert raw.read_bytes() == before


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


def test_public_budget_exhaustion_before_audit_never_publishes(tmp_path):
    from text2ifc_agent.generation_budget import BudgetLimits
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import _write_ready_design_brief_call, _SequenceLiveProvider, PHASE6_1_COMPLETE
    store = SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path)
    session = store.create_session(original_input='Generate a room')
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, 'ready')
    candidate = json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    provider = _SequenceLiveProvider([candidate])
    result = run_ready_session_to_ifc(store=store, session=session.session_id,
        provider_factory=lambda:provider, budget_limits=BudgetLimits(max_calls=2))
    assert result.status == 'budget_blocked' and result.ifc_path is None
    assert len(provider.session_ids) == 1
    assert store.get_session(session.session_id).status == 'budget_blocked'
    assert not (session.run_dir/'final-acceptance.json').exists()


def test_scoped_recovery_stops_repeated_failed_patch_and_keeps_attempts(tmp_path):
    from tests.agent.test_early_field_recovery import candidate, group, patch, _expected_facts
    from text2ifc_agent.scoped_loop import run_scoped_changeset_round
    from text2ifc_contract.validation_v2 import validate_v2_document
    value = candidate()
    g = group(value)
    partial = patch(value, g['scope'], omit_last=True)
    raw = SequenceProvider([partial, partial, patch(value, g['scope'])])
    result = run_scoped_changeset_round(provider=raw, output_dir=tmp_path, case_id='repeat',
        round_number=1, user_request='Generate a room', conversation=[], design_brief={},
        expected_facts=_expected_facts(), candidate=value,
        issues=[vars(i) for i in validate_v2_document(value)], field_recovery=True)
    assert not result['valid'] and result['status'] == 'repeated_candidate'
    assert len(raw.calls) == 2
    assert (tmp_path/'attempt-02/response.raw.json').is_file()
    assert not (tmp_path/'revisions').exists()


def test_contract_progress_with_same_operations_is_not_a_repeat(tmp_path):
    from copy import deepcopy
    from tests.agent.test_early_field_recovery import candidate, group, patch, _expected_facts
    from text2ifc_agent.scoped_loop import run_scoped_changeset_round
    from text2ifc_contract.validation_v2 import validate_v2_document
    value = candidate()
    good = patch(value, group(value)['scope'])
    first, second = deepcopy(good), deepcopy(good)
    first.pop('changeset_id')
    second.pop('base_revision_id')
    provider = SequenceProvider([first, second, good])
    result = run_scoped_changeset_round(provider=provider, output_dir=tmp_path, case_id='contract-progress',
        round_number=1, user_request='Generate a room', conversation=[], design_brief={},
        expected_facts=_expected_facts(), candidate=value,
        issues=[vars(i) for i in validate_v2_document(value)], field_recovery=True)
    assert result['valid']
    assert len(provider.calls) == 3
