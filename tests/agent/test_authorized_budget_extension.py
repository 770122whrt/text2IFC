"""An explicitly approved rerun ceiling changes limits, never recorded spend."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/run_branches.py'


def harness():
    spec=importlib.util.spec_from_file_location('approved_budget_runner',RUNNER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def history_and_approval(tmp_path):
    module=harness()
    history={'schema_version':'text2ifc/generation-budget/1.0',
        'limits':{'max_calls':32,'max_tokens':2000000,'max_active_seconds':3600},
        'attempts':[{'attempt':1,'stage':'audit','status':'failed','tokens_charged':1925775,
            'reserved_tokens':1925775,'elapsed_seconds':1695.485}]}
    path=tmp_path/'original-budget.json';module.write(path,history)
    approval={'status':'approved','branch':'A-revise','prior_budget_sha256':module.sha(path),
        'previous_limits':history['limits'],'new_limits':{**history['limits'],'max_tokens':3000000}}
    return module,path,approval


@pytest.mark.parametrize('invalid',['unapproved','wrong_branch','wrong_hash','wrong_prior','calls','time','lower','unsettled'])
def test_invalid_extension_or_unsettled_history_cannot_create_new_budget(tmp_path,invalid):
    module,path,approval=history_and_approval(tmp_path)
    if invalid=='unapproved':approval['status']='proposed'
    elif invalid=='wrong_branch':approval['branch']='B-retain'
    elif invalid=='wrong_hash':approval['prior_budget_sha256']='0'*64
    elif invalid=='wrong_prior':approval['previous_limits']={**approval['previous_limits'],'max_tokens':1000000}
    elif invalid=='calls':approval['new_limits']['max_calls']=33
    elif invalid=='time':approval['new_limits']['max_active_seconds']=3601
    elif invalid=='lower':approval['new_limits']['max_tokens']=1000000
    else:
        history=module.read(path);history['attempts'][0]['status']='reserved';module.write(path,history)
        approval['prior_budget_sha256']=module.sha(path)
    before=path.read_bytes()
    with pytest.raises(ValueError):module.prepare_budget_history(path,branch='A-revise',approval=approval)
    assert path.read_bytes()==before


def test_approved_extension_preserves_every_prior_attempt_and_budget_failure(tmp_path):
    from text2ifc_agent.generation_budget import BudgetLimits,GenerationBudget,GenerationBudgetExceeded
    module,path,approval=history_and_approval(tmp_path)
    original=module.read(path);before=path.read_bytes()
    unchanged=module.prepare_budget_history(path,branch='A-revise',approval=None)
    assert unchanged==original
    old=tmp_path/'old';old.mkdir();module.write(old/'generation-budget.json',unchanged)
    with pytest.raises(GenerationBudgetExceeded):
        GenerationBudget(old).reserve(stage='brief',reserved_tokens=150000)
    amended=module.prepare_budget_history(path,branch='A-revise',approval=approval)
    assert amended['attempts']==original['attempts'] and path.read_bytes()==before
    new=tmp_path/'new';new.mkdir();module.write(new/'generation-budget.json',amended)
    budget=GenerationBudget(new,BudgetLimits(**amended['limits']))
    assert budget.snapshot()['tokens_used_or_reserved']==1925775
    budget.reserve(stage='brief',reserved_tokens=150000)
    assert budget.snapshot()['tokens_used_or_reserved']==2075775
    assert path.read_bytes()==before


def test_extended_budget_runs_fresh_public_generation_without_resetting_spend(tmp_path):
    import ifcopenshell
    from tests.agent.test_design_review_audit import _audit
    from tests.agent.test_interactive_cli_generation import _write_ready_design_brief_call,PHASE6_1_COMPLETE
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    module,path,approval=history_and_approval(tmp_path)
    parent=tmp_path/'parent';_write_ready_design_brief_call(parent)
    call=parent/'calls/01-design-brief'
    brief=module.read(call/'design-brief.json');turns=module.read(call/'conversation.json')
    brief['schema_version']='text2ifc/design-brief/2.3'
    brief['known_facts']['semantic_requirements']=[]
    brief['known_facts']['semantic_review']={kind:{'status':'not_specified','source_turns':[turns[0]['turn_id']]}
        for kind in ['material','property','type','appearance','template']}
    turns.append({'turn_id':'approved-revision','role':'user','content':'按已确认的修订继续生成。'})
    case=tmp_path/'A-revise';case.mkdir()
    module.write(case/'conversation.json',turns);module.write(case/'reference-review.json',{'source':'offline fixture'})
    candidate=module.read(PHASE6_1_COMPLETE/'generator/candidate.json');candidate['schema_version']='bim-json/2.1'
    for entity in candidate['entities']:entity['materials'],entity['property_sets']=[],{}
    audit=_audit('not_verified');audit['design_review']['concerns'][0]['id']='reference-stair-walking-clearance'
    provider=SequenceProvider([brief,candidate,audit]);before=path.read_bytes()
    result=module.execute(case=case,output=tmp_path/'run',provider_factory=lambda:provider,
        prior_budget=path,budget_approval=approval)
    assert result['status']=='compiled',result
    assert result['reused_design_brief'] is False and len(provider.calls)==3
    assert result['budget_before']['tokens_used_or_reserved']==1925775
    assert result['budget_after']['calls_used']==4
    assert result['budget_after']['limits']['max_tokens']==3000000
    assert result['budget_after']['attempts'][0]==module.read(path)['attempts'][0]
    assert path.read_bytes()==before
    assert ifcopenshell.open(str(Path(result['run_dir'])/'output.ifc')).schema=='IFC2X3'
