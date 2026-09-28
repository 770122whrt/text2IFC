"""Explicit world elevations have the same meaning in interval and endpoint form."""
import copy
import json
import math

import pytest

from tests.agent.test_space_geometry_projection_v12 import brief, derive

VERSION = "text2ifc/design-geometry-expectation/1.3"


def endpoint_brief():
    value = brief()
    room = value['known_facts']['storeys'][0]['spaces'][0]
    room.pop('z_mm')
    room.update(z_min_mm=-1140.0004, z_max_mm=1298.4004)
    return value


def test_world_endpoints_survive_without_storey_height_or_mutation():
    value = endpoint_brief()
    before = copy.deepcopy(value)
    result = derive(value, schema_version=VERSION)
    assert result['complete'], result['unresolved']
    assert result['spaces']['room-a']['bbox']['z'] == [-1.1400004, 1.2984004]
    assert result['tolerance'] == .001
    assert value == before


@pytest.mark.parametrize('patch', [
    {'z_min_mm': None}, {'z_max_mm': True}, {'z_min_mm': math.nan},
    {'z_max_mm': math.inf}, {'z_max_mm': -1140.0004}, {'z_min_mm': 9999},
    {'z_mm': [0, 3000]}, {'height_mm': 3000},
])
def test_invalid_or_conflicting_explicit_endpoints_never_use_storey_fallback(patch):
    value = endpoint_brief()
    floor = value['known_facts']['storeys'][0]
    floor['net_height_mm'] = 3000
    floor['spaces'][0].update(patch)
    result = derive(value, schema_version=VERSION)
    assert not result['complete'] and not result['spaces']
    assert result['unresolved'][0]['reason'] == 'space_geometry_invalid_or_conflicting'


@pytest.mark.parametrize('missing', ['z_min_mm', 'z_max_mm'])
def test_half_endpoint_pair_is_not_an_inferred_interval(missing):
    value = endpoint_brief()
    del value['known_facts']['storeys'][0]['spaces'][0][missing]
    result = derive(value, schema_version=VERSION)
    assert not result['complete'] and not result['spaces']


def test_matching_interval_and_endpoints_agree():
    value = endpoint_brief()
    value['known_facts']['storeys'][0]['spaces'][0]['z_mm'] = [-1140.0004, 1298.4004]
    assert derive(value, schema_version=VERSION)['complete']


def test_old_version_replays_old_missing_result():
    result = derive(endpoint_brief(), schema_version='text2ifc/design-geometry-expectation/1.2')
    assert not result['complete'] and not result['spaces']


def test_public_component_case_selects_new_expectation(tmp_path):
    from text2ifc_agent.expected_facts import build_expected_facts
    from text2ifc_agent.live_pipeline import _semantic_geometry_expectation_from_case
    from tests.agent.test_component_requirements_v26 import component_brief
    value = component_brief()
    review = value['known_facts']['semantic_review']
    for entry in review.values():
        entry['status'] = 'not_specified'
    value['known_facts'] = {**endpoint_brief()['known_facts'], 'semantic_review': review,
                            'semantic_requirements': [], 'plan_constraints': value['known_facts']['plan_constraints']}
    facts = build_expected_facts(case_id='independent', design_brief=value)
    (tmp_path/'design-brief.json').write_text(json.dumps(value), encoding='utf-8')
    (tmp_path/'expected-facts.json').write_text(json.dumps(facts), encoding='utf-8')
    candidate = {'entities': [
        {'id': 'ground', 'ifc_class': 'IfcBuildingStorey', 'attributes': {'Elevation': -200}},
        {'id': 'room-a', 'ifc_class': 'IfcSpace', 'attributes': {}}], 'relationships': []}
    result = _semantic_geometry_expectation_from_case(case_root=tmp_path, case_id='independent', candidate=candidate)
    assert result['schema_version'] == VERSION
    assert result['complete'], result['unresolved']
