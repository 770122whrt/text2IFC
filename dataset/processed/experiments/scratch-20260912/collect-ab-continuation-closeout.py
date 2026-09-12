from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910')
OUT = BASE / 'continuation-20260910'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


a = read(OUT / 'A-revise/execution.json')
b = read(OUT / 'B-retain/execution.json')
arun = OUT / 'A-revise/runtime/runs' / a['session_hash']
brun = OUT / 'B-retain/runtime/runs' / b['session_hash']
original = BASE.parent / 'three-storey-human-review-20260909/generated.ifc'
original_sha = '756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63'
assert digest(original) == original_sha
historical = read(BASE / 'LIVE-ATTEMPT-FILES.json')['files']
changed = [x['path'] for x in historical if not (BASE/x['path']).is_file() or digest(BASE/x['path']) != x['sha256']]
assert not changed, changed
assert a['budget_after']['calls_used'] == b['budget_after']['calls_used'] == 6
assert all(x['status'] != 'reserved' for e in [a,b] for x in e['budget_after']['attempts'])
assert not list(arun.rglob('*.ifc'))

source_ifc = brun / 'output.ifc'
check = read(OUT / 'B-retain/independent-ifc-check-final.json')
clearance = read(OUT / 'B-retain/clearance-check-final.json')
mesh = read(OUT / 'B-retain/views/overall-mesh.json')
candidate_sha = digest(source_ifc)
assert candidate_sha == check['ifc_sha256'] == clearance['ifc_sha256'] == mesh['source_sha256']
assert len(check['checks']) == 290 and all(check['checks'].values()) and not check['failed']
assert len(mesh['products']) == 40 and not mesh['mesh_failures']
candidate_copy = OUT / 'B-retain/candidate.ifc'
assert not candidate_copy.exists()
shutil.copyfile(source_ifc, candidate_copy)
assert digest(candidate_copy) == candidate_sha

candidate = read(brun / 'generator/candidate.json')
expected = read(brun / 'semantic-geometry-expectation.json')
feedback = read(brun / 'geometry-feedback.json')
assert Counter(x['code'] for x in feedback['issues']) == {'MISSING_STAIR_OPENING': 2, 'MISSING_STAIR_FLIGHT': 2}
assert not read(brun / 'semantic-verification.json')['issues']
write(OUT / 'B-retain/identity-diagnosis.json', {
    'role': 'post-run read-only identity comparison, not a gate override or provider output',
    'session_hash': b['session_hash'],
    'inputs': {x: digest(brun/x) for x in ['generator/candidate.json', 'semantic-geometry-expectation.json', 'geometry-feedback.json']},
    'expected_stairs': expected['stairs'],
    'expected_floor_openings': expected['floor_openings'],
    'candidate_stairs_and_flights': [{'id': e['id'], 'ifc_class': e['ifc_class'], 'name': e.get('attributes',{}).get('Name')} for e in candidate['entities'] if e['ifc_class'] in {'IfcStair', 'IfcStairFlight'}],
    'candidate_floor_openings': [{'id': e['id'], 'ifc_class': e['ifc_class']} for e in candidate['entities'] if e['ifc_class'] == 'IfcOpeningElement' and 'floor-slab' in e['id']],
    'candidate_stair_aggregates_and_slab_voids': [e for e in candidate['relationships'] if e['id'].startswith('aggregate-stair') or e['id'].startswith('void-floor-slab')],
    'production_issues': feedback['issues'],
    'independent_ifc_check': '../B-retain/independent-ifc-check-final.json',
    'assessment': 'Identity obligations do not match candidate IDs. Physical/request checks do not establish the strict identity contract. Localize Brief identity roles, deterministic child derivation and Generator identity preservation before changing gates.'
})

round2 = brun / 'changeset-round-02'
assert not (round2/'response.raw.json').exists()
write(OUT / 'B-retain/failure-observation.json', {
    'role': 'post-run Codex observation; not raw provider evidence',
    'observed_execution_exception': 'OpenAICompatError',
    'observed_terminal_message': 'OpenAI-compatible chat completion is truncated: finish_reason=length',
    'observation_source': 'execution tool traceback during this authorized run; traceback was not written into run.log',
    'run_log_size_bytes': (OUT/'B-retain/run.log').stat().st_size,
    'independently_persisted_evidence': ['execution.json: exception_type and failed budget attempt 6', 'runtime/runs/51592773914118fb/changeset-round-02/: pre-call inputs'],
    'available_attempt_inputs': [{'path': p.relative_to(OUT/'B-retain').as_posix(), 'sha256': digest(p)} for p in sorted(round2.iterdir()) if p.is_file()],
    'unavailable': ['raw response body', 'response id', 'provider-reported usage'],
    'actual_usage': None,
    'usage_status': 'unknown; no reconstructed or fabricated provider values',
    'budget_charge_kind': 'conservative original reservation, not reported usage',
    'budget_tokens_charged': b['budget_after']['attempts'][-1]['tokens_charged'],
    'diagnosed_boundary': 'OpenAI-compatible parser carries evidence in its truncation exception; ChangeSet stage does not persist it before the harness records only exception_type and re-raises.',
    'backfill_performed': False,
})

