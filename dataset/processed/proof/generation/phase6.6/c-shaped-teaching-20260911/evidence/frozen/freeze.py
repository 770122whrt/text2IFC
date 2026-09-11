"""Integrity checks and inventory for a new, pending-review live result."""
import hashlib
import json
from pathlib import Path
import re
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

usage=read(OUT/'usage-summary.json')
assert usage['status']=='compiled' and usage['new_actual_responses']>0
assert usage['new_input_tokens']+usage['new_output_tokens_including_reasoning']==usage['new_tokens_charged']
checked=read(OUT/'independent-ifc-check.json')
assert checked['status']=='passed' and checked['ifc_sha256']==sha(OUT/'generated.ifc')
for name in ['REPORT.md','CLARIFICATIONS.md']:
    for target in re.findall(r'\]\(([^)]+)\)',(OUT/name).read_text(encoding='utf-8')):
        assert (OUT/target.split('#')[0]).exists(),target
scan=scan_path(OUT)
extra=[scan_path(p) for p in OUT.rglob('*') if p.is_file() and p.suffix in {'.py','.ifc','.sqlite','.html','.xml'}]
assert scan['finding_count']==0 and all(x['finding_count']==0 for x in extra)
write(OUT/'artifact-validation.json',{'status':'passed','human_accepted':False,'proof_registered':False,
    'ifc_sha256':checked['ifc_sha256'],'independent_check_count':checked['check_count'],
    'scan':scan,'extra_scan_files':len(extra),'full_preflight':False,'validation_scope':'Current result integrity, native IFC fidelity, review links and existing secret-pattern scan.'})
files=sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='FILES.json')
write(OUT/'FILES.json',{'schema_version':'text2ifc/local-file-inventory/1.0','status':'pending_human_review_not_accepted_proof',
    'files':[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],
    'manifest_excludes_itself':True})
files.append(OUT/'FILES.json')
(ROOT/'.tmp/c-current-evidence-paths.txt').write_text('\n'.join(p.relative_to(ROOT).as_posix() for p in files)+'\n.planning/STATE.md\n',encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(p.stat().st_size for p in files),'scan_findings':0}))
