"""S2 version routing and fake Provider seams; not live capability evidence."""
import json
import pytest

from tests.agent.test_component_requirements_v26 import component_brief
from tests.agent.test_generation_v24_route import prepare_source
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.compiler.test_component_geometry_v26 import document


def test_component_formal_is_classified_with_the_new_schema():
    from text2ifc_agent.generator import validate_generation_document
    assert validate_generation_document(document('IfcDoor'))['status']=='formal'


def test_cli_accepts_new_brief_version_without_network(tmp_path):
    from io import StringIO
    from scripts.agent.run_phase6_2_cli import main
    result=main(['--dry-run','--prompt','创建一扇已描述的窗。',
        '--design-brief-schema-version','2.9','--output-root',str(tmp_path/'run'),
        '--env-file',str(tmp_path/'no-credentials.env')],stdin=StringIO(''))
    assert result==0


def test_component_authoring_contract_describes_parts_and_parent_product():
    from text2ifc_agent.authoring_contract import build_authoring_contract
    value=build_authoring_contract(['IfcDoor','IfcWindow'],version='1.6')
    geometry=value['geometry_encoding']['component_geometry']
    assert geometry['family']==['IfcDoor','IfcWindow']
    assert geometry['part_products'] is False
    assert 'schemas/bim-json/2.6/schema.json' in value['source_hashes']


