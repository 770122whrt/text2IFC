"""Counterfactuals on copies: no Provider, no published IFC, no runtime edits."""
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

root = next(p for p in Path(__file__).resolve().parents if (p / 'pyproject.toml').is_file())
sys.path.insert(0, str(root / 'src'))
from text2ifc_agent.changeset_apply import apply_changeset
from text2ifc_agent.changesets import validate_changeset
from text2ifc_agent.semantic_requirements import bind_semantic_targets, unauthorized_candidate_semantics
from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_contract.validation_v2 import validate_v2_document

base = root / 'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910'
run = base / 'A-revise/runtime/runs/48dcf264b1a6df16'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = ['candidate.json', 'expected-facts.json', 'request-semantics.json',
         'changeset-round-01/change-scope.json', 'changeset-round-01/base-revision.json',
         'generator/prompt-rendered.md', 'generator/prompt-render-input.json']
before = {p: sha(run / p) for p in paths}
candidate, expected, request = [load(run / p) for p in paths[:3]]
scope = load(run / paths[3])
revision = load(run / paths[4])
bound = bind_semantic_targets(candidate, request)
unauthorized = unauthorized_candidate_semantics(candidate, bound['expectations'])
targets = sorted({i['path'].split('/')[2] for i in unauthorized if i['code'] == 'UNREQUESTED_MATERIAL'})
assert len(targets) == 18
index = build_candidate_index(candidate)
material_refs = load(base / 'A-revise/offline-failure-diagnosis.json')['material_issue_refs']
issue_for = {eid: next(r['issue_id'] for r in material_refs if r['actual_ref'] == f'entity:{eid}#/attributes') for eid in targets}
changeset = {'schema_version': 'text2ifc/bim-json-changeset/1.0',
             'changeset_id': 'diagnostic-clear-materials',
             'base_revision_id': revision['revision_id'], 'base_candidate_hash': revision['candidate_hash'],
             'expected_facts_hash': revision['expected_facts_hash'],
             'source_issue_ids': scope['source_issue_ids'], 'scope_id': scope['scope_id'],
             'operations': [{'operation_id': f'clear-{n}', 'op': 'update_entity', 'target_id': eid,
                             'target_component_hash': index['component_hashes'][eid],
                             'changes': {'/materials': []},
                             'evidence_refs': [f"{issue_for[eid]}:/entities/{eid}/materials"]}
                            for n, eid in enumerate(targets, 1)]}
schema_issues = validate_changeset(changeset)
assert not schema_issues, schema_issues
old = apply_changeset(candidate=candidate, changeset=changeset, scope=scope,
                      base_revision=revision, expected_facts=expected)
assert not old['valid'] and any(i['code'] == 'CHANGESET_SCOPE_VIOLATION' for i in old['issues'])
precise = copy.deepcopy(scope)
for target in targets:
    precise['allowed_paths'][target] = ['/materials']
new = apply_changeset(candidate=candidate, changeset=changeset, scope=precise,
                      base_revision=revision, expected_facts=expected)
assert new['valid'], new['issues']
assert not validate_v2_document(new['candidate'])
assert not unauthorized_candidate_semantics(new['candidate'], bound['expectations'])
after_index = build_candidate_index(new['candidate'])
changed = [eid for eid, digest in index['component_hashes'].items()
           if digest != after_index['component_hashes'][eid]]
assert sorted(changed) == targets
assert candidate == load(run / 'candidate.json')
prompt = (run / 'generator/prompt-rendered.md').read_text(encoding='utf-8')
inputs = load(run / 'generator/prompt-render-input.json')
contract_keys = [k for k in inputs if 'CONTRACT' in k]
types = [e for e in candidate['entities'] if e['ifc_class'].endswith(('Type', 'Style'))]
material_expectations = [e for e in bound['expectations'] if e['kind'] == 'material']
rows = []
rels = [r for r in candidate['relationships'] if r['ifc_class'] == 'IfcRelDefinesByType']
for target in targets:
    instances = [i for r in rels if r['attributes']['RelatingType'] == target for i in r['attributes']['RelatedObjects']]
    rows.append({'type_id': target, 'type_materials': index['entities'][target]['materials'],
                 'instances': [{'id': i, 'materials': index['entities'][i].get('materials', [])} for i in instances]})
assert before == {p: sha(run / p) for p in paths}
report = {'scope': 'diagnostic hand-authored ChangeSet against preserved live candidate; not Provider output or accepted model',
          'source_hashes_unchanged': before, 'generator_input_keys': list(inputs),
          'authoring_contract_input_keys': contract_keys,
          'explicit_no_unrequested_type_instruction_present': '未请求 Type 时不生成额外 Type 或 Style' in prompt,
          'contract_no_type_instruction_present': 'No requested Type means omit explicit Type/Style entities and associations.' in prompt,
          'material_expectation_scopes': dict(Counter(e['scope'] for e in material_expectations)),
          'type_expectation_count': sum(e['kind'] == 'type' for e in bound['expectations']),
          'candidate_type_counts': dict(Counter(e['ifc_class'] for e in types)), 'duplicated_material_rows': rows,
          'changeset_schema_valid': not schema_issues,
          'old_scope_result': {'valid': old['valid'], 'issue_codes': dict(Counter(i['code'] for i in old['issues']))},
          'precise_scope_result': {'valid': new['valid'], 'changed_components': changed,
                                   'unrelated_component_drift': False, 'remaining_unauthorized_semantics': 0},
          'remaining_type_entities_after_material_only_repair': len(types),
          'limits': 'No compiler/IFC test in this probe. Material-only repair does not remove unrequested Type entities; it isolates field-scope and schema feasibility, not full product compliance.'}
out = Path(sys.argv[1]) if len(sys.argv) > 1 else base / 'A-revise/pipeline-localization.json'
with out.open('x', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(json.dumps({k: report[k] for k in ['explicit_no_unrequested_type_instruction_present', 'contract_no_type_instruction_present',
                                      'type_expectation_count', 'candidate_type_counts', 'changeset_schema_valid',
                                      'old_scope_result', 'precise_scope_result']}, ensure_ascii=False))
