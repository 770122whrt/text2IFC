"""Request-owned identity aliases must bind uniquely without changing values."""
import copy
import json

import pytest

from text2ifc_agent.live_pipeline import run_candidate_gate_stage
from tests.agent.test_generation_semantic_closure import setup_case


@pytest.mark.parametrize('identity', ['wall-1', 'wall-storey-1-wall-1'])
@pytest.mark.parametrize('actual', ['60', '30'])
def test_public_gate_binds_frozen_identity_and_still_reads_value(tmp_path, identity, actual):
    candidate = setup_case(tmp_path, actual)
    candidate = json.loads(json.dumps(candidate).replace('"wall-1"', json.dumps(identity)))
    (tmp_path / 'generator/candidate.json').write_text(json.dumps(candidate), encoding='utf-8')
    frozen = {'entity_id_contract': {'walls': [
        {'brief_id': 'wall-1', 'entity_id': 'wall-storey-1-wall-1', 'storey': 'storey-1'}]}}
    path = tmp_path / 'expected-facts.json'
    path.write_text(json.dumps(frozen), encoding='utf-8')
    frozen_bytes = path.read_bytes()
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='identity-family')
    assert result['compile_reopen_success'] is (actual == '60')
    assert path.read_bytes() == frozen_bytes


@pytest.mark.parametrize('scenario', ['canonical', 'legacy', 'both', 'duplicate-storeys', 'wrong-family', 'unoffered'])
def test_identity_binding_is_unique_and_family_scoped(scenario):
    from text2ifc_agent.semantic_requirements import bind_semantic_targets

    contract = {'walls': [{'brief_id': 'w', 'entity_id': 'wall-s1-w', 'storey': 's1'}]}
    entities = [{'id': 'wall-s1-w', 'ifc_class': 'IfcWallStandardCase'}]
    if scenario == 'legacy':
        entities[0]['id'] = 'w'
    elif scenario == 'both':
        entities.append({'id': 'w', 'ifc_class': 'IfcWall'})
    elif scenario == 'duplicate-storeys':
        contract['walls'].append({'brief_id': 'w', 'entity_id': 'wall-s2-w', 'storey': 's2'})
        entities.append({'id': 'wall-s2-w', 'ifc_class': 'IfcWall'})
    elif scenario == 'wrong-family':
        entities[0]['ifc_class'] = 'IfcSlab'
    elif scenario == 'unoffered':
        entities[0]['id'] = 'arbitrary-w'
    request = {'expectations': [{'entity_id': 'w', 'kind': 'material', 'scope': 'direct',
                                'value': {'kind': 'single_material', 'name': 'brick'}}],
               'entity_id_contract': contract, 'issues': []}
    frozen = copy.deepcopy(request['expectations'])
    bound = bind_semantic_targets({'entities': entities}, request)
    assert request['expectations'] == frozen
    if scenario in {'canonical', 'legacy'}:
        assert bound['issues'] == []
        assert bound['expectations'][0]['entity_id'] == entities[0]['id']
        assert bound['expectations'][0]['value'] == frozen[0]['value']
    else:
        assert bound['issues']


@pytest.mark.parametrize('wall_class', ['IfcWall', 'IfcWallStandardCase', 'IfcSlab'])
@pytest.mark.parametrize('wrong_host', [False, True])
def test_dynamic_host_binding_and_wall_family(wall_class, wrong_host):
    from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates
    from tests.agent.test_phase6_3_dynamic_gates import _candidate, _expected_facts
    expected = _expected_facts(storeys=['storey-1'], doors=[
        {'id': 'door-1', 'storey': 'storey-1', 'host_wall': 'w'}], windows=[])
    expected['walls'] = [{'id': 'w', 'storey': 'storey-1'}]
    expected['total_counts']['IfcWall'] = 1
    expected['entity_id_contract'] = {'walls': [
        {'brief_id': 'w', 'entity_id': 'wall-storey-1-w', 'storey': 'storey-1'}]}
    candidate = _candidate(storeys=['storey-1'], walls=[('wall-storey-1-w', 'storey-1'), ('other', 'storey-1')],
                           doors=[('door-1', 'storey-1', 'other' if wrong_host else 'wall-storey-1-w')],
                           windows=[], include_opening_relationships=True)
    for entity in candidate['entities']:
        if entity['id'] in {'wall-storey-1-w', 'other'}:
            entity['ifc_class'] = wall_class
    gates = evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
    assert all(g['status'] != 'failed' for g in gates) is (wall_class != 'IfcSlab' and not wrong_host)


