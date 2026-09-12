"""New railing contract must reach generation, authority and resumed paths."""
from copy import deepcopy
import pytest

from tests.agent.test_brief_semantic_roles import brief_with_roles
from tests.agent.test_semantic_authority_completeness import review
from text2ifc_agent.design_brief import design_brief_template_id
from text2ifc_agent.semantic_requirements import generation_schema_version, project_semantic_requirements
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation


def brief():
    b=brief_with_roles();b['schema_version']='text2ifc/design-brief/2.6'
    b['known_facts']['plan_constraints']=[]
    b['known_facts']['railings']=[{'id':'guard','storey':'storey-1','start_mm':[1000,2000,0],
        'end_mm':[1000,6000,1800],'height_mm':1100,'thickness_mm':40}]
    b['known_facts']['semantic_requirements']=[{'entity_id':'guard','template':{
        'template_id':'metal-picket','template_version':'text2ifc/basic-railing/1.0'}}]
    b['known_facts']['semantic_review']=review(template=True)
    return b


def test_new_brief_selects_new_generation_and_prompt_versions():
    assert generation_schema_version(brief())=='bim-json/2.3'
    assert design_brief_template_id('text2ifc/design-brief/2.6',design_review_enabled=False)=='design-brief.v2.20'
    assert design_brief_template_id('text2ifc/design-brief/2.6',design_review_enabled=True)=='design-brief.v2.21'


@pytest.mark.parametrize('attack',['none','old_version','wrong_family','inherited','type_target'])
def test_railing_template_authority_requires_new_occurrence_family_contract(attack):
    b=brief();row=b['known_facts']['semantic_requirements'][0]
    if attack=='old_version':b['schema_version']='text2ifc/design-brief/2.5'
    if attack=='wrong_family':row['entity_id']='opaque-door'
    if attack=='inherited':row['scope']='inherited'
    if attack=='type_target':row['entity_id']='opaque-door-type'
    before=deepcopy(b);projected=project_semantic_requirements(b)
    assert projected['valid']==(attack=='none'),projected
    assert b==before


def test_sloping_railing_preserves_endpoints_in_geometry_and_staged_ownership():
    b=brief()
    # Minimal geometry input isolates this public projection seam; no Provider.
    b['known_facts']={k:v for k,v in b['known_facts'].items() if k in {'railings','semantic_requirements','semantic_review','plan_constraints'}}
    b['known_facts']['storeys']=[{'id':'storey-1','elevation_mm':0,'net_height_mm':3400}]
    facts=build_expected_facts(case_id='slope',design_brief=b)
    assert facts['generation_package_manifest']['status']=='ready',facts['generation_package_manifest']
    geometry=build_design_geometry_expectation(case_id='slope',design_brief=b,expected_facts=facts)
    assert geometry['products']['guard']['bbox']=={'x':[.98,1.02],'y':[2,6],'z':[0,2.9]}


