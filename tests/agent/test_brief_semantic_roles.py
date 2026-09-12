"""Frozen role/scope family: explicit identities, no courtyard-specific values."""
import copy
import pytest
from text2ifc_agent.semantic_requirements import project_semantic_requirements
from tests.agent.test_semantic_authority_completeness import review, valid_brief
from tests.agent.test_brief_material_grammar import SINGLE, LAYERED, USAGE

def brief_with_roles():
    _, brief=valid_brief(); brief['schema_version']='text2ifc/design-brief/2.4'
    brief['known_facts']={'storeys':[{'id':'level', 'walls':{'exterior':[
        {'id':'opaque-wall','thickness_mm':200}]},'doors':[{'id':'opaque-door'}],
        'windows':[{'id':'opaque-window'}]}],
        'types':[{'id':'opaque-wall-type','ifc_class':'IfcWallType'},
                 {'id':'opaque-door-type','ifc_class':'IfcDoorStyle'},
                 {'id':'opaque-window-type','ifc_class':'IfcWindowStyle'}],
        'semantic_requirements':[], 'semantic_review':review()}
    return brief

def check_record(record):
    b=brief_with_roles();b['known_facts']['semantic_requirements']=[record]
    b['known_facts']['semantic_review']=review(**{k:True for k,f in [('material','material'),('type','type_id'),('template','template')] if f in record})
    return project_semantic_requirements(b)

@pytest.mark.parametrize('record,code',[
    ({'entity_id':'opaque-door-type','type_id':'opaque-door-type'},'SEMANTIC_TYPE_TARGET_ROLE'),
    ({'entity_id':'opaque-door-type','type_id':'opaque-window-type'},'SEMANTIC_TYPE_TARGET_ROLE'),
    ({'entity_id':'opaque-door','type_id':'opaque-window-type'},'SEMANTIC_TYPE_FAMILY_MISMATCH'),
    ({'entity_id':'opaque-wall','material':LAYERED,'scope':'direct'},'SEMANTIC_MATERIAL_SCOPE_MISMATCH'),
    ({'entity_id':'opaque-wall-type','material':USAGE},'SEMANTIC_MATERIAL_SCOPE_MISMATCH'),
    ({'entity_id':'opaque-door','material':USAGE},'SEMANTIC_MATERIAL_SCOPE_MISMATCH'),
    ({'entity_id':'opaque-wall','material':{**USAGE,'direction':'AXIS3'}},'SEMANTIC_MATERIAL_AXIS_MISMATCH'),
    ({'entity_id':'opaque-door-type','template':{'template_id':'door-left','template_version':'text2ifc/basic-filling/1.0'}},'SEMANTIC_TEMPLATE_TARGET_ROLE'),
    ({'entity_id':'opaque-window','template':{'template_id':'door-right','template_version':'text2ifc/basic-filling/1.0'}},'SEMANTIC_TEMPLATE_TARGET_ROLE'),
    ({'entity_id':'opaque-door','scope':'inherited','template':{'template_id':'door-left','template_version':'text2ifc/basic-filling/1.0'}},'SEMANTIC_TEMPLATE_TARGET_ROLE'),
    ({'entity_id':'opaque-wall-type','scope':'inherited','material':LAYERED},'SEMANTIC_MATERIAL_SCOPE_MISMATCH'),
])
def test_invalid_roles_are_rejected_before_becoming_frozen_authority(record,code):
    result=check_record(record)
    assert code in {i['code'] for i in result['issues']}
    assert not result['expectations']

@pytest.mark.parametrize('record',[
    {'entity_id':'opaque-door','type_id':'opaque-door-type'},
    {'entity_id':'opaque-window','type_id':'opaque-window-type'},
    {'entity_id':'opaque-wall','material':USAGE,'scope':'direct'},
    {'entity_id':'opaque-wall','material':LAYERED,'scope':'inherited'},
    {'entity_id':'opaque-wall-type','material':LAYERED},
    {'entity_id':'opaque-door-type','material':SINGLE},
    {'entity_id':'opaque-door','template':{'template_id':'door-right','template_version':'text2ifc/basic-filling/1.0'}},
])
def test_legal_roles_remain_executable(record):
    result=check_record(record);assert result['valid'],result
    assert result['expectations']

def test_two_type_assignments_and_duplicate_definitions_fail_closed():
    b=brief_with_roles();k=b['known_facts'];k['semantic_review']=review(type=True)
    k['types'].append({'id':'second-door-type','ifc_class':'IfcDoorStyle'})
    k['semantic_requirements']=[{'entity_id':'opaque-door','type_id':t} for t in ['opaque-door-type','second-door-type']]
    assert 'SEMANTIC_TYPE_MULTIPLE' in {i['code'] for i in project_semantic_requirements(b)['issues']}
    k['types'].append(copy.deepcopy(k['types'][0]))
    assert 'SEMANTIC_ROLE_IDENTITY_AMBIGUOUS' in {i['code'] for i in project_semantic_requirements(b)['issues']}

