"""Scoped admission after a typed appearance source-grammar fix; offline only."""
import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
ROOT=BASE.parents[3]
PARENT=BASE/'semantic-authority-rerun-20260910'
ORIGINAL=BASE/'rerun-20260910'
CHANGED={
    'src/text2ifc_agent/semantic_requirements.py','src/text2ifc_agent/design_brief.py',
    'src/text2ifc_agent/live_pipeline.py','src/text2ifc_agent/interactive_cli_flow.py',
    'src/text2ifc_agent/brief_semantic_repair.py','scripts/agent/run_phase6_2_cli.py',
    'prompts/agent/registry.json','tests/agent/test_semantic_public_paths.py',
    'tests/agent/test_design_review_audit.py','tests/agent/test_semantic_authority_completeness.py',
    'docs/architecture/semantic-appearance-plan.md'}
NEW={'prompts/agent/design-brief-v2.7.md','prompts/agent/design-brief-v2.8.md',
     'prompts/agent/design-brief-semantic-repair-v1.1.md','schemas/agent/design-brief/2.3/schema.json',
     'tests/agent/test_brief_appearance_grammar.py'}


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    with p.open('x',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False,indent=2)
def rows(path):
    return {(t.get('classname'),t.get('name')):not any(t.find(k) is not None for k in ['failure','error','skipped'])
            for t in ET.parse(path).getroot().iter('testcase')}
def replace_classes(original,current):
    classes={key[0] for key in current}
    return {**{k:v for k,v in original.items() if k[0] not in classes},**current}


