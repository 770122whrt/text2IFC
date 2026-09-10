"""Scoped Generation revalidation after source-material and failure-routing fixes."""
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
PARENT=BASE/'typed-appearance-rerun-20260910'
ORIGINAL=BASE/'rerun-20260910'
CHANGED={'src/text2ifc_agent/semantic_requirements.py','src/text2ifc_agent/live_pipeline.py',
    'src/text2ifc_agent/interactive_cli_flow.py','src/text2ifc_agent/issue_normalizers.py',
    'src/text2ifc_agent/gate_audit_bundle.py','docs/architecture/semantic-appearance-plan.md'}
NEW={'tests/agent/test_brief_material_grammar.py','tests/agent/test_compile_failure_ownership.py',
     'tests/agent/test_audit_failure_terminal.py'}


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def rows(path):
    return {(t.get('classname'),t.get('name')):not any(t.find(k) is not None for k in ['failure','error','skipped'])
        for t in ET.parse(path).getroot().iter('testcase')}
def replace_classes(original,current):
    classes={key[0] for key in current}
    return {**{k:v for k,v in original.items() if k[0] not in classes},**current}


def main():
    parent=read(PARENT/'admission.json')
    drift={p for p,digest in parent['files_sha256'].items() if sha(ROOT/p)!=digest}
    assert drift.issubset(CHANGED),drift-CHANGED
    for package,version in parent['dependencies'].items():assert metadata.version(package)==version
    frozen=[]
    for authority in [*parent['frozen_authority_checks'],
        {'path':(PARENT/'FILES.json').relative_to(ROOT).as_posix(),'sha256':sha(PARENT/'FILES.json')}]:
        path=ROOT/authority['path']
        assert sha(path)==authority['sha256']
        files=read(path)['files']
        assert all(sha(path.parent/r['path'])==r['sha256'] for r in files),str(path)
        frozen.append({**authority,'files':len(files)})
    for branch in ['A-revise','B-retain']:
        for p in (OUT/'inputs'/branch).iterdir():
            if p.is_file():assert sha(p)==sha(ORIGINAL/'inputs'/branch/p.name)
    history=PARENT/'A-revise/runtime/runs/411166603facdde6/generation-budget.json'
    budget=read(history)
    assert len(budget['attempts'])==22 and all(a['status'] in {'completed','failed'} for a in budget['attempts'])
    write(OUT/'authorization.json',{'confirmation_path':(ORIGINAL/'explicit-egress-confirmation.json').relative_to(ROOT).as_posix(),
        'confirmation_sha256':sha(ORIGINAL/'explicit-egress-confirmation.json'),
        'approved_payload_preview':(ORIGINAL/'payload-preview.json').relative_to(ROOT).as_posix(),
        'approved_payload_sha256':sha(ORIGINAL/'payload-preview.json'),
        'destination':'https://api.deepseek.com','model':'deepseek-v4-flash',
        'scope':'Same approved frozen A/B inputs and own subsequent payloads after scoped offline fixes.',
        'limits':budget['limits'],'A_prior_budget_slots':22,'A_prior_provider_responses':20,
        'A_prior_local_rejections':2,'B_prior_calls':0,
        'A_budget_extension':'Proposal only; no increase authorized or applied.',
        'excluded':['original IFC bytes','private Gold','other-task data','credential text'],
        'github_push_authorized':False})
    effective={(r['classname'],r['name']):r['passed'] for r in read(PARENT/'validation/effective-results.json')}
    assert len(effective)==parent['effective_unique_tests']==712 and all(effective.values())
    material={}
    for label in ['green2','public']:
        material.update(rows(PARENT/'material-source-validation'/f'material-source-{label}-20260910.xml'))
    assert len(material)==203 and all(material.values())
    effective=replace_classes(effective,material)
    validation=OUT/'validation';validation.mkdir(exist_ok=False)
    checks=[];scoped={}
    for name,count in [('failure-recovery-scoped',62),('geometry-skip-guard',2),('failure-recovery-public',84)]:
        for suffix in ['xml','log']:
            shutil.copyfile(ROOT/'.tmp'/f'{name}-20260910.{suffix}',validation/f'{name}.{suffix}')
        current=rows(validation/f'{name}.xml')
        assert len(current)==count and all(current.values())
        assert not set(scoped).intersection(current)
        scoped.update(current)
        checks.append({'group':name,'tests':count,'passed':count,
            'xml_sha256':sha(validation/f'{name}.xml'),'log_sha256':sha(validation/f'{name}.log')})
    effective=replace_classes(effective,scoped)
    write(validation/'checks.json',checks)
    write(validation/'effective-results.json',[{'classname':k[0],'name':k[1],'passed':v} for k,v in sorted(effective.items())])
    bound={p:sha(ROOT/p) for p in parent['files_sha256']}
    bound.update({p:sha(ROOT/p) for p in CHANGED|NEW})
    for p in OUT.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:bound[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [history,PARENT/'FILES.json',PARENT/'RUN-HOLD.json']:
        bound[p.relative_to(ROOT).as_posix()]=sha(p)
    for name,command in [('compileall',[sys.executable,'-m','compileall','-q','src','tests/agent',str(OUT)]),
        ('diff-check',['git','-c','core.whitespace=cr-at-eol','diff','--check','--',*sorted(CHANGED|NEW)])]:
        result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180)
        (validation/f'{name}.log').write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,result.stderr.decode(errors='replace')
    assert all(sha(ROOT/p)==digest for p,digest in bound.items())
    bound.update({p.relative_to(ROOT).as_posix():sha(p) for p in validation.iterdir()})
    write(OUT/'admission.json',{'status':'admitted','stage':'Generation with faithful failure ownership and terminal Audit failure',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'parent_admission':(PARENT/'admission.json').relative_to(ROOT).as_posix(),
        'parent_admission_sha256':sha(PARENT/'admission.json'),
        'scope':'Same admitted Generation stage. Source material grammar, raw compile/reopen feedback, skip safety, error ownership, first/later Audit failure, both strategies, public correction and persisted terminal state.',
        'checks':checks,'scoped_tests':len(scoped),'effective_unique_tests':len(effective),
        'material_fix_checks':len(material),'dependencies':parent['dependencies'],
        'changed_prior_bindings':sorted(drift),'files_sha256':bound,'frozen_authority_checks':frozen,
        'supersedes_holds':[{'path':(PARENT/'RUN-HOLD.json').relative_to(ROOT).as_posix(),'sha256':sha(PARENT/'RUN-HOLD.json')}],
        'supersession_basis':'Invalid material source values cannot freeze; geometry is not fabricated from an unexecuted check; native failure ownership cannot authorize geometry edits; Audit Provider failures persist and stop without publication or extra calls.',
        'budget_history':{'A-revise':history.relative_to(ROOT).as_posix()},
        'full_preflight':False,'network_transport_attempted':False,
        'invalidation':'Binding/dependency drift, deterministic defects or local RUN-HOLD block new transport.',
        'limits':'No class/system improvement claim or code compliance certification. A extension preview is not authorization; original cumulative budget remains enforced.'})
    print(json.dumps({'status':'admitted','scoped_tests':len(scoped),'material_tests':len(material),
        'effective_unique_tests':len(effective),'old_frozen_files':sum(f['files'] for f in frozen)}))


if __name__=='__main__':main()
