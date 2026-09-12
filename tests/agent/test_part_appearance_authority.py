"""Frozen request/role/authorization family for part appearance 2.5/2.2."""
import copy
import pytest

from tests.agent.test_brief_semantic_roles import brief_with_roles
from tests.agent.test_semantic_authority_completeness import review
from text2ifc_agent.semantic_requirements import project_semantic_requirements, generation_schema_version, unauthorized_candidate_semantics


def brief():
    b = brief_with_roles(); b['schema_version'] = 'text2ifc/design-brief/2.5'
    b['known_facts']['plan_constraints'] = []
    b['known_facts']['semantic_requirements'] = [{'entity_id': 'opaque-door',
        'part_appearance': {'frame': {'color': [.2, .3, .4]}, 'panel': {'transparency': 0}},
        'template': {'template_id': 'door-left', 'template_version': 'text2ifc/basic-filling/1.0'}}]
    b['known_facts']['semantic_review'] = review(appearance=True, template=True)
    return b


def test_projection_freezes_exact_parts_and_new_version_without_mutation():
    b = brief(); before = copy.deepcopy(b); result = project_semantic_requirements(b)
    assert result['valid'], result
    assert generation_schema_version(b) == 'bim-json/2.2'
    assert next(r['value'] for r in result['expectations'] if r['kind'] == 'part_appearance') == b['known_facts']['semantic_requirements'][0]['part_appearance']
    assert b == before


@pytest.mark.parametrize('attack', ['old', 'type', 'wall', 'inherited', 'wrong_part', 'whole', 'type_whole', 'no_template', 'duplicate_value', 'malformed'])
def test_invalid_or_ambiguous_part_requests_block_before_generation(attack):
    b = brief(); k = b['known_facts']; r = k['semantic_requirements'][0]
    if attack == 'old': b['schema_version'] = 'text2ifc/design-brief/2.4'
    if attack == 'type': r['entity_id'] = 'opaque-door-type'
    if attack == 'wall': r['entity_id'] = 'opaque-wall'
    if attack == 'inherited': r['scope'] = 'inherited'
    if attack == 'wrong_part': r['part_appearance']['glazing'] = {'transparency': .4}
    if attack == 'whole': k['semantic_requirements'].append({'entity_id': 'opaque-door', 'appearance': {'color': [0, 0, 0]}})
    if attack == 'type_whole':
        r['type_id'] = 'opaque-door-type'; k['semantic_review'] = review(appearance=True, template=True, type=True)
        k['semantic_requirements'].append({'entity_id': 'opaque-door-type', 'appearance': {'color': [0, 0, 0]}})
    if attack == 'no_template': r.pop('template'); k['semantic_review'] = review(appearance=True)
    if attack == 'duplicate_value':
        other = copy.deepcopy(r); other['part_appearance']['frame']['color'][0] = .9
        k['semantic_requirements'].append(other)
    if attack == 'malformed': r['part_appearance']['frame']['color'][0] = True
    assert not project_semantic_requirements(b)['valid']


def test_authorization_is_per_part_and_channel_not_just_entity():
    expectations = project_semantic_requirements(brief())['expectations']
    requested = next(e['value'] for e in expectations if e['kind'] == 'part_appearance')
    candidate = {'schema_version': 'bim-json/2.2', 'entities': [{'id': 'opaque-door', 'ifc_class': 'IfcDoor', 'part_appearance': copy.deepcopy(requested)}], 'relationships': []}
    assert not unauthorized_candidate_semantics(candidate, expectations)
    candidate['entities'][0]['part_appearance']['frame']['transparency'] = .5
    assert any(i['code'] == 'UNREQUESTED_PART_APPEARANCE' for i in unauthorized_candidate_semantics(candidate, expectations))
