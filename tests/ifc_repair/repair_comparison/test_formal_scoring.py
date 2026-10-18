"""Independent synthetic evaluator controls, never formal-model evidence."""
from __future__ import annotations

from collections import Counter
import copy
import importlib
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
from ifcopenshell.api.root import remove_product
from ifcopenshell.util.element import copy as copy_entity, copy_deep
import pytest
import numpy as np

from tests.ifc_repair.repair_comparison.test_preparation import sample
from scripts.ifc_repair.repair_comparison.contracts import sha256
from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot, relation_evidence


def scorer():
    return importlib.import_module('scripts.ifc_repair.repair_comparison.formal_scoring')


@pytest.fixture
def cases(sample):
    """Author a small family from a hand-built source, not formal benchmark G."""
    root, source, _ = sample

    def build(kinds=('door',), keep_opening=True, reference_rotation_deg=0, host_rotation_deg=0):
        case = root / ('case-' + '-'.join(kinds) + str(keep_opening))
        private = case / 'private'
        (private / 'mutation').mkdir(parents=True)
        model = ifcopenshell.open(str(source))
        template = model.by_type('IfcDoor')[0]
        template_opening = model.by_type('IfcOpeningElement')[0]
        wall = model.by_type('IfcWall')[0]
        previous_placement=wall.ObjectPlacement
        wall.ObjectPlacement = copy_deep(model,previous_placement)
        model.remove(previous_placement)
        host_angle=math.radians(host_rotation_deg)
        wall.ObjectPlacement.RelativePlacement.Axis=model.createIfcDirection((0.,0.,1.))
        wall.ObjectPlacement.RelativePlacement.RefDirection=model.createIfcDirection((math.cos(host_angle),math.sin(host_angle),0.))
        storey = model.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=wall.OwnerHistory, Name='Ground', CompositionType='ELEMENT', Elevation=0.)
        model.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory,
            RelatingObject=model.by_type('IfcProject')[0], RelatedObjects=[storey])
        target_entities, target_rows, refs = [], [], {}

        def product(kind, x):
            result = model.create_entity('IfcDoor' if kind == 'door' else 'IfcWindow',
                GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory,
                OverallWidth=.9, OverallHeight=2.1)
            result.Representation = copy_deep(model, template.Representation,
                exclude=('IfcGeometricRepresentationContext',))
            result.ObjectPlacement = model.createIfcLocalPlacement(None,
                model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((float(x), 0., 0.))))
            result.ObjectPlacement.RelativePlacement.Axis=model.createIfcDirection((0.,0.,1.))
            result.ObjectPlacement.RelativePlacement.RefDirection=model.createIfcDirection((math.cos(host_angle),math.sin(host_angle),0.))
            return result

        for kind in set(kinds):
            refs[kind] = product(kind, 30. if kind == 'door' else 35.)
            ref = refs[kind]
            rotation = math.radians(reference_rotation_deg)
            ref.ObjectPlacement.RelativePlacement.Axis = model.createIfcDirection((0.,0.,1.))
            ref.ObjectPlacement.RelativePlacement.RefDirection = model.createIfcDirection((math.cos(rotation),math.sin(rotation),0.))
            ref_host = copy_entity(model,wall)
            ref_host.ObjectPlacement = copy_deep(model,ref.ObjectPlacement)
            ref_host.Representation = copy_deep(model,wall.Representation,exclude=('IfcGeometricRepresentationContext',))
            ref_opening = copy_entity(model,template_opening)
            ref_opening.ObjectPlacement = copy_deep(model,ref.ObjectPlacement)
            ref_opening.Representation = copy_deep(model,template_opening.Representation,exclude=('IfcGeometricRepresentationContext',))
            model.create_entity('IfcRelFillsElement', GlobalId=ifcopenshell.guid.new(),OwnerHistory=wall.OwnerHistory,
                RelatingOpeningElement=ref_opening,RelatedBuildingElement=ref)
            model.create_entity('IfcRelVoidsElement', GlobalId=ifcopenshell.guid.new(),OwnerHistory=wall.OwnerHistory,
                RelatingBuildingElement=ref_host,RelatedOpeningElement=ref_opening)
        for index, kind in enumerate(kinds):
            target = product(kind, 3. * index)
            opening = copy_entity(model, template_opening)
            opening.Representation = copy_deep(model, template_opening.Representation,
                exclude=('IfcGeometricRepresentationContext',))
            opening.ObjectPlacement = copy_deep(model, target.ObjectPlacement)
            for relation, attrs in (
                ('IfcRelFillsElement', dict(RelatingOpeningElement=opening, RelatedBuildingElement=target)),
                ('IfcRelVoidsElement', dict(RelatingBuildingElement=wall, RelatedOpeningElement=opening)),
                ('IfcRelContainedInSpatialStructure', dict(RelatingStructure=storey, RelatedElements=[target])),
            ):
                model.create_entity(relation, GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory, **attrs)
            keep = kind == 'door' and keep_opening
            required = [('fill', 'IfcRelFillsElement'), ('storey', 'IfcRelContainedInSpatialStructure')]
            if not keep:
                required.append(('void', 'IfcRelVoidsElement'))
            target_rows.append(dict(kind=kind, target_guid=target.GlobalId,
                opening_guid=opening.GlobalId, wall_guid=wall.GlobalId, preserve_opening=keep,
                target=geometry_snapshot(target), opening=geometry_snapshot(opening),
                required_relations=[dict(id=f'target-{index+1}.{name}', ifc_class=cls, basis='authored control') for name, cls in required]))
            target_entities.append(target)
        remove_product(model, product=template)
        remove_product(model, product=template_opening)
        reference = private / 'reference.ifc'
        model.write(str(reference))
        damaged = ifcopenshell.file.from_string(model.to_string())
        for row in target_rows:
            remove_product(damaged, product=damaged.by_guid(row['target_guid']))
            if not row['preserve_opening']:
                remove_product(damaged, product=damaged.by_guid(row['opening_guid']))
        damaged_path = private / 'mutation/damaged.ifc'
        damaged.write(str(damaged_path))
        edges = []
        for row in target_rows:
            edges += relation_evidence(model, damaged, {'damage': row, 'task': {'required_relations': row['required_relations']}}, row['opening_guid'])
        spec = dict(schema_version='repair-comparison-task-candidate/0.1', purpose='formal_candidate',
            case_id='synthetic-control', source_sha256=sha256(reference), damaged_sha256=sha256(damaged_path),
            required_product_count=len(kinds), required_products=dict(Counter(p.is_a() for p in target_entities)),
            required_relation_count=len(edges), targets=target_rows, review={'status': 'pending_human_review'},
            metrics={'formal_scoring_frozen': False}, request='Hand-authored dimensions and retained style reference.',
            source={'task_proposal': {'retained_reference_step_ids': [p.id() for p in refs.values()]}})
        checks = {'checks': {'synthetic_fixture': True}, 'required_relation_evidence': edges}
        for name, payload in [('task.json', spec), ('checks.json', checks), ('answer-card.json', {'required_user_facts': []})]:
            (private / name).write_text(json.dumps(payload), encoding='utf8')
        policy = {'targets': {f'target-{i+1}': dict(
            basis='authored_test_contract', ifc_class=row['target']['class'], width_mm=900., height_mm=2100.,
            opening_center_xy_m=[3.*i,0.], opening_bottom_world_m=0., match_center_world_m=[3.*i,0.,1.05],
            target_center_offset_from_opening_m=[0.,0.,0.],
            host_guid=wall.GlobalId, storey_guid=storey.GlobalId, reference_guid=refs[row['kind']].GlobalId)
            for i, row in enumerate(target_rows)}}
        return case, model, spec, policy
    return build


