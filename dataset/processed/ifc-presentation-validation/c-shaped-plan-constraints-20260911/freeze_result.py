"""Hash and check the new review bundle, without installing accepted Proof."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

for name,count in [('plan-final3',96),('name-context-final',99),('c-plan-public4',2)]:
    cases=list(ET.parse(OUT/'validation'/(name+'.xml')).getroot().iter('testcase'))
    assert len(cases)==count and not any(n.tag in {'failure','error','skipped'} for c in cases for n in c)
baseline=read(OUT/'name-baseline.json');candidate=read(OUT/'name-candidate.json')
for before,after in zip(baseline['rows'],candidate['rows']):
    assert before['sha256']==after['sha256'] and before['other_gates']==after['other_gates']
assert baseline['ifc_sha256']==candidate['ifc_sha256']==sha(OUT/'generated.ifc')
assert read(OUT/'independent-ifc-check.json')['status']=='passed'
source=OUT.parent/'c-shaped-clarified-entry-20260911'
assert sha(source/'request.txt')==sha(OUT/'request.txt')
assert sha(source/'conversation.json')==sha(OUT/'conversation.json')
for name in ['REPORT.md','CLARIFICATIONS.md']:
    report=OUT/name
    for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
        assert (report.parent/target.split('#')[0]).exists(),target
scan=scan_path(OUT)
extra=[scan_path(p) for p in OUT.rglob('*') if p.is_file() and p.suffix.lower() in {'.sqlite','.py','.xml','.html','.ifc'}]
assert scan['finding_count']==0 and all(s['finding_count']==0 for s in extra)
write(OUT/'artifact-validation.json',{'status':'passed','human_accepted':False,'proof_registered':False,
    'full_preflight':False,'validation_class':'scoped_artifact_integrity_and_request_fidelity',
    'core_scan':scan,'additional_scan_files':len(extra),'secret_pattern_findings':0,
    'view_mesh_failures':0,'ifc_sha256':sha(OUT/'generated.ifc'),
    'live_run_commit':'7fba0151','post_run_fix_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'post_run_live_calls':0,'historical_admission_not_reusable_after_name_fix':True,
    'known_limitation':'Pattern scan is not a proof that arbitrary private information is absent; explicit payload and source boundaries were separately preserved.'})
files=sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='FILES.json')
write(OUT/'FILES.json',{'schema_version':'text2ifc/local-file-inventory/1.0','status':'pending_human_review_not_accepted_proof',
    'files':[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],
    'manifest_excludes_itself':True})
files.append(OUT/'FILES.json')
paths=[p.relative_to(ROOT).as_posix() for p in files]+['.planning/STATE.md']
(ROOT/'.tmp/c-plan-evidence-paths.txt').write_text('\n'.join(paths)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(p.stat().st_size for p in files),'scan_findings':0,'pending_human_review':True}))
