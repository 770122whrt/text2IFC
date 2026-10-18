"""Frozen public-anchor family: no Gold, mutation identities or live calls."""
from copy import deepcopy
import hashlib
import json
import math

import numpy as np
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.spatial_grounding import bind_spatial_intent, GroundingError
from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent, _draft, _section
from tests.ifc_repair.test_window_installation_anchor import scene as window_scene
from tests.ifc_repair.test_window_installation_anchor import PublicWindowProvider


def frame(translation=(0, 0, 0), angle=0):
    a = math.radians(angle)
    m = np.array([[math.cos(a), -math.sin(a), 0, translation[0]],
                  [math.sin(a), math.cos(a), 0, translation[1]],
                  [0, 0, 1, translation[2]], [0, 0, 0, 1.]])
    return m.tolist()


def bounds(lo, hi):
    return {a: [lo[i], hi[i]] for i, a in enumerate('xyz')}


class Facts:
    def __init__(self, records, details):
        self.records = records
        self.details = details
        self.offered_ids = {r['id'] for r in records}

    def offered_record(self, identity):
        return next(r for r in self.records if r['id'] == identity)

    def geometry_detail(self, identity):
        return deepcopy(self.details[identity])


COLUMN = ('1. 补建一根柱：归属楼层「Upper」。放置基点世界坐标为（1，-0.5，11）米。'
          '形状为单一长方体，沿自身三个轴方向的尺寸为（400，600，3000）毫米；'
          '基点距对应负向面的距离为（-3000，-2000，-1000）毫米。'
          '朝向相对项目坐标系，按高、厚、宽轴依次旋转0度、0度、0度。')


def column_body():
    body = fixture_intent('window', {'allowed_ifc_classes': ['IfcBuildingStorey']}, {})
    op = body['operations'][0]
    op.update(operation_type='add_column', parameters={
        'axis': {'base': {'x_mm': 4200, 'y_mm': 1800, 'z_mm': 0},
                 'top': {'x_mm': 4200, 'y_mm': 1800, 'z_mm': 3000}},
        'section': {'shape': 'rectangle', 'width_mm': 400, 'depth_mm': 600,
                    'orientation': {'x': 1, 'y': 0}}})
    op['routing_intent'].update(component_family='column', action='add', operation_profile='column.add.v0.3')
    op['provenance'][0]['excerpt'] = COLUMN
    return body


@pytest.mark.parametrize('angle', [0, 90, 37])
def test_world_box_is_converted_with_full_storey_transform(angle):
    scene = Facts([{'id': 'upper', 'ifc_class': 'IfcBuildingStorey', 'name': 'Upper'}],
                  {'upper': {'placement_world_mm': frame((4000, -500, 12000), angle),
                             'body_bounds_local_mm': None}})
    original = column_body()
    body, evidence = bind_spatial_intent(original,
        [{'operation_id': 'offline-repair', 'target_id': 'upper'}], scene, repair_request=COLUMN)
    params = body['operations'][0]['parameters']
    axis = params['axis']
    local = [axis['base'][a + '_mm'] for a in 'xyz']
    world = np.array(frame((4000, -500, 12000), angle)) @ [*local, 1]
    assert world[:3] == pytest.approx([4200, 1800, 12000], abs=.001)
    assert params['section']['orientation']['x'] == pytest.approx(math.cos(math.radians(angle)))
    assert params['section']['orientation']['y'] == pytest.approx(-math.sin(math.radians(angle)))
    requirement = evidence[0]['public_geometry_requirement']
    assert requirement['bounds_world_mm'] == bounds([4000, 1500, 12000], [4400, 2100, 15000])
    assert requirement['source_excerpt'] in COLUMN
    assert original == column_body()


@pytest.mark.parametrize('angle', [0, 37, 90])
def test_beam_box_retains_world_axis_with_rotated_storey(angle):
    body = column_body()
    operation = body['operations'][0]
    operation['operation_type'] = 'add_beam'
    request = COLUMN.replace('一根柱', '一根梁').replace('（400，600，3000）', '（3000，400，600）')
    operation['provenance'][0]['excerpt'] = request
    scene = Facts([{'id': 'upper', 'ifc_class': 'IfcBuildingStorey', 'name': 'Upper'}],
                  {'upper': {'placement_world_mm': frame((4000, -500, 12000), angle)}})
    bound, evidence = bind_spatial_intent(body, [{'operation_id': 'offline-repair', 'target_id': 'upper'}],
                                         scene, repair_request=request)
    axis = bound['operations'][0]['parameters']['axis']
    world = [np.array(frame((4000, -500, 12000), angle)) @ [*[axis[k][a + '_mm'] for a in 'xyz'], 1]
             for k in ('start', 'end')]
    assert world[0][:3] == pytest.approx([4000, 1700, 12300], abs=.001)
    assert world[1][:3] == pytest.approx([7000, 1700, 12300], abs=.001)
    assert evidence[0]['public_geometry_requirement']['bounds_world_mm'] == bounds([4000, 1500, 12000], [7000, 1900, 12600])


