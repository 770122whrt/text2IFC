"""Bounded Generation stage admission; no Provider transport."""
import datetime as dt
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    OUT.mkdir(exist_ok=False)
    source = ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
    for name in ['request.txt','frozen-expectations.json']:
        shutil.copyfile(source/name, OUT/name)
    admission = OUT/'admission'
    admission.mkdir()
    files = [p for folder in ['src/text2ifc_agent','src/text2ifc_compiler','src/text2ifc_contract','src/text2ifc_quality','prompts/agent','schemas','scripts/agent']
             for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.json','.md','.exp'} and '__pycache__' not in p.parts]
    hashes = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    record = {'status':'running','scope':'Generation public CLI legacy_full and staged; new field recovery/context/budget contracts',
              'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),
              'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'network_transport_attempted':False, 'full_preflight':False, 'files_sha256':hashes,'commands':[]}
    save(admission/'admission.json',record)
    commands = [
      [sys.executable,'-m','pytest','tests/agent','tests/compiler','tests/contract_v2','tests/ifc_quality','-q','-p','no:cacheprovider',
       '--basetemp',str(ROOT/'.tmp/generation-stage-20260909'), '--junitxml',str(admission/'pytest.xml')],
      [sys.executable,'-m','compileall','-q','src','tests','scripts'],
      ['git','diff','--check','--','src','tests','scripts','prompts','schemas','docs']]
    for number, cmd in enumerate(commands):
        start = time.monotonic(); started = dt.datetime.now(dt.timezone.utc).isoformat()
        path = admission/f'command-{number+1}.log'
        with path.open('w',encoding='utf-8') as log:
            try:
                result = subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
                code=result.returncode; timed_out=False
            except subprocess.TimeoutExpired:
                code=None; timed_out=True
        record['commands'].append({'command':cmd,'started_at':started,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),
             'seconds':time.monotonic()-start,'exit_code':code,'timeout':timed_out,'log':path.name,'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        save(admission/'admission.json',record)
        print(json.dumps({'command':number+1,'exit_code':code,'seconds':time.monotonic()-start}),flush=True)
        if code != 0:
            break
    xml=admission/'pytest.xml'
    if xml.exists():
        suites=list(ET.parse(xml).iter('testsuite'))
        record['tests']={k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
    clean=len(record['commands'])==3 and all(c['exit_code']==0 for c in record['commands']) and record.get('tests',{}).get('skipped',1)==0
    record['status']='offline_checks_passed_pending_matrix_review' if clean else 'blocked'
    record['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
    save(admission/'admission.json',record)
    print(json.dumps({'status':record['status'],'tests':record.get('tests')}),flush=True)

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
