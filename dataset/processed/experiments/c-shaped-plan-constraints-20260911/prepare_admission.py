"""Generation-stage admission for the new explicit planar Brief contract."""
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
PARENT=OUT.parent/'c-shaped-wall-join-20260911'
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2)

parent=read(PARENT/'admission.json')
changed={p:[h,sha(ROOT/p)] for p,h in parent['files_sha256'].items() if sha(ROOT/p)!=h}
allowed={'prompts/agent/registry.json','src/text2ifc_agent/brief_semantic_repair.py',
    'src/text2ifc_agent/changeset_stage.py','src/text2ifc_agent/design_brief.py',
    'src/text2ifc_agent/early_recovery.py','src/text2ifc_agent/expected_facts.py',
    'src/text2ifc_agent/interactive_cli_flow.py','src/text2ifc_agent/issue_normalizers.py',
    'src/text2ifc_agent/live_pipeline.py','src/text2ifc_agent/semantic_requirements.py',
    'tests/agent/test_design_review_audit.py','tests/agent/test_semantic_authority_completeness.py','docs/architecture/semantic-appearance-plan.md',
    'docs/architecture/token-efficiency-plan.md'}
assert set(changed)<=allowed,set(changed)-allowed
for p,v in parent['dependencies'].items():assert importlib.metadata.version(p)==v,p
checks={'plan-final3':96,'plan-entry':100,'plan-stage':125,'c-plan-public4':2,'plan-review':27,'plan-enum':13}
validation=OUT/'validation';validation.mkdir(exist_ok=True)
for name,count in checks.items():
    p=ROOT/'.tmp'/(name+'.xml');rows=list(ET.parse(p).getroot().iter('testcase'))
    assert len(rows)==count and not any(n.tag in {'error','failure','skipped'} for r in rows for n in r),(name,len(rows))
    shutil.copyfile(p,validation/p.name)
for name in ['plan-red.xml','plan-public-red.xml','plan-owner-red.xml','plan-conflict-red.xml','plan-trace-red.xml',
             'plan-legacy-baseline.json','plan-secondary.json','plan-c-probe.json']:
    shutil.copyfile(ROOT/'.tmp'/name,validation/name)
field_result=read(PARENT/'validation/field-recovery-results.json')
for p in ['src/text2ifc_agent/early_recovery.py','src/text2ifc_agent/changeset_stage.py',
          'prompts/agent/bim-json-changeset-v1.8.md','tests/agent/test_enum_field_recovery.py']:
    assert sha(ROOT/p)==field_result['source_hashes'][p],p
for name in ['field-recovery-regression.xml','field-recovery-results.json']:
    shutil.copyfile(PARENT/'validation'/name,validation/name)
ledger=PARENT/'live-run/runs/916d8afe752160e3/generation-budget.json';budget=read(ledger)
assert len(budget['attempts'])==11 and sum(a['tokens_charged'] for a in budget['attempts'])==831626
preview={'purpose':'Same authorized C request and actual entry clarification; new Brief2.4 checks and at most one derived-bound correction, then Generation/Audit/bounded loop.',
    'destination':'https://api.deepseek.com','model':'deepseek-v4-flash','limits':budget['limits'],
    'request':(SOURCE/'request.txt').read_text(encoding='utf-8'),'conversation':read(SOURCE/'conversation.json'),
    'allowed_followup_data':['design brief','typed public planar feedback','candidate JSON','production gate feedback','runtime metadata'],
    'excluded':['IFC bytes','private Gold','independent evaluator or expected values','A/B evidence','credentials'],
    'previous_budget_sha256':sha(ledger),'brief_schema':'text2ifc/design-brief/2.4','prompt':'design-brief.v2.14'}
write(OUT/'payload-preview.json',preview)
write(OUT/'authorization.json',{'status':'approved','basis':'Existing C loop approval and latest explicit request to finish C with general fixes. No new destination, case input, limit or design decision.',
    'destination':preview['destination'],'model':preview['model'],'limits':budget['limits'],
    'request_sha256':sha(SOURCE/'request.txt'),'payload_preview_sha256':sha(OUT/'payload-preview.json')})
bound={p:sha(ROOT/p) for p in parent['files_sha256']}
new=['schemas/agent/design-brief/2.4/schema.json','src/text2ifc_agent/brief_plan_constraints.py',
    'src/text2ifc_agent/brief_plan_repair.py','prompts/agent/design-brief-v2.14.md','prompts/agent/design-brief-v2.15.md',
    'prompts/agent/design-brief-plan-repair-v1.md','prompts/agent/bim-json-changeset-v1.8.md',
    'tests/agent/test_enum_field_recovery.py','tests/agent/test_brief_plan_constraints.py','tests/agent/test_c_plan_run.py']
for p in [*(ROOT/n for n in new),ledger]:bound[p.relative_to(ROOT).as_posix()]=sha(p)
for p in OUT.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:bound[p.relative_to(ROOT).as_posix()]=sha(p)
scan=scan_path(OUT);assert scan['finding_count']==0
write(OUT/'admission.json',{'status':'admitted','scope':'Generation-stage revalidation for opt-in Brief2.4, both public strategies plus complete C compile/reopen/final acceptance offline, clarification/persistence/budget/rollback/strict output and unchanged inherited stage safety evidence. Full Preflight not run.',
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'parent_admission':(PARENT/'admission.json').relative_to(ROOT).as_posix(),
    'parent_sha256':sha(PARENT/'admission.json'),'dependencies':parent['dependencies'],'files_sha256':bound,
    'changed_bindings':changed,'checks':checks,'checks_overlap':True,'artifact_scan':scan,'full_preflight':False,
    'transport_attempted':False,'limitations':'Fake public paths, same-scene checks and post-development secondary geometry cases are not blind capability evidence. Earlier partial-scope XML is supplemented by final 96 tests and direct C eligibility probe.'})
print(json.dumps({'status':'admitted','bindings':len(bound),'checks':checks}))