def submit(case, model, policy=None):
    result = case / 'result.ifc'
    model.write(str(result))
    return scorer().score(case, result, terminal='submitted', policy=policy)


@pytest.mark.parametrize('kinds,keep', [(('door',), True), (('door',), False), (('window','window'), False), (('door','door'),False), (('window','door'),False), (('window','window','door'),False)])
def test_complete_single_double_mixed_and_three_targets(cases, kinds, keep):
    case, model, spec, policy = cases(kinds, keep)
    for row in spec['targets']:
        model.by_guid(row['target_guid']).GlobalId = ifcopenshell.guid.new()
        if not row['preserve_opening']:
            model.by_guid(row['opening_guid']).GlobalId = ifcopenshell.guid.new()
    report = submit(case, model, policy)
    assert report['repair_success'] is True, json.dumps(report, indent=2)
    for metric in ('quantity_completion', 'component_completion', 'relation_completion'):
        assert report['metrics'][metric]['value'] == 1, report
    assert report['formal_eligible'] is False
    assert report['policy']['frozen'] is False
    assert report['policy']['length_mm'] == 1.


def test_partial_counts_are_independent_and_wrong_class_cannot_substitute(cases):
    case, model, spec, policy = cases(('window','window','door'), False)
    remove_product(model, product=model.by_guid(spec['targets'][2]['target_guid']))
    extra = copy_entity(model, model.by_guid(spec['targets'][0]['target_guid']))
    report = submit(case, model, policy)
    quantity = report['metrics']['quantity_completion']
    assert (quantity['numerator'], quantity['denominator'], quantity['value']) == (2, 3, 2/3)
    assert quantity['excess_by_class']['IfcWindow'] == 1
    assert report['repair_success'] is False
    assert report['target_results'][0]['matching']['status'] == 'ambiguous'
    assert extra.GlobalId in report['target_results'][0]['matching']['candidates']


