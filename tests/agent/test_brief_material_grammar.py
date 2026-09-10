"""Source material values must be executable before they become immutable authority."""
import copy
import json

import pytest

from text2ifc_agent.semantic_requirements import project_semantic_requirements
from tests.agent.test_semantic_authority_completeness import review, valid_brief


SINGLE = {'kind': 'single_material', 'name': 'Brick'}
LAYERED = {'kind': 'material_layer_set', 'layer_set_name': 'Assembly',
           'layers': [{'name': 'Brick', 'thickness': 180}, {'name': 'Finish', 'thickness': 20}]}
USAGE = {**LAYERED, 'kind': 'material_layer_set_usage', 'direction': 'AXIS2',
         'direction_sense': 'NEGATIVE', 'offset_from_reference_line': -100}


def source(record):
    return {'schema_version': 'text2ifc/design-brief/2.3', 'status': 'ready', 'known_facts': {
        'semantic_requirements': [record], 'semantic_review': review(material=True)}}


@pytest.mark.parametrize('identity', ['wall-elsewhere', 'door-elsewhere', 'slab-elsewhere'])
@pytest.mark.parametrize('value', [{}, None, [], {'name': 'Brick'},
    {'kind': 'single_material'}, {'kind': 'single_material', 'name': ''},
    {**SINGLE, 'strength': 0}, {**LAYERED, 'layers': []},
    {**LAYERED, 'layers': [{'name': 'Brick', 'thickness': 0}]},
    {**USAGE, 'direction': 'Y'}])
def test_malformed_material_is_not_frozen(identity, value):
    brief = source({'entity_id': identity, 'material': value})
    before = copy.deepcopy(brief)
    result = project_semantic_requirements(brief)
    assert not result['valid']
    assert any(i['code'] == 'SEMANTIC_MATERIAL_INCOMPLETE' for i in result['issues'])
    assert not any(e['kind'] == 'material' for e in result['expectations'])
    assert brief == before


@pytest.mark.parametrize('field', ['material', 'materials'])
@pytest.mark.parametrize('value', [SINGLE, LAYERED, USAGE])
def test_valid_single_and_layered_material_values_are_preserved(field, value):
    result = project_semantic_requirements(source({'entity_id': 'opaque-id',
        'scope': 'inherited', field: [value] if field == 'materials' else value}))
    assert result['valid'], result
    assert result['expectations'][0]['value'] == value
    assert result['expectations'][0]['scope'] == 'inherited'


@pytest.mark.parametrize('assignments', [[], [{}], [SINGLE, LAYERED]])
def test_legacy_assignment_array_cannot_hide_incomplete_or_multiple_values(assignments):
    result = project_semantic_requirements(source({'entity_id': 'opaque-id', 'materials': assignments}))
    assert not result['valid']
    assert not result['expectations']


@pytest.mark.parametrize('design_review', [False, True])
def test_public_brief_repair_can_remove_invalid_material_without_erasing_valid_requirement(tmp_path, design_review):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, brief = valid_brief()
    brief['schema_version'] = 'text2ifc/design-brief/2.3'
    brief['known_facts']['semantic_requirements'] = [{'entity_id': 'wall-keep', 'material': SINGLE}]
    brief['known_facts']['semantic_review'] = review(material=True)
    broken = copy.deepcopy(brief)
    broken['known_facts']['semantic_requirements'].append({'entity_id': 'window-other', 'material': {}})
    provider = SequenceProvider([broken, brief])
    result = run_design_brief_stage(provider=provider, output_dir=tmp_path, case=case,
        design_review_enabled=design_review, design_brief_schema_version=brief['schema_version'])
    assert result['valid'], result
    assert len(provider.calls) == 2
    assert json.loads((tmp_path/'design-brief.json').read_text(encoding='utf-8')) == brief
    assert json.loads((tmp_path/'parsed-output.json').read_text(encoding='utf-8')) == broken
