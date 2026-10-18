"""Frozen synthetic public-source volume family, independent of benchmark Gold.

Expected volumes are analytic trapezoid/rectangle areas times wall intersection.
Cases cover thick/partial voids, rotated hosts, metre/mm units, single/batch/mixed,
and corrupt output with unchanged envelopes or additional unintended host cuts.
"""
import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.util.element
import ifcopenshell.util.placement
import pytest

from tests.ifc_repair.test_window_installation_anchor import scene
from text2ifc_ifc_repair.operations.window import _comparison_adapter
from text2ifc_ifc_repair.public_geometry import place_public_product


def _family(*, trapezoid=True, depth=1000., center=0., mm=False, angle=0., count=1):
    before, wall, reference_opening, reference, _, unit = scene(
        extension=0., cut_depth=depth, cut_center=center, millimetres=mm, angle=angle)
    if trapezoid:
        # 900 wide, height 1200 at left and 1000 at right; area 0.99 m2.
        vertices = [(x / 1000, y / 1000, z / 1000)
                    for y in (center - depth / 2, center + depth / 2)
                    for x, z in ((0, 0), (900, 0), (900, 1000), (0, 1200))]
        faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        rep = ifcopenshell.api.geometry.add_mesh_representation(
            before, context=reference_opening.Representation.Representations[0].ContextOfItems,
            vertices=[vertices], faces=[faces], force_faceted_brep=True)
        reference_opening.Representation = before.createIfcProductDefinitionShape(None, None, [rep])
    after = ifcopenshell.file.from_string(before.to_string())
    operations, applications = [], {}
    for index in range(count):
        start = 1000. + index * 1700.
        operation = {'operation_id': f'volume-{index}',
                     'operation_type': 'add_window_with_opening_to_wall',
                     'target': {'wall_global_id': wall.GlobalId},
                     'parameters': {'position': {'center_offset_mm': start + 450.},
                                    'opening': {'width_mm': 900., 'height_mm': 1200., 'sill_height_mm': 700.},
                                    'window': {'fit_opening': True}}, 'evidence_refs': []}
        requirement = {'reference_id': reference.GlobalId, 'reference_opening_id': reference_opening.GlobalId,
                       'target_id': wall.GlobalId, 'retained_opening': False}
        delta = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)[:3, 0] * (start - 5000.) * unit
        for entity, key in ((reference, 'placement_world_mm'), (reference_opening, 'opening_placement_world_mm')):
            pose = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement).copy()
            pose[:3, 3] += delta
            pose[:3, 3] /= unit
            requirement[key] = pose.tolist()
        created = []
        for role, original, key in (('opening', reference_opening, 'opening_placement_world_mm'),
                                    ('window', reference, 'placement_world_mm')):
            entity = after.create_entity(original.is_a(), GlobalId=ifcopenshell.guid.new(),
                OwnerHistory=after.by_guid(wall.GlobalId).OwnerHistory,
                Representation=ifcopenshell.util.element.copy_deep(after, after.by_guid(original.GlobalId).Representation))
            place_public_product(entity, after.by_guid(wall.GlobalId), requirement[key])
            created.append({'role': role, 'global_id': entity.GlobalId})
        opening, window = [after.by_guid(e['global_id']) for e in created]
        window.OverallWidth, window.OverallHeight = 900 * unit, 1200 * unit
        for cls, kw in [('IfcRelVoidsElement', {'RelatingBuildingElement': after.by_guid(wall.GlobalId), 'RelatedOpeningElement': opening}),
                        ('IfcRelFillsElement', {'RelatingOpeningElement': opening, 'RelatedBuildingElement': window})]:
            after.create_entity(cls, GlobalId=ifcopenshell.guid.new(), OwnerHistory=opening.OwnerHistory, **kw)
        containment = after.by_guid(wall.GlobalId).ContainedInStructure[0]
        containment.RelatedElements = (*containment.RelatedElements, window)
        changes = {'created': created, 'resolved': {'opening_depth_mm': depth, 'opening_void_depth_mm': 150.}}
        changes['public_geometry_requirement'] = requirement
        operations.append(operation)
        applications[operation['operation_id']] = {'changes': changes}
    cut_depth = max(0., min(center + depth / 2, 75.) - max(center - depth / 2, -75.))
    analytic_volume = (0.99 if trapezoid else 1.08) * cut_depth / 1000. * count
    return before, after, operations, applications, analytic_volume


