"""Scoped revalidation of the existing C Generation stage; no transport."""
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
SOURCE=OUT.parent/'c-shaped-clarified-entry-20260911'
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

parent_path=SOURCE/'admission.json';parent=read(parent_path)
changed={p:(h,sha(ROOT/p)) for p,h in parent['files_sha256'].items() if sha(ROOT/p)!=h}
allowed={'prompts/agent/registry.json','src/text2ifc_agent/design_brief.py',
    'src/text2ifc_agent/gate_audit_bundle.py','src/text2ifc_agent/interactive_cli_flow.py',
    'src/text2ifc_agent/live_pipeline.py','src/text2ifc_agent/semantic_coverage.py',
    'tests/agent/test_design_review_audit.py','docs/architecture/semantic-appearance-plan.md',
    'docs/architecture/token-efficiency-plan.md'}
assert set(changed)<=allowed, set(changed)-allowed
for p,v in parent['dependencies'].items():assert importlib.metadata.version(p)==v,p
validation=OUT/'validation';validation.mkdir(exist_ok=True)
commands={
    'wall-prompt-green':64,'wall-public-paths':109,'c-wall-run-green':4,
    'c-gates-final':108,'c-scope-final':6,'c-gates-public':4}
for name,count in commands.items():
    p=ROOT/'.tmp'/(name+'.xml')
    rows=list(ET.parse(p).getroot().iter('testcase'))
    assert len(rows)==count and not any(n.tag in {'error','failure','skipped'} for r in rows for n in r),name
    shutil.copyfile(p,validation/p.name)
for name in ['wall-boundary-red','c-wall-run-red']:shutil.copyfile(ROOT/'.tmp'/(name+'.xml'),validation/(name+'.xml'))
ledger=SOURCE/'live-run/runs/9b00e53444a948e7/generation-budget.json';budget=read(ledger)
assert len(budget['attempts'])==8 and sum(a['tokens_charged'] for a in budget['attempts'])==583435
preview={'purpose':'Same approved C request/actual entry clarification, new wall-boundary Brief prompt, ordinary Generation/Audit/bounded correction loop.',
    'destination':'https://api.deepseek.com','model':'deepseek-v4-flash','limits':budget['limits'],
    'request':(SOURCE/'request.txt').read_text(encoding='utf-8'),'conversation':read(SOURCE/'conversation.json'),
    'allowed_followup_data':['design brief','candidate JSON','production gate feedback','runtime metadata'],
    'excluded':['source IFC bytes','independent evaluator and expected values','private Gold','A/B data','credentials'],
    'prompt_versions':['design-brief.v2.12','audit.v2'],'previous_budget_sha256':sha(ledger)}
write(OUT/'payload-preview.json',preview)
write(OUT/'authorization.json',{'status':'approved','basis':'Existing C full-loop authorization, confirmed entry move, and latest user request to fix C bugs. No increase to total budget or new destination.',
    'destination':preview['destination'],'model':preview['model'],'limits':budget['limits'],
    'request_sha256':sha(SOURCE/'request.txt'),'payload_preview_sha256':sha(OUT/'payload-preview.json')})
bound={p:sha(ROOT/p) for p in parent['files_sha256']}
for p in [ledger,ROOT/'prompts/agent/design-brief-v2.12.md',ROOT/'prompts/agent/design-brief-v2.13.md',
    ROOT/'tests/agent/test_brief_wall_boundary.py',ROOT/'tests/agent/test_c_wall_join_run.py',
    ROOT/'docs/validation/brief-wall-boundary/family.json',
    ROOT/'tests/agent/test_geometry_outline_wrapper.py',ROOT/'tests/agent/test_repair_assessment_scope.py']:
    bound[p.relative_to(ROOT).as_posix()]=sha(p)
for p in OUT.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:bound[p.relative_to(ROOT).as_posix()]=sha(p)
scan=scan_path(OUT);assert scan['finding_count']==0
write(OUT/'admission.json',{'status':'admitted','scope':'Existing Generation stage with scoped Prompt and gate revalidation; no schema/compiler/transaction/provider/evaluator changes. Full Preflight not run.',
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'parent_admission':parent_path.relative_to(ROOT).as_posix(),'parent_sha256':sha(parent_path),
    'dependencies':parent['dependencies'],'files_sha256':bound,'changed_bindings':changed,
    'checks':commands,'checks_overlap':True,'artifact_scan':scan,'full_preflight':False,
    'transport_attempted':False,'limitations':'Prompt rule validation and fake/replay public paths are not live model-quality or blind capability evidence. New C run remains a known-case retry.'})
print(json.dumps({'status':'admitted','file_bindings':len(bound),'changed_bindings':list(changed),'checks':commands}))