@pytest.mark.parametrize('strategy',['legacy_full','staged'])
def test_new_railing_runs_through_public_generation_and_actual_ifc(tmp_path,strategy):
    import json
    import ifcopenshell
    from tests.compiler.test_basic_railing import document
    from tests.agent.test_phase6_2_fix_semantic_fidelity import _outside_boundary_design_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider, _changesets
    from text2ifc_agent.staged_generation import build_skeleton_workspace, run_staged_generation
    from text2ifc_agent.live_pipeline import run_design_brief_stage, run_generator_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    b=_outside_boundary_design_brief();b['schema_version']='text2ifc/design-brief/2.6'
    b['original_request']='在一层外侧建立四米长的钢制细杆护栏，沿北向升高1.8米，栏高1.1米，深40毫米，使用深灰色。'
    b['provenance'].update(selected_evidence_ids=[],few_shot_ids=[])
    b['known_facts']={'storeys':[{'id':'level','elevation_mm':0,'net_height_mm':3400}],
        'railings':[{'id':'guard','storey':'level','start_mm':[1000,2000,0],'end_mm':[1000,6000,1800],
                     'height_mm':1100,'thickness_mm':40}],
        'semantic_requirements':[{'entity_id':'guard','template':{'template_id':'metal-picket',
          'template_version':'text2ifc/basic-railing/1.0'},'material':{'kind':'single_material','name':'Steel'},
          'appearance':{'color':[.2,.24,.25],'transparency':0}}],
        'semantic_review':review(material=True,appearance=True,template=True),'plan_constraints':[]}
    facts=build_expected_facts(case_id='public-railing',design_brief=b)
    skeleton=build_skeleton_workspace(facts)
    guard=document(rise=1800,yaw=90)['entities'][-1]
    candidate=deepcopy(skeleton);candidate['entities'].append(guard)
    store=SessionStore.open(tmp_path/'session.sqlite',artifact_root=tmp_path/'session')
    session=store.create_session(original_input=b['original_request'])
    source=session.run_dir/'design-brief';source.mkdir()
    result=run_design_brief_stage(provider=SequenceProvider([b]),output_dir=source,
        case={'case_id':'public-railing','user_request':b['original_request'],
        'conversation':[{'turn_id':'turn-user-001','role':'user','content':b['original_request']}]},
        design_brief_schema_version=b['schema_version'])
    assert result['valid'],result
    if strategy=='staged':
        manifest=facts['generation_package_manifest']
        values=[[guard] if 'guard' in package['owned_component_ids'] else [] for package in manifest['packages'][1:]]
        provider=SequenceProvider(_changesets(skeleton,manifest,facts,values))
        result=run_staged_generation(provider=provider,output_dir=tmp_path/'staged',case_id='public-railing',
            user_request=b['original_request'],conversation=[],design_brief=b,expected_facts=facts,
            skeleton=skeleton,manifest=manifest)
        assert result['valid'],result
        candidate=result['candidate']
    (session.run_dir/'design-brief.json').write_text(json.dumps(b),encoding='utf-8')
    store.mark_session_status(session.session_id,'ready')
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],
        'evidence_paths':['generator/candidate.json','ifc-verification.json','semantic-verification.json']}
    provider=SequenceProvider([candidate,audit])
    result=run_ready_session_to_ifc(store=store,session=session.session_hash,provider_factory=lambda:provider)
    assert result.status=='compiled',result
    assert len(provider.calls)==2
    model=ifcopenshell.open(result.ifc_path)
    assert len(model.by_type('IfcRailing'))==1
    assert len(model.by_type('IfcRailing')[0].Representation.Representations[0].Items)==42
    assert json.loads((session.run_dir/'semantic-verification.json').read_text(encoding='utf-8'))['valid']
    store.close()


@pytest.mark.parametrize('mirror',[False,True])
def test_same_bbox_cannot_hide_reversed_railing_slope(tmp_path,mirror):
    from tests.compiler.test_basic_railing import document
    from text2ifc_compiler import compile_document
    from text2ifc_quality.generated_ifc import check_generated_ifc
    b=brief();b['known_facts']={k:v for k,v in b['known_facts'].items() if k in {'railings','semantic_requirements','semantic_review','plan_constraints'}}
    b['known_facts']['storeys']=[{'id':'level','elevation_mm':0,'net_height_mm':3400}]
    b['known_facts']['railings'][0]['storey']='level'
    expected=build_expected_facts(case_id='mirror',design_brief=b)
    geometry=build_design_geometry_expectation(case_id='mirror',design_brief=b,expected_facts=expected)
    doc=document(rise=-1800 if mirror else 1800,yaw=90)
    if mirror:doc['entities'][-1]['attributes']['ObjectPlacement']['origin'][2]=1800
    compiled=compile_document(doc,tmp_path/'mirror.ifc');assert compiled.success
    result=check_generated_ifc(compiled.output_path,geometry)
    assert result.success == (not mirror),result