def main():
    parent=read(PARENT/'admission.json')
    drift={p for p,digest in parent['files_sha256'].items() if sha(ROOT/p)!=digest}
    assert drift.issubset(CHANGED), drift-CHANGED
    for package,version in parent['dependencies'].items(): assert metadata.version(package)==version
    validation=OUT/'validation';validation.mkdir(exist_ok=False)
    frozen=[]
    for folder,name in [(BASE,'LIVE-ATTEMPT-FILES.json'),(BASE/'continuation-20260910','FILES.json'),
        (ORIGINAL,'FILES.json'),(BASE/'projection-retry-20260910','FILES.json'),
        (BASE/'appearance-guard-rerun-20260910','FILES.json'),(PARENT,'FILES.json')]:
        files=read(folder/name)['files']
        assert all(sha(folder/r['path'])==r['sha256'] for r in files), str(folder)
        frozen.append({'path':(folder/name).relative_to(ROOT).as_posix(),'sha256':sha(folder/name),'files':len(files)})
    for branch in ['A-revise','B-retain']:
        for p in (OUT/'inputs'/branch).iterdir():
            if p.is_file(): assert sha(p)==sha(ORIGINAL/'inputs'/branch/p.name)
    history=PARENT/'A-revise/runtime/runs/135976189dc358f9/generation-budget.json'
    budget=read(history)
    assert len(budget['attempts'])==16 and all(a['status'] in {'completed','failed'} for a in budget['attempts'])
    write(OUT/'authorization.json', {'confirmation_path':(ORIGINAL/'explicit-egress-confirmation.json').relative_to(ROOT).as_posix(),
        'confirmation_sha256':sha(ORIGINAL/'explicit-egress-confirmation.json'),
        'approved_payload_preview':(ORIGINAL/'payload-preview.json').relative_to(ROOT).as_posix(),
        'approved_payload_sha256':sha(ORIGINAL/'payload-preview.json'),
        'destination':'https://api.deepseek.com','model':'deepseek-v4-flash',
        'scope':'Same authorized A/B task after offline typed-source fix; fresh Brief/candidate from unchanged approved requests and conversation, and subsequent own feedback/metadata.',
        'A_prior_budget_slots':16,'A_prior_provider_responses':15,'A_prior_local_rejections':1,'B_prior_calls':0,
        'limits':budget['limits'],'excluded':['original IFC bytes','private Gold','other-task data','credential text'],
        'github_push_authorized':False})
    effective={(r['classname'],r['name']):r['passed'] for r in read(PARENT/'validation-completion/effective-results.json')}
    effective=replace_classes(effective,rows(PARENT/'validation-nonready/nonready-authority-scoped-20260910.xml'))
    assert len(effective)==parent['effective_unique_tests']==658 and all(effective.values())
    checks=[];scoped={}
    for name,count in [('typed-brief-seams',99),('typed-brief-public',116),('typed-brief-style-regression',69)]:
        for suffix in ['xml','log']:
            shutil.copyfile(ROOT/'.tmp'/(name+'-20260910.'+suffix),validation/(name+'.'+suffix))
        result=rows(validation/(name+'.xml'))
        assert len(result)==count and all(result.values())
        assert not set(scoped).intersection(result)
        scoped.update(result)
        checks.append({'group':name,'tests':count,'passed':count,'xml_sha256':sha(validation/(name+'.xml')),
                       'log_sha256':sha(validation/(name+'.log'))})
    effective=replace_classes(effective,scoped)
    assert all(effective.values())
    write(validation/'checks.json',checks)
    write(validation/'effective-results.json',[{'classname':k[0],'name':k[1],'passed':v} for k,v in sorted(effective.items())])
    bound={p:sha(ROOT/p) for p in parent['files_sha256']}
    bound.update({p:sha(ROOT/p) for p in CHANGED|NEW})
    for p in OUT.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            bound[p.relative_to(ROOT).as_posix()]=sha(p)
    bound[history.relative_to(ROOT).as_posix()]=sha(history)
    bound[(PARENT/'FILES.json').relative_to(ROOT).as_posix()]=sha(PARENT/'FILES.json')
    bound[(PARENT/'RUN-HOLD.json').relative_to(ROOT).as_posix()]=sha(PARENT/'RUN-HOLD.json')
    for name,command in [('compileall',[sys.executable,'-m','compileall','-q','src','tests/agent',str(OUT)]),
        ('diff-check',['git','-c','core.whitespace=cr-at-eol','diff','--check','--',*sorted(CHANGED|NEW)])]:
        result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180)
        (validation/(name+'.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0, result.stderr.decode(errors='replace')
    assert all(sha(ROOT/p)==digest for p,digest in bound.items())
    bound.update({p.relative_to(ROOT).as_posix():sha(p) for p in validation.iterdir()})
    write(OUT/'admission.json',{'status':'admitted','stage':'Generation with typed Brief appearance authority',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'parent_admission':(PARENT/'admission.json').relative_to(ROOT).as_posix(),'parent_admission_sha256':sha(PARENT/'admission.json'),
        'scope':'Scoped revalidation in the admitted Generation stage: source appearance grammar and Brief version dispatch, both generation strategies, complete public flow, atomic correction, clarification/resume, trace preservation, budgets and existing explicit appearance. Compiler and unrelated production paths unchanged.',
        'checks':checks,'scoped_tests':len(scoped),'effective_unique_tests':len(effective),
        'changed_prior_bindings':sorted(drift),'dependencies':parent['dependencies'],'files_sha256':bound,
        'frozen_authority_checks':frozen,
        'supersedes_holds':[{'path':(PARENT/'RUN-HOLD.json').relative_to(ROOT).as_posix(),'sha256':sha(PARENT/'RUN-HOLD.json')}],
        'supersession_basis':'Actual entity appearance grammar is enforced before freezing source expectations. Legacy malformed source is rejected; new Brief2.3/Prompt2.7-2.8 and bounded repair1.1 distinguish part-style narratives from whole-element numeric overrides. Offline old-Brief replay rejects34 malformed overrides while retaining19 material requirements.',
        'budget_history':{'A-revise':history.relative_to(ROOT).as_posix()},'full_preflight':False,'network_transport_attempted':False,
        'invalidation':'Binding/dependency drift, a new deterministic defect or local RUN-HOLD blocks further Provider transport.',
        'limits':'Offline tests and revealed live retries are not class/system capability metrics. Structured source checks do not prove natural-language completeness; final IFC and human review remain required.'})
    print('ADMITTED',len(scoped),'scoped tests;',len(effective),'effective stage cases')


if __name__=='__main__':main()
