"""Rebind an approved C clarification; product and evaluator code unchanged."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=OUT.parent/'c-shaped-integrated-20260911/admission.json'
parent=read(parent_path)
for p,h in parent['files_sha256'].items():assert sha(ROOT/p)==h,p
for p,v in parent['dependencies'].items():assert importlib.metadata.version(p)==v,p
rows=list(ET.parse(ROOT/'.tmp/c-entry-green.xml').getroot().iter('testcase'))
assert len(rows)==4 and all(not any(n.tag in {'error','failure','skipped'} for n in r) for r in rows)
negative=read(OUT/'entry-negative-control.json')
assert negative['status']=='failed' and negative['failed']==['all_doors_match']
diagnosis=OUT.parent/'c-shaped-integrated-20260911/failure-diagnosis.json'
assert read(diagnosis)['network_calls']==0 and read(diagnosis)['source_unchanged']
validation=OUT/'validation';validation.mkdir(exist_ok=True)
for name in ['c-entry-green','c-entry-red']:shutil.copyfile(ROOT/'.tmp'/(name+'.xml'),validation/(name+'.xml'))
bound=dict(parent['files_sha256'])
for p in [diagnosis,ROOT/'tests/agent/test_c_clarified_entry_run.py',OUT.parent/'c-shaped-integrated-20260911/live-run/runs/cf0a6e858a2a74a8/generation-budget.json']:
    bound[p.relative_to(ROOT).as_posix()]=sha(p)
for p in OUT.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts and p.name!='admission.json':bound[p.relative_to(ROOT).as_posix()]=sha(p)
scan=scan_path(OUT);assert scan['finding_count']==0
result={'status':'admitted','scope':'Same admitted Generation pipeline and Prompt; genuine user clarification changes only entry center. Four exact-runner/public-chain checks, independent old-entry negative control and malformed-output replay supplement the inherited 64/3/246 checks. No new product behavior.',
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'parent_admission':parent_path.relative_to(ROOT).as_posix(),'parent_sha256':sha(parent_path),
    'dependencies':parent['dependencies'],'files_sha256':bound,'checks':{'exact_runner':4,'old_entry_expected_rejection':True,'malformed_replay_blocked':True},
    'artifact_scan':scan,'full_preflight':False,'transport_attempted':False,
    'limitations':'C is a known case; no statistical quality improvement claim. Old syntax-invalid attempt remains invalid. Original request plus actual clarification are the input authority.'}
with (OUT/'admission.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'admitted','bindings':len(bound),'additional_checks':result['checks']}))
