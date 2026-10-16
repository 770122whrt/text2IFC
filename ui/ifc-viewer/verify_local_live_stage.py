"""Run the bounded local-Repair stage checks; never load credentials or call a model.

This is not a repository-wide preflight. It records the public Web/Repair paths used
by the local demo, its SDK seams, state transitions and transaction boundaries.
"""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]

def main(label):
    out=ROOT/'.tmp/repair-ui-api/stage-checks'/label
    out.mkdir(parents=True,exist_ok=False)
    junit=out/'pytest.xml'
    tests=['tests/web','tests/ifc_repair/test_scene_repair_api.py','tests/ifc_repair/test_scene_context.py',
           'tests/ifc_repair/test_scene_grounding.py','tests/ifc_repair/test_spatial_grounding.py',
           'tests/ifc_repair/test_orchestrator_terminal_matrix.py','tests/ifc_repair/test_clarification_state.py',
           'tests/ifc_repair/test_evaluation_contract.py',
           'tests/agent/test_phase6_2_openai_compat.py']
    # Current public-IFC multi-target tests cover mid-apply and final-write rollback.
    # The older test_apply_transaction suite depends on an absent external checkout;
    # do not substitute a different file at that authoritative source path.
    commands=[('backend',[sys.executable,'-m','pytest',*tests,'-q','--tb=short','--basetemp='+str(ROOT/'.tmp'/('stage-'+label[-18:])),'--junitxml='+str(junit)]),
              ('viewer',['node','--test',*[str(p) for p in sorted((ROOT/'ui/ifc-viewer/tests').glob('*.test.mjs'))]]),
              ('compile',[sys.executable,'-m','compileall','-q','src/text2ifc_web','src/text2ifc_ifc_repair/api.py','src/text2ifc_ifc_repair/orchestrator.py','ui/ifc-viewer/api_launcher.py'])]
    checks=[]
    for name,command in commands:
        start=datetime.now(timezone.utc).isoformat();tic=time.monotonic();log=out/(name+'.log')
        try:
            with log.open('wb') as handle:
                result=subprocess.run(command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,timeout=480)
            code=result.returncode
        except subprocess.TimeoutExpired:
            code=124
        skipped=0
        if name=='backend' and junit.exists():
            skipped=sum(int(s.get('skipped',0)) for s in ET.parse(junit).getroot().iter('testsuite'))
        check={'name':name,'command':command,'started_at':start,'elapsed_seconds':round(time.monotonic()-tic,2),
               'exit_code':code,'skipped':skipped,'passed':code==0 and skipped==0,'log':log.relative_to(ROOT).as_posix(),
               'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
        checks.append(check)
        print(json.dumps({k:v for k,v in check.items() if k not in ('command','log_sha256')},ensure_ascii=False),flush=True)
        if not check['passed']:break
    # Bind this review to the implementation, not to an arbitrary passing test string.
    files=[*sorted((ROOT/'src/text2ifc_web').glob('*.py')),ROOT/'src/text2ifc_ifc_repair/api.py',ROOT/'src/text2ifc_ifc_repair/orchestrator.py']
    report={'scope':'repair-ui-local','status':'passed' if len(checks)==len(commands) and all(c['passed'] for c in checks) else 'blocked',
            'created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'network_transport_attempted':False,
            'environment':{'python':sys.version,'platform':platform.platform()},
            'source_files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'scope_note':'Local IFC2X3 Web API, single/multi-target fixtures, clarification, source preservation, transaction/publication, Provider/SDK seams. No full-repository or model-quality claim.'}
    path=out/'admission.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'admission':path.relative_to(ROOT).as_posix(),'real_model_calls':0},ensure_ascii=False),flush=True)
    if report['status']!='passed':raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);main(parser.parse_args().label)