def test_generator_receives_new_component_contract_and_preserves_parameters(tmp_path):
    from text2ifc_agent.live_pipeline import run_generator_stage
    source=prepare_source(tmp_path,selected=False)
    (source/'design-brief.json').write_text(json.dumps(component_brief()),encoding='utf-8')
    candidate=document('IfcDoor');provider=SequenceProvider([candidate])
    result=run_generator_stage(provider=provider,output_dir=tmp_path/'generator',design_source_dir=source,case_id='components')
    assert result['valid'],result
    assert provider.calls[0]['schema']['properties']['schema_version']['const']=='bim-json/2.6'
    prompt=(tmp_path/'generator/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'BIM JSON 2.6' in prompt and 'component_geometry' in prompt
    assert 'Layered wall coordinate construction' in prompt
    assert 'p_local = inverse(W_wall) * p_world' in prompt
    from text2ifc_agent.prompt_registry import load_prompt_registry
    registry=load_prompt_registry()
    assert registry['bim-json-generator.v2.10']['role']=='bim_json_generator'
    assert registry['bim-json-generator.v2.9']['sha256']=='sha256:027dd14e7c7bfd8e0b9711d8631834e373ab61f8e049b81dcf7c5dd026c3016d'
    saved=json.loads((tmp_path/'generator/candidate.json').read_text(encoding='utf-8'))
    assert saved==candidate


def test_public_brief_stage_preserves_components_with_fake_provider(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_semantic_authority_completeness import valid_brief
    case,_=valid_brief();brief=component_brief();provider=SequenceProvider([brief])
    result=run_design_brief_stage(provider=provider,output_dir=tmp_path/'brief',case=case,
                                design_brief_schema_version='text2ifc/design-brief/2.9')
    assert result['valid'],result
    saved=json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8'))
    assert saved['known_facts']['semantic_requirements']==brief['known_facts']['semantic_requirements']
    prompt=(tmp_path/'brief/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'component_geometry' in prompt and 'text2ifc/design-brief/2.9' in prompt


def test_v26_staged_route_refuses_before_provider():
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    with pytest.raises(ValueError, match='legacy_full'):
        run_ready_session_to_ifc(store=None, session='unused',
            provider_factory=lambda: pytest.fail('Provider called'),
            generation_strategy='staged', bim_json_schema_version='bim-json/2.6')


def test_explicit_selection_cannot_downgrade_component_brief(tmp_path):
    from text2ifc_agent.generation_contract import selected_generation_version
    (tmp_path/'generation-contract.json').write_text(json.dumps({
        'schema_version':'text2ifc/generation-contract-selection/1.0',
        'bim_json_schema_version':'bim-json/2.5','generation_strategy':'legacy_full'}),encoding='utf-8')
    with pytest.raises(ValueError,match='downgrade'):
        selected_generation_version(component_brief(),tmp_path)


def test_generator_cannot_invent_component_detail_without_request():
    from text2ifc_agent.semantic_requirements import unauthorized_candidate_semantics
    issues=unauthorized_candidate_semantics(document(),[])
    assert any(i['code']=='UNREQUESTED_COMPONENT_GEOMETRY' for i in issues)


@pytest.mark.parametrize('change',['none','drop','change'])
def test_brief_review_repair_preserves_previously_written_components(tmp_path,change):
    import copy
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    initial=component_brief();initial['known_facts'].pop('semantic_review')
    corrected=component_brief()
    if change=='drop':
        corrected['known_facts']['semantic_requirements']=[]
        corrected['known_facts']['semantic_review']['component_geometry']['status']='not_specified'
    elif change=='change':
        corrected['known_facts']['semantic_requirements'][0]['component_geometry']['definitions'][0]['depth']+=10
    case={'user_request':initial['original_request'],'conversation':[{'turn_id':'turn-user-001','role':'user','content':initial['original_request']}]}
    result=repair_semantic_brief(provider=SequenceProvider([corrected]),output_dir=tmp_path/'repair',
        brief=initial,case=case,evidence_catalog=[],session_id='offline-components')
    assert result['valid']==(change=='none'),result
    assert (tmp_path/'repair/parsed-output.json').exists()


def test_changeset_draft_uses_component_version_bundle(tmp_path):
    from text2ifc_agent.changeset_stage import run_changeset_stage
    partial=document()
    partial['entities'][-1]['attributes']['Representation']['definitions'][0].pop('depth')
    draft={'draft_version':'bim-json-draft/1.6','target_schema_version':'bim-json/2.6',
        'partial_document':partial,'missing_facts':[{'entity_id':'filling-1','path':f'/entities/{len(partial["entities"])-1}/attributes/Representation/definitions/0/depth',
            'code':'MISSING_DEPTH','message':'Need extrusion depth.'}],
        'losses':[],'clarification_targets':[],'provenance':{'source':'test'}}
    result=run_changeset_stage(provider=SequenceProvider([draft]),output_dir=tmp_path,case_id='component-draft',
        call_index=1,user_request='Preserve all parts.',conversation=[],design_brief={},expected_facts={},
        candidate=document(),base_revision={},scope={'entity_ids':['filling-1'],'relationship_ids':[]},issues=[])
    assert result['classification']=='draft',result
    inputs=json.loads((tmp_path/'prompt-render-input.json').read_text(encoding='utf-8'))
    assert inputs['FORMAL_SCHEMA']['properties']['schema_version']['const']=='bim-json/2.6'
    assert inputs['DRAFT_SCHEMA']['properties']['draft_version']['const']=='bim-json-draft/1.6'
    assert 'component_geometry' in inputs['IFC_AUTHORING_CONTRACT']['geometry_encoding']


def test_public_v26_session_compiles_component_door_without_losing_request(tmp_path):
    import ifcopenshell
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import (
        _write_ready_design_brief_call, _SequenceLiveProvider, PHASE6_1_COMPLETE)
    from tests.compiler.test_component_geometry_v26 import components
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input='Create the confirmed room with the explicitly described component door.')
    _write_ready_design_brief_call(session.run_dir)
    geometry=components()
    for path in [session.run_dir/'design-brief.json',session.run_dir/'calls/01-design-brief/design-brief.json']:
        brief=json.loads(path.read_text(encoding='utf-8'))
        brief['schema_version']='text2ifc/design-brief/2.9'
        brief['known_facts']['plan_constraints']=[]
        brief['known_facts']['door'].update(id='door-1',ifc_class='IfcDoor')
        brief['known_facts']['semantic_requirements']=[{'entity_id':'door-1','scope':'direct','component_geometry':geometry}]
        brief['known_facts']['semantic_review']=component_brief()['known_facts']['semantic_review']
        path.write_text(json.dumps(brief),encoding='utf-8')
    before=(session.run_dir/'design-brief.json').read_bytes()
    candidate=json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    candidate['schema_version']='bim-json/2.6'
    next(e for e in candidate['entities'] if e['id']=='door-1')['attributes']['Representation']=geometry
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
    provider=_SequenceLiveProvider([candidate,audit])
    store.mark_session_status(session.session_id,'ready')
    try:
        result=run_ready_session_to_ifc(store=store,session=session.session_id,
            provider_factory=lambda:provider,bim_json_schema_version='bim-json/2.6')
        assert result.status=='compiled',result
        model=ifcopenshell.open(str(result.ifc_path))
        assert len(model.by_type('IfcDoor')[0].Representation.HasShapeAspects)==15
        assert (session.run_dir/'design-brief.json').read_bytes()==before
        expected=json.loads((session.run_dir/'expected-facts.json').read_text(encoding='utf-8'))
        assert expected['generation_schema_version']=='bim-json/2.6'
        assert any(e['kind']=='component_geometry' and e['value']==geometry for e in expected['semantic_expectations'])
        assert (tmp_path/'final-acceptance.json').is_file()
    finally:
        store.close()
