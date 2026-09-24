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
