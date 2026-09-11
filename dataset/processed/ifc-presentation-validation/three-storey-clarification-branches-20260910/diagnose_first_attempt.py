"""Offline reproduction; reads frozen live artifacts without changing them."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

base = Path(__file__).resolve().parent
root = base.parents[3]
sys.path[:0] = [str(root), str(root / 'src')]
from text2ifc_agent.issue_normalizers import normalize_gate_sidecars
from text2ifc_agent.change_scope import derive_change_scope
from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates

load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
execution = load(base / 'A-revise/execution.json')
runtime = root / execution['run_dir']
assert runtime.resolve().is_relative_to((base / 'A-revise').resolve())
candidate = load(runtime / 'candidate.json')
expected = load(runtime / 'expected-facts.json')
sources = [runtime / p for p in ['candidate.json', 'expected-facts.json', 'gate-summary.json',
                               'changeset-round-01/draft.json', 'generation-budget.json']]
before = {p.relative_to(root).as_posix(): sha(p) for p in sources}
issues = normalize_gate_sidecars(runtime)
material_issues = [i for i in issues if i.evidence.startswith('UNREQUESTED_MATERIAL:')]
scope_result = derive_change_scope(candidate=candidate, issues=material_issues,
                                  scope_id='offline-material-diagnosis', base_revision_id='revision-0')
assert scope_result['scope'] is not None, scope_result['issues']
scope = scope_result['scope']
rows = [{'issue_id': i.issue_id, 'actual_ref': i.actual_ref} for i in material_issues]
assert rows and all(i['actual_ref'].endswith('#/attributes') for i in rows)
assert all('/materials' not in scope['allowed_paths'][eid] for eid in scope['entity_ids'])
name_gate = next(g for g in evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
                 if g['name'] == 'dynamic_storey_name_consistency')
stairs = {s['id']: s for s in expected['stairs']}
name_rows = []
for issue in name_gate['issues']:
    stair = stairs.get(issue.get('entity_id'))
    if stair:
        name_rows.append({'entity_id': issue['entity_id'], 'name': issue['actual_name'],
                          'expected_from_storey': stair['from_storey'],
                          'expected_to_storey': stair['to_storey'],
                          'gate_ownership': issue['expected_storey'],
                          'gate_rejected_label_storey': issue['conflicting_storey'],
                          'destination_label_matches_request': issue['conflicting_storey'] == stair['to_storey']})
assert len(name_rows) == 2 and all(r['destination_label_matches_request'] for r in name_rows)

# Small synthetic family exercises the same public normalizer, not a live run.
family = []
with tempfile.TemporaryDirectory(prefix='design-scope-diagnosis-', dir=root / '.tmp') as scratch:
    scratch = Path(scratch)
    for entity_id, field in [('type-north', 'materials'), ('type-south', 'materials'),
                             ('wall-east', 'attributes/Name'), ('unknown-type', 'materials')]:
        known = entity_id != 'unknown-type'
        fixture = {'entities': [{'id': entity_id, 'ifc_class': 'IfcWallType', 'attributes': {}}] if known else []}
        (scratch / 'candidate.json').write_text(json.dumps(fixture), encoding='utf-8')
        (scratch / 'gate-summary.json').write_text(json.dumps({'overall_status': 'failed', 'gates': [{
            'name': 'fixture', 'status': 'failed', 'issues': [{'code': 'UNREQUESTED_MATERIAL' if field == 'materials' else 'STOREY_NAME_CONFLICT',
            'path': f'/entities/{entity_id}/{field}'}]}]}), encoding='utf-8')
        normalized = normalize_gate_sidecars(scratch)
        actual = normalized[0].actual_ref
        desired = f'entity:{entity_id}#/{field}' if known else f'/entities/{entity_id}/{field}'
        family.append({'entity_id': entity_id, 'known': known, 'source_field': field,
                       'desired_ref': desired, 'actual_ref': actual, 'desired_invariant_holds': actual == desired})
after = {p.relative_to(root).as_posix(): sha(p) for p in sources}
assert before == after
report = {'evidence_class': 'offline diagnosis of preserved real attempt plus synthetic boundary probes',
          'source_sha256': before, 'source_unchanged': before == after,
          'material_issue_count_including_duplicate_sidecars': len(material_issues),
          'material_target_count': len(scope['entity_ids']), 'material_issue_refs': rows,
          'material_scope': scope, 'cross_storey_name_false_positives': name_rows,
          'synthetic_path_family': family,
          'production_changed': False, 'provider_called_by_diagnosis': False,
          'limits': 'Reproduces scope truncation and endpoint-name false positives, not a fix or capability improvement.'}
output = Path(sys.argv[1])
with output.open('x', encoding='utf-8') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
print(json.dumps({'source_unchanged': report['source_unchanged'],
                  'material_targets': report['material_target_count'], 'stair_name_false_positives': len(name_rows),
                  'synthetic_expected_pass': sum(r['desired_invariant_holds'] for r in family),
                  'synthetic_expected_fail': sum(not r['desired_invariant_holds'] for r in family)}))
