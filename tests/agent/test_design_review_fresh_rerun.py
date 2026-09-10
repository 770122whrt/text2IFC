"""Fresh A/B execution starts at Brief with one shared whole-run budget."""
import importlib.util
from pathlib import Path

import ifcopenshell
import pytest

from tests.agent.test_design_review_audit import _audit
from tests.agent.test_interactive_cli_generation import PHASE6_1_COMPLETE, _write_ready_design_brief_call
from tests.agent.test_phase6_5_staged_generation import SequenceProvider

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/rerun-20260910/run_branches.py'


@pytest.mark.parametrize('branch', ['A-revise', 'B-retain'])
def test_fresh_branches_compile_without_reusing_prior_brief_or_budget(tmp_path, branch):
    spec = importlib.util.spec_from_file_location('fresh_branch_harness', SCRIPT)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    prior = tmp_path / 'prior'
    _write_ready_design_brief_call(prior)
    call = prior / 'calls/01-design-brief'
    turns = harness.read(call / 'conversation.json')
    turns.append({'turn_id': 'turn-authorized', 'role': 'user', 'content': '按已确认的决定建模并记录局限。'})
    brief = harness.read(call / 'design-brief.json')
    brief['schema_version'] = 'text2ifc/design-brief/2.1'
    harness.write(prior / 'generation-budget.json', {'unusable_old_budget': True})
    frozen = {p.relative_to(prior): p.read_bytes() for p in prior.rglob('*') if p.is_file()}
    case = tmp_path / branch
    case.mkdir()
    harness.write(case / 'conversation.json', turns)
    harness.write(case / 'reference-review.json', {'source': 'offline fixture', 'gap_mm': 0})
    candidate = harness.read(PHASE6_1_COMPLETE / 'generator/candidate.json')
    candidate['schema_version'] = 'bim-json/2.1'
    for entity in candidate['entities']:
        entity['materials'], entity['property_sets'] = [], {}
    audit = _audit('not_verified' if branch == 'A-revise' else 'retained_known_issue')
    audit['design_review']['concerns'][0]['id'] = 'reference-stair-walking-clearance'
    provider = SequenceProvider([brief, candidate, audit])
    output = tmp_path / 'fresh' / branch
    result = harness.execute(case=case, output=output, provider_factory=lambda: provider)
    assert result['status'] == 'compiled', result
    assert result['reused_design_brief'] is False
    assert result['budget_before']['calls_used'] == 0
    assert result['budget_after']['calls_used'] == 3
    assert len(provider.calls) == 3
    assert result['limits'] == {'max_calls': 32, 'max_tokens': 2000000, 'max_active_seconds': 3600}
    run = Path(result['run_dir'])
    assert ifcopenshell.open(str(run / 'output.ifc')).schema == 'IFC2X3'
    assert '合理性问题与用户决定' in (run / 'report.md').read_text(encoding='utf-8')
    assert {p.relative_to(prior): p.read_bytes() for p in prior.rglob('*') if p.is_file()} == frozen
    with pytest.raises(FileExistsError):
        harness.execute(case=case, output=output, provider_factory=lambda: provider)
