import json
from pathlib import Path
import pytest
from text2ifc_web.live_runtime import local_live_factory,read_approval


def test_live_disabled_does_not_read_credentials_or_create_a_provider(tmp_path):
    factory,status=local_live_factory(tmp_path,{})
    assert factory is None and status['enabled'] is False


def test_live_requires_explicit_budget_and_passed_stage_record(tmp_path):
    path=tmp_path/'approval.json'
    path.write_text(json.dumps({'scope':'repair-ui-local','approved':True,'approval_id':'round1'}))
    with pytest.raises(ValueError):read_approval(path,tmp_path)
    admission=tmp_path/'admission.json';admission.write_text(json.dumps({'scope':'repair-ui-local','status':'failed','checks':[]}))
    data={'scope':'repair-ui-local','approved':True,'approval_id':'round1','max_calls':8,'max_tokens':500000,'max_active_seconds':1200,'admission_file':'admission.json'}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):read_approval(path,tmp_path)


def test_factory_reuses_native_api_and_a_shared_budget_without_real_transport(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from text2ifc_web.live_runtime import LocalLiveFactory
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_agent.generation_budget import GenerationBudgetExceeded
    admission=tmp_path/'admission.json';admission.write_text(json.dumps({'scope':'repair-ui-local','status':'passed','checks':[{'name':'unit-fixture','exit_code':0,'passed':True}]}))
    approval=tmp_path/'approval.json';approval.write_text(json.dumps({'scope':'repair-ui-local','approved':True,'approval_id':'fixture','max_calls':1,'max_tokens':1000,'max_active_seconds':60,'admission_file':'admission.json'}))
    calls=[]
    class Provider:
        config=SimpleNamespace(max_completion_tokens=20)
        def generate_live(self,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(response={'usage':{'prompt_tokens':10,'completion_tokens':5}},output=object())
    monkeypatch.setattr('text2ifc_web.live_runtime.load_local_provider_environment',lambda root:{'DEEPSEEK_API_KEY':'[REDACTED_SECRET]'})
    monkeypatch.setattr(RepairAPI,'from_environment',lambda root,scene_grounding,environment:SimpleNamespace(provider=Provider()))
    factory=LocalLiveFactory(str(tmp_path),str(approval))
    first=factory(tmp_path/'data/native');first.provider.generate_live(prompt='test',state={'stage':'unit'})
    second=factory(tmp_path/'data/native')
    with pytest.raises(GenerationBudgetExceeded):second.provider.generate_live(prompt='next',state={'stage':'unit'})
    assert len(calls)==1 and second.integration_budget.snapshot()['calls_used']==1


def test_only_a_stage_record_with_completed_passing_checks_can_be_referenced(tmp_path):
    admission=tmp_path/'admission.json';admission.write_text(json.dumps({'scope':'repair-ui-local','status':'passed','checks':[{'name':'offline_fixture_test_only','exit_code':0,'passed':True}]}))
    path=tmp_path/'approval.json';data={'scope':'repair-ui-local','approved':True,'approval_id':'round1','max_calls':8,'max_tokens':500000,'max_active_seconds':1200,'admission_file':'admission.json'};path.write_text(json.dumps(data))
    config=read_approval(path,tmp_path);assert config['max_calls']==8
    data['approved']=False;path.write_text(json.dumps(data))
    with pytest.raises(ValueError):read_approval(path,tmp_path)