def _measure(before, after, operations, applications, *, mode='batch'):
    operation = operations[0]
    extra = {} if mode == 'single' else {'batch_operations': operations, 'batch_applications': applications}
    return _comparison_adapter(operation=operation, before_model=before, after_model=after,
                               application=applications[operation['operation_id']]['changes'], **extra)


@pytest.mark.parametrize('config,mode', [
    ({'trapezoid': False, 'depth': 150.}, 'single'),
    ({'trapezoid': False}, 'single'),
    ({}, 'single'),
    ({'mm': True, 'angle': 37.}, 'batch'),
    ({'depth': 100., 'center': 75.}, 'batch'),
    ({'count': 2}, 'batch'),
    ({'mm': True, 'angle': 90.}, 'mixed'),
])
def test_public_void_uses_source_profile_intersection(config, mode):
    before, after, operations, applications, expected = _family(**config)
    if mode == 'mixed':
        operations.append({'operation_id': 'unrelated-door', 'operation_type': 'fill_existing_opening_with_door'})
    source = before.to_string()
    report = _measure(before, after, operations, applications, mode=mode)
    assert report['metrics']['restored_void_volume_m3'] == pytest.approx(expected, abs=1e-6)
    assert report['metrics']['expected_void_volume_m3'] == pytest.approx(expected, abs=1e-6)
    assert report['l1_checks']['l1.window.volume-preservation']['status'] == 'passed'
    assert before.to_string() == source


@pytest.mark.parametrize('corruption', ['profile', 'extra-cut', 'application-depth'])
def test_public_void_rejects_unrequested_loss_and_ignores_reported_depth(corruption):
    before, after, operations, applications, expected = _family()
    changes = applications[operations[0]['operation_id']]['changes']
    opening = after.by_guid(next(e['global_id'] for e in changes['created'] if e['role'] == 'opening'))
    if corruption == 'profile':
        # Replace slope with a rectangle with the SAME full bounding envelope.
        for point in after.traverse(opening.Representation):
            if point.is_a('IfcCartesianPoint') and len(point.Coordinates) == 3 and abs(point.Coordinates[2] - 1.) < 1e-8:
                point.Coordinates = (*point.Coordinates[:2], 1.2)
    elif corruption == 'extra-cut':
        extra = after.create_entity('IfcOpeningElement', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=opening.OwnerHistory, Representation=opening.Representation,
            ObjectPlacement=deepcopy_placement(after, opening.ObjectPlacement))
        p = extra.ObjectPlacement.RelativePlacement.Location
        p.Coordinates = (p.Coordinates[0] + 1.5, *p.Coordinates[1:])
        after.create_entity('IfcRelVoidsElement', GlobalId=ifcopenshell.guid.new(), OwnerHistory=opening.OwnerHistory,
            RelatingBuildingElement=after.by_guid(operations[0]['target']['wall_global_id']), RelatedOpeningElement=extra)
    else:
        changes['resolved']['opening_void_depth_mm'] = 999999.
    report = _measure(before, after, operations, applications)
    assert report['metrics']['expected_void_volume_m3'] == pytest.approx(expected, abs=1e-6)
    assert report['l1_checks']['l1.window.volume-preservation']['status'] == (
        'passed' if corruption == 'application-depth' else 'failed')
    if corruption == 'profile':
        assert report['l1_checks']['l1.window.geometry-fit']['status'] == 'failed'


def deepcopy_placement(model, placement):
    import ifcopenshell.util.element
    return ifcopenshell.util.element.copy_deep(model, placement)


def test_revealed_mixed_brep_public_request_passes_offline_api(tmp_path):
    """Revealed regression only: hand-authored Provider, original public files."""
    from pathlib import Path
    from tests.ifc_repair.test_public_rotation_api import PublicMixedRotationProvider
    from text2ifc_ifc_repair.api import RepairAPI

    public = (Path(__file__).resolve().parents[2] /
        'dataset/processed/ifc-repair/external-20-pilot-40-20261010/sources/external-020/cases/case-001-a01/public')
    source = public / 'model.ifc'
    if not source.is_file() or not (public / 'request.txt').is_file():
        pytest.skip('requires the local frozen external-020 public fixture; not admission when skipped')
    original = source.read_bytes()
    request = (public / 'request.txt').read_text(encoding='utf-8')
    api = RepairAPI(tmp_path / 'run', provider=PublicMixedRotationProvider(source, request), scene_grounding=True)
    result = api.start(source, request)
    assert result.status == 'succeeded', result.to_dict()
    assert source.read_bytes() == original
    assert (api.store.runs_root / result.run_id / result.artifacts['successful_ifc']).is_file()