def test_legacy_unresolved_context_contract_is_preserved():
    b=brief_with_roles();b['schema_version']='text2ifc/design-brief/2.3'
    b['known_facts']['semantic_requirements']=[{'entity_id':'opaque-wall','material':LAYERED}]
    b['known_facts']['semantic_review']=review(material=True)
    assert project_semantic_requirements(b)['valid']


def test_local_geometry_names_are_not_global_semantic_targets_until_referenced():
    b=brief_with_roles();k=b['known_facts']
    upper=copy.deepcopy(k['storeys'][0]);upper['id']='upper';upper['doors']=[];upper['windows']=[]
    k['storeys'].append(upper)
    assert project_semantic_requirements(b)['valid']
    k['semantic_requirements']=[{'entity_id':'opaque-wall','material':SINGLE}]
    k['semantic_review']=review(material=True)
    assert 'SEMANTIC_ROLE_IDENTITY_AMBIGUOUS' in {i['code'] for i in project_semantic_requirements(b)['issues']}


@pytest.mark.parametrize('known',[None,[],{'semantic_requirements':None},{'semantic_requirements':5}])
def test_malformed_semantic_container_fails_closed_without_role_index_exception(known):
    assert not project_semantic_requirements({'schema_version':'text2ifc/design-brief/2.4','known_facts':known})['valid']

@pytest.mark.parametrize('attack',['none','equivalent_type_scope','geometry','lost_type','changed_material','type_class','unknown_field','missing_parent'])
def test_scattered_semantic_recovery_is_atomic_and_preserves_values(tmp_path,attack):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief, semantic_repair_eligible
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,base=valid_brief();base['schema_version']='text2ifc/design-brief/2.4'
    base['known_facts']['plan_constraints']=[]
    roles=brief_with_roles()['known_facts']
    base['known_facts'].update(types=roles['types'])
    # Existing complete-room geometry stays byte-for-byte frozen. Add a separate
    # typed occurrence record for this recovery-only boundary test.
    base['known_facts']['doors']=[{'id':'opaque-door','width_mm':900,'type_id':'opaque-door-type'}]
    base['known_facts']['types'][1]['material']='Timber'
    base['known_facts']['semantic_requirements']=[{'entity_id':'opaque-door','type_id':'opaque-door-type'},
        {'entity_id':'opaque-door-type','material':{'kind':'single_material','name':'Timber'}}]
    base['known_facts']['semantic_review']=review(type=True,material=True)
    before=copy.deepcopy(base);corrected=copy.deepcopy(base)
    corrected['known_facts']['doors'][0].pop('type_id')
    corrected['known_facts']['types'][1].pop('material')
    if attack=='equivalent_type_scope':corrected['known_facts']['semantic_requirements'][0]['scope']='inherited'
    if attack=='geometry':corrected['known_facts']['doors'][0]['width_mm']=1000
    if attack=='lost_type':corrected['known_facts']['semantic_requirements'].pop(0);corrected['known_facts']['semantic_review']=review(material=True)
    if attack=='changed_material':corrected['known_facts']['semantic_requirements'][1]['material']['name']='Steel'
    if attack=='type_class':corrected['known_facts']['types'][1]['ifc_class']='IfcWindowStyle'
    if attack=='unknown_field':corrected['known_facts']['doors'][0]['new_field']='hidden'
    if attack=='missing_parent':corrected['known_facts']['doors']=[]
    from text2ifc_agent.design_brief import validate_design_brief
    issues=validate_design_brief(base,expected_schema_version=base['schema_version'])
    assert semantic_repair_eligible(base,issues),issues
    result=repair_semantic_brief(provider=SequenceProvider([corrected]),output_dir=tmp_path/'repair',brief=base,
        case=case,evidence_catalog=None,session_id='offline')
    accepted=attack in {'none','equivalent_type_scope'}
    assert result['valid']==accepted,result
    assert base==before
    assert (tmp_path/'repair/design-brief.json').exists()==accepted


def test_conflicting_materials_cannot_be_recovered_by_silently_choosing_one():
    from text2ifc_agent.brief_semantic_repair import semantic_repair_eligible
    b=brief_with_roles();b['known_facts']['semantic_review']=review(material=True)
    b['known_facts']['semantic_requirements']=[{'entity_id':'opaque-door','scope':'direct',
        'material':{'kind':'single_material','name':name}} for name in ['Timber','Steel']]
    result=project_semantic_requirements(b)
    assert 'SEMANTIC_VALUE_CONFLICT' in {i['code'] for i in result['issues']}
    assert not semantic_repair_eligible(b,result['issues'])


