"""Development failure family; independent analytic layouts, no capability score."""
import copy
import pytest

from text2ifc_agent.design_brief import validate_design_brief
from tests.agent.test_semantic_authority_completeness import valid_brief

LAYOUTS = {
    'rectangle': ([(0,0),(8000,0),(8000,6000),(0,6000),(0,0)],
        [(0,8000,0,200),(7800,8000,200,5800),(0,8000,5800,6000),(0,200,200,5800)]),
    'elbow': ([(0,0),(8000,0),(8000,3000),(3000,3000),(3000,6000),(0,6000),(0,0)],
        [(0,8000,0,200),(7800,8000,200,2800),(2800,8000,2800,3000),(2800,3000,3000,5800),(0,3000,5800,6000),(0,200,200,5800)]),
    'courtyard': ([(0,0),(8000,0),(8000,3000),(3000,3000),(3000,6000),(8000,6000),(8000,9000),(0,9000),(0,0)],
        [(0,8000,0,200),(7800,8000,200,2800),(2800,8000,2800,3000),(2800,3000,3000,6000),(2800,8000,6000,6200),(7800,8000,6200,8800),(0,8000,8800,9000),(0,200,200,8800)]),
}


def fixture(layout='rectangle', transform=0):
    case, b = valid_brief()
    b['schema_version'] = 'text2ifc/design-brief/2.4'
    poly, boxes = LAYOUTS[layout]
    def point(x,y):
        return [x,y] if transform == 0 else ([-y+1700,x-4300] if transform == 1 else [-x-1100,y+2200])
    walls=[]
    for i,(x1,x2,y1,y2) in enumerate(boxes):
        pts=[point(x,y) for x in [x1,x2] for y in [y1,y2]]
        walls.append({'id':f'boundary-{i}', 'bounds':{'x':[min(p[0] for p in pts),max(p[0] for p in pts)],
            'y':[min(p[1] for p in pts),max(p[1] for p in pts)]}})
    k=b['known_facts']
    k['outline']=[point(x,y) for x,y in poly]
    k['storeys']=[{'id':'level','name':'Ground','elevation_mm':0,'height_mm':3000,'walls':{'exterior':walls,'interior':[]}}]
    k['plan_constraints']=[{'id':'envelope', 'kind':'inside_wall_envelope',
        'outline_ref':'/known_facts/outline','storey_ref':'/known_facts/storeys/0','thickness_mm':200,
        'derived_wall_ids':[w['id'] for w in walls], 'source_turns':['turn-user-001']}]
    return case,b


@pytest.mark.parametrize('layout',LAYOUTS)
@pytest.mark.parametrize('transform',[0,1,2])
def test_valid_layouts_preserve_brief_and_accept_different_scene_shapes(layout,transform):
    case,b=fixture(layout,transform);before=copy.deepcopy(b)
    assert validate_design_brief(b,conversation=case['conversation']) == []
    assert b==before


@pytest.mark.parametrize('layout',LAYOUTS)
@pytest.mark.parametrize('failure',['outside','overlap','gap'])
def test_geometry_failure_is_detected_before_generation(layout,failure):
    case,b=fixture(layout);walls=b['known_facts']['storeys'][0]['walls']['exterior']
    if failure=='outside': walls[0]['bounds']['y']=[-200,0]
    elif failure=='overlap': walls[1]['bounds']['y'][0]=0
    else: walls[0]['bounds']['x'][0]=100
    issues=validate_design_brief(b,conversation=case['conversation'])
    assert any(i.code=='BRIEF_PLAN_GEOMETRY' and failure in i.message for i in issues),issues


def test_explicit_internal_wall_can_complete_a_concave_join():
    case,b=fixture('courtyard');walls=b['known_facts']['storeys'][0]['walls']
    walls['exterior'][2]['bounds']['x'][0]=3000
    walls['interior']=[{'id':'fixed-partition','bounds':{'x':[2800,3000],'y':[200,3000]}}]
    assert validate_design_brief(b,conversation=case['conversation'])==[]


