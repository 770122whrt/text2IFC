"""An explicit component frame may oppose the opening frame without an error."""
import copy
import pytest

from tests.ifc2text.test_component_hosted_public_chain import hosted_document
from tests.agent.test_phase6_3_dynamic_gates import _expected_facts
from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates


def scene(cls, rotated_host=False):
    candidate, label, storey = hosted_document(cls)
    entities = {e['id']: e for e in candidate['entities']}
    wall = entities['W001']['attributes']['ObjectPlacement']
    wall['origin'] = [100, 200, 0]
    if rotated_host: wall['ref_direction'] = [0, 1, 0]
    placement = entities[label]['attributes']['ObjectPlacement']
    placement.update(origin=[425, -100, 0], ref_direction=[-1, 0, 0])
    record = {'id': label, 'storey': storey, 'host_wall': 'W001', 'installation': 'hosted',
        'placement': {'origin': [200, 625, 500] if rotated_host else [525, 100, 500],
                      'axis': [0, 0, 1], 'ref_direction': [0, -1, 0] if rotated_host else [-1, 0, 0]}}
    expected = _expected_facts(storeys=[storey], doors=[record] if cls == 'IfcDoor' else [],
                               windows=[record] if cls == 'IfcWindow' else [])
    expected['generation_schema_version'] = 'bim-json/2.6'
    expected['semantic_expectations'] = [{'kind': 'component_geometry', 'entity_id': label,
        'value': copy.deepcopy(entities[label]['attributes']['Representation'])}]
    return candidate, expected, label


def gate(candidate, expected):
    return next(g for g in evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
                if g['name'] == 'dynamic_opening_fill')


@pytest.mark.parametrize('cls', ['IfcDoor', 'IfcWindow'])
@pytest.mark.parametrize('rotated_host', [False, True])
def test_requested_world_frame_can_have_reverse_opening_relative_direction(cls, rotated_host):
    candidate, expected, label = scene(cls, rotated_host)
    result = gate(candidate, expected)
    assert result['status'] == 'passed', result


@pytest.mark.parametrize('offset,passed', [(0.5, True), (1., True), (1.0001, False), (2., False)])
def test_world_frame_displacement_uses_fixed_one_mm_tolerance(offset, passed):
    candidate, expected, label = scene('IfcWindow', True)
    next(e for e in candidate['entities'] if e['id'] == label)['attributes']['ObjectPlacement']['origin'][0] += offset
    result = gate(candidate, expected)
    assert (result['status'] == 'passed') is passed, result
    if not passed: assert 'COMPONENT_WORLD_PLACEMENT_MISMATCH' in result['issue_codes']


@pytest.mark.parametrize('change', ['wrong-rotation', 'wrong-parent', 'missing-parent', 'cycle', 'tiny-candidate'])
def test_wrong_actual_frames_cannot_hide_behind_component_mode(change):
    candidate, expected, label = scene('IfcWindow', True)
    element = next(e for e in candidate['entities'] if e['id'] == label)
    pose = element['attributes']['ObjectPlacement']
    if change == 'wrong-rotation': pose['ref_direction'] = [1, 0, 0]
    elif change == 'wrong-parent': pose['relative_to'] = 'W001'
    elif change == 'missing-parent': pose['relative_to'] = 'absent'
    elif change == 'cycle': pose['relative_to'] = label
    elif change == 'tiny-candidate':
        pose['ref_direction'] = [1, 0, 0]
        representation = element['attributes']['Representation']
        representation['definitions'] = [{'id': 'tiny', 'profile': {'kind': 'rectangle', 'x': 1, 'y': 1},
            'position': {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref_direction': [1, 0, 0]},
            'direction': [0, 0, 1], 'depth': 1}]
        representation['parts'] = [{'id': 'tiny', 'role': 'solid', 'geometry_refs': ['tiny'],
            'placement': {'origin': [0, 0, 0], 'axis': [0, 0, 1], 'ref_direction': [1, 0, 0]}}]
    result = gate(candidate, expected)
    assert result['status'] == 'failed', result
    assert any(c in result['issue_codes'] for c in ('COMPONENT_WORLD_PLACEMENT_MISMATCH',
        'COMPONENT_WORLD_PLACEMENT_UNASSESSED', 'FILLING_PLACEMENT_CHAIN_MISMATCH'))


def test_without_public_component_expectation_old_rotation_rule_still_applies():
    candidate, expected, label = scene('IfcDoor')
    expected['semantic_expectations'] = []
    result = gate(candidate, expected)
    assert 'FILLING_RELATIVE_ROTATION_MISMATCH' in result['issue_codes']