@pytest.mark.parametrize('code',['SEMANTIC_TYPE_TARGET_ROLE','SEMANTIC_TYPE_FAMILY_MISMATCH',
    'SEMANTIC_TYPE_MULTIPLE','SEMANTIC_ROLE_IDENTITY_AMBIGUOUS','SEMANTIC_TEMPLATE_TARGET_ROLE',
    'SEMANTIC_MATERIAL_SCOPE_MISMATCH','SEMANTIC_MATERIAL_AXIS_MISMATCH','SEMANTIC_VALUE_CONFLICT'])
def test_role_diagnostics_return_to_brief_not_candidate_repair(code):
    from text2ifc_agent.issue_normalizers import normalize_validation_issues
    issue=normalize_validation_issues([{'code':code,'path':'/known_facts/semantic_requirements/0','message':'Role conflict'}],
        source='semantic_validation')[0]
    assert (issue.owner,issue.suggested_route)==('design_brief','revise_design_brief')


@pytest.mark.parametrize('review_enabled',[False,True])
def test_public_brief_stage_repairs_scattered_fields_with_same_budget(tmp_path,review_enabled):
    import json
    from text2ifc_agent.generation_budget import GenerationBudget,BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,initial=valid_brief();initial['schema_version']='text2ifc/design-brief/2.4'
    initial['known_facts'].update(plan_constraints=[],doors=[{'id':'opaque-door','type_id':'opaque-type'}],
        types=[{'id':'opaque-type','ifc_class':'IfcDoorStyle'}],
        semantic_requirements=[{'entity_id':'opaque-door','type_id':'opaque-type','scope':'inherited'}],
        semantic_review=review(type=True))
    corrected=copy.deepcopy(initial);corrected['known_facts']['doors'][0].pop('type_id')
    provider=SequenceProvider([initial,corrected]);budget=GenerationBudget(tmp_path)
    result=run_design_brief_stage(provider=BudgetedProvider(provider,budget),output_dir=tmp_path/'brief',
        case=case,design_review_enabled=review_enabled,design_brief_schema_version=initial['schema_version'])
    assert result['valid'],result
    assert len(provider.calls)==len(budget.snapshot()['attempts'])==2
    trace=json.loads((tmp_path/'brief/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id']==('design-brief.v2.17' if review_enabled else 'design-brief.v2.16')
    assert json.loads((tmp_path/'brief/parsed-output.json').read_text(encoding='utf-8'))==initial
    assert json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8'))==corrected


@pytest.mark.parametrize('attack',['none','layer_name','layer_thickness','omit_group_member'])
def test_role_correction_preserves_layer_content_and_every_template_member(tmp_path,attack):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case,initial=valid_brief();initial['schema_version']='text2ifc/design-brief/2.4'
    template={'template_id':'door-left','template_version':'text2ifc/basic-filling/1.0'}
    initial['known_facts'].update(plan_constraints=[],
        role_wall={'id':'opaque-wall','ifc_class':'IfcWall'},
        doors=[{'id':name} for name in ['opaque-a','opaque-b']],
        types=[{'id':'opaque-type','ifc_class':'IfcDoorStyle'}],
        semantic_requirements=[{'entity_id':'opaque-wall','material':copy.deepcopy(LAYERED),'scope':'direct'},
            {'entity_id':'opaque-type','type_id':'opaque-type','template':template},
            *[{'entity_id':name,'type_id':'opaque-type'} for name in ['opaque-a','opaque-b']]],
        semantic_review=review(material=True,type=True,template=True))
    corrected=copy.deepcopy(initial);rows=corrected['known_facts']['semantic_requirements']
    rows[0]['material']=copy.deepcopy(USAGE)
    rows.pop(1)
    rows.extend({'entity_id':name,'template':template} for name in ['opaque-a','opaque-b'])
    if attack=='layer_name':rows[0]['material']['layers'][0]['name']='Changed'
    if attack=='layer_thickness':rows[0]['material']['layers'][0]['thickness']=170
    if attack=='omit_group_member':rows.pop()
    frozen=copy.deepcopy(initial)
    result=repair_semantic_brief(provider=SequenceProvider([corrected]),output_dir=tmp_path/'repair',brief=initial,
        case=case,evidence_catalog=None,session_id='offline')
    assert result['valid'] is (attack=='none'),result
    assert (tmp_path/'repair/design-brief.json').exists() is (attack=='none')
    assert initial==frozen