@pytest.mark.parametrize('failure',['self_crossing','diagonal','unknown_source','unknown_wall','duplicate_id','missing','duplicate_constraint','negative_index','thickness_conflict'])
def test_malformed_contract_cannot_be_used_as_repair_authority(failure):
    case,b=fixture();k=b['known_facts'];c=k['plan_constraints'][0]
    if failure=='self_crossing':k['outline']=[[0,0],[4000,0],[4000,6000],[2000,6000],[2000,-1000],[0,-1000],[0,0]]
    elif failure=='diagonal':k['outline'][1][1]=10
    elif failure=='unknown_source':c['source_turns']=['invented-user-turn']
    elif failure=='unknown_wall':c['derived_wall_ids']=['missing']
    elif failure=='duplicate_id':k['storeys'][0]['walls']['exterior'][1]['id']='boundary-0'
    elif failure=='duplicate_constraint':k['plan_constraints'].append(copy.deepcopy(c))
    elif failure=='negative_index':c['storey_ref']='/known_facts/storeys/-1'
    elif failure=='thickness_conflict':k['storeys'][0]['walls']['exterior'][0]['thickness_mm']=300
    else:k.pop('plan_constraints')
    assert validate_design_brief(b,conversation=case['conversation'])


def test_no_requested_envelope_and_old_contract_remain_usable():
    case,b=valid_brief();b['schema_version']='text2ifc/design-brief/2.3'
    assert not validate_design_brief(b,conversation=case['conversation'])
    b['schema_version']='text2ifc/design-brief/2.4';b['known_facts']['plan_constraints']=[]
    assert not validate_design_brief(b,conversation=case['conversation'])


