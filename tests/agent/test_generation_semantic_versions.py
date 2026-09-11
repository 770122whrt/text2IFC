import copy
import json
from pathlib import Path

from text2ifc_agent.generator import validate_generation_document
from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.staged_generation import build_skeleton_workspace
from text2ifc_agent.semantic_requirements import project_semantic_requirements

ROOT = Path(__file__).resolve().parents[2]


def test_new_formal_version_accepted_without_rewriting_old():
    old = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    new = copy.deepcopy(old)
    new['schema_version'] = 'bim-json/2.1'
    assert validate_generation_document(new)['status'] == 'formal'
    assert validate_generation_document(old)['status'] == 'formal'


def test_staged_skeleton_keeps_request_contract_version():
    assert build_skeleton_workspace({'storeys': [{'id': 'floor-1', 'elevation_mm': 0}],
        'generation_schema_version': 'bim-json/2.1'})['schema_version'] == 'bim-json/2.1'


def test_semantic_expectations_frozen_before_generation_and_survive_projection():
    brief = {'schema_version': 'text2ifc/design-brief/2.1', 'status': 'ready', 'known_facts': {
        'storeys': [{'id': 'floor-1', 'elevation_mm': 0}],
        'semantic_requirements': [{'entity_id': 'wall-1', 'property_sets': {
            'Pset_WallCommon': {'FireRating': '60'}}}]}}
    facts = build_expected_facts(case_id='vertical', design_brief=brief)
    assert facts['generation_schema_version'] == 'bim-json/2.1'
    assert facts['semantic_expectations'][0]['value'] == '60'
    brief['known_facts']['semantic_requirements'][0]['property_sets']['Pset_WallCommon']['FireRating'] = '30'
    assert facts['semantic_expectations'][0]['value'] == '60'


def test_absent_performance_does_not_create_a_requirement():
    assert project_semantic_requirements({'known_facts': {}})['expectations'] == []


def test_saved_projection_errors_remain_blocking_on_resume(tmp_path):
    from text2ifc_agent.semantic_requirements import request_semantics_for_case
    (tmp_path / 'expected-facts.json').write_text(json.dumps({
        'semantic_expectations': [], 'semantic_projection_issues': [
            {'code':'SEMANTIC_TARGET_REQUIRED','path':'/known_facts','message':'Unbound'}]}), encoding='utf-8')
    assert not request_semantics_for_case(tmp_path)['valid']


def test_unbound_material_request_is_blocking_not_represented():
    assert not project_semantic_requirements({'known_facts': {'wall': {'material': 'wood'}}})['valid']


def test_staged_type_package_owns_shared_definition_once_after_occurrences():
    from text2ifc_agent.generation_packages import build_generation_package_manifest
    facts = {'storeys': [{'id': 'floor-1', 'elevation_mm': 0}],
             'doors': [{'id':'door-a','storey':'floor-1','host_wall':'wall-a'},
                       {'id':'door-b','storey':'floor-1','host_wall':'wall-a'}],
             'semantic_expectations': [
                 {'entity_id':'door-a','kind':'type','value':'shared-door'},
                 {'entity_id':'door-b','kind':'type','value':'shared-door'}]}
    manifest = build_generation_package_manifest(facts)
    package = manifest['packages'][-1]
    assert package['kind'] == 'semantic_types'
    assert package['owned_component_ids'] == ['shared-door']
    assert set(package['allowed_reference_ids']) >= {'door-a','door-b'}


def test_new_brief_semantics_survive_public_clarification_and_persistence(tmp_path):
    from dataclasses import replace
    from tests.agent.test_interactive_cli_flow import _call
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    store = SessionStore.open(tmp_path/'session.sqlite',artifact_root=tmp_path)
    session = store.create_session(original_input='创建房间，墙用砖，耐火要求60分钟。')
    requirement = {'entity_id':'wall-1','material':{'kind':'single_material','name':'Brick'},
        'property_sets':{'Pset_WallCommon':{'FireRating':'60'}}}
    def invoke(transcript, call_index):
        call = _call(call_index,original_request=session.original_input,
            status='needs_clarification' if call_index == 1 else 'ready',
            source_turns=['turn-user-001'] if call_index == 1 else ['turn-user-001','turn-user-003'])
        call.brief['schema_version']='text2ifc/design-brief/2.1'
        call.brief['known_facts']['semantic_requirements']=[requirement]
        return replace(call,prompt_template_id='design-brief.v2.2')
    result = run_design_brief_clarification_loop(store=store,session=session.session_hash,
        invoke_design_brief=invoke,user_answers=['200毫米'])
    assert result.status == 'ready'
    saved = json.loads((session.run_dir/'design-brief.json').read_text(encoding='utf-8'))
    assert saved['known_facts']['semantic_requirements']==[requirement]
    assert saved['schema_version']=='text2ifc/design-brief/2.1'
    assert project_semantic_requirements(saved)['valid']
