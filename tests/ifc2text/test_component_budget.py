"""Reallocate call slots, never grant tokens or erase previous consumption."""
import json

import pytest

from text2ifc_ifc2text.goal_budget import GoalBudget,GoalStopped


def previous(tmp_path):
    old=GoalBudget(tmp_path/'old',writing_calls=10,reconstruction_calls=2,tokens=1000,historical_tokens=100,historical_writing_calls=3)
    n=old.reserve('reconstruction',200);old.settle(n,usage={'prompt_tokens':40,'completion_tokens':10})
    return old


def test_successor_keeps_same_token_ceiling_and_all_consumption(tmp_path):
    from scripts.ifc2text.component_budget import allocate,open_allocation
    old=previous(tmp_path);before=old.path.read_bytes()
    manifest=allocate(old,tmp_path/'new',additional_call_slots=5)
    new=open_allocation(manifest)
    assert old.path.read_bytes()==before
    snapshot=new.snapshot()
    assert snapshot['limits']=={'writing':10,'reconstruction':6,'tokens':1000}
    assert snapshot['tokens_used_or_reserved']==150
    assert snapshot['calls']=={'writing':3,'reconstruction':1}
    with pytest.raises(GoalStopped,match='EXCEEDED'):new.reserve('reconstruction',851)
    n=new.reserve('reconstruction',850)
    new.settle(n,usage={'prompt_tokens':30,'completion_tokens':20})
    reopened=open_allocation(manifest)
    assert reopened.snapshot()['tokens_used_or_reserved']==200
    assert reopened.snapshot()['calls']['reconstruction']==2
    assert old.path.read_bytes()==before


def test_explicit_human_token_extension_preserves_previous_charges(tmp_path):
    from scripts.ifc2text.component_budget import allocate, open_allocation
    old=previous(tmp_path);before=old.path.read_bytes()
    manifest=allocate(old,tmp_path/'extended',additional_call_slots=5,
                      additional_tokens=1000000,authorization='Human approved an additional 1000000 tokens.')
    new=open_allocation(manifest);snapshot=new.snapshot()
    assert snapshot['limits']['tokens']==1001000
    assert snapshot['tokens_used_or_reserved']==150
    assert snapshot['calls']['reconstruction']==1
    assert old.path.read_bytes()==before
    record=json.loads(manifest.read_text(encoding='utf8'))
    assert record['additional_tokens']==1000000 and record['authorization']
    record['token_ceiling']+=1
    manifest.write_text(json.dumps(record),encoding='utf8')
    with pytest.raises(GoalStopped,match='INVALID_COMPONENT_BUDGET_ALLOCATION'):
        open_allocation(manifest)


@pytest.mark.parametrize('amount,authority',[(1,''),(-1,'yes'),(True,'yes'),(1.5,'yes')])
def test_token_extension_requires_explicit_integer_authorization(tmp_path,amount,authority):
    from scripts.ifc2text.component_budget import allocate
    with pytest.raises(ValueError,match='TOKEN_EXTENSION'):
        allocate(previous(tmp_path),tmp_path/'invalid',additional_call_slots=5,
                 additional_tokens=amount,authorization=authority)
    assert not (tmp_path/'invalid').exists()



@pytest.mark.parametrize('halted',[False,True])
def test_unsettled_or_halted_predecessor_cannot_be_reallocated(tmp_path,halted):
    from scripts.ifc2text.component_budget import allocate
    old=previous(tmp_path);n=old.reserve('reconstruction',100)
    if halted:old.settle(n,failure='test failure')
    with pytest.raises(GoalStopped,match='HALTED_OR_UNSETTLED'):
        allocate(old,tmp_path/'new',additional_call_slots=5)
    assert not (tmp_path/'new').exists()


def test_changed_predecessor_blocks_successor_transport(tmp_path):
    from scripts.ifc2text.component_budget import allocate,open_allocation
    old=previous(tmp_path);manifest=allocate(old,tmp_path/'new',additional_call_slots=5)
    new=open_allocation(manifest)
    n=old.reserve('reconstruction',50);old.settle(n,usage={'prompt_tokens':1,'completion_tokens':1})
    with pytest.raises(GoalStopped,match='PREDECESSOR_CHANGED'):new.reserve('reconstruction',50)
    assert json.loads(new.path.read_text(encoding='utf-8'))['attempts']==[]


def test_explicit_allocation_cannot_overwrite_existing_authority(tmp_path):
    from scripts.ifc2text.component_budget import allocate
    old=previous(tmp_path);manifest=allocate(old,tmp_path/'new',additional_call_slots=5)
    before=manifest.read_bytes()
    with pytest.raises(FileExistsError):allocate(old,tmp_path/'new',additional_call_slots=5)
    assert manifest.read_bytes()==before


