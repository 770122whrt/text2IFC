"""Record the user's explicit A extension and rebind only its tested runner change."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def main():
    assert not (OUT/'A-revise').exists() and not (OUT/'B-retain').exists()
    old=read(OUT/'admission.json')
    allowed={(OUT/'run_branches.py').relative_to(ROOT).as_posix(),'docs/architecture/semantic-appearance-plan.md'}
    drift={p for p,d in old['files_sha256'].items() if sha(ROOT/p)!=d}
    assert drift.issubset(allowed),drift-allowed
    preview=read(OUT/'A-budget-extension-preview.json')
    approval={'status':'approved','branch':'A-revise','user_reply':'可以',
        'question_item':'call_JuZ3pxoDAFin91jUYLhF3Jxp:0',
        'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'preview_sha256':sha(OUT/'A-budget-extension-preview.json'),
        'prior_budget_sha256':preview['prior_budget_sha256'],
        'previous_limits':preview['current_limits'],'new_limits':preview['proposed_limits'],
        'destination':preview['destination'],'model':preview['model'],
        'scope':'Additional 1000000 tokens for the same complete A Generation/Audit loop; unchanged frozen request and approved conversation, own subsequent payloads only.',
        'prior_budget_not_refunded':True,'github_push_authorized':False}
    write(OUT/'A-budget-extension-approval.json',approval)
    shutil.copyfile(OUT/'authorization.json',OUT/'authorization-before-budget-extension.json')
    authorization=read(OUT/'authorization.json')
    authorization['A_budget_extension']={'status':'approved','approval_path':'A-budget-extension-approval.json',
        'approval_sha256':sha(OUT/'A-budget-extension-approval.json')}
    authorization['branch_limits']={'A-revise':approval['new_limits'],'B-retain':approval['previous_limits']}
    (OUT/'authorization.json').write_text(json.dumps(authorization,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    validation=OUT/'budget-extension-validation';validation.mkdir(exist_ok=False)
    current={};checks=[]
    for name,count in [('budget-extension-green',14),('budget-extension-public',1)]:
        for suffix in ['xml','log']:
            shutil.copyfile(ROOT/'.tmp'/f'{name}-20260910.{suffix}',validation/f'{name}.{suffix}')
        result={(t.get('classname'),t.get('name')):not any(t.find(k) is not None for k in ['failure','error','skipped'])
            for t in ET.parse(validation/f'{name}.xml').getroot().iter('testcase')}
        assert len(result)==count and all(result.values())
        assert not set(current).intersection(result)
        current.update(result);checks.append({'group':name,'passed':count})
    for suffix in ['xml','log']:
        shutil.copyfile(ROOT/'.tmp'/f'budget-extension-red-20260910.{suffix}',validation/f'budget-extension-red.{suffix}')
    effective={(r['classname'],r['name']):r['passed'] for r in read(OUT/'validation/effective-results.json')}
    classes={k[0] for k in current}
    effective={**{k:v for k,v in effective.items() if k[0] not in classes},**current}
    write(validation/'effective-results.json',[{'classname':k[0],'name':k[1],'passed':v} for k,v in sorted(effective.items())])
    write(validation/'checks.json',checks)
    paths=[OUT/'run_branches.py',ROOT/'tests/agent/test_authorized_budget_extension.py']
    for p in paths:compile(p.read_text(encoding='utf-8'),str(p),'exec')
    check=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check','--',
        *[p.relative_to(ROOT).as_posix() for p in paths],'docs/architecture/semantic-appearance-plan.md'],capture_output=True)
    assert check.returncode==0,check.stderr.decode(errors='replace')
    shutil.copyfile(OUT/'admission.json',OUT/'admission-before-budget-extension.json')
    old['files_sha256'].update({p:sha(ROOT/p) for p in allowed})
    for p in [*OUT.rglob('*'),ROOT/'tests/agent/test_authorized_budget_extension.py']:
        if p.is_file() and '__pycache__' not in p.parts and p!=OUT/'admission.json':
            old['files_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    old['budget_extension_revalidation']={'previous_admission_sha256':sha(OUT/'admission-before-budget-extension.json'),
        'scoped_tests':len(current),'changed_bindings':sorted(drift),
        'approval_sha256':sha(OUT/'A-budget-extension-approval.json')}
    old['effective_unique_tests']=len(effective)
    old['head']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    old['limits']='A extension explicitly approved to3000000 tokens; calls32/time3600 unchanged, prior ledger preserved. B retains2000000. Offline checks do not establish class/system capability or code compliance.'
    (OUT/'admission.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'status':'admitted','extension_tests':len(current),'effective_unique_tests':len(effective),
        'A_max_tokens':3000000,'B_max_tokens':2000000,'source_ledger_unchanged':sha(ROOT/preview['prior_budget_path'])==preview['prior_budget_sha256']}))


if __name__=='__main__':main()
