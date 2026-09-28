"""Geometry repair authorizes only the reported wall or filling's placement."""
import copy
import json

import pytest

from text2ifc_agent.live_pipeline import _repair_allowed_change_paths, _repair_evidence_by_path
from text2ifc_agent.fact_delta import evaluate_repair_fact_delta
from text2ifc_agent.failure_routing import route_generation_failure
from tests.agent.test_component_world_placement import scene, gate
from text2ifc_contract.placement import world_transform_for


@pytest.mark.parametrize('code', ['WALL_OUTLINE_MISMATCH','FILLING_PLACEMENT_CHAIN_MISMATCH'])
def test_measured_geometry_defects_have_a_bounded_repair_route(code):
    candidate, expected, label = scene('IfcDoor')
    result = route_generation_failure(previous_candidate=candidate, validation_feedback=[],
        geometry_feedback=[{'code':code,'path':'/walls/W001'}], known_facts={})
    assert result['route']=='repair_attempted',result


@pytest.mark.parametrize('cls', ['IfcDoor','IfcWindow'])
def test_reparent_requires_the_complete_pose_but_cannot_change_parts(cls):
    candidate, expected, label = scene(cls)
    index = next(i for i,e in enumerate(candidate['entities']) if e['id']==label)
    correct = copy.deepcopy(candidate)
    matrix = world_transform_for(candidate,label)
    storey = next(e['id'] for e in candidate['entities'] if e['ifc_class']=='IfcBuildingStorey')
    candidate['entities'][index]['attributes']['ObjectPlacement'] = {
        'relative_to':storey, 'origin':[matrix[i][3] for i in range(3)],
        'axis':[matrix[i][2] for i in range(3)],'ref_direction':[matrix[i][0] for i in range(3)]}
    issue = next(i for i in gate(candidate,expected)['issues'] if i['code']=='FILLING_PLACEMENT_CHAIN_MISMATCH')
    paths = _repair_allowed_change_paths([issue],candidate=candidate)
    assert f'/entities/{index}/attributes/ObjectPlacement' in paths
    evidence = _repair_evidence_by_path([issue],paths)
    result = evaluate_repair_fact_delta(before=candidate,after=correct,allowed_change_paths=paths,evidence_by_path=evidence)
    assert result['valid'],result
    assert gate(correct,expected)['status']=='passed'
    wrong = copy.deepcopy(correct)
    wrong['entities'][index]['attributes']['Representation']['parts'][0]['role']='changed'
    assert not evaluate_repair_fact_delta(before=candidate,after=wrong,allowed_change_paths=paths,evidence_by_path=evidence)['valid']


def test_unknown_or_unmeasured_geometry_does_not_gain_a_repair_route():
    result = route_generation_failure(previous_candidate={'entities':[]}, validation_feedback=[],
        geometry_feedback=[{'code':'WALL_OUTLINE_UNASSESSED','path':'/walls/x'}],known_facts={})
    assert result['route']=='blocked_failure'


@pytest.mark.parametrize('cls', ['IfcDoor','IfcWindow'])
def test_production_repair_stage_can_rebase_a_reported_filling(tmp_path, cls):
    from tests.agent.test_component_requirements_v26 import component_brief
    from tests.agent.test_generation_v24_route import prepare_source
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    from text2ifc_agent.live_pipeline import run_generator_stage, run_repair_stage
    candidate, expected, label = scene(cls)
    correct = copy.deepcopy(candidate)
    element = next(e for e in candidate['entities'] if e['id']==label)
    element['attributes']['ObjectPlacement']['relative_to'] = next(
        e['id'] for e in candidate['entities'] if e['ifc_class']=='IfcBuildingStorey')
    issue = next(i for i in gate(candidate,expected)['issues'] if i['code']=='FILLING_PLACEMENT_CHAIN_MISMATCH')
    source = prepare_source(tmp_path,selected=False)
    (source/'design-brief.json').write_text(json.dumps(component_brief()),encoding='utf-8')
    result = run_generator_stage(provider=SequenceProvider([candidate]),output_dir=tmp_path/'generator',
        design_source_dir=source,case_id='offline-rebase')
    assert result['valid'],result
    before = (tmp_path/'generator/candidate.json').read_bytes()
    provider = SequenceProvider([correct])
    result = run_repair_stage(provider_factory=lambda:provider,output_dir=tmp_path/'repair',
        generator_source_dir=tmp_path/'generator',case_id='offline-rebase',geometry_feedback=[issue])
    assert result['valid'],result
    assert result['provider_call_count']==1
    repaired = json.loads((tmp_path/'repair/repaired-candidate.json').read_text(encoding='utf-8'))
    assert repaired==correct
    assert gate(repaired,expected)['status']=='passed'
    assert before==(tmp_path/'generator/candidate.json').read_bytes()