def test_campaign_requires_frozen_allocation_before_using_its_budget(tmp_path):
    from scripts.ifc2text.component_budget import allocate
    from scripts.ifc2text.component_campaign import budget_for,digest
    manifest=allocate(previous(tmp_path),tmp_path/'new',additional_call_slots=5)
    cfg={'budget_allocation':{'path':str(manifest),'sha256':digest(manifest)}}
    assert budget_for(cfg).snapshot()['tokens_used_or_reserved']==150
    cfg['budget_allocation']['sha256']='wrong'
    with pytest.raises(GoalStopped,match='ALLOCATION_CHANGED'):budget_for(cfg)


def truncated(tmp_path):
    from scripts.ifc2text.component_budget import allocate,open_allocation
    old=previous(tmp_path);b=open_allocation(allocate(old,tmp_path/'new',additional_call_slots=5))
    n=b.reserve('reconstruction',200)
    b.settle(n,usage={'prompt_tokens':40,'completion_tokens':100},failure='UNUSABLE_RESPONSE_length',response_id='response-1')
    p=tmp_path/'response.json';p.write_text(json.dumps({'id':'response-1','choices':[{'finish_reason':'length'}],
        'usage':{'prompt_tokens':40,'completion_tokens':100}}),encoding='utf-8')
    return b,p


def test_explicit_settled_truncation_recovery_retains_charge_failure_and_limits(tmp_path):
    from scripts.ifc2text.component_budget import resume_settled_truncation
    b,p=truncated(tmp_path);before=b.snapshot()
    receipt=resume_settled_truncation(b,p,rationale='Increase the separately admitted output cap after diagnosis')
    after=b.snapshot()
    assert not after['halted'] and after['halt_reason'] is None
    for key in ['limits','historical','attempts','calls','tokens_used_or_reserved']:assert after[key]==before[key]
    r=json.loads(receipt.read_text(encoding='utf-8'));assert r['before_snapshot']==before
    assert r['response_sha256'] and r['action']=='resume_settled_truncation'
    with pytest.raises(GoalStopped,match='TRUNCATION_RECOVERY_NOT_APPLICABLE'):resume_settled_truncation(b,p,rationale='duplicate')
    b.check_capacity('reconstruction',tokens=1)


@pytest.mark.parametrize('fault',['wrong_response','wrong_usage','wrong_finish','other_halt','unknown_usage','prior_failure','no_reason'])
def test_truncation_recovery_refuses_other_budget_failures(tmp_path,fault):
    from scripts.ifc2text.component_budget import resume_settled_truncation
    b,p=truncated(tmp_path);data=json.loads(p.read_text(encoding='utf-8'))
    if fault=='wrong_response':data['id']='other'
    elif fault=='wrong_usage':data['usage']['completion_tokens']=101
    elif fault=='wrong_finish':data['choices'][0]['finish_reason']='stop'
    elif fault=='other_halt':b.halt('USAGE_UNAVAILABLE')
    elif fault in {'unknown_usage','prior_failure'}:
        ledger=json.loads(b.path.read_text(encoding='utf-8'))
        if fault=='unknown_usage':ledger['attempts'][-1]['usage_known']=False
        else:ledger['attempts'].insert(0,{**ledger['attempts'][0],'attempt':0,'failure':'TIMEOUT'})
        b.path.write_text(json.dumps(ledger),encoding='utf-8')
    p.write_text(json.dumps(data),encoding='utf-8');before=b.path.read_bytes()
    with pytest.raises(GoalStopped):resume_settled_truncation(b,p,rationale='' if fault=='no_reason' else 'Diagnosis complete')
    assert b.path.read_bytes()==before


def test_recovery_finishes_same_transition_after_receipt_write_crash(tmp_path,monkeypatch):
    from scripts.ifc2text.component_budget import resume_settled_truncation
    b,p=truncated(tmp_path);write=b._write
    def crash(data):raise OSError('injected ledger write failure')
    monkeypatch.setattr(b,'_write',crash)
    with pytest.raises(OSError):resume_settled_truncation(b,p,rationale='Same diagnosed truncation')
    assert b.snapshot()['halted']
    monkeypatch.setattr(b,'_write',write)
    resume_settled_truncation(b,p,rationale='Same diagnosed truncation')
    assert not b.snapshot()['halted'] and b.snapshot()['attempts'][-1]['status']=='failed'


def test_96k_output_cap_is_sent_as_deepseek_max_tokens():
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config,token_limit_request
    config=load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek','API_KEY':'offline-only',
        'OpenAI_BASE_URL':'https://api.deepseek.com','TEXT2IFC_DEEPSEEK_MODEL':'deepseek-v4-flash',
        'TEXT2IFC_DEEPSEEK_MAX_TOKENS':'98304'})
    assert token_limit_request(config)=={'max_tokens':98304}
