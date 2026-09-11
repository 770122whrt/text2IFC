"""Scoped extension of existing Generation admission; never calls a Provider."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

parent_path = OUT.parent/'audit-token-pair-20260911/admission.json'
parent = json.loads(parent_path.read_text(encoding='utf-8'))
allowed = {'prompts/agent/registry.json', 'src/text2ifc_agent/design_brief.py',
           'src/text2ifc_agent/interactive_cli_flow.py', 'tests/agent/test_design_review_audit.py',
           'docs/architecture/semantic-appearance-plan.md', 'docs/architecture/token-efficiency-plan.md'}
changed = [p for p,h in parent['files_sha256'].items() if sha(ROOT/p) != h]
assert set(changed) <= allowed, changed
for name, version in parent['dependencies'].items():
    assert importlib.metadata.version(name) == version
checks = []
for name in ['space-opening-green', 'c-integrated-green', 'c-integrated-regression']:
    source = ROOT/'.tmp'/(name+'.xml')
    rows = list(ET.parse(source).getroot().iter('testcase'))
    assert rows and all(not any(n.tag in {'failure','error','skipped'} for n in r) for r in rows), name
    target = OUT/'validation'/(name+'.xml')
    shutil.copyfile(source, target)
    checks.append({'name':name, 'tests':len(rows), 'failures':0, 'errors':0, 'skipped':0,
                   'path':target.relative_to(ROOT).as_posix(), 'sha256':sha(target)})
assert next(c['tests'] for c in checks if c['name']=='space-opening-green') == 64
assert next(c['tests'] for c in checks if c['name']=='c-integrated-green') == 3
bound = {p:sha(ROOT/p) for p in parent['files_sha256']}
extra = ['prompts/agent/design-brief-v2.10.md','prompts/agent/design-brief-v2.11.md',
         'tests/agent/test_brief_space_opening_scope.py','tests/agent/test_c_integrated_run.py',
         'docs/validation/brief-space-opening/family.json']
for p in extra:
    bound[p] = sha(ROOT/p)
for p in OUT.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts and p.name != 'admission.json':
        bound[p.relative_to(ROOT).as_posix()] = sha(p)
scan = scan_path(OUT)
assert scan['finding_count'] == 0
result = {'status':'admitted', 'stage':'Existing C Generation loop; Brief prompt scope correction',
          'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
          'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'parent_admission':parent_path.relative_to(ROOT).as_posix(), 'parent_sha256':sha(parent_path),
          'scope':'Reuse inherited Generation full-chain and frozen C checker evidence; new Prompt scope, review-context guard and exact continuation runner revalidated offline through public APIs. Audit representation shadow requires a later input-specific binding before transport.',
          'changed_bindings':changed, 'checks':checks, 'dependencies':parent['dependencies'],
          'files_sha256':bound, 'artifact_scan':scan, 'full_preflight':False,
          'transport_attempted':False,
          'limitations':'Offline fixture is hand-authored fake, not live generation. C is already seen; no capability or statistical quality claim. Public API signatures, schema, compiler, acceptance and truth boundaries unchanged.',
          'invalidate_on':'Bound source, prompt, input, budget or dependency drift; failed applicable check; newly revealed deterministic defect.'}
with (OUT/'admission.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':checks,'bindings':len(bound)}))
