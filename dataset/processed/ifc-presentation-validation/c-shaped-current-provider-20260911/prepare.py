"""Scoped revalidation after the committed cross-storey name fix."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
PARENT=OUT.parent/'c-shaped-plan-constraints-20260911'
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

parent=read(PARENT/'admission.json')
changes={p:[h,sha(ROOT/p)] for p,h in parent['files_sha256'].items() if sha(ROOT/p)!=h}
assert set(changes)=={'src/text2ifc_agent/dynamic_gates.py','tests/agent/test_cross_storey_name_boundary.py','docs/architecture/semantic-appearance-plan.md'}
assert sha(ROOT/'src/text2ifc_agent/dynamic_gates.py')==read(PARENT/'name-candidate.json')['module_sha256']
for package,version in parent['dependencies'].items():assert importlib.metadata.version(package)==version
assert not subprocess.check_output(['git','diff','35813a00','--','src/text2ifc_agent','tests/agent'],cwd=ROOT)
validation=OUT/'validation';validation.mkdir()
checks=[(PARENT/'validation/name-context-final.xml',99),(ROOT/'.tmp/c-current-runner.xml',2)]
for path,count in checks:
    cases=list(ET.parse(path).getroot().iter('testcase'))
    assert len(cases)==count and not any(n.tag in {'error','failure','skipped'} for c in cases for n in c)
    shutil.copyfile(path,validation/path.name)
ledger=PARENT/'live-run/runs/defec36086974f4b/generation-budget.json';budget=read(ledger)
assert len(budget['attempts'])==17 and sum(a['tokens_charged'] for a in budget['attempts'])==1377030
preview={'purpose':'Fresh full C Generation/Audit loop on current committed name-gate fix, at explicit user request.',
    'destination':'https://api.deepseek.com','model':'deepseek-v4-flash','limits':budget['limits'],
    'request':(SOURCE/'request.txt').read_text(encoding='utf-8'),'conversation':read(SOURCE/'conversation.json'),
    'allowed_followup_data':['new Design Brief','new candidate JSON','production checks and public feedback','runtime metadata'],
    'excluded':['old IFC or old candidate/Brief','independent evaluator or expected values','Gold','A/B evidence','credentials'],
    'previous_ledger_sha256':sha(ledger),'prior_calls':17,'prior_tokens':1377030,
    'max_completion_tokens':65536,'full_preflight':False}
write(OUT/'payload-preview.json',preview)
write(OUT/'authorization.json',{'status':'approved','basis':'Latest explicit user request to call Provider and deliver a newly generated IFC, plus existing C input/destination/budget authorization.',
    'destination':preview['destination'],'model':preview['model'],'limits':budget['limits'],
    'request_sha256':sha(SOURCE/'request.txt'),'payload_preview_sha256':sha(OUT/'payload-preview.json')})
bound={p:sha(ROOT/p) for p in parent['files_sha256']}
for p in [PARENT/'name-candidate.json',PARENT/'name-baseline.json',ledger,ROOT/'tests/agent/test_storey_name_context.py',
          *[p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]]:
    bound[p.relative_to(ROOT).as_posix()]=sha(p)
scan=scan_path(OUT);assert scan['finding_count']==0
write(OUT/'admission.json',{'status':'admitted','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'scope':'Scoped name-gate revalidation: 99 related tests include both public generation strategies and independent IFC checks; exact latest-ledger runner additionally tests full compile and invalid-output stop. All other stage safety bindings inherited unchanged.',
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'parent_admission':(PARENT/'admission.json').relative_to(ROOT).as_posix(),
    'parent_sha256':sha(PARENT/'admission.json'),'dependencies':parent['dependencies'],'files_sha256':bound,
    'changed_bindings':changes,'new_tests':2,'inherited_scoped_tests':99,'full_preflight':False,'transport_attempted':False,'scan':scan})
print(json.dumps({'status':'admitted','bindings':len(bound),'new_tests':2,'name_fix_regression':99}))
