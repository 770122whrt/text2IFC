"""Public CLI + wire ledger + real Linux B runtime, keyless fake HTTP only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION

REPO=Path(__file__).resolve().parents[2]
COMMAND=[sys.executable,'-m','scripts.ifc_repair.repair_comparison.demo_workflow']


@pytest.mark.skipif(os.environ.get('REPAIR_SCENE_DEMO_DOCKER')!='1',reason='explicit scene-stage Docker validation')
def test_two_scene_demo_runtimes_through_public_cli_and_wire_ledger(tmp_path):
    root=tmp_path/'experiment'
    def call(action,*extra,timeout=360):
        process=subprocess.run(COMMAND+[action,'--root',str(root),*extra],cwd=REPO,
                               capture_output=True,text=True,encoding='utf8',timeout=timeout)
        assert process.returncode==0,(process.stdout[-6000:],process.stderr[-6000:])
        return json.loads(process.stdout)
    config=call('init','--arms','B','--scene-grounding')
    assert config['order']==['case-001-B','case-002-B']
    assert config['scene_grounding_version']==SCENE_GROUNDING_VERSION
    # Mixed windows/openings + redundant floor and a different ordering must
    # not require an extra model request to establish the ranked window set.
    config['fixture_mixed_queries']=True
    (root/'experiment.json').write_text(json.dumps(config),encoding='utf8')
    console=(tmp_path/'service.txt').open('wb')
    service=subprocess.Popen(COMMAND+['serve','--root',str(root)],cwd=REPO,stdout=console,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists():
            assert service.poll() is None,(tmp_path/'service.txt').read_text(encoding='utf8')
            assert time.monotonic()<deadline
            time.sleep(.25)
        for run_id in config['order']:
            state=call('run','--run-id',run_id)
            assert state['status']=='submitted',(run_id,state)
            assert state['usage']['calls']==4 and state['usage']['coverage']=='complete'
            assert state['mode']=='real_runtime_fake_model'
            source=REPO/'dataset/processed/ifc-repair/repair-comparison/development'/state['case_id']/'public/model.ifc'
            assert (root/'workspaces'/run_id/'model.ifc').read_bytes()==source.read_bytes()
        checks=call('check')
        assert all(c['evaluation']['repair_success'] for c in checks),checks
        assert all(c['evaluation']['checks']['native_schema_express'] for c in checks)
    finally:
        if (root/'service.json').exists():
            call('stop')
        service.wait(timeout=45)
        console.close()
        (tmp_path/'retained-evidence.txt').write_text(str(root),encoding='utf8')


@pytest.mark.skipif(os.environ.get('REPAIR_SCENE_DEMO_DOCKER')!='1',reason='explicit scene-stage Docker validation')
def test_scene_linux_clarification_keeps_task_method_and_cumulative_usage(tmp_path):
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    root=tmp_path/'experiment'
    def call(action,*extra):
        process=subprocess.run(COMMAND+[action,'--root',str(root),*extra],cwd=REPO,
                               capture_output=True,text=True,encoding='utf8',timeout=360)
        assert process.returncode==0,(process.stdout[-6000:],process.stderr[-6000:])
        return json.loads(process.stdout)
    config=call('init','--arms','B','--scene-grounding')
    config['fixture_scenarios']={'case-001-B':'question'}
    (root/'experiment.json').write_text(json.dumps(config),encoding='utf8')
    log=(tmp_path/'service.txt').open('wb')
    service=subprocess.Popen(COMMAND+['serve','--root',str(root)],cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists():
            assert service.poll() is None and time.monotonic()<deadline
            time.sleep(.25)
        before=call('run','--run-id','case-001-B')
        assert before['status']=='awaiting_user' and before['usage']['calls']==3
        native=before['native']['result']
        question=before['question']
        assert '宽度' in question['text']
        assert not before['activities'] and not any(c['state']=='inflight' for c in Ledger(root/'control.sqlite').calls('case-001-B'))
        answer=tmp_path/'answer.json'
        answer.write_text(json.dumps({'text':'窗宽915毫米，按公开请求执行。'}),encoding='utf8')
        call('answer','--run-id','case-001-B','--answer-file',str(answer))
        after=call('run','--run-id','case-001-B')
        assert after['status']=='submitted' and after['usage']['calls']==7
        resumed=after['native']['result']
        assert resumed['run_id']==native['run_id'] and resumed['state_version']>native['state_version']
        assert after['usage']['known_total_tokens']>before['usage']['known_total_tokens']
    finally:
        if (root/'service.json').exists():
            call('stop')
        service.wait(timeout=45)
        log.close()