def test_beam_roll_outside_existing_section_contract_is_rejected():
    body = column_body()
    body['operations'][0]['operation_type'] = 'add_beam'
    request = COLUMN.replace('一根柱', '一根梁').replace('（400，600，3000）', '（3000，400，600）').replace('0度、0度、0度', '0度、0度、20度')
    facts = Facts([{'id': 'upper', 'ifc_class': 'IfcBuildingStorey', 'name': 'Upper'}],
                  {'upper': {'placement_world_mm': frame((4000, -500, 12000))}})
    with pytest.raises(GroundingError, match='STRUCTURAL_ORIENTATION_UNSUPPORTED'):
        bind_spatial_intent(body, [{'operation_id': 'offline-repair', 'target_id': 'upper'}], facts,
                            repair_request=request)


WINDOW = ('1. 补建一扇窗：归属楼层「Upper」。宿主墙「Public host」，长度正向大致朝西，'
          '厚度正向大致朝南。放置基点距墙长度起端3000毫米，距墙厚度负向侧100毫米，高出墙底1000毫米。'
          '完整形状复制参照：楼层「Upper」的现存IfcWindow「Public reference」。朝向与参照相同。'
          '洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。')


def window_facts():
    records = [{'id': 'wall', 'name': 'Public host', 'ifc_class': 'IfcWall', 'storey_id': 'upper',
                'storey_name': 'Upper', 'wall_axis': {'start_world_mm': [20000, 1000, 7500],
                    'direction_world': [-1, 0, 0], 'length_mm': 10000, 'thickness_mm': 500}},
               {'id': 'peer', 'name': 'Public reference', 'ifc_class': 'IfcWindow',
                'type_id': 'style', 'storey_id': 'upper', 'storey_name': 'Upper'}]
    details = {
        'wall': {'placement_world_mm': frame((20000, 1000, 7500), 180),
                 'body_bounds_local_mm': bounds([-200, -250, 0], [10000, 250, 3500])},
        'peer': {'placement_world_mm': frame((13000, 1150, 8500), 180),
                 'body_bounds_local_mm': bounds([300, 100, 0], [1300, 335, 2200]),
                 'opening': {'id': 'peer-void', 'host_id': 'wall',
                    'placement_in_product_mm': frame((300, -150, 0)),
                    'body_bounds_local_mm': bounds([0, -250, 0], [1000, 250, 2200])}}}
    return Facts(records, details)


def test_instance_anchor_is_not_an_opening_center_or_wall_axis_origin():
    body = fixture_intent('window', {'allowed_ifc_classes': ['IfcWall']}, {
        'opening': {'width_mm': 1000, 'height_mm': 2200, 'sill_height_mm': 1000},
        'window': {'fit_opening': True}})
    body['operations'][0]['provenance'][0]['excerpt'] = WINDOW
    bound, evidence = bind_spatial_intent(body, [{'operation_id': 'offline-repair', 'target_id': 'wall',
        'reference_id': 'peer', 'position': {'kind': 'world_point', 'point_world_mm': [17200, 1150, 8500]}}],
        window_facts(), repair_request=WINDOW)
    assert bound['operations'][0]['parameters']['position']['center_offset_mm'] == pytest.approx(3600)
    requirement = evidence[0]['public_geometry_requirement']
    assert requirement['bounds_world_mm']['x'] == pytest.approx([15900, 16900])
    assert requirement['opening_bounds_world_mm']['x'] == pytest.approx([15900, 16900])


def test_missing_operations_cannot_skip_explicit_public_requirements():
    body = column_body()
    body['operations'] = []
    with pytest.raises(GroundingError, match='PUBLIC_GEOMETRY_CLAUSE_CARDINALITY_MISMATCH'):
        bind_spatial_intent(body, [], Facts([], {}), repair_request=COLUMN)


def test_reference_floor_must_match_original_public_request():
    body = fixture_intent('window', {'allowed_ifc_classes': ['IfcWall']}, {})
    facts = window_facts()
    facts.records[1]['storey_name'] = 'Other floor'
    with pytest.raises(GroundingError, match='PUBLIC_GEOMETRY_REFERENCE_OR_HOST_BINDING_MISMATCH'):
        bind_spatial_intent(body, [{'operation_id': 'offline-repair', 'target_id': 'wall',
            'reference_id': 'peer'}], facts, repair_request=WINDOW)


