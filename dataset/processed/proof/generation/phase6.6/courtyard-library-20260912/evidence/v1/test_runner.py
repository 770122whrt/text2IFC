"""Public runner seam only; reused C fixture is explicitly offline evidence."""
import importlib.util
import shutil
from pathlib import Path
import pytest
from tests.agent.test_c_plan_run import fixture, Provider

OUT=Path(__file__).resolve().parent
def runner():
    spec=importlib.util.spec_from_file_location('courtyard_run',OUT/'run_case.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_new_runner_fresh_budget_compiles_via_public_flow(tmp_path):
    brief,candidate=fixture()
    p=Provider(brief,candidate)
    r=runner();r.SOURCE=tmp_path
    from tests.agent.test_c_plan_run import SOURCE
    for name in ['request.txt','conversation.json']:
        shutil.copyfile(SOURCE/name,tmp_path/name)
    result=r.execute(output=tmp_path/'run',provider_factory=lambda:p,evidence_class='offline_fake_existing_C_fixture')
    assert result['status']=='compiled',result
    assert result['budget_before']['calls_used']==0
    assert Path(result['result']['ifc_path']).is_file()

def test_new_runner_preserves_invalid_brief_and_stops(tmp_path):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    p=SequenceProvider([{'invalid':True}]*3)
    r=runner();r.SOURCE=tmp_path
    (tmp_path/'request.txt').write_text('离线无效响应边界',encoding='utf8')
    result=r.execute(output=tmp_path/'run',provider_factory=lambda:p,evidence_class='offline_fake')
    assert result['status']!='compiled'
    assert not list((tmp_path/'run').rglob('output.ifc'))
