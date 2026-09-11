"""A connecting stair may name only its frozen endpoints, not arbitrary floors."""
import copy

import pytest

from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates


def _case(labels=('首层', '二层', '三层'), kind='IfcStairFlight'):
    storeys = [{'id': f'level-{i}', 'name': label} for i, label in enumerate(labels)]
    candidate = {'entities': [
        *[{'id': s['id'], 'ifc_class': 'IfcBuildingStorey', 'attributes': {'Name': s['name']}} for s in storeys],
        {'id': 'flight-a', 'ifc_class': kind, 'attributes': {
            'Name': f'{labels[0]}至{labels[1]}楼梯', 'ObjectPlacement': {'relative_to': 'level-0'}}}],
        'relationships': []}
    expected = {'storeys': storeys, 'stairs': [{'id': 'flight-a', 'from_storey': 'level-0', 'to_storey': 'level-1'}]}
    return candidate, expected


def _gate(candidate, expected):
    return next(g for g in evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
                if g['name'] == 'dynamic_storey_name_consistency')


@pytest.mark.parametrize('labels', [('首层', '二层', '三层'), ('Ground', 'Upper', 'Roof'), ('地下层', '夹层', '屋顶层')])
@pytest.mark.parametrize('kind', ['IfcStair', 'IfcStairFlight'])
def test_frozen_stair_endpoint_names_are_valid(labels, kind):
    candidate, expected = _case(labels, kind)
    before = copy.deepcopy(candidate)
    assert _gate(candidate, expected)['status'] == 'passed'
    assert candidate == before


@pytest.mark.parametrize('failure', ['unrelated', 'missing', 'duplicate',
                                   'wrong_owner', 'wall', 'wrong_destination', 'candidate_claim'])
def test_endpoint_exception_cannot_hide_wrong_or_unproven_names(failure):
    candidate, expected = _case()
    stair = candidate['entities'][-1]
    if failure == 'unrelated':
        stair['attributes']['Name'] += '三层'
    elif failure == 'missing':
        expected['stairs'] = []
    elif failure == 'duplicate':
        expected['stairs'] *= 2
    elif failure == 'wrong_owner':
        stair['attributes']['ObjectPlacement']['relative_to'] = 'level-1'
    elif failure == 'wall':
        stair['ifc_class'] = 'IfcWall'
    elif failure == 'wrong_destination':
        expected['stairs'][0]['to_storey'] = 'level-2'
    else:
        expected['stairs'] = []
        stair['attributes']['to_storey'] = 'level-1'
    assert _gate(candidate, expected)['status'] == 'failed'
