"""New batch configuration through four real runtimes and keyless HTTP."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger

ROOT=Path(__file__).resolve().parents[3]
CLI=[sys.executable,'-m','scripts.ifc_repair.repair_comparison.demo_workflow']


@pytest.mark.skipif(os.environ.get('REPAIR_LATER_TEN_DOCKER')!='1',reason='explicit native Linux RSS regression')
def test_linux_worker_rss_is_independent_of_warmed_parent(tmp_path):
    from scripts.ifc_repair.repair_comparison.isolated_b import build_runtime_bundle
    bundle=tmp_path/'bundle';build_runtime_bundle(ROOT,bundle)
    command=['docker','run','--rm','--network=none','--read-only','--memory=8g','--cpus=4',
             '--pids-limit=256','--cap-drop=ALL','--security-opt=no-new-privileges',
             '--env=PYTHONPATH=/runtime/src','--env=PYTHONDONTWRITEBYTECODE=1',
             '--mount',f'type=bind,source={bundle},target=/runtime,readonly',
             '--mount',f'type=bind,source={ROOT/"tests/ifc_repair/test_validation_worker_rss.py"},target=/check.py,readonly',
             'text2ifc/repair-tools:py312-ifc085-property-v1','python','-c',
             'import runpy; runpy.run_path("/check.py")["test_exec_worker_excludes_parent_memory_but_retains_own_peak"](); print("RSS regression passed")']
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=90)
    (tmp_path/'native-rss.log').write_text(result.stdout+result.stderr,encoding='utf8')
    assert result.returncode==0,result.stdout+result.stderr


@pytest.mark.skipif(os.environ.get('REPAIR_LATER_TEN_DOCKER')!='1',reason='explicit keyless four-runtime stage run')
def test_four_real_runtimes_with_property_b_and_persistent_questions(tmp_path):
    root=tmp_path/'runtime'
    budget={'tokens':450000,'calls':48,'active_seconds':2400,'tool_seconds':120,'extensions':[]}
    models=ROOT/'.cache/models/BAAI-bge-m3'
    cases={arm:('case-001' if arm=='B' else 'case-002') for arm in 'ABCD'}
    before={(case,name):sha256(carrier.CASES/case/'public'/name) for case in set(cases.values())
            for name in ('model.ifc','request.txt')}
    config=carrier.initialize(root,mode='offline',cases_root=carrier.CASES,case_ids=sorted(set(cases.values())),
        budgets={case:budget for case in set(cases.values())},stage=carrier.FORMAL_STAGE,scene_grounding=True,
        b={'image':'text2ifc/repair-tools:py312-ifc085-property-v1','property_model_directory':str(models)})
    config['fixture_scenarios']={f'{case}-{arm}':'question' for arm,case in cases.items()}
    write_json(root/'experiment.json',config)
    output=(tmp_path/'service.log').open('wb')
    service=subprocess.Popen(CLI+['serve','--root',str(root)],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
    native=None;native_output=None;rows=[]
    try:
        deadline=time.monotonic()+90
        while not (root/'service.json').exists():
            assert service.poll() is None,'keyless gateway startup failed'
            assert time.monotonic()<deadline,'keyless gateway startup timed out'
            time.sleep(.2)
        ledger=Ledger(root/'control.sqlite')
        for arm in 'ABCD':
            case=cases[arm];run_id=case+'-'+arm
            if arm=='D':
                native_output=(tmp_path/'d-native.log').open('wb')
                native=subprocess.Popen(CLI+['run','--root',str(root),'--run-id',run_id],cwd=ROOT,stdout=native_output,stderr=subprocess.STDOUT)
                deadline=time.monotonic()+240
                while ledger.snapshot(run_id)['status']!='awaiting_user':
                    assert native.poll() is None,'DSH exited before the question'
                    assert time.monotonic()<deadline,'DSH question timed out'
                    time.sleep(.2)
            else:
                action=subprocess.run(CLI+['run','--root',str(root),'--run-id',run_id],cwd=ROOT,capture_output=True,timeout=1500)
                assert action.returncode==0,'runtime failed; retained CLI output and ledger are authority'
            state=ledger.snapshot(run_id);assert state['status']=='awaiting_user'
            count=state['usage']['calls'];elapsed=state['active_elapsed_s']
            time.sleep(.3)
            assert abs(ledger.snapshot(run_id)['active_elapsed_s']-elapsed)<.01
            carrier.answer(root,run_id,{'text':('窗宽915毫米。' if arm=='B' else
                          '确认二层唯一空门洞；离线夹具采用 SINGLE_SWING_LEFT。')})
            if arm=='D':
                native.wait(timeout=300);native_output.close();assert native.returncode==0
            else:
                action=subprocess.run(CLI+['run','--root',str(root),'--run-id',run_id],cwd=ROOT,capture_output=True,timeout=1500)
                assert action.returncode==0,'resume failed; inspect retained ledger'
            final=ledger.snapshot(run_id)
            assert final['status']=='submitted',f'{arm} did not submit; inspect retained ledger'
            assert final['budget']==state['budget'] and final['usage']['calls']>count
            assert final['usage']['coverage']=='complete'
            assert Path(final['artifact']['path']).is_file()
            assert final['mode']=='real_runtime_fake_model'
            rows.append({'arm':arm,'run_id':run_id,'source_unchanged':sha256(root/'inputs'/case/'model.ifc')==before[case,'model.ifc'],
                         'budget_persisted':True,'submitted':True,'known_tokens':final['usage']['known_total_tokens']})
        assert len({ledger.snapshot(cases[arm]+'-'+arm)['artifact']['path'] for arm in 'ABCD'})==4
        assert all(sha256(carrier.CASES/case/'public'/name)==value for (case,name),value in before.items())
        from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources
        write_json(tmp_path/'native-stage.json',{'root':str(root),'source_bindings':capture_sources('execution'),
                    'real_models_called':False,'four_runtime_clarification_resume':rows,
                    'property_b_image':config['b']['image'],'gateway_mode':'offline','all_passed':True})
    finally:
        if (root/'service.json').exists():
            subprocess.run(CLI+['stop','--root',str(root)],cwd=ROOT,capture_output=True,timeout=120)
        service.wait(timeout=45);output.close()
        if native_output and not native_output.closed:native_output.close()
