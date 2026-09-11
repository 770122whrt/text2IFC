"""Cross-storey IDs must reach authoring, packages and checks unchanged."""
import copy
import json
from pathlib import Path

import pytest

from text2ifc_agent.expected_facts import build_expected_facts, ExpectedFactsError
from text2ifc_agent.semantic_coverage import build_design_geometry_expectation as build_geometry_expectation


def _brief(stair_id='stair-north-flight', flight_ids=None, explicit_opening=True):
    stair = {'id': stair_id, 'from_storey': 'ground', 'to_storey': 'upper',
             'bounds': {'x': [1000, 2200], 'y': [1000, 6400]},
             'start_elevation_mm': 0, 'end_elevation_mm': 3150}
    if flight_ids is not None:
        stair['flight_ids'] = flight_ids
    opening = {'bounds': {'x': [800, 2400], 'y': [800, 6600]}}
    if explicit_opening:
        opening['id'] = 'upper-stair-void'
    return {'schema_version': 'text2ifc/design-brief/2.1', 'status': 'ready',
            'known_facts': {'storeys': [
                {'id': 'ground', 'name': '首层', 'elevation_mm': 0},
                {'id': 'upper', 'name': '二层', 'elevation_mm': 3150}],
                'stairs': [stair], 'floor_slabs': [{'id': 'upper-slab', 'storey': 'upper',
                    'top_elevation_mm': 3150, 'thickness_mm': 150,
                    'bounds': {'x': [0, 8000], 'y': [0, 9000]}, 'opening': opening}],
                'roof_slab': {'id': 'top-roof', 'bottom_elevation_mm': 6150,
                    'thickness_mm': 150, 'bounds': {'x': [0, 8000], 'y': [0, 9000]}}}}


@pytest.mark.parametrize('stair_id,flights', [
    ('stair-north-flight', ['stair-flight-north-flight']),
    ('stair-link', ['stair-flight-link']),
    ('north-link', ['north-link-flight']),
    ('北梯', ['北梯-flight']),
])
@pytest.mark.parametrize('explicit_opening', [True, False])
def test_contract_offers_same_opaque_ids_as_package_and_geometry(stair_id, flights, explicit_opening):
    brief = _brief(stair_id, explicit_opening=explicit_opening)
    frozen = copy.deepcopy(brief)
    expected = build_expected_facts(case_id='identity-family', design_brief=brief)
    contract = expected['entity_id_contract']
    assert contract['stairs'][0]['entity_id'] == stair_id
    assert [r['entity_id'] for r in contract['stair_flights']] == flights
    assert contract['stair_flights'][0]['parent_id'] == stair_id
    opening_id = 'upper-stair-void' if explicit_opening else 'opening-upper-slab-stair'
    assert contract['floor_openings'][0]['entity_id'] == opening_id
    assert contract['floor_openings'][0]['host_id'] == 'upper-slab'
    assert contract['floor_openings'][0]['identity_source'] == ('explicit' if explicit_opening else 'derived')
    cross = expected['generation_package_manifest']['packages'][-1]
    assert {stair_id, *flights, opening_id, 'upper-slab', 'top-roof'} <= set(cross['owned_component_ids'])
    geometry = build_geometry_expectation(case_id='identity-family', design_brief=brief, expected_facts=expected)
    assert geometry['stairs'][stair_id]['flight_ids'] == flights
    assert opening_id in geometry['floor_openings']
    assert brief == frozen


def test_explicit_children_keep_their_ids_and_order():
    expected = build_expected_facts(case_id='explicit', design_brief=_brief(flight_ids=['part-z', 'part-a']))
    assert [r['entity_id'] for r in expected['entity_id_contract']['stair_flights']] == ['part-z', 'part-a']


@pytest.mark.parametrize('failure', ['parent_child_collision', 'duplicate_child', 'shared_child', 'opening_collision'])
def test_ambiguous_role_identity_stops_projection(failure):
    brief = _brief()
    known = brief['known_facts']
    if failure == 'parent_child_collision':
        known['stairs'][0]['flight_ids'] = ['stair-north-flight']
    elif failure == 'duplicate_child':
        known['stairs'][0]['flight_ids'] = ['child', 'child']
    elif failure == 'shared_child':
        known['stairs'][0]['flight_ids'] = ['shared-child']
        known['stairs'].append({**known['stairs'][0], 'id': 'another-connection'})
    else:
        known['floor_slabs'][0]['opening']['id'] = 'upper-slab'
    with pytest.raises(ExpectedFactsError, match='IDENTITY'):
        build_expected_facts(case_id='ambiguous', design_brief=brief)


def test_public_generator_receives_cross_storey_ids_and_versioned_instruction(tmp_path):
    from text2ifc_agent.live_pipeline import run_generator_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    root = Path(__file__).resolve().parents[2]
    brief = _brief(flight_ids=['actual-child'])
    expected = build_expected_facts(case_id='offered', design_brief=brief)
    source = tmp_path/'design-brief'
    source.mkdir()
    (source/'input.txt').write_text('按确认的两层楼梯和洞口建模。', encoding='utf-8')
    for name, value in [('conversation', []), ('context-selection', {'evidence': []}), ('design-brief', brief)]:
        (source/f'{name}.json').write_text(json.dumps(value), encoding='utf-8')
    (tmp_path/'expected-facts.json').write_text(json.dumps(expected), encoding='utf-8')
    candidate = json.loads((root/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.1'
    # The fake payload is only to exercise prompt transport, not IFC acceptance.
    run_generator_stage(provider=SequenceProvider([candidate]), output_dir=tmp_path/'generator',
                        design_source_dir=source, case_id='offered')
    rendered = json.loads((tmp_path/'generator/prompt-render-input.json').read_text(encoding='utf-8'))
    assert rendered['ENTITY_ID_CONTRACT']['stair_flights'][0]['entity_id'] == 'actual-child'
    trace = json.loads((tmp_path/'generator/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id'] == 'bim-json-generator.v2.4'
    prompt = (tmp_path/'generator/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'entity_id' in prompt and 'parent_id' in prompt and 'host_id' in prompt


@pytest.mark.parametrize('failure', [None, 'wrong_parent', 'no_aggregate', 'duplicate_parent', 'unoffered_child', 'wrong_owner'])
def test_endpoint_names_follow_unique_frozen_parent_child_binding(failure):
    from tests.agent.test_cross_storey_name_boundary import _case, _gate
    candidate, expected = _case()
    expected['stairs'][0].update(id='parent-stair', flight_ids=['flight-a'])
    candidate['entities'].append({'id': 'parent-stair', 'ifc_class': 'IfcStair',
        'attributes': {'ObjectPlacement': {'relative_to': 'level-0'}}})
    relation = {'id': 'aggregate', 'ifc_class': 'IfcRelAggregates',
                'attributes': {'RelatingObject': 'parent-stair', 'RelatedObjects': ['flight-a']}}
    candidate['relationships'].append(relation)
    if failure == 'wrong_parent':
        relation['attributes']['RelatingObject'] = 'other'
    elif failure == 'no_aggregate':
        candidate['relationships'] = []
    elif failure == 'duplicate_parent':
        candidate['relationships'].append({**copy.deepcopy(relation), 'id': 'duplicate'})
    elif failure == 'unoffered_child':
        expected['stairs'][0]['flight_ids'] = ['other']
    elif failure == 'wrong_owner':
        candidate['entities'][-2]['attributes']['ObjectPlacement']['relative_to'] = 'level-1'
    assert (_gate(candidate, expected)['status'] == 'passed') is (failure is None)
