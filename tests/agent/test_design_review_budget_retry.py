"""Restart generation from Brief while retaining the authorized task's spend."""
import importlib.util
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_agent.generation_budget import GenerationBudgetExceeded
from tests.agent.test_design_review_audit import _audit
from tests.agent.test_interactive_cli_generation import PHASE6_1_COMPLETE, _write_ready_design_brief_call
from tests.agent.test_phase6_5_staged_generation import SequenceProvider

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/projection-retry-20260910/run_branches.py'


def load_harness():
    spec = importlib.util.spec_from_file_location('projection_retry_harness', SCRIPT)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    return harness


@pytest.mark.parametrize('branch,used', [('A-revise', 3), ('B-retain', 0), ('A-revise', 32)])
def test_retry_keeps_task_spend_but_requests_new_brief(tmp_path, branch, used):
    harness = load_harness()
    parent = tmp_path / 'parent'
    _write_ready_design_brief_call(parent)
    call = parent / 'calls/01-design-brief'
    brief = harness.read(call / 'design-brief.json')
    brief['schema_version'] = 'text2ifc/design-brief/2.1'
    brief['known_facts']['semantic_requirements'] = []
    brief['known_facts']['appearance'] = {'profile': 'warm-residential', 'style_notes': '协调外观，仍需视觉核对。'}
    turns = harness.read(call / 'conversation.json')
    turns.append({'turn_id': 'approved', 'role': 'user', 'content': '保留已确认决定并继续。'})
    prior_budget = parent / 'generation-budget.json'
    harness.write(prior_budget, {'schema_version': 'text2ifc/generation-budget/1.0',
        'limits': {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600},
        'attempts': [{'attempt': i + 1, 'stage': 'preserved-prior-call', 'status': 'completed',
                      'tokens_charged': 10, 'elapsed_seconds': 1} for i in range(used)]})
    frozen = {p.relative_to(parent): p.read_bytes() for p in parent.rglob('*') if p.is_file()}
    case = tmp_path / branch
    case.mkdir()
    harness.write(case / 'conversation.json', turns)
    harness.write(case / 'reference-review.json', {'source': 'offline fixture', 'gap_mm': 0})
    candidate = harness.read(PHASE6_1_COMPLETE / 'generator/candidate.json')
    candidate['schema_version'] = 'bim-json/2.1'
    candidate['appearance'] = {'profile': 'warm-residential'}
    for entity in candidate['entities']:
        entity['materials'], entity['property_sets'] = [], {}
    audit = _audit('not_verified' if branch == 'A-revise' else 'retained_known_issue')
    audit['design_review']['concerns'][0]['id'] = 'reference-stair-walking-clearance'
    provider = SequenceProvider([brief, candidate, audit])
    output = tmp_path / 'retry' / branch
    if used == 32:
        with pytest.raises(GenerationBudgetExceeded):
            harness.execute(case=case, output=output, provider_factory=lambda: provider, prior_budget=prior_budget)
        assert not provider.calls
        assert not list(output.rglob('*.ifc'))
        assert harness.read(output / 'execution.json')['budget_after']['calls_used'] == used
    else:
        result = harness.execute(case=case, output=output, provider_factory=lambda: provider,
                                 prior_budget=prior_budget if used else None)
        assert result['status'] == 'compiled', result
        assert result['reused_design_brief'] is False
        assert len(provider.calls) == 3
        assert result['budget_before']['calls_used'] == used
        assert result['budget_after']['calls_used'] == used + 3
        assert ifcopenshell.open(str(Path(result['run_dir']) / 'output.ifc')).schema == 'IFC2X3'
    assert {p.relative_to(parent): p.read_bytes() for p in parent.rglob('*') if p.is_file()} == frozen


def test_unsettled_previous_attempt_blocks_before_provider(tmp_path):
    harness = load_harness()
    case = tmp_path / 'A-revise'
    case.mkdir()
    harness.write(case / 'conversation.json', [{'turn_id': 'one', 'role': 'user', 'content': '离线输入'}])
    prior = tmp_path / 'previous-budget.json'
    harness.write(prior, {'limits': {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600},
                         'attempts': [{'status': 'reserved'}]})
    frozen = prior.read_bytes()
    provider = SequenceProvider([])
    with pytest.raises(ValueError, match='Unsettled prior budget'):
        harness.execute(case=case, output=tmp_path / 'out', provider_factory=lambda: provider, prior_budget=prior)
    assert not provider.calls and prior.read_bytes() == frozen


def test_cli_honors_new_hold_before_reading_admission_or_credentials(tmp_path, monkeypatch):
    harness = load_harness()
    harness.write(tmp_path / 'RUN-HOLD.json', {'status': 'hold'})
    monkeypatch.setattr(harness, 'COLLECTION', tmp_path)
    monkeypatch.setattr('sys.argv', ['run_branches.py', 'B-retain', '--live'])
    with pytest.raises(SystemExit, match='Active run hold'):
        harness.main()
    assert list(tmp_path.iterdir()) == [tmp_path / 'RUN-HOLD.json']
