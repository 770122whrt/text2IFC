"""Offline public generation paths. Only Provider transport is deterministic fake."""
import copy
import json
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_agent.live_pipeline import run_generator_stage, run_candidate_gate_stage
from text2ifc_agent.staged_generation import run_staged_generation
from text2ifc_compiler import compile_document
from tests.agent.test_phase6_5_staged_generation import _fixture, _changesets, SequenceProvider


def test_new_design_call_cannot_silently_return_old_contract(tmp_path):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_1_live import _valid_ready_brief, complete_room_case
    case = complete_room_case()
    brief = _valid_ready_brief(case)
    brief['schema_version']='text2ifc/design-brief/2.0'
    result=run_design_brief_stage(provider=SequenceProvider([brief]),case=case,output_dir=tmp_path)
    assert not result['valid']
    assert any(i['code']=='REQUEST_CONTRACT_DOWNGRADE' for i in json.loads((tmp_path/'validation.json').read_text(encoding='utf-8'))['issues'])


@pytest.mark.parametrize('strategy', ['legacy_full', 'staged'])
@pytest.mark.parametrize('template', ['window-single','window-double-vertical','door-left','door-right'])
def test_public_strategies_preserve_explicit_material_and_property(tmp_path, strategy, template):
    skeleton, manifest, expected, values = _fixture(1)
    skeleton['schema_version'] = 'bim-json/2.1'
    for group in values:
        for item in group:
            if item['ifc_class'] == 'IfcSpace':
                item['attributes']['InteriorOrExteriorSpace'] = 'INTERNAL'
    wall = next(e for e in values[0] if e['id'] == 'wall-1')
    wall['attributes']['Representation']['profile']['x'] = 4000
    opening = next(e for e in values[0] if e['id'] == 'opening-1')
    opening['attributes']['Representation']['depth'] = 2100
    filling = next(e for e in values[0] if e['id'] == 'window-1')
    filling['ifc_class'] = 'IfcDoor' if template.startswith('door') else 'IfcWindow'
    filling['attributes'].update(OverallWidth=1000, OverallHeight=2100)
    filling['attributes']['Representation'] = {'kind':'basic_filling', 'template_id':template,
        'template_version':'text2ifc/basic-filling/1.0', 'width':1000, 'height':2100, 'depth':200, 'parameters':{}}
    wall['materials'] = [{'kind':'single_material','name':'Requested brick'}]
    wall['property_sets'] = {'Pset_WallCommon': {'FireRating':'60'}}
    brief = {'schema_version':'text2ifc/design-brief/2.1','status':'ready','known_facts': {
        'semantic_requirements':[{'entity_id':'wall-1', 'material':wall['materials'][0],
                                  'property_sets':wall['property_sets']},
            {'entity_id':'window-1', 'template':{'template_id':template,'template_version':'text2ifc/basic-filling/1.0'}}]}}
    if strategy == 'staged':
        provider = SequenceProvider(_changesets(skeleton,manifest,expected,values))
        result = run_staged_generation(provider=provider,output_dir=tmp_path/'generator',case_id='public',
            user_request='墙体材料为砖，耐火设计要求60分钟。',conversation=[],design_brief=brief,
            expected_facts=expected,skeleton=skeleton,manifest=manifest)
        assert result['valid'], result
        candidate = result['candidate']
        assert all('2.1' in call['schema'].get('$id','') or 'changeset' in call['schema'].get('$id','') for call in provider.calls)
    else:
        candidate = copy.deepcopy(skeleton)
        for group in values:
            for item in group:
                candidate['relationships' if item['ifc_class'].startswith('IfcRel') else 'entities'].append(item)
        source = tmp_path/'design-brief';source.mkdir()
        (source/'input.txt').write_text('墙体材料为砖，耐火设计要求60分钟。',encoding='utf-8')
        for name, payload in [('conversation',[]),('design-brief',brief),('context-selection',{'evidence':[]})]:
            (source/(name+'.json')).write_text(json.dumps(payload),encoding='utf-8')
        provider = SequenceProvider([candidate])
        result = run_generator_stage(provider=provider,output_dir=tmp_path/'generator',design_source_dir=source,case_id='public')
        assert result['valid'], json.loads((tmp_path/'generator/validation.json').read_text(encoding='utf-8'))
        assert provider.calls[0]['schema']['properties']['schema_version']['const']=='bim-json/2.1'
    (tmp_path/'generator/candidate.json').write_text(json.dumps(candidate),encoding='utf-8')
    (tmp_path/'design-brief.json').write_text(json.dumps(brief),encoding='utf-8')
    gates = run_candidate_gate_stage(case_dir=tmp_path,output_dir=tmp_path,case_id='public')
    assert gates['compile_reopen_success'], gates['ifc_verification']
    assert gates['semantic_verification']['valid']
    model=ifcopenshell.open(str(tmp_path/'output.ifc'))
    assert any(m.Name=='Requested brick' for m in model.by_type('IfcMaterial'))


