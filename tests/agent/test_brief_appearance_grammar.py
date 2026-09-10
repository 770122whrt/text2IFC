"""Typed source appearance must match the executable IFC authoring contract."""
import copy
import json

import pytest

from text2ifc_agent.semantic_requirements import project_semantic_requirements
from tests.agent.test_semantic_authority_completeness import review, valid_brief


@pytest.mark.parametrize('identity', ['wall-opaque', 'window-opaque', 'door-opaque'])
@pytest.mark.parametrize('value', [
    {'frame_color': 'dark', 'glazing_transparency': 'clear'},
    {'profile': 'warm-residential'}, {'color': 'warm white'},
    {'color': [.1, .2]}, {'color': [0, 1, 1.1]},
    {'transparency': 'transparent'}, {'transparency': None}, {}, [],
])
def test_non_executable_appearance_is_not_frozen_as_authority(identity, value):
    brief = {'schema_version': 'text2ifc/design-brief/2.2', 'status': 'ready', 'known_facts': {
        'semantic_requirements': [{'entity_id': identity, 'appearance': value}],
        'semantic_review': review(appearance=True)}}
    before = copy.deepcopy(brief)
    result = project_semantic_requirements(brief)
    assert not result['valid']
    assert any(i['code'] == 'SEMANTIC_AUTHORITY_APPEARANCE_INVALID' for i in result['issues'])
    assert not any(e['kind'] == 'appearance' for e in result['expectations'])
    assert brief == before


@pytest.mark.parametrize('value', [{'color': [0, 0, 0]}, {'color': [1, 1, 1], 'transparency': 0},
                                 {'transparency': 1}, {'transparency': .65}])
def test_legal_whole_element_numeric_overrides_remain_supported(value):
    brief = {'schema_version': 'text2ifc/design-brief/2.2', 'status': 'ready', 'known_facts': {
        'semantic_requirements': [{'entity_id': 'explicit-element', 'appearance': value}],
        'semantic_review': review(appearance=True)}}
    result = project_semantic_requirements(brief)
    assert result['valid'], result
    assert result['expectations'][0]['value'] == value


@pytest.mark.parametrize('design_review', [False, True])
@pytest.mark.parametrize('repair', [False, True])
def test_new_public_brief_contract_keeps_part_style_in_theme_notes(tmp_path, design_review, repair):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, brief = valid_brief()
    brief['schema_version'] = 'text2ifc/design-brief/2.3'
    brief['known_facts']['appearance'] = {'profile': 'warm-residential',
        'style_notes': 'Use the selected theme and basic template: dark frame, clear glazing.'}
    broken = copy.deepcopy(brief)
    if repair:
        broken['known_facts']['semantic_requirements'] = [
            {'entity_id': 'window-opaque', 'appearance': {'frame_color': 'dark'}}]
        broken['known_facts']['semantic_review'] = review(appearance=True)
    provider = SequenceProvider([broken, brief] if repair else [brief])
    result = run_design_brief_stage(provider=provider, output_dir=tmp_path,
        case=case, design_review_enabled=design_review, design_brief_schema_version=brief['schema_version'])
    assert result['valid'], result
    assert len(provider.calls) == 1 + repair
    assert json.loads((tmp_path/'design-brief.json').read_text(encoding='utf-8')) == brief
    if repair:
        rendered = json.loads((tmp_path/'semantic-repair/prompt-render-input.json').read_text(encoding='utf-8'))
        assert rendered['ELEMENT_APPEARANCE_SCHEMA']['additionalProperties'] is False
        assert set(rendered['ELEMENT_APPEARANCE_SCHEMA']['properties']) == {'color','transparency'}
