"""S2 request propagation family: deterministic fixtures, zero real Provider calls."""
import copy

import pytest

from tests.agent.test_material_list_v25_route import list_brief
from tests.compiler.test_component_geometry_v26 import components, document
from text2ifc_agent.semantic_requirements import project_semantic_requirements, generation_schema_version
from text2ifc_agent.design_brief import validate_design_brief
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_compiler.compiler import compile_document


def component_brief(version='2.9'):
    brief = list_brief(version=version)
    brief['fact_sources'] = []
    brief['provenance']['selected_evidence_ids'] = []
    brief['known_facts']['doors'] = [{'id':'filling-1','ifc_class':'IfcDoor'}]
    brief['known_facts']['semantic_requirements'] = [{'entity_id':'filling-1','scope':'direct','component_geometry':components()}]
    brief['known_facts']['semantic_review']['material']['status'] = 'not_specified'
    if version == '2.9':
        brief['known_facts']['semantic_review']['component_geometry'] = {'status':'specified','source_turns':['turn-user-001']}
    return brief


def test_public_brief_component_parameters_are_frozen_without_changes():
    brief = component_brief(); before = copy.deepcopy(brief)
    assert validate_design_brief(brief) == []
    projected = project_semantic_requirements(brief)
    assert projected['valid'], projected['issues']
    requirements = [e for e in projected['expectations'] if e['kind']=='component_geometry']
    assert len(requirements)==1 and requirements[0]['value']==components()
    assert generation_schema_version(brief)=='bim-json/2.6'
    frozen = build_expected_facts(design_brief=brief,case_id='component-parameters')
    assert frozen['generation_schema_version']=='bim-json/2.6'
    assert requirements[0] in frozen['semantic_expectations']
    assert brief == before


def test_public_unsupported_notice_cannot_disappear_from_ready_brief():
    brief=component_brief()
    brief['original_request']='#### filling-1 部件几何\n本构件不支持完整重建，需要人工确认。\n- 不支持 IfcFacetedBrep：曲面。'
    assert any(i.code=='PUBLIC_COMPONENT_UNSUPPORTED' for i in validate_design_brief(brief))


@pytest.mark.parametrize('fault',['missing-request','missing-part'])
def test_explicit_public_component_catalog_cannot_be_silently_shortened(fault):
    brief=component_brief()
    brief['original_request']='#### filling-1 部件几何\n部件与实体引用：\n- frame：角色=frame；实体=frame-solid。\n- blade-014：角色=slat；实体=blade-solid。'
    if fault=='missing-request':
        brief['known_facts']['semantic_requirements']=[]
        brief['known_facts']['semantic_review']['component_geometry']['status']='not_specified'
    else:
        brief['known_facts']['semantic_requirements'][0]['component_geometry']['parts'][1]['repeat']['count']=13
    assert any(i.code=='PUBLIC_COMPONENT_DESCRIPTION_INCOMPLETE' for i in validate_design_brief(brief))


def test_older_brief_explicitly_refuses_components_instead_of_dropping_them():
    brief = component_brief('2.8')
    projected = project_semantic_requirements(brief)
    assert not projected['valid']
    assert any(i['code']=='COMPONENT_REQUEST_VERSION_UNSUPPORTED' for i in projected['issues'])


@pytest.mark.parametrize('problem', ['type-target','inherited','missing-depth','mixed-template','conflicting-requests','missing-review'])
def test_incomplete_or_conflicting_component_requirements_cannot_be_ready(problem):
    brief=component_brief(); requirement=brief['known_facts']['semantic_requirements'][0]
    if problem=='type-target': brief['known_facts']['doors'][0]['ifc_class']='IfcDoorStyle'
    elif problem=='inherited': requirement['scope']='inherited'
    elif problem=='missing-depth': requirement['component_geometry']['definitions'][0].pop('depth')
    elif problem=='mixed-template': requirement['template']={'template_id':'door-left'}
    elif problem=='conflicting-requests':
        other=copy.deepcopy(requirement);other['component_geometry']['definitions'][0]['depth']+=30
        brief['known_facts']['semantic_requirements'].append(other)
    elif problem=='missing-review': brief['known_facts']['semantic_review'].pop('component_geometry')
    assert validate_design_brief(brief)


@pytest.mark.parametrize('change', ['unchanged','missing-blade','changed-angle','filled-hole'])
def test_reopened_output_is_checked_against_brief_not_just_candidate(tmp_path,change):
    requirements=project_semantic_requirements(component_brief())['expectations']
    candidate=document('IfcDoor')
    rep=candidate['entities'][-1]['attributes']['Representation']
    if change=='missing-blade': rep['parts'][1]['repeat']['count']-=1
    elif change=='changed-angle': rep['parts'][1]['placement']['ref_direction']=[0,-1,0]
    elif change=='filled-hole': rep['definitions'][0]['profile'].pop('holes')
    result=compile_document(candidate,tmp_path/'candidate.ifc',semantic_expectations=requirements)
    assert result.success == (change=='unchanged'), result
    if change!='unchanged':
        assert result.ifc_issues
        assert not (tmp_path/'candidate.ifc').exists()


@pytest.mark.parametrize('change',['split-solid','half-mm-shift','one-mm-shift','over-one-mm-shift','two-mm-shift','duplicate-solid'])
def test_component_request_accepts_equivalent_partition_and_one_mm_tolerance(tmp_path,change):
    brief=component_brief(); r=brief['known_facts']['semantic_requirements'][0]['component_geometry']
    r['definitions']=r['definitions'][1:]
    r['definitions'][0]['profile']={'kind':'rectangle','x':20,'y':10}
    r['definitions'][0]['depth']=100
    from tests.compiler.test_component_geometry_v26 import position
    r['parts']=[{'id':'panel','role':'panel','geometry_refs':['blade-solid'],'placement':position()}]
    requirements=project_semantic_requirements(brief)['expectations']
    candidate=document('IfcDoor')
    actual=copy.deepcopy(r);candidate['entities'][-1]['attributes']['Representation']=actual
    if change in {'split-solid','duplicate-solid'}:
        other=copy.deepcopy(actual['definitions'][0]);other['id']='other'
        actual['definitions'].append(other);actual['parts'][0]['geometry_refs'].append('other')
        if change=='split-solid':
            for value,offset in zip(actual['definitions'],[-5,5]):
                value['profile']['x']=10;value['position']['origin'][0]=offset
    else:
        actual['parts'][0]['placement']['origin'][0]={'half-mm-shift':.5,'one-mm-shift':1.,'over-one-mm-shift':1.0001,'two-mm-shift':2.}[change]
    result=compile_document(candidate,tmp_path/'candidate.ifc',semantic_expectations=requirements)
    assert result.success == (change in {'split-solid','half-mm-shift','one-mm-shift'}),result
