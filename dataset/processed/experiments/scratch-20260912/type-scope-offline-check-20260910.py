"""Read-only recheck of preserved A evidence; no provider, IFC output, or promotion."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.scoped_loop import resolve_issue_component_refs
from text2ifc_agent.semantic_requirements import unauthorized_candidate_semantics

root = Path(__file__).resolve().parents[1]
collection = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
run = collection / 'A-revise/runtime/runs/48dcf264b1a6df16'
diagnosis = json.loads((collection / 'A-revise/pipeline-localization.json').read_text(encoding='utf-8'))
frozen = diagnosis['source_hashes_unchanged']

def hashes():
    return {name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in frozen}

assert hashes() == frozen
candidate = json.loads((run / 'candidate.json').read_text(encoding='utf-8'))
expectations = json.loads((run / 'request-semantics.json').read_text(encoding='utf-8'))['expectations']
before_candidate = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
issues = unauthorized_candidate_semantics(candidate, expectations)
counts = dict(Counter(i['code'] for i in issues))
assert counts == {'UNREQUESTED_TYPE': 37, 'UNREQUESTED_TYPE_ASSIGNMENT': 37, 'UNREQUESTED_MATERIAL': 18}, counts
resolved = resolve_issue_component_refs(candidate=candidate, issues=normalize_gate_sidecars(run))
materials = [i for i in resolved['resolved'] if 'UNREQUESTED_MATERIAL' in i['evidence']]
material_refs = sorted({i['actual_ref'] for i in materials})
assert len(material_refs) == 18 and all(ref.endswith('#/materials') for ref in material_refs)
assert json.dumps(candidate, ensure_ascii=False, sort_keys=True) == before_candidate
assert hashes() == frozen
report = {
    'evidence_class': 'offline_read_only_regression_against_disclosed_failed_case',
    'candidate_diagnostic_counts': counts,
    'material_targets_with_exact_field': len(material_refs),
    'material_diagnostic_rows_across_gate_views': len(materials),
    'frozen_source_hashes_unchanged': frozen,
    'candidate_mutated': False,
    'provider_calls': 0,
    'ifc_created': False,
    'limits': 'Detects and scopes existing violations only; no Type deletion, stair-name fix, acceptance, or capability claim.'
}
output = root / '.tmp/type-scope-offline-check-20260910.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'frozen_source_hashes_unchanged'}, ensure_ascii=False))
