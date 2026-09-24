"""Storey aliases may change labels, never actual membership or identity uniqueness."""
import copy

import pytest

from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates


def scene():
    expected = {'storeys': [{'id': 'S01', 'name': 'Ground'}, {'id': 'S02', 'name': 'Upper'}],
        'walls': [{'id': 'W001', 'storey': 'S01'}],
        'entity_id_contract': {'walls': [{'brief_id': 'W001', 'entity_id': 'wall-S01-w001', 'storey': 'S01'}]}}
    candidate = {'entities': [
        {'id': 'storey-S01', 'ifc_class': 'IfcBuildingStorey', 'attributes': {'Name': 'Ground'}},
        {'id': 'storey-S02', 'ifc_class': 'IfcBuildingStorey', 'attributes': {'Name': 'Upper'}},
        {'id': 'wall-S01-w001', 'ifc_class': 'IfcWall', 'attributes': {
            'Name': 'Ground wall', 'ObjectPlacement': {'relative_to': 'storey-S01'}}}],
        'relationships': [{'id': 'containment', 'ifc_class': 'IfcRelContainedInSpatialStructure',
            'attributes': {'RelatingStructure': 'storey-S01', 'RelatedElements': ['wall-S01-w001']}}]}
    return expected, candidate


def gates(expected, candidate):
    return {g['name']: g for g in evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)}


def test_exact_prefixed_storey_alias_passes_without_modifying_inputs():
    expected, candidate = scene()
    before = copy.deepcopy((expected, candidate))
    result = gates(expected, candidate)
    assert result['dynamic_storey_containment']['status'] == 'passed', result
    assert result['dynamic_storey_name_consistency']['status'] == 'passed'
    assert (expected, candidate) == before
    assert result['dynamic_storey_containment']['storey_matches'][0] == {
        'brief_id': 'S01', 'candidate_id': 'storey-S01', 'match_basis': 'exact_storey_prefix_alias'}


def test_aliases_do_not_hide_wrong_storey_containment():
    expected, candidate = scene()
    candidate['relationships'][0]['attributes']['RelatingStructure'] = 'storey-S02'
    result = gates(expected, candidate)['dynamic_storey_containment']
    assert result['status'] == 'failed'
    assert any(i['code'] == 'STOREY_CONTAINMENT_MISMATCH' and i.get('path') == '/walls/W001/storey' for i in result['issues'])


def test_aliases_do_not_disable_storey_name_gate():
    expected, candidate = scene()
    candidate['entities'][2]['attributes']['Name'] = 'Upper wall'
    result = gates(expected, candidate)['dynamic_storey_name_consistency']
    assert result['status'] == 'failed' and result['issue_codes'] == ['STOREY_NAME_CONFLICT']


@pytest.mark.parametrize('variant', ['both_ids', 'duplicate_id', 'wrong_class', 'brief_collision', 'fabricated_provenance'])
def test_ambiguous_or_unoffered_storey_identity_cannot_pass(variant):
    expected, candidate = scene()
    if variant == 'both_ids':
        candidate['entities'].append({'id': 'S01', 'ifc_class': 'IfcBuildingStorey', 'attributes': {}})
    elif variant == 'duplicate_id':
        candidate['entities'].append(copy.deepcopy(candidate['entities'][0]))
    elif variant == 'wrong_class':
        candidate['entities'][0]['ifc_class'] = 'IfcBuilding'
    elif variant == 'brief_collision':
        expected['storeys'].append({'id': 'storey-S01'})
    else:
        candidate['entities'][0]['id'] = 'arbitrary-floor'
        candidate['entities'][0]['provenance'] = {'brief_id': 'S01'}
        candidate['relationships'][0]['attributes']['RelatingStructure'] = 'arbitrary-floor'
        candidate['entities'][2]['attributes']['ObjectPlacement']['relative_to'] = 'arbitrary-floor'
    assert gates(expected, candidate)['dynamic_storey_containment']['status'] == 'failed'


def test_exact_original_storey_id_still_passes():
    expected, candidate = scene()
    candidate['entities'][0]['id'] = 'S01'
    candidate['relationships'][0]['attributes']['RelatingStructure'] = 'S01'
    candidate['entities'][2]['attributes']['ObjectPlacement']['relative_to'] = 'S01'
    assert gates(expected, candidate)['dynamic_storey_containment']['status'] == 'passed'


def test_storey_alias_offer_is_frozen_before_candidate_generation():
    from text2ifc_agent.expected_facts import build_expected_facts
    brief = {'schema_version': 'text2ifc/design-brief/1.0', 'status': 'ready',
        'known_facts': {'storeys': [{'id': 'ground-east', 'elevation_mm': 0}]}}
    expected = build_expected_facts(case_id='alias-offer', design_brief=brief)
    assert expected['entity_id_contract']['storeys'] == [{
        'brief_id': 'ground-east', 'entity_id': 'ground-east',
        'aliases': ['ground-east', 'storey-ground-east'], 'ifc_class': 'IfcBuildingStorey'}]


@pytest.mark.parametrize('wrong_floor', [False, True])
def test_reopened_space_geometry_binds_storey_alias_without_accepting_wrong_floor(tmp_path, wrong_floor):
    import json
    from pathlib import Path
    from text2ifc_agent.semantic_requirements import bind_geometry_targets
    from text2ifc_compiler import compile_document
    from text2ifc_quality.generated_ifc import check_generated_ifc
    root = Path(__file__).resolve().parents[2]
    candidate = json.loads((root/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8').replace('"storey-1"', '"storey-S01"'))
    upper = copy.deepcopy(next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcBuildingStorey'))
    upper['id'] = 'storey-S02'
    candidate['entities'].append(upper)
    if wrong_floor:
        next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcSpace')['attributes']['ObjectPlacement']['relative_to'] = 'storey-S02'
    expected = {'storeys': [{'id': 'S01'}, {'id': 'S02'}]}
    geometry = {'complete': True, 'tolerance': .001, 'spaces': {'space-1': {
        'ifc_class': 'IfcSpace', 'storey_id': 'S01'}}, 'walls': {}}
    before = copy.deepcopy(geometry)
    bound = bind_geometry_targets(candidate, expected, geometry)
    compiled = compile_document(candidate, tmp_path/'candidate.ifc')
    assert compiled.success, compiled
    checked = check_generated_ifc(compiled.output_path, bound)
    assert checked.success is not wrong_floor, checked.issues
    if wrong_floor:
        assert any(i['code'] == 'PRODUCT_STOREY_MISMATCH' for i in checked.issues)
    assert geometry == before
    assert bound['spaces']['space-1']['storey_id'] == 'storey-S01'


def test_geometry_cannot_resolve_ambiguous_storey_and_keeps_requested_bounds():
    from text2ifc_agent.semantic_requirements import bind_geometry_targets
    expected, candidate = scene()
    candidate['entities'].append({'id': 'S01', 'ifc_class': 'IfcBuildingStorey', 'attributes': {}})
    geometry = {'complete': True, 'products': {'p': {'storey_id': 'S01', 'bbox': {'x': [0,1]}}}}
    bound = bind_geometry_targets(candidate, expected, geometry)
    assert not bound['complete']
    assert any(x['reason'] == 'STOREY_IDENTITY_AMBIGUOUS' for x in bound['unresolved'])
    assert bound['products']['p']['bbox'] == geometry['products']['p']['bbox']
