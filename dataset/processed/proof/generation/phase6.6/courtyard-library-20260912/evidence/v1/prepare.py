"""Reuse unchanged Generation admission and add recorded scoped checks."""
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_agent.artifact_scan import scan_path
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    parent_path=ROOT/'dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911/evidence/frozen/admission.json'
    parent=read(parent_path)
    bound={}
    for p,h in parent['files_sha256'].items():
        if p.startswith(('src/','schemas/','prompts/','scripts/agent/')):
            assert sha(ROOT/p)==h,('changed-production-binding',p)
            bound[p]=h
    for p,v in parent['dependencies'].items(): assert importlib.metadata.version(p)==v,p
    checks={}
    for name in ['scoped.xml','runner-v2.xml']:
        cases=list(ET.parse(OUT/name).getroot().iter('testcase'))
        assert cases and not any(n.tag in {'error','failure','skipped'} for c in cases for n in c),name
        checks[name]={'passed':len(cases),'sha256':sha(OUT/name)}
    assert read(OUT/'offline-combination/result.json')['status']=='passed'
    request=(OUT/'request.txt').read_text(encoding='utf8')
    preview={'purpose':'New two-storey open-courtyard library based on user-approved concept and delegated design.',
        'destination':'https://api.deepseek.com','model':'deepseek-v4-flash',
        'request':request,'request_sha256':sha(OUT/'request.txt'),
        'allowed_followup_data':['this case Design Brief','this case candidate JSON','production validation feedback','approved clarification','runtime and usage metadata'],
        'excluded':['concept image','IFC files','previous A/B/C requests or outputs','independent evaluator expectations','private Gold','credential contents'],
        'limits':{'max_calls':32,'max_tokens':2000000,'max_active_seconds':3600},
        'max_completion_tokens':65536,'generation_strategy':'legacy_full',
        'brief_schema':'text2ifc/design-brief/2.4','fresh_budget':True}
    write('payload-preview.json',preview)
    write('authorization.json',{'status':'pending_explicit_payload_authorization',
        'basis':'Automatic approval review requires explicit consent for this case payload and destination. Request is pending; no transport occurred.',
        'destination':preview['destination'],'model':preview['model'],'limits':preview['limits'],
        'request_sha256':preview['request_sha256'],'payload_preview_sha256':sha(OUT/'payload-preview.json')})
    scan=scan_path(OUT); assert scan['finding_count']==0,scan
    for p in [parent_path,*[OUT/n for n in ['request.txt','run_case.py','prepare.py','check_combination.py','check_ifc.py','test_runner.py','scoped.xml','runner-v2.xml','payload-preview.json','authorization.json','offline-combination/result.json']]]:
        bound[p.relative_to(ROOT).as_posix()]=sha(p)
    write('admission.json',{'status':'admitted','scope':'Unchanged Generation 2.4/public legacy_full stage; current scoped material/template/railing/stair/geometry/budget/clarification checks plus exact fresh runner complete and invalid-output offline checks. Whole courtyard has not yet been generated.',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'parent_admission':parent_path.relative_to(ROOT).as_posix(),'parent_sha256':sha(parent_path),
        'dependencies':parent['dependencies'],'files_sha256':bound,'checks':checks,
        'full_preflight':False,'network_transport_attempted':False,'scan':scan,
        'limitations':['offline C fixture in runner checks is not the new design or live evidence','initial runner test failed from omitted frozen clarification, fixed in runner test input; failure XML retained','compiler probe is hand-authored and not a public generation success']})
    print(json.dumps({'status':'admitted','checks':checks,'production_bindings':len(bound),'provider_calls':0}))

if __name__=='__main__': main()