@pytest.mark.parametrize('fault', ['width','missing_fill','wrong_host','no_geometry','other_property','other_deleted','wall_thickness'])
def test_target_and_preservation_failures(cases, fault):
    case, model, spec, policy = cases(('window','door'),False)
    row = spec['targets'][0]
    target = model.by_guid(row['target_guid'])
    if fault == 'width': target.OverallWidth = 1.2
    elif fault == 'missing_fill': model.remove(target.FillsVoids[0])
    elif fault == 'wrong_host': target.FillsVoids[0].RelatingOpeningElement = model.by_guid(spec['targets'][1]['opening_guid'])
    elif fault == 'no_geometry': target.Representation = None
    elif fault == 'other_property': model.by_guid(policy['targets']['target-1']['reference_guid']).Description = 'unauthorized'
    elif fault == 'other_deleted': remove_product(model, product=model.by_guid(policy['targets']['target-1']['reference_guid']))
    elif fault == 'wall_thickness': model.by_type('IfcWall')[0].Representation.Representations[0].Items[0].SweptArea.YDim = .4
    report = submit(case, model, policy)
    assert report['repair_success'] is False, report
    assert report['metrics']['quantity_completion']['value'] == 1
    if fault in {'width','missing_fill','wrong_host','no_geometry'}:
        assert report['metrics']['component_completion']['value'] < 1


def test_schema_invalid_submission_keeps_computable_partial_scores(cases):
    case, model, _, policy = cases(('door',), True)
    # Invalid independent extra root: does not change the correct target geometry/edges.
    model.create_entity('IfcDoorStyle', GlobalId=ifcopenshell.guid.new())
    report = submit(case, model, policy)
    assert report['metrics']['ifc_validation_pass']['value'] is False
    assert report['metrics']['quantity_completion']['value'] == 1
    assert report['metrics']['relation_completion']['value'] == 1
    assert report['repair_success'] is False


@pytest.mark.parametrize('terminal', ['no_output','budget_exhausted','cancelled','runtime_error','unsupported'])
def test_terminal_no_output_retains_all_denominators(cases, terminal):
    case, _, spec, policy = cases(('window','door'),False)
    report = scorer().score(case, None, terminal=terminal, policy=policy)
    assert report['metrics']['quantity_completion']['denominator'] == 2
    assert report['metrics']['component_completion']['value'] == 0
    assert report['metrics']['relation_completion']['denominator'] == 6
    assert report['metrics']['relation_completion']['value'] == 0
    assert report['preservation']['status'] == 'not_evaluable'
    assert report['repair_success'] is False


@pytest.mark.parametrize('terminal,expected', [('not_run','not_run'),('ready','pending'),('running','pending'),('awaiting_user','pending')])
def test_pending_and_not_run_are_not_zero_scores(cases, terminal, expected):
    case, _, _, policy = cases()
    report = scorer().score(case,None,terminal=terminal,policy=policy)
    assert report['status'] == expected
    assert report['metrics']['component_completion'] == {'numerator': None,'denominator':1,'value':None,'status':expected}
    assert report['repair_success'] is None
    assert report['preservation']['status'] == expected


def test_bad_file_and_evaluator_error_are_distinct(cases, monkeypatch):
    case, _, _, policy = cases()
    bad = case / 'bad.ifc'
    bad.write_text('not an IFC', encoding='utf8')
    report = scorer().score(case,bad,terminal='submitted',policy=policy)
    assert report['repair_success'] is False
    assert report['metrics']['quantity_completion']['value'] == 0
    def broken(_): raise RuntimeError('engine crashed')
    monkeypatch.setattr(scorer(), 'native_validation', broken)
    report = scorer().score(case,case/'private/reference.ifc',terminal='submitted',policy=policy)
    assert report['status'] == 'not_evaluable'
    assert report['metrics']['ifc_validation_pass']['value'] is None
    assert report['repair_success'] is None
    assert report['metrics']['quantity_completion']['value'] is None
    assert report['diagnostic_metrics']['quantity_completion']['value'] == 1