@pytest.mark.parametrize('kind', ['floor', 'missing_geometry', 'ambiguous_clause', 'shape_incomplete'])
def test_explicit_geometry_never_falls_back_to_model_guesses(kind):
    body = column_body()
    scene = Facts([{'id': 'upper', 'ifc_class': 'IfcBuildingStorey', 'name': 'Upper'}],
        {'upper': {'placement_world_mm': frame((4000, -500, 12000)), 'body_bounds_local_mm': None}})
    request = COLUMN
    if kind == 'floor': scene.records[0]['name'] = 'Other'
    elif kind == 'missing_geometry': scene.details['upper']['placement_world_mm'] = None
    elif kind == 'ambiguous_clause': request += '\n' + COLUMN.replace('1.', '2.')
    else: request = COLUMN.split('形状为')[0]
    with pytest.raises(GroundingError, match='PUBLIC_GEOMETRY'):
        bind_spatial_intent(body, [{'operation_id': 'offline-repair', 'target_id': 'upper'}], scene,
                            repair_request=request)


class ColumnProvider:
    def generate_candidate(self, **kw):
        if '## Immutable bindings' in kw['prompt']:
            value = _draft(kw['prompt'], kw['schema'])
        else:
            floor = _section(kw['prompt'], 'Current public scene')['storeys'][0]
            value = {'kind': 'intent', 'intent': column_body(),
                     'bindings': [{'operation_id': 'offline-repair', 'target_id': floor['id']}]}
        return ProviderOutput(text=json.dumps(value), metadata={'model': 'offline-public-anchor',
                                                               'evidence_class': 'deterministic_fake'})


@pytest.mark.parametrize('millimetres', [False, True])
def test_public_api_calibrates_column_and_final_check_uses_request_source(tmp_path, millimetres):
    import ifcopenshell
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
    m, wall, _, _, _, unit = window_scene(millimetres=millimetres)
    storey = m.by_type('IfcBuildingStorey')[0]
    storey.Name = 'Upper'
    storey.ObjectPlacement.RelativePlacement.Location.Coordinates = (4000 * unit, -500 * unit, 12000 * unit)
    source = tmp_path / 'public.ifc'
    m.write(str(source))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    api = RepairAPI(tmp_path / 'runs', provider=ColumnProvider(), scene_grounding=True)
    result = api.start(source, COLUMN)
    assert result.status == 'succeeded', result.to_dict()
    run = tmp_path / 'runs' / result.run_directory
    repaired = ifcopenshell.open(str(run / result.artifacts['successful_ifc']))
    column = repaired.by_type('IfcColumn')[0]
    assert measure_straight_rectangular_member(column)['axis_start_mm'] == pytest.approx([4200, 1800, 12000])
    report = json.loads((run / result.artifacts['evaluation']).read_text(encoding='utf-8'))
    checks = [c for op in report['operations'] for level in op['levels'] for c in level['checks']]
    assert any(c['check_id'] == 'l2.public-request-geometry' and c['status'] == 'passed' for c in checks)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest

    # Independent C must reject a later shift, stale request, missing A facts,
    # or tampered expectations, even if other checks still accept the IFC.
    from text2ifc_ifc_repair.public_geometry import public_geometry_check
    context = json.loads((run / 'api-context.json').read_text(encoding='utf-8'))
    requirement = context['public_geometry_requirements']['offline-repair']
    arguments = dict(requirement=requirement, repair_request=COLUMN, damaged_model=m,
                     repaired_model=repaired, roles={'column': column.GlobalId})
    assert public_geometry_check(**arguments).status.value == 'passed'
    loc = column.ObjectPlacement.RelativePlacement.Location
    xyz = list(loc.Coordinates)
    xyz[0] += 100 * unit
    loc.Coordinates = tuple(xyz)
    assert public_geometry_check(**arguments).status.value == 'failed'
    for changed in ({'requirement': {}}, {'repair_request': COLUMN.replace('（1，', '（2，')},
                    {'requirement': {**requirement, 'bounds_world_mm': bounds([0, 0, 0], [1, 1, 1])}}):
        assert public_geometry_check(**{**arguments, **changed}).status.value == 'not_evaluable'


def test_final_evaluation_cannot_skip_missing_original_geometry_authority(tmp_path):
    from dataclasses import replace
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_ifc_repair.production_evaluation import evaluate_production
    m, _, _, _, _, unit = window_scene()
    floor = m.by_type('IfcBuildingStorey')[0]
    floor.Name = 'Upper'
    floor.ObjectPlacement.RelativePlacement.Location.Coordinates = (4000 * unit, -500 * unit, 12000 * unit)
    source = tmp_path / 'public.ifc'
    m.write(str(source))
    def lost_binding(inputs):
        return evaluate_production(replace(inputs, public_geometry_requirements={}))
    api = RepairAPI(tmp_path / 'runs', provider=ColumnProvider(), scene_grounding=True,
                    orchestrator_options={'evaluation_stage': lost_binding})
    result = api.start(source, COLUMN)
    assert result.status == 'not_publishable', result.to_dict()
    assert not result.successful_artifact_publishable
    report = json.loads((api.store.runs_root / result.run_id / result.artifacts['evaluation']).read_text(encoding='utf-8'))
    checks = [c for op in report['operations'] for level in op['levels'] for c in level['checks']]
    assert any(c['check_id'] == 'l2.public-request-geometry' and c['status'] == 'not_evaluable' for c in checks)


