"""Offline continuation harness: public compile/reopen and preserved budget."""
import importlib.util
import json
from pathlib import Path

import ifcopenshell
import pytest

from tests.agent.test_design_review_audit import _audit
from tests.agent.test_interactive_cli_generation import PHASE6_1_COMPLETE, _write_ready_design_brief_call
from tests.agent.test_phase6_5_staged_generation import SequenceProvider

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/continue_branches.py'
spec = importlib.util.spec_from_file_location('branch_continuation_harness', SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


@pytest.mark.parametrize('branch,used', [('A-revise', 4), ('B-retain', 0), ('A-revise', 6)])
def test_continuation_public_path_preserves_parent_and_cumulative_budget(tmp_path, branch, used):
    parent = tmp_path / 'parent'
    _write_ready_design_brief_call(parent)
    call = parent / 'calls/01-design-brief'
    turns = harness.read(call / 'conversation.json')
    turns.append({'turn_id': 'turn-authorized', 'role': 'user', 'content': '按已确认的决定建模并记录局限。'})
    harness.write(call / 'conversation.json', turns)
    brief = harness.read(call / 'design-brief.json')
    brief['schema_version'] = 'text2ifc/design-brief/2.1'
    harness.write(call / 'design-brief.json', brief)
    harness.write(parent / 'generation-budget.json', {
        'schema_version': 'text2ifc/generation-budget/1.0',
        'limits': {'max_calls': 6, 'max_tokens': 800000, 'max_active_seconds': 1800},
        'attempts': [{'attempt': i + 1, 'stage': 'offline-previous', 'status': 'completed',
                      'tokens_charged': 10, 'elapsed_seconds': 1} for i in range(used)]})
    frozen = {p.relative_to(parent).as_posix(): p.read_bytes() for p in parent.rglob('*') if p.is_file()}
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
    provider = SequenceProvider(([brief] if branch == 'B-retain' else []) + [candidate, audit])
    output = tmp_path / 'continuation' / branch
    result = harness.execute(case=case, output=output, provider_factory=lambda: provider,
                             prior_run=parent if branch == 'A-revise' else None)
    assert {p.relative_to(parent).as_posix(): p.read_bytes() for p in parent.rglob('*') if p.is_file()} == frozen
    run = Path(result['run_dir'])
    if used == 6:
        assert result['status'] == 'budget_blocked'
        assert provider.calls == []
        assert not (run / 'output.ifc').exists()
    else:
        assert result['status'] == 'compiled', result
        assert len(provider.calls) == (2 if used else 3)
        assert ifcopenshell.open(str(run / 'output.ifc')).schema == 'IFC2X3'
        assert result['budget_after']['calls_used'] == (6 if used else 3)
        assert '合理性问题与用户决定' in (run / 'report.md').read_text(encoding='utf-8')
    with pytest.raises(FileExistsError):
        harness.execute(case=case, output=output, provider_factory=lambda: provider)