def test_declared_submission_missing_from_disk_is_an_artifact_failure(cases):
    case,_,_,policy = cases()
    report=scorer().score(case,case/'absent.ifc',terminal='submitted',policy=policy)
    assert report['repair_success'] is False
    assert report['metrics']['quantity_completion']['value'] == 0


def test_candidate_snapshot_is_not_silently_a_frozen_task_contract(cases):
    case, model, _, _ = cases()
    report = submit(case,model)
    assert report['formal_eligible'] is False
    assert report['status'] == 'needs_review'
    assert report['repair_success'] is None


def test_appearance_unknown_blocks_strict_success_without_destroying_quantity(cases, monkeypatch):
    case, model, _, policy = cases()
    monkeypatch.setattr(scorer(), '_appearance', lambda *args: None)
    report = submit(case,model,policy)
    assert report['status'] == 'needs_review'
    assert report['repair_success'] is None
    assert report['metrics']['quantity_completion']['value'] == 1
    assert report['metrics']['component_completion']['status'] == 'needs_review'


def test_clarification_and_artifact_are_separate(cases):
    case, model, _, policy = cases()
    (case/'private/answer-card.json').write_text(json.dumps({'required_user_facts':[{'fact_id':'location'}]}),encoding='utf8')
    report = submit(case,model,policy)
    assert report['repair_success'] is True
    assert report['interaction_success'] is False
    events = [{'kind':'answer','payload':{'requested_fact_ids':['location'],'answered_fact_ids':['location']}}]
    report = scorer().score(case,None,terminal='no_output',policy=policy,events=events)
    assert report['clarification']['success'] is True
    assert report['interaction_success'] is False


def test_duplicate_correct_edge_retains_credit_but_blocks_complete_component(cases):
    case, model, spec, policy = cases()
    target = model.by_guid(spec['targets'][0]['target_guid'])
    copy_entity(model, target.FillsVoids[0])
    report = submit(case, model, policy)
    assert report['metrics']['relation_completion']['value'] == 1
    assert report['repair_success'] is False
    assert report['relation_details'][0]['duplicate']


def test_unchanged_damaged_model_is_zero_completion_and_preserved(cases):
    case, _, _, policy = cases(('window','door'),False)
    report = scorer().score(case,case/'private/mutation/damaged.ifc',terminal='submitted',policy=policy)
    assert report['metrics']['quantity_completion']['value'] == 0
    assert report['metrics']['component_completion']['value'] == 0
    assert report['metrics']['relation_completion']['value'] == 0
    assert report['preservation']['passed'] is True


def test_unrelated_added_property_set_is_collateral(cases):
    case, model, spec, policy = cases()
    root = model.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=model.by_type('IfcOwnerHistory')[0], Name='unrequested',
        HasProperties=[model.create_entity('IfcPropertySingleValue',Name='extra',NominalValue=model.createIfcLabel('x'))])
    report = submit(case,model,policy)
    assert report['preservation']['passed'] is False
    assert root.GlobalId in report['preservation']['unrelated_added_roots']
    assert report['repair_success'] is False


def test_delegated_review_requires_actual_authorization_record(cases):
    case, model, spec, policy = cases()
    policy.update(frozen=True,version='synthetic-test-frozen-1')
    spec['metrics']['formal_scoring_frozen'] = True
    spec['review'] = dict(status='accepted_by_delegation',kind='delegated_technical',reviewer='Codex',human_viewed=False,
                          technical_review_passed=True)
    path=case/'private/task.json'
    path.write_text(json.dumps(spec),encoding='utf8')
    assert submit(case,model,policy)['formal_eligible'] is False
    spec['review']['authorization'] = {'user_quote':'Synthetic fixture delegation','at':'2026-01-01T00:00:00Z'}
    path.write_text(json.dumps(spec),encoding='utf8')
    assert submit(case,model,policy)['formal_eligible'] is True
    assert scorer().score(case,None,terminal='no_output',policy=policy)['formal_eligible'] is True


def test_explicit_target_offset_is_strict_and_gold_bounds_are_not_extra_obligations(cases):
    case, model, spec, policy = cases()
    model.by_guid(spec['targets'][0]['target_guid']).ObjectPlacement.RelativePlacement.Location.Coordinates = (.01,0.,0.)
    report = submit(case,model,policy)
    assert report['target_results'][0]['checks']['target_position'] is False
    assert report['repair_success'] is False