ANCHOR_WINDOW = ('1. 补建一扇窗：归属楼层「Ground」。宿主墙「Public straight host」。'
    '放置基点距墙长度起端2400毫米，距墙厚度负向侧30毫米，高出墙底700毫米。'
    '完整形状复制参照：楼层「Ground」的现存IfcWindow「Public reference window」。朝向与参照相同。'
    '洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。')


class AnchorWindowProvider(PublicWindowProvider):
    def generate_candidate(self, **kw):
        output = super().generate_candidate(**kw)
        value = json.loads(output.text)
        if value.get('kind') == 'intent':
            for operation in value['intent']['operations']:
                operation['provenance'][0]['excerpt'] = ANCHOR_WINDOW
        return ProviderOutput(text=json.dumps(value), metadata={'model': 'offline-public-anchor',
                                                               'evidence_class': 'deterministic_fake'})


@pytest.mark.parametrize('millimetres', [False, True])
def test_public_api_preserves_reversed_reference_anchor_and_opening(tmp_path, millimetres):
    import ifcopenshell
    from text2ifc_ifc_repair.api import RepairAPI
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    m, wall, _, ref, _, _ = window_scene(extension=0., sign=-1., millimetres=millimetres)
    source = tmp_path / 'public.ifc'
    m.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'runs', provider=AnchorWindowProvider(), scene_grounding=True)
    result = api.start(source, ANCHOR_WINDOW)
    assert result.status == 'succeeded', result.to_dict()
    run = api.store.runs_root / result.run_id
    repaired = ifcopenshell.open(str(run / result.artifacts['successful_ifc']))
    window = next(w for w in repaired.by_type('IfcWindow') if w.GlobalId != ref.GlobalId)
    placement = ifcopenshell.util.placement.get_local_placement(window.ObjectPlacement)
    scale = ifcopenshell.util.unit.calculate_unit_scale(repaired) * 1000
    assert placement[:3, 3] * scale == pytest.approx([3400, 1955, 700], abs=.001)
    context = json.loads((run / 'api-context.json').read_text(encoding='utf-8'))
    requirement = context['public_geometry_requirements']['offline-window-0']
    assert requirement['bounds_world_mm']['x'] == pytest.approx([2500, 3400], abs=.001)
    assert source.read_bytes() == before


def test_exact_reference_opening_depth_is_copied_and_checked(tmp_path):
    """C must not accept a shallower regenerated cutter as an exact copy."""
    import ifcopenshell
    from text2ifc_ifc_repair.api import RepairAPI
    from text2ifc_ifc_repair.geometry import opening_dimensions_mm
    from text2ifc_ifc_repair.public_geometry import public_geometry_check
    m, _, _, ref, _, _ = window_scene(extension=0., sign=-1., cut_depth=400.)
    source = tmp_path / 'public.ifc'
    m.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'runs', provider=AnchorWindowProvider(), scene_grounding=True)
    result = api.start(source, ANCHOR_WINDOW)
    assert result.status == 'succeeded', result.to_dict()
    assert result.successful_artifact_publishable
    report = json.loads((api.store.runs_root / result.run_id / result.artifacts['evaluation']).read_text(encoding='utf-8'))
    checks = [c for op in report['operations'] for level in op['levels'] for c in level['checks']]
    assert any(c['check_id'] == 'l2.public-request-geometry' and c['status'] == 'passed' for c in checks)
    run = api.store.runs_root / result.run_id
    repaired = ifcopenshell.open(str(run / result.artifacts['successful_ifc']))
    window = next(w for w in repaired.by_type('IfcWindow') if w.GlobalId != ref.GlobalId)
    opening = window.FillsVoids[0].RelatingOpeningElement
    assert opening_dimensions_mm(opening)['depth'] == pytest.approx(400.)
    context = json.loads((run / 'api-context.json').read_text(encoding='utf-8'))
    opening.Representation.Representations[0].Items[0].SweptArea.YDim *= .5
    assert public_geometry_check(requirement=context['public_geometry_requirements']['offline-window-0'],
        repair_request=ANCHOR_WINDOW, damaged_model=m, repaired_model=repaired,
        roles={'window': window.GlobalId, 'opening': opening.GlobalId}).status.value == 'failed'
    assert source.read_bytes() == before
