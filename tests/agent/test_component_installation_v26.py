import pytest
from tests.agent.test_component_requirements_v26 import component_brief as base_brief
from text2ifc_agent.expected_facts import build_expected_facts, ExpectedFactsError


def component_brief():
    brief=base_brief()
    brief['known_facts']['doors'][0]['storey']='ground'
    return brief


@pytest.mark.parametrize('installation,count',[(None,1),('hosted',1),('standalone',0)])
def test_only_explicit_standalone_request_removes_opening_obligation(installation,count):
    brief=component_brief()
    if installation: brief['known_facts']['doors'][0]['installation']=installation
    expected=build_expected_facts(case_id='installation',design_brief=brief)
    assert expected['required_relationships']['opening_fill']['doors']==count
    assert expected['total_counts']['IfcDoor']==1


def test_standalone_and_explicit_host_cannot_both_be_requested():
    brief=component_brief()
    brief['known_facts']['doors'][0].update(installation='standalone',host_wall='wall-1')
    with pytest.raises(ExpectedFactsError,match='STANDALONE_HOST_CONFLICT'):
        build_expected_facts(case_id='installation',design_brief=brief)


@pytest.mark.parametrize('value',['other',{},True])
def test_invalid_installation_is_a_localized_contract_error(value):
    brief=component_brief();brief['known_facts']['doors'][0]['installation']=value
    with pytest.raises(ExpectedFactsError,match='COMPONENT_INSTALLATION_INVALID'):
        build_expected_facts(case_id='installation',design_brief=brief)


def test_standalone_cannot_gain_host_relationships():
    from tests.agent.test_phase6_3_dynamic_gates import _candidate
    from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates
    brief=component_brief();brief['known_facts']['doors'][0]['installation']='standalone'
    expected=build_expected_facts(case_id='installation',design_brief=brief)
    candidate=_candidate(storeys=['ground'],walls=[('wall-1','ground')],
        doors=[('filling-1','ground','wall-1')],windows=[],include_opening_relationships=True)
    gates=evaluate_dynamic_gates(candidate=candidate,expected_facts=expected)
    gate=next(g for g in gates if g['name']=='dynamic_opening_fill')
    assert gate['status']=='failed'
    assert any(i['code']=='STANDALONE_FILL_HAS_OPENING' for i in gate['issues'])


def test_standalone_needs_explicit_identity():
    brief=component_brief();brief['known_facts']['doors'][0]['installation']='standalone'
    brief['known_facts']['doors'][0].pop('id')
    with pytest.raises(ExpectedFactsError,match='STANDALONE_IDENTITY_REQUIRED'):
        build_expected_facts(case_id='installation',design_brief=brief)


def test_explicit_component_identity_survives_flat_opening_projection():
    expected=build_expected_facts(case_id='installation',design_brief=component_brief())
    assert expected['doors'][0]['id']=='filling-1'
    assert expected['entity_id_contract']['doors'][0]['brief_id']=='filling-1'
