"""Scoped supplement to the existing Generation stage; no new request or budget."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent;SOURCE=OUT.parent;ROOT=OUT.parents[4]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(path):return json.loads(path.read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf8') as handle:json.dump(value,handle,ensure_ascii=False,indent=2)

parent=read(SOURCE/'admission.json')
allowed=set(subprocess.check_output(['git','diff','--name-only','d2a62b76..e390c046','--','src','prompts','schemas'],cwd=ROOT,text=True).splitlines())
bound={};changed={}
for path,old in parent['files_sha256'].items():
    if not path.startswith(('src/','schemas/','prompts/','scripts/agent/')):continue
    current=sha(ROOT/path)
    if current!=old:
        assert path in allowed,('unvalidated production change',path)
        changed[path]={'prior':old,'current':current}
    bound[path]=current
for path in allowed:bound[path]=sha(ROOT/path)
for package,version in parent['dependencies'].items():assert importlib.metadata.version(package)==version,package
checks={}
for path in [*(SOURCE/n for n in ['scoped-complete.xml','public.xml','public-final.xml','regression2.xml']),OUT/'runner.xml']:
    cases=list(ET.parse(path).getroot().iter('testcase'))
    assert cases and not any(n.tag in {'failure','error','skipped'} for c in cases for n in c),path
    checks[path.relative_to(ROOT).as_posix()]={'passed':len(cases),'sha256':sha(path)}
ledger=SOURCE/'live-run/runs/a06665c5f155025f/generation-budget.json'
prior=read(ledger)
assert len(prior['attempts'])==1 and sum(a['tokens_charged'] for a in prior['attempts'])==71204
assert sum(a['elapsed_seconds'] for a in prior['attempts'])==177.125
assert not any(a['status']=='reserved' for a in prior['attempts'])
authorization=read(SOURCE/'authorization.json');assert authorization['status']=='approved'
assert authorization['request_sha256']==sha(SOURCE/'request.txt')
preview=read(SOURCE/'payload-preview.json')
preview.update(purpose='Same courtyard request after scoped role/recovery/roof projection fixes; a new complete public Generation/Audit loop inheriting the first attempt budget.',
    fresh_budget=False,previous_budget_sha256=sha(ledger),prompt='design-brief.v2.16')
write(OUT/'payload-preview.json',preview)
authorization.update(basis='Existing courtyard destination/payload approval plus latest explicit instruction: git和push；继续完成光庭的IFC生成 开启goal模式. Same input, destination, model and cumulative limits.',
    payload_preview_sha256=sha(OUT/'payload-preview.json'),previous_authorization_sha256=sha(SOURCE/'authorization.json'))
write(OUT/'authorization.json',authorization)
assert subprocess.run([sys.executable,'-m','compileall','-q','src/text2ifc_agent','src/text2ifc_quality',str(OUT.relative_to(ROOT))],cwd=ROOT).returncode==0
assert subprocess.run(['git','diff','--check','--','src','tests','prompts','schemas'],cwd=ROOT).returncode==0
for path in [SOURCE/'admission.json',SOURCE/'request.txt',SOURCE/'authorization.json',ledger,
    *(OUT/n for n in ['run_case.py','test_runner.py','prepare_admission.py','runner.xml','authorization.json','payload-preview.json']),
    *(ROOT/p for p in checks)]:bound[path.relative_to(ROOT).as_posix()]=sha(path)
# Freeze the independent checker locally; it is excluded from Provider render inputs.
bound[(SOURCE/'check_ifc.py').relative_to(ROOT).as_posix()]=sha(SOURCE/'check_ifc.py')
scan=scan_path(OUT);assert scan['finding_count']==0,scan
write(OUT/'admission.json',{'status':'admitted','scope':'Scoped supplement within Generation Brief2.4/public legacy_full stage. Inherited unchanged stage safety tests; changed semantic role/recovery/roof paths, both strategies and exact inherited-budget public runner checked offline.',
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'parent_admission':(SOURCE/'admission.json').relative_to(ROOT).as_posix(),'parent_sha256':sha(SOURCE/'admission.json'),
    'dependencies':parent['dependencies'],'files_sha256':bound,'changed_bindings':changed,'checks':checks,
    'full_preflight':False,'network_transport_attempted':False,'scan':scan,
    'limitations':['Focused tests overlap; no aggregate capability score.','C fixture in runner test is fake and does not prove courtyard success.','This is a disclosed development retry, not unseen validation.']})
print(json.dumps({'status':'admitted','changed_production_bindings':len(changed),'checks':checks,'prior_calls':1,'prior_tokens':71204}))
