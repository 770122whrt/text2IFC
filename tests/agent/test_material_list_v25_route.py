"""Material names must survive request projection and the public offline route."""
import copy
import json
from pathlib import Path

import pytest

from text2ifc_agent.semantic_requirements import project_semantic_requirements
from text2ifc_agent.expected_facts import build_expected_facts


MATERIAL = {'kind': 'material_list', 'materials': [{'name': 'Steel'}, {'name': 'Wood'}]}


def list_brief(material=None, version='2.8'):
    from tests.agent.test_design_brief import _brief_v2
    return _brief_v2(**{'schema_version': f'text2ifc/design-brief/{version}', 'status': 'ready',
        'known_facts': {'doors': [{'id': 'door-1', 'ifc_class': 'IfcDoor'}],
            'storeys': [{'id': 'ground', 'elevation_mm': 0}],
            'plan_constraints': [],
            'semantic_requirements': [{'entity_id': 'door-1', 'scope': 'direct',
                'material': copy.deepcopy(MATERIAL if material is None else material)}],
            'semantic_review': {k: {'status': 'specified' if k == 'material' else 'not_specified',
                'source_turns': ['turn-user-001']} for k in ['material', 'property', 'type', 'appearance', 'template']}}})


def test_list_projection_preserves_names_without_invented_layers():
    brief = list_brief()
    projected = project_semantic_requirements(brief)
    assert projected['valid'], projected['issues']
    assert projected['expectations'][0]['value'] == MATERIAL
    expected = build_expected_facts(design_brief=brief, case_id='material-list')
    assert expected['generation_schema_version'] == 'bim-json/2.5'
    assert expected['semantic_expectations'][0]['value'] == MATERIAL


@pytest.mark.parametrize('material', [
    {'kind': 'material_list', 'materials': []},
    {'kind': 'material_list', 'materials': [{'name': ''}]},
    {'kind': 'material_list', 'materials': [{'name': 'Steel', 'thickness': 50}]},
    {'kind': 'unknown', 'materials': [{'name': 'Steel'}]},
])
def test_invalid_lists_cannot_be_frozen_as_requests(material):
    assert not project_semantic_requirements(list_brief(material))['valid']


def test_old_brief_does_not_silently_gain_new_material_contract():
    assert not project_semantic_requirements(list_brief(version='2.7'))['valid']