@pytest.mark.parametrize('canonical', [False, True])
@pytest.mark.parametrize('wrong_geometry', [False, True])
def test_reopened_geometry_uses_frozen_id_contract(tmp_path, canonical, wrong_geometry):
    from text2ifc_agent.expected_facts import build_expected_facts
    from tests.agent.test_phase6_2_fix_semantic_fidelity import _outside_boundary_design_brief, _outside_boundary_center_overlap_candidate
    brief = _outside_boundary_design_brief()
    candidate = _outside_boundary_center_overlap_candidate()
    expected = build_expected_facts(case_id='geometry-identity', design_brief=brief)
    if wrong_geometry:
        space = next(e for e in candidate['entities'] if e['ifc_class'] == 'IfcSpace')
        space['attributes']['ObjectPlacement']['origin'][0] += 1000
    if canonical:
        aliases = {r['brief_id']: r['entity_id'] for records in expected['entity_id_contract'].values() for r in records}
        def replace(value):
            if isinstance(value, str):
                return aliases.get(value, value)
            if isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            if isinstance(value, list):
                return [replace(v) for v in value]
            return value
        candidate = replace(candidate)
    (tmp_path / 'generator').mkdir()
    for name, value in [('generator/candidate.json', candidate), ('design-brief.json', brief), ('expected-facts.json', expected)]:
        (tmp_path / name).write_text(json.dumps(value), encoding='utf-8')
    frozen = (tmp_path / 'expected-facts.json').read_bytes()
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='geometry-identity')
    assert result['geometry_success'] is not wrong_geometry
    assert (tmp_path / 'expected-facts.json').read_bytes() == frozen


@pytest.mark.parametrize('scenario', ['both-ids', 'wrong-class', 'duplicate-contract'])
def test_dynamic_identity_contract_cannot_select_ambiguous_or_wrong_target(scenario):
    from text2ifc_agent.dynamic_gates import _CandidateGraph, _resolve_expected_entity
    from tests.agent.test_phase6_3_dynamic_gates import _entity
    entries = [{'brief_id': 'room', 'entity_id': 'space-level-a-room', 'storey': 'level-a'}]
    entities = [_entity('level-a', 'IfcBuildingStorey', None),
                _entity('space-level-a-room', 'IfcSpace', 'level-a')]
    if scenario == 'both-ids':
        entities.append(_entity('room', 'IfcSpace', 'level-a'))
    elif scenario == 'wrong-class':
        entities[1]['ifc_class'] = 'IfcSlab'
    elif scenario == 'duplicate-contract':
        entries.append({'brief_id': 'room', 'entity_id': 'other-space', 'storey': 'level-a'})
    match = _resolve_expected_entity(graph=_CandidateGraph({'entities': entities, 'relationships': []}),
                                     expected_facts={'entity_id_contract': {'spaces': entries}},
                                     collection='spaces', record={'id': 'room', 'storey': 'level-a'})
    assert match is None


def test_dynamic_repeated_brief_id_resolves_by_explicit_storey():
    from text2ifc_agent.dynamic_gates import _CandidateGraph, _resolve_expected_entity
    from tests.agent.test_phase6_3_dynamic_gates import _entity
    entries = [{'brief_id': 'room', 'entity_id': f'space-{level}-room', 'storey': level}
               for level in ['level-a', 'level-b']]
    entities = [_entity(level, 'IfcBuildingStorey', None) for level in ['level-a', 'level-b']]
    entities += [_entity(e['entity_id'], 'IfcSpace', e['storey']) for e in entries]
    for entry in entries:
        match = _resolve_expected_entity(graph=_CandidateGraph({'entities': entities, 'relationships': []}),
                                         expected_facts={'entity_id_contract': {'spaces': entries}},
                                         collection='spaces', record={'id': 'room', 'storey': entry['storey']})
        assert match['candidate_id'] == entry['entity_id']