def test_duplicate_guids_do_not_inflate_quantity(cases):
    case, model, spec, policy = cases(('window','window'),False)
    added=copy_entity(model,model.by_guid(spec['targets'][0]['target_guid']))
    added.GlobalId = spec['targets'][0]['target_guid']
    report=submit(case,model,policy)
    assert report['metrics']['quantity_completion']['numerator']==2
    assert report['duplicate_guids']==[added.GlobalId]
    assert report['repair_success'] is False


def test_reference_rotated_with_its_wall_can_define_correct_window_style(cases):
    case,model,_,policy=cases(('window',),False,reference_rotation_deg=90)
    report=submit(case,model,policy)
    assert report['repair_success'] is True, json.dumps(report,indent=2)


def test_rotating_window_in_same_host_cannot_hide_behind_object_placement(cases):
    case,model,spec,policy=cases(('window',),False)
    target=model.by_guid(spec['targets'][0]['target_guid'])
    target.ObjectPlacement.RelativePlacement.RefDirection=model.createIfcDirection((0.,1.,0.))
    target.ObjectPlacement.RelativePlacement.Axis=model.createIfcDirection((0.,0.,1.))
    report=submit(case,model,policy)
    assert report['target_results'][0]['checks']['appearance'] is None
    assert report['repair_success'] is not True


def test_public_position_alternatives_do_not_change_object_matching(cases):
    case,model,spec,policy=cases()
    target=model.by_guid(spec['targets'][0]['target_guid'])
    target.ObjectPlacement.RelativePlacement.Location.Coordinates=(.01,0.,0.)
    denied=submit(case,model,policy)
    assert denied['repair_success'] is False
    expectation=policy['targets']['target-1']
    del expectation['target_center_offset_from_opening_m']
    expectation['target_center_offsets_from_opening_m']=[[0.,0.,0.],[.01,0.,0.]]
    allowed=submit(case,model,policy)
    assert allowed['repair_success'] is True, json.dumps(allowed,indent=2)
    assert allowed['target_results'][0]['matching']==denied['target_results'][0]['matching']


def test_explicit_opening_width_catches_real_hole_size_despite_correct_door_nominal(cases):
    case,model,spec,policy=cases(('door',),False)
    policy['targets']['target-1']['opening_width_mm']=900.
    opening=model.by_guid(spec['targets'][0]['opening_guid'])
    opening.Representation.Representations[0].Items[0].SweptArea.XDim=1.2
    report=submit(case,model,policy)
    assert report['target_results'][0]['checks']['nominal_dimensions'] is True
    assert report['target_results'][0]['checks']['opening_width'] is False
    assert report['metrics']['quantity_completion']['value']==1
    assert report['repair_success'] is False


def test_opening_width_is_measured_on_rotated_host_axis(cases):
    case,model,_,policy=cases(('door',),False,host_rotation_deg=90)
    policy['targets']['target-1']['opening_width_mm']=900.
    report=submit(case,model,policy)
    assert report['target_results'][0]['checks']['opening_width'] is True
    assert report['repair_success'] is True, json.dumps(report,indent=2)


@pytest.mark.parametrize('nanometres',[-7.,7.])
def test_triangle_witness_accepts_fixed_quantization_boundary_noise(nanometres):
    vertices=np.array([[-.45,-.025,0.],[.45,-.025,0.],[.45,.025,0.],[-.45,.025,0.],[-.45,-.025,2.100001]])
    faces=np.array([[0,1,2],[0,2,3],[0,1,4]])
    reference=(vertices,faces,[(.5,.2,.1,None)],[0,0,0])
    changed=vertices.copy();changed[4,2]+=nanometres*1e-9
    actual=(changed,faces,reference[2],reference[3])
    assert scorer()._same_centered_surface(actual,reference,'window') is True


@pytest.mark.parametrize('fault',['over_micron','missing_face','style'])
def test_triangle_witness_does_not_ignore_shape_faces_or_style(fault):
    vertices=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,0.,2.100001]])
    faces=np.array([[0,1,2],[0,2,3],[0,1,4]])
    reference=(vertices,faces,[(.5,.2,.1,None)],[0,0,0])
    actual=copy.deepcopy(reference)
    if fault=='over_micron':actual[0][4,2]+=.000003
    elif fault=='missing_face':actual=(actual[0],actual[1][:2],actual[2],actual[3][:2])
    else:actual=(actual[0],actual[1],[(.6,.2,.1,None)],actual[3])
    assert scorer()._same_centered_surface(actual,reference,'window') is False
