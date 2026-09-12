"""Supplement the existing stage with the pre-transport source-catalog guard."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent
PRIOR = SOURCE / 'rerun-01'
ROOT = OUT.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from text2ifc_agent.artifact_scan import scan_path
from text2ifc_agent.clarification import ClarificationController
from text2ifc_agent.design_brief import validate_design_brief


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


parent = read(PRIOR / 'admission.json')
allowed = {'src/text2ifc_agent/' + name for name in (
    'brief_conversation.py', 'live_pipeline.py', 'interactive_cli_flow.py',
    'brief_semantic_repair.py', 'brief_plan_repair.py')}
bound, changed = {}, {}
for path, old in parent['files_sha256'].items():
    current = sha(ROOT / path)
    if current != old:
        assert path in allowed, ('unexpected admission drift', path)
        changed[path] = {'prior': old, 'current': current}
    bound[path] = current
for path in allowed:
    bound[path] = sha(ROOT / path)
for package, version in parent['dependencies'].items():
    assert importlib.metadata.version(package) == version, package
checks = {}
for path in (PRIOR / 'conversation-green.xml', OUT / 'public.xml'):
    cases = list(ET.parse(path).getroot().iter('testcase'))
    assert cases and not any(n.tag in {'failure', 'error', 'skipped'} for c in cases for n in c), path
    checks[path.relative_to(ROOT).as_posix()] = {'passed': len(cases), 'sha256': sha(path)}
ledger = PRIOR / 'live-run/runs/0b57f15f4af1b7c7/generation-budget.json'
attempts = read(ledger)['attempts']
assert len(attempts) == 3 and sum(a['tokens_charged'] for a in attempts) == 222977
assert not any(a['status'] == 'reserved' for a in attempts)
request = (SOURCE / 'request.txt').read_text(encoding='utf-8')
turns = ClarificationController.start(case_id='offline-diagnosis', user_request=request).transcript_dicts()
old_stage = ledger.parent / 'calls/01-design-brief'
old_brief = read(old_stage / 'parsed-output.json')
catalog = read(old_stage / 'context-selection.json')['evidence']
def codes(conversation):
    return [i.code for i in validate_design_brief(old_brief, evidence_catalog=catalog,
        expected_schema_version='text2ifc/design-brief/2.4', conversation=conversation)]
before, after = codes(read(old_stage / 'conversation.json')), codes(turns)
assert before == ['SEMANTIC_AUTHORITY_SOURCE_INVALID'] * 5 and after == []
write(OUT / 'diagnosis-replay.json', {'evidence_class': 'offline_diagnostic_replay',
    'original_response_sha256': sha(old_stage / 'parsed-output.json'),
    'initial_codes': before, 'normal_controller_codes': after,
    'brief_bytes_changed': False, 'not_a_live_success': True})
preview = read(PRIOR / 'payload-preview.json')
preview.update(purpose='Same frozen courtyard request after input-catalog fix; fresh extraction through the existing controller transcript, then public Generation/Audit loop.',
    previous_budget_sha256=sha(ledger), fresh_budget=False,
    conversation=turns, inherited_calls=3, inherited_tokens=222977)
write(OUT / 'payload-preview.json', preview)
approval = read(PRIOR / 'authorization.json')
approval.update(basis='Explicit user approval: Provider 真实生成与GitHub证据包推送 批准进行. Same request/destination/model/cumulative budget; source-turn identifiers supplied by the existing production controller.',
    payload_preview_sha256=sha(OUT / 'payload-preview.json'),
    explicit_approval_path=(PRIOR / 'user-approval-20260912.json').relative_to(ROOT).as_posix(),
    previous_budget_sha256=sha(ledger))
assert approval['status'] == 'approved' and approval['request_sha256'] == sha(SOURCE / 'request.txt')
write(OUT / 'authorization.json', approval)
assert subprocess.run([sys.executable, '-m', 'compileall', '-q',
    *(str(ROOT / p) for p in allowed), str(OUT)], cwd=ROOT).returncode == 0
assert subprocess.run(['git', 'diff', '--check', '--', *sorted(allowed),
    'tests/agent/test_brief_conversation_boundary.py'], cwd=ROOT).returncode == 0
for p in [PRIOR / 'admission.json', PRIOR / 'user-approval-20260912.json', ledger,
    ROOT / 'tests/agent/test_brief_conversation_boundary.py',
    *(OUT / n for n in ('run_case.py', 'test_runner.py', 'prepare_admission.py',
        'public.xml', 'payload-preview.json', 'authorization.json', 'diagnosis-replay.json')),
    *(ROOT / p for p in checks)]:
    bound[p.relative_to(ROOT).as_posix()] = sha(p)
scan = scan_path(OUT)
assert scan['finding_count'] == 0, scan
write(OUT / 'admission.json', {'status': 'admitted',
    'scope': 'Scoped source-turn catalog guard at both public Brief seams and both bounded repair seams. Valid-input production behavior and Prompt/Schema bytes unchanged; exact runner tests cover inherited budget and both Generation strategies. Existing stage admission remains applicable.',
    'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'parent_admission': (PRIOR / 'admission.json').relative_to(ROOT).as_posix(),
    'parent_sha256': sha(PRIOR / 'admission.json'), 'dependencies': parent['dependencies'],
    'files_sha256': bound, 'changed_bindings': changed, 'checks': checks,
    'full_preflight': False, 'network_transport_attempted': False, 'scan': scan,
    'limitations': ['Disclosed same-case development retry, not unseen validation.',
        'Synthetic public-flow success does not prove the courtyard will succeed.',
        'Previous failures and reservations remain in the cumulative ledger.']})
print(json.dumps({'status': 'admitted', 'checks': checks, 'prior_calls': 3, 'prior_tokens': 222977}))