write(OUT / 'RUN-HOLD.json', {
    'status': 'suspended',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'role': 'post-run operational suspension; admission.json remains the frozen pre-run state',
    'blocked_actions': ['further A/B provider transport', 'acceptance or Proof registration as successful output'],
    'reasons': ['A and B each used their cumulative 6-call limit', 'B parent/child stair and opening identity disagreement remains unresolved', 'B truncated ChangeSet response body and usage were not persisted'],
    'remaining_calls': {'A-revise': 0, 'B-retain': 0},
    'required_before_retry': ['offline red-capable failure families and fixes for the applicable shared defects', 'scoped admission revalidation; do not escalate to Full Preflight automatically', 'explicit additional provider budget'],
    'github_push_authorized': False,
    'proof_registered': False,
    'human_acceptance': 'not accepted for these new outputs',
})

support = OUT / 'support'
support.mkdir(exist_ok=True)
prep_source = Path('.tmp/prepare-branch-continuation-admission.py')
prep_hash = read(OUT/'admission.json')['files_sha256'][prep_source.as_posix()]
assert digest(prep_source) == prep_hash
prep_copy = support / prep_source.name
assert not prep_copy.exists()
shutil.copyfile(prep_source, prep_copy)
assert digest(prep_copy) == prep_hash
write(support/'source-mirrors.json', {'role': 'byte-identical durable mirror; frozen admission paths are not rewritten', 'files': [{'original_path': prep_source.as_posix(), 'mirror_path': prep_copy.relative_to(OUT).as_posix(), 'sha256': prep_hash}]})

def response_ids(root):
    found = {}
    for p in root.rglob('response-metadata.json'):
        x = read(p)
        rid = x.get('response_id')
        if rid:
            found.setdefault(rid, []).append(p.relative_to(OUT).as_posix())
    return found

write(OUT/'closeout-check.json', {
    'role': 'post-run factual closeout, not acceptance or capability evaluation',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'code_head_at_execution': read(OUT/'admission.json')['head'],
    'historical_files_checked': len(historical),
    'historical_files_changed': changed,
    'reference_ifc': {'path': original.as_posix(), 'sha256': original_sha, 'unchanged': True},
    'requests_equal_original_sha256': all(digest(BASE/branch/'request.txt') == '2046a23ec544596aead827abe9ef734aa118694f9af6c8bc20c2649b9a2f818e' for branch in ['A-revise','B-retain']),
    'new_provider_attempts': 8,
    'A': {'session_hash': a['session_hash'], 'execution_status': a['status'], 'new_provider_attempts': 2, 'inherited_provider_attempts': 4, 'budget': a['budget_after'], 'ifc_available': False, 'saved_response_metadata': response_ids(arun), 'copied_brief_is_not_a_new_call': True},
    'B': {'session_hash': b['session_hash'], 'execution_status': b['status'], 'new_provider_attempts': 6, 'known_reported_tokens_first_five': sum(t['tokens_charged'] for t in b['budget_after']['attempts'][:5]), 'last_reported_usage_status': 'unknown; conservative budget reservation charged', 'budget': b['budget_after'], 'saved_response_metadata': response_ids(brun), 'candidate_role': 'diagnostic only; not final published or accepted IFC', 'candidate_ifc_sha256': candidate_sha, 'independent_request_checks_passed': len(check['checks']), 'production_geometry_issue_counts': dict(Counter(x['code'] for x in feedback['issues'])), 'mesh_products': len(mesh['products']), 'mesh_failures': mesh['mesh_failures'], 'clearance_sample_count': clearance['sample_count'], 'minimum_sampled_gap_m': clearance['minimum_sampled_gap_m'], 'zero_gap_count': clearance['zero_gap_count']},
    'full_preflight_run': False,
    'accepted_proof_curator_run': False,
    'proof_registered': False,
    'human_review_status': 'pending, diagnostic candidate only',
    'visual_check': 'Codex inspected four actual IFC mesh renderings; coordinated colors and basic box geometry; no fancy/publication-ready claim',
    'render_environment': 'IFC export used repository .venv; PNG rendering of exported JSON meshes used bundled Python 26.905.11957 after repository .venv lacked PIL; no production environment changes',
    'github_push_performed': False,
})
print(json.dumps({'historical_files_checked': len(historical), 'changed': changed, 'candidate_sha256': candidate_sha, 'new_provider_attempts': 8, 'status': 'closed with hold'}, indent=2))