def test_new_schema_compilation_cli(tmp_path):
    from scripts.bim_json.compile_ifc import main
    candidate=json.loads((Path(__file__).parents[1]/'contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version']='bim-json/2.1'
    source=tmp_path/'candidate.json';source.write_text(json.dumps(candidate),encoding='utf-8')
    out=tmp_path/'output.ifc'
    assert main([str(source),str(out)])==0
    assert ifcopenshell.open(str(out)).schema=='IFC2X3'


def test_staged_shared_type_is_authored_once_after_instances(tmp_path):
    from text2ifc_agent.semantic_requirements import project_semantic_requirements
    import ifcopenshell.util.element as util
    skeleton, manifest, expected, values = _fixture(1)
    skeleton['schema_version']='bim-json/2.1'
    # This case freezes only two requested walls plus their explicitly shared Type.
    walls = [copy.deepcopy(values[0][0]) for _ in range(2)]
    walls[1]['id']='wall-2'
    values=[walls]
    manifest['packages']=manifest['packages'][:2]
    manifest['packages'][1]['owned_component_ids']=['wall-1','wall-2']
    type_record={'id':'shared-wall','ifc_class':'IfcWallType','attributes':{'Name':'Requested common wall','PredefinedType':'STANDARD'},
        'property_sets':{'Pset_WallCommon':{'FireRating':'60'}},'materials':[{'kind':'single_material','name':'Brick'}],'provenance':{'source':'user'}}
    relationships=[{'id':f'rel-type-{w["id"]}','ifc_class':'IfcRelDefinesByType',
        'attributes':{'RelatingType':'shared-wall','RelatedObjects':[w['id']]},'provenance':{'source':'user'}} for w in walls]
    package={'package_id':'package-semantic-types','kind':'semantic_types','storey_id':None,
        'owned_component_ids':['shared-wall'],'owned_relationship_ids':[r['id'] for r in relationships],
        'allowed_reference_ids':['wall-1','wall-2']}
    manifest['packages'].append(package)
    values.append([type_record,*relationships])
    brief={'schema_version':'text2ifc/design-brief/2.1','known_facts':{'semantic_requirements':[
        *[{'entity_id':w['id'],'type_id':'shared-wall','material':type_record['materials'][0], 'property_sets':type_record['property_sets']} for w in walls],
        {'entity_id':'shared-wall','material':type_record['materials'][0], 'property_sets':type_record['property_sets']}]}}
    provider=SequenceProvider(_changesets(skeleton,manifest,expected,values))
    result=run_staged_generation(provider=provider,output_dir=tmp_path/'generator',case_id='shared',
        user_request='两墙共享同一砖墙类型，耐火要求60分钟。',conversation=[],design_brief=brief,
        expected_facts=expected,skeleton=skeleton,manifest=manifest)
    assert result['valid'],result
    out=tmp_path/'shared.ifc'
    compiled=compile_document(result['candidate'],out,semantic_expectations=project_semantic_requirements(brief)['expectations'])
    assert compiled.success,compiled
    model=ifcopenshell.open(str(out))
    assert len(model.by_type('IfcWallType'))==1
    assert len({util.get_type(w).id() for w in model.by_type('IfcWall')})==1


@pytest.mark.parametrize('detailed', [False, True])
def test_ready_session_public_chain_reaches_final_acceptance(tmp_path, detailed):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_phase6_2_fix_semantic_fidelity import _outside_boundary_design_brief, _outside_boundary_center_overlap_candidate
    brief = _outside_boundary_design_brief()
    brief['schema_version']='text2ifc/design-brief/2.1'
    brief['original_request'] += ' 墙体使用Requested brick，耐火设计要求60分钟。'
    brief['provenance'].update(selected_evidence_ids=[], few_shot_ids=[])
    brief['known_facts']['semantic_requirements']=[{'entity_id':'wall-south',
        'material':{'kind':'single_material','name':'Requested brick'},
        'property_sets':{'Pset_WallCommon':{'FireRating':'60'}}}]
    candidate = _outside_boundary_center_overlap_candidate()
    candidate['schema_version']='bim-json/2.1'
    if detailed:
        by_id={e['id']:e for e in candidate['entities']}
        for filling_id, template in [('door-1','door-left'),('window-1','window-double-vertical')]:
            record=by_id[filling_id]
            opening=by_id[record['attributes']['ObjectPlacement']['relative_to']]
            opening_rep=opening['attributes']['Representation']
            host=by_id[opening['attributes']['ObjectPlacement']['relative_to']]
            width=opening_rep['profile']['x'];height=opening_rep['depth'];depth=host['attributes']['Representation']['profile']['y']
            record['attributes'].update(OverallWidth=width,OverallHeight=height)
            record['attributes']['Representation']={'kind':'basic_filling','template_id':template,
                'template_version':'text2ifc/basic-filling/1.0','width':width,'height':height,'depth':depth,'parameters':{}}
            brief['known_facts']['semantic_requirements'].append({'entity_id':filling_id,
                'template':{'template_id':template,'template_version':'text2ifc/basic-filling/1.0','width':width,'height':height,'depth':depth}})
            brief['original_request'] += f' {filling_id}使用{template}，总体宽{width}高{height}、开口深{depth}毫米。'
    for record in candidate['entities']:
        record['property_sets']={}
        record.pop('materials',None)
        if record['id']=='wall-south':
            record['materials']=[brief['known_facts']['semantic_requirements'][0]['material']]
            record['property_sets']={'Pset_WallCommon':{'FireRating':'60'}}
    store=SessionStore.open(tmp_path/'sessions.sqlite',artifact_root=tmp_path)
    session=store.create_session(original_input=brief['original_request'])
    design = run_design_brief_stage(provider=SequenceProvider([brief]),
        case={'case_id':session.session_hash,'user_request':brief['original_request'],'conversation':[]},
        output_dir=session.run_dir/'design-brief')
    assert design['valid'],design
    (session.run_dir/'design-brief.json').write_text(json.dumps(brief),encoding='utf-8')
    store.mark_session_status(session.session_id,'ready')
    audit={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
        'deterministic_gate_status':'passed','findings':[],
        'evidence_paths':['generator/candidate.json','ifc-verification.json','semantic-verification.json']}
    provider=SequenceProvider([candidate,audit])
    result=run_ready_session_to_ifc(store=store,session=session.session_hash,provider_factory=lambda:provider)
    assert result.status=='compiled', result
    assert len(provider.calls)==2
    assert Path(result.ifc_path).is_file()
    assert json.loads((session.run_dir/'semantic-verification.json').read_text(encoding='utf-8'))['valid']