@pytest.mark.parametrize('with_material', [True, False])
def test_explicit_v25_generator_route(tmp_path, with_material):
    from tests.agent.test_generation_v24_route import fixture_candidate, prepare_source
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_generator_stage
    source = prepare_source(tmp_path)
    selection = tmp_path/'generation-contract.json'
    selection.write_text(selection.read_text(encoding='utf-8').replace('bim-json/2.4', 'bim-json/2.5'), encoding='utf-8')
    candidate = fixture_candidate()
    candidate['schema_version'] = 'bim-json/2.5'
    door = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcDoor')
    if with_material:
        door['materials'] = [copy.deepcopy(MATERIAL)]
    result = run_generator_stage(provider=SequenceProvider([candidate]), output_dir=tmp_path/'generator',
        design_source_dir=source, case_id='material-list')
    assert result['valid'], result
    prompt = (tmp_path/'generator/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'material_list' in prompt and 'BIM JSON 2.5' in prompt


def test_public_brief_accepts_explicit_material_names(tmp_path):
    from tests.agent.test_semantic_authority_completeness import valid_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    case, _ = valid_brief()
    brief = list_brief()
    brief['fact_sources'] = []
    brief['provenance']['selected_evidence_ids'] = []
    result = run_design_brief_stage(provider=SequenceProvider([brief]), output_dir=tmp_path/'brief',
        case=case, design_brief_schema_version='text2ifc/design-brief/2.8')
    assert result['valid'], result
    saved = json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8'))
    assert saved['known_facts']['semantic_requirements'][0]['material'] == MATERIAL
    prompt = (tmp_path/'brief/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'material_list' in prompt and 'text2ifc/design-brief/2.8' in prompt


def test_public_v25_compiles_reopens_and_missing_name_fails_gate(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.element
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage
    from tests.agent.test_interactive_cli_generation import (
        _write_ready_design_brief_call, _SequenceLiveProvider, PHASE6_1_COMPLETE)
    store = SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path)
    session = store.create_session(original_input='Create the confirmed room. The door materials are Steel and Wood.')
    _write_ready_design_brief_call(session.run_dir)
    for path in [session.run_dir/'design-brief.json', session.run_dir/'calls/01-design-brief/design-brief.json']:
        brief = json.loads(path.read_text(encoding='utf-8'))
        brief['schema_version'] = 'text2ifc/design-brief/2.8'
        for key in ['semantic_requirements', 'semantic_review', 'plan_constraints']:
            brief['known_facts'][key] = list_brief()['known_facts'][key]
        path.write_text(json.dumps(brief), encoding='utf-8')
    before = (session.run_dir/'design-brief.json').read_bytes()
    store.mark_session_status(session.session_id, 'ready')
    candidate = json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.5'
    door = next(e for e in candidate['entities'] if e['id'] == 'door-1')
    door['materials'] = [copy.deepcopy(MATERIAL)]
    audit = {'schema_version': 'text2ifc/audit/2.0', 'recommendation': 'accept', 'blocking': False,
        'deterministic_gate_status': 'passed', 'findings': [], 'evidence_paths': ['generator/candidate.json']}
    provider = _SequenceLiveProvider([candidate, audit])
    try:
        result = run_ready_session_to_ifc(store=store, session=session.session_id,
            provider_factory=lambda: provider,
            bim_json_schema_version='bim-json/2.5')
        assert result.status == 'compiled', result
        model = ifcopenshell.open(str(result.ifc_path))
        actual = ifcopenshell.util.element.get_material(model.by_type('IfcDoor')[0], should_inherit=False)
        assert actual.is_a('IfcMaterialList')
        assert [m.Name for m in actual.Materials] == ['Steel', 'Wood']
        assert (tmp_path/'final-acceptance.json').is_file()
        assert (session.run_dir/'design-brief.json').read_bytes() == before
        expected = json.loads((session.run_dir/'expected-facts.json').read_text(encoding='utf-8'))
        assert expected['semantic_expectations'][0]['value'] == MATERIAL
        # Alter only the candidate; independent frozen Brief requirements stay unchanged.
        door['materials'][0]['materials'].pop()
        (session.run_dir/'generator/candidate.json').write_text(json.dumps(candidate), encoding='utf-8')
        negative = run_candidate_gate_stage(case_dir=session.run_dir, output_dir=tmp_path/'missing-name', case_id='missing-name')
        assert not negative['compile_reopen_success']
        verification = json.loads((tmp_path/'missing-name/semantic-verification.json').read_text(encoding='utf-8'))
        assert any(i['code'] == 'IFC_SEMANTIC_MISMATCH' and 'Wood' in i['message'] for i in verification['issues']), verification
        assert not (tmp_path/'missing-name/output.ifc').exists()
    finally:
        store.close()


def test_v25_rejects_staged_before_provider_call():
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    with pytest.raises(ValueError, match='legacy_full'):
        run_ready_session_to_ifc(store=None, session='unused', provider_factory=lambda: pytest.fail('called'),
            generation_strategy='staged', bim_json_schema_version='bim-json/2.5')


def test_v25_selected_contract_rejects_generator_downgrade(tmp_path):
    from tests.agent.test_generation_v24_route import fixture_candidate, prepare_source
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_generator_stage
    source = prepare_source(tmp_path)
    selection = tmp_path/'generation-contract.json'
    selection.write_text(selection.read_text(encoding='utf-8').replace('bim-json/2.4', 'bim-json/2.5'), encoding='utf-8')
    result = run_generator_stage(provider=SequenceProvider([fixture_candidate()]), output_dir=tmp_path/'generator',
        design_source_dir=source, case_id='downgrade')
    assert not result['valid']


def test_v25_changeset_draft_uses_matching_material_contract(tmp_path):
    from tests.agent.test_generation_v24_route import fixture_candidate
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.changeset_stage import run_changeset_stage
    draft = {'draft_version': 'bim-json-draft/1.5', 'target_schema_version': 'bim-json/2.5',
        'partial_document': {}, 'missing_facts': [{'entity_id': 'door-1', 'path': '/materials',
            'code': 'MISSING_MATERIAL_NAMES', 'message': 'Need the explicit names.'}],
        'losses': [], 'clarification_targets': [], 'provenance': {'source': 'test'}}
    candidate = fixture_candidate()
    candidate['schema_version'] = 'bim-json/2.5'
    result = run_changeset_stage(provider=SequenceProvider([draft]), output_dir=tmp_path, case_id='draft', call_index=1,
        user_request='Preserve the named materials.', conversation=[], design_brief={}, expected_facts={},
        candidate=candidate, base_revision={}, scope={'entity_ids': ['door-1'], 'relationship_ids': []}, issues=[])
    assert result['classification'] == 'draft', result
    inputs = json.loads((tmp_path/'prompt-render-input.json').read_text(encoding='utf-8'))
    assert inputs['FORMAL_SCHEMA']['properties']['schema_version']['const'] == 'bim-json/2.5'
    assert inputs['DRAFT_SCHEMA']['properties']['draft_version']['const'] == 'bim-json-draft/1.5'