@pytest.mark.parametrize('attack',['none','outline','explicit','window','scope','partial'])
def test_repair_is_atomic_and_only_edits_derived_bounds(tmp_path,attack):
    from text2ifc_agent.brief_plan_repair import repair_plan_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,good=fixture();good['known_facts']['windows']=[{'id':'fixed-window','center_mm':2300}]
    good['known_facts']['storeys'][0]['walls']['interior']=[{'id':'fixed','bounds':{'x':[3000,3200],'y':[200,3000]}}]
    bad=copy.deepcopy(good);bad['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    response=copy.deepcopy(good)
    if attack=='outline': response['known_facts']['outline'][0][0]=1
    elif attack=='explicit':response['known_facts']['storeys'][0]['walls']['interior'][0]['bounds']['x']=[4000,4200]
    elif attack=='window':response['known_facts']['windows'][0]['center_mm']=2500
    elif attack=='scope':response['known_facts']['plan_constraints'][0]['derived_wall_ids'].append('fixed')
    elif attack=='partial':response=copy.deepcopy(bad)
    original=copy.deepcopy(bad)
    result=repair_plan_brief(provider=SequenceProvider([response]),output_dir=tmp_path/'repair',brief=bad,
        case=case,evidence_catalog=[],session_id='offline-plan')
    assert result['valid']==(attack=='none'),result
    assert bad==original


@pytest.mark.parametrize('other_derived',[False,True])
def test_explicit_geometry_conflict_is_not_auto_movable(tmp_path,other_derived):
    from text2ifc_agent.brief_plan_repair import plan_repair_eligible
    case,b=fixture();b['known_facts']['plan_constraints'][0]['derived_wall_ids']=['boundary-1','boundary-2','boundary-3'] if other_derived else []
    b['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    issues=validate_design_brief(b,conversation=case['conversation'])
    assert issues and not plan_repair_eligible(b,issues)


def test_expected_facts_cannot_freeze_an_invalid_plan():
    from text2ifc_agent.expected_facts import build_expected_facts, ExpectedFactsError
    _,b=fixture();b['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    with pytest.raises(ExpectedFactsError,match='BRIEF_PLAN_GEOMETRY'):
        build_expected_facts(case_id='invalid-plan',design_brief=b)


def test_public_brief_stage_repairs_then_returns_only_valid_brief(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,good=fixture();bad=copy.deepcopy(good)
    bad['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    provider=SequenceProvider([bad,good])
    result=run_design_brief_stage(provider=provider,output_dir=tmp_path/'brief',case=case,
        design_brief_schema_version='text2ifc/design-brief/2.4')
    assert result['valid'] and result['status']=='ready',result
    assert (tmp_path/'brief/plan-repair/validation.json').is_file()
    import json
    trace=json.loads((tmp_path/'brief/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['artifacts']['initial_plan_validation']=='initial-plan-validation.json'
    assert (tmp_path/'brief'/trace['artifacts']['initial_plan_validation']).is_file()


def test_plan_repair_cannot_revise_other_valid_storey(tmp_path):
    from text2ifc_agent.brief_plan_repair import repair_plan_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,good=fixture();k=good['known_facts'];k['storeys'].append(copy.deepcopy(k['storeys'][0]))
    k['storeys'][1]['id']='upper';k['storeys'][1]['name']='Upper'
    c=copy.deepcopy(k['plan_constraints'][0]);c.update(id='upper-envelope',storey_ref='/known_facts/storeys/1');k['plan_constraints'].append(c)
    bad=copy.deepcopy(good);bad['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    # Equivalent upper corner ownership would be geometrically valid, but is unrequested.
    upper=k['storeys'][1]['walls']['exterior'];upper[0]['bounds']['x'][1]=7800;upper[1]['bounds']['y'][0]=0
    result=repair_plan_brief(provider=SequenceProvider([good]),output_dir=tmp_path/'repair',brief=bad,
        case=case,evidence_catalog=[],session_id='offline-two-storey')
    assert not result['valid'] and any(i['code']=='BRIEF_PLAN_REPAIR_SCOPE_VIOLATION' for i in result['issues'])


def test_projection_preserves_valid_upstream_evidence_refs():
    from text2ifc_agent.expected_facts import build_expected_facts
    case,b=fixture()
    b['fact_sources']=[{'path':'/known_facts','source_turns':['turn-user-001'],'evidence_refs':['supplied-evidence']}]
    assert not validate_design_brief(b,conversation=case['conversation'],evidence_catalog=[{'evidence_id':'supplied-evidence'}])
    assert build_expected_facts(case_id='valid-plan',design_brief=b)


def test_plan_issues_keep_upstream_owner_in_public_normalizer():
    from text2ifc_agent.issue_normalizers import normalize_validation_issues
    rows=normalize_validation_issues([{'code':'BRIEF_PLAN_GEOMETRY','path':'/known_facts/plan_constraints/0','message':'outside'}],source='semantic_validation')
    assert rows[0].owner=='design_brief' and rows[0].suggested_route=='revise_design_brief'


@pytest.mark.parametrize('mode',['corrected','still_invalid','truncated'])
def test_interactive_plan_repair_has_shared_budget_and_preserves_attempt(tmp_path,mode):
    import json
    from types import SimpleNamespace
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config,OpenAICompatError
    case,good=fixture();bad=copy.deepcopy(good)
    bad['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
    sent=[]
    def create(**kwargs):
        sent.append(kwargs);n=len(sent)
        payload={'id':f'fake-{n}','model':'fake','choices':[{'finish_reason':'length' if mode=='truncated' and n==2 else 'stop',
            'message':{'content':json.dumps(good if n==2 and mode=='corrected' else bad)}}],
            'usage':{'prompt_tokens':10,'completion_tokens':20,'total_tokens':30}}
        return SimpleNamespace(model_dump=lambda:payload)
    config=load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek','API_KEY':'fake-key','OPENAI_BASE_URL':'https://example.invalid','TEXT2IFC_DEEPSEEK_MODEL':'fake'})
    invoke=make_openai_design_brief_invoker(config=config,run_dir=tmp_path,design_brief_schema_version='text2ifc/design-brief/2.4',
        client_factory=lambda **_:SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    if mode=='corrected':assert invoke(case['conversation'],1).brief==good
    else:
        with pytest.raises((OpenAICompatError,ValueError)):invoke(case['conversation'],1)
    assert len(sent)==2
    assert json.loads((tmp_path/'calls/01-design-brief/parsed-output.json').read_text(encoding='utf-8'))==bad
    ledger=json.loads((tmp_path/'generation-budget.json').read_text(encoding='utf-8'))
    assert len(ledger['attempts'])==2
    assert not list(tmp_path.rglob('output.ifc'))
