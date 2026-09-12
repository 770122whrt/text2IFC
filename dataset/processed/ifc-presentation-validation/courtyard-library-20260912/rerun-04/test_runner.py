"""Exact rerun transport seam: shared prior ledger, public flow, no live calls."""
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits
from tests.agent.test_c_plan_run import fixture as old_fixture,Provider,SOURCE
import copy

def fixture():
    brief,candidate=old_fixture()
    brief['schema_version']='text2ifc/design-brief/2.5'
    candidate['schema_version']='bim-json/2.2'
    for record in candidate['entities']:
        if record['ifc_class'] in {'IfcDoor', 'IfcWindow'}:
            record['part_appearance']={'frame':{'color':[.1,.2,.3]}}
            brief['known_facts']['semantic_requirements'].append({'entity_id':record['id'],'part_appearance':copy.deepcopy(record['part_appearance'])})
    brief['known_facts']['semantic_review']['appearance']['status']='specified'
    return brief,candidate

def runner(tmp_path):
    spec=importlib.util.spec_from_file_location('courtyard_rerun',Path(__file__).with_name('run_case.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.SOURCE=tmp_path
    budget=GenerationBudget(tmp_path/'prior',BudgetLimits(**module.LIMITS))
    slot=budget.reserve(stage='old-failure',reserved_tokens=100)
    budget.settle(slot,usage={'prompt_tokens':20,'completion_tokens':30},elapsed_seconds=3,failed=True)
    module.PRIOR_BUDGET=budget.path
    return module

@pytest.mark.parametrize('strategy',['legacy_full','staged'])
def test_inherited_budget_public_complete_preserves_source(tmp_path,strategy):
    r=runner(tmp_path)
    for name in ['request.txt','conversation.json']:shutil.copyfile(SOURCE/name,tmp_path/name)
    before=r.PRIOR_BUDGET.read_bytes();p=Provider(*fixture())
    result=r.execute(output=tmp_path/'run',provider_factory=lambda:p,evidence_class='offline_fake_existing_C_fixture',strategy=strategy)
    assert result['status']=='compiled',result
    assert result['budget_before']['calls_used']==1
    assert result['budget_before']['tokens_used_or_reserved']==50
    assert result['budget_before']['active_seconds']==3
    assert result['budget_after']['attempts'][0]==result['budget_before']['attempts'][0]
    assert result['prior_budget_unchanged'] and r.PRIOR_BUDGET.read_bytes()==before
    assert Path(result['result']['ifc_path']).is_file()

def test_inherited_budget_invalid_brief_never_publishes(tmp_path):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    r=runner(tmp_path);(tmp_path/'request.txt').write_text('无效响应的离线边界',encoding='utf8')
    before=r.PRIOR_BUDGET.read_bytes();p=SequenceProvider([{'invalid':True}])
    result=r.execute(output=tmp_path/'run',provider_factory=lambda:p,evidence_class='offline_fake')
    assert result['status']=='blocked_prompt_defect'
    assert result['budget_after']['calls_used']==2 and len(p.calls)==1
    run=Path(result['run_dir'])
    turns=json.loads((run/'calls/01-design-brief/conversation.json').read_text(encoding='utf8'))
    assert turns==[{'turn_id':'turn-user-001','role':'user','content':'无效响应的离线边界','question_ids':[]}]
    assert r.PRIOR_BUDGET.read_bytes()==before
    assert not list((tmp_path/'run').rglob('output.ifc'))

def test_changed_inherited_limits_stop_before_transport(tmp_path):
    r=runner(tmp_path);(tmp_path/'request.txt').write_text('预算不得重置',encoding='utf8')
    prior=json.loads(r.PRIOR_BUDGET.read_text(encoding='utf8'));prior['limits']['max_calls']=1
    r.PRIOR_BUDGET.write_text(json.dumps(prior),encoding='utf8')
    def forbidden():raise AssertionError('transport should not be constructed')
    with pytest.raises(Exception,match='Resuming cannot change'):
        r.execute(output=tmp_path/'run',provider_factory=forbidden,evidence_class='offline_fake')
