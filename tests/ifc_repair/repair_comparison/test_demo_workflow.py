import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

REPO=Path(__file__).resolve().parents[3]
COMMAND=[sys.executable,'-m','scripts.ifc_repair.repair_comparison.demo_workflow']


def test_live_requires_current_admission_before_secret_read(tmp_path):
    from scripts.ifc_repair.repair_comparison.demo_workflow import initialize
    admission=tmp_path/'admission.json'
    admission.write_text('{"passed":false,"stage":"repair-comparison-two-demo-live"}')
    with pytest.raises(ValueError,match='ADMISSION'):
        initialize(tmp_path/'live',mode='live',admission=admission)
    assert not (tmp_path/'live').exists()


@pytest.mark.skipif(os.environ.get('REPAIR_DEMO_DOCKER')!='1',reason='explicit development stage Docker run')
def test_eight_real_runtimes_via_public_cli_keyless_http(tmp_path):
    root=tmp_path/'experiment'
    def call(action,*extra,timeout=600):
        p=subprocess.run(COMMAND+[action,'--root',str(root),*extra],cwd=REPO,capture_output=True,text=True,encoding='utf8',timeout=timeout)
        assert p.returncode==0,(p.stdout[-5000:],p.stderr[-5000:])
        return json.loads(p.stdout)
    config=call('init')
    console=(tmp_path/'service.txt').open('wb')
    service=subprocess.Popen(COMMAND+['serve','--root',str(root)],cwd=REPO,stdout=console,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists():
            assert service.poll() is None,(tmp_path/'service.txt').read_text()
            assert time.monotonic()<deadline
            time.sleep(.25)
        results=[]
        for run_id in config['order']:
            state=call('run','--run-id',run_id)
            results.append(state)
            assert state['status']=='submitted',(run_id,state)
            assert state['mode']=='real_runtime_fake_model'
            assert state['usage']['calls']>=2 and state['usage']['coverage']=='complete'
            assert Path(state['artifact']['path']).is_file()
        reports=call('check')
        assert all(r['evaluation']['checks'].get('reopen') and r['evaluation']['checks'].get('native_schema_express') for r in reports)
        assert all(r['evaluation']['repair_success'] for r in reports if r['run_id'][-1] in {'A','C','D'})
        assert len({r['artifact']['path'] for r in results})==8
        # Frozen inputs are common and immutable, isolated workspace copies.
        for case in ('case-001','case-002'):
            source=(REPO/'dataset/processed/ifc-repair/repair-comparison/development'/case/'public/model.ifc').read_bytes()
            assert (root/'inputs'/case/'model.ifc').read_bytes()==source
            assert all((root/'workspaces'/(case+'-'+arm)/'model.ifc').read_bytes()==source for arm in 'ABCD')
    finally:
        if (root/'service.json').exists():call('stop')
        service.wait(timeout=30)
        console.close()
        (tmp_path/'retained-evidence.txt').write_text(str(root),encoding='utf8')


@pytest.mark.skipif(os.environ.get('REPAIR_DEMO_DOCKER')!='1',reason='explicit development stage Docker run')
def test_four_runtime_clarifications_resume_with_the_same_budget_and_dsh_process(tmp_path):
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    root=tmp_path/'questions'
    def call(action,*extra,timeout=600):
        p=subprocess.run(COMMAND+[action,'--root',str(root),*extra],cwd=REPO,capture_output=True,text=True,encoding='utf8',timeout=timeout)
        assert p.returncode==0,(p.stdout[-5000:],p.stderr[-5000:])
        return json.loads(p.stdout)
    config=call('init')
    config['fixture_scenarios']={f'case-002-{arm}':'question' for arm in 'ABCD'}
    (root/'experiment.json').write_text(json.dumps(config),encoding='utf8')
    console=(tmp_path/'service.txt').open('wb')
    service=subprocess.Popen(COMMAND+['serve','--root',str(root)],cwd=REPO,stdout=console,stderr=subprocess.STDOUT)
    native=None
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists():
            assert service.poll() is None,(tmp_path/'service.txt').read_text()
            assert time.monotonic()<deadline
            time.sleep(.25)
        ledger=Ledger(root/'control.sqlite')
        for arm in 'ABCD':
            run_id='case-002-'+arm
            if arm=='D':
                output=(tmp_path/'native.txt').open('wb')
                native=subprocess.Popen(COMMAND+['run','--root',str(root),'--run-id',run_id],cwd=REPO,stdout=output,stderr=subprocess.STDOUT)
                deadline=time.monotonic()+150
                while ledger.snapshot(run_id)['status']!='awaiting_user':
                    assert native.poll() is None,(tmp_path/'native.txt').read_text()
                    assert time.monotonic()<deadline,ledger.snapshot(run_id)
                    time.sleep(.25)
                state=ledger.snapshot(run_id)
            else:state=call('run','--run-id',run_id)
            assert state['status']=='awaiting_user',state
            count=state['usage']['calls']
            active=state['active_elapsed_s']
            time.sleep(.3)  # Explicit fake-human delay only in this keyless test.
            paused=ledger.snapshot(run_id)
            assert paused['usage']['calls']==count and abs(paused['active_elapsed_s']-active)<.01
            text='确认二层空門洞；离线夹具选择 SINGLE_SWING_LEFT。'
            answer=tmp_path/'answer.json';answer.write_text(json.dumps({'text':text}),encoding='utf8')
            call('answer','--run-id',run_id,'--answer-file',str(answer))
            if arm=='D':
                native.wait(timeout=150);output.close()
                assert native.returncode==0,(tmp_path/'native.txt').read_text()
                final=ledger.snapshot(run_id)
            else:final=call('run','--run-id',run_id)
            assert final['status']=='submitted',final
            assert final['usage']['calls']>count and final['budget']==state['budget']
            assert final['human_wait_s']>=.3
            assert len([e for e in ledger.events(run_id) if e['kind']=='answer'])==1
            if arm=='D':
                lineage={c['metadata']['native_session_id'] for c in ledger.calls(run_id)}
                assert lineage=={run_id}
                container=json.loads((root/'runtime'/run_id/'container.json').read_text())
                assert not container['State']['Running'] and container['State']['Pid']==0
    finally:
        if native and native.poll() is None:native.terminate()
        if (root/'service.json').exists():call('stop')
        service.wait(timeout=30);console.close()


@pytest.mark.skipif(os.environ.get('REPAIR_DEMO_DOCKER')!='1',reason='explicit development stage Docker run')
def test_shared_generic_shell_isolated_and_background_children_stop(tmp_path):
    from scripts.ifc_repair.repair_comparison.container_tools import ContainerTools
    work=tmp_path/'work';work.mkdir()
    private=tmp_path/'private-gold.ifc';private.write_text('private canary')
    tools=ContainerTools(work,tool_seconds=10)
    check=tools.execute(['python','-c',
        'import os,socket,ifcopenshell; from pathlib import Path; '
        'assert os.getuid()!=0; assert not Path("/var/run/docker.sock").exists(); '
        'assert not Path("/private-gold.ifc").exists(); '
        's=socket.socket(); s.settimeout(1); assert s.connect_ex(("1.1.1.1",443))!=0; '
        'Path("plain.ifc").write_text("ordinary direct text editing"); print("ISOLATION_OK")'])
    assert check['exit_code']==0 and 'ISOLATION_OK' in check['stdout'] and check['quiescent']
    assert (work/'plain.ifc').read_text()=='ordinary direct text editing'
    missing=tools.execute(['no-such-development-command'])
    assert missing['exit_code']==127 and missing['quiescent']
    before=private.read_bytes()
    child="import time\nfrom pathlib import Path\nwhile True:\n Path('heartbeat').write_text(str(time.time()))\n time.sleep(.05)\n"
    parent=f"import subprocess,time; subprocess.Popen(['python','-c',{child!r}]);time.sleep(30)"
    result=tools.execute(['python','-c',parent],timeout_s=2)
    assert result['timed_out'] and result['quiescent']
    heartbeat=(work/'heartbeat').read_text();time.sleep(.3)
    assert (work/'heartbeat').read_text()==heartbeat and private.read_bytes()==before
    assert all(r['network_mode']=='none' and r['state']['Pid']==0 for r in tools.records)
