"""Private task authoring checks; real tiny geometry, no model transport."""
from __future__ import annotations

import hashlib
import importlib
import json

import ifcopenshell
import pytest


@pytest.fixture(params=[1.0, 0.001], ids=['metres', 'millimetres'])
def author_source(tmp_path, request):
    scale = request.param
    model = ifcopenshell.file(schema='IFC2X3')
    def point(values):
        return model.create_entity('IfcCartesianPoint', Coordinates=tuple(v / scale for v in values))
    def axis(values):
        return model.create_entity('IfcAxis2Placement3D', Location=point(values))
    origin = axis((0., 0., 0.))
    context = model.create_entity('IfcGeometricRepresentationContext', ContextType='Model', CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=origin)
    unit = model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE', Prefix='MILLI' if scale == .001 else None)
    model.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), UnitsInContext=model.create_entity('IfcUnitAssignment', Units=[unit]), RepresentationContexts=[context])
    # Deliberately disagree with Elevation/Name: actual placement is authoritative.
    storey = model.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), Name='SECRET FLOOR NAME', Elevation=77. / scale, ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=axis((0., 0., 1.))))
    def product(kind, x, width, depth, height):
        product = model.create_entity(kind, GlobalId=ifcopenshell.guid.new(), Name='SECRET PRODUCT NAME', ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=axis((x, 0., 1.8))))
        profile = model.create_entity('IfcRectangleProfileDef', ProfileType='AREA', Position=model.create_entity('IfcAxis2Placement2D', Location=point((0., 0.))), XDim=width / scale, YDim=depth / scale)
        solid = model.create_entity('IfcExtrudedAreaSolid', SweptArea=profile, Position=origin, ExtrudedDirection=model.create_entity('IfcDirection', DirectionRatios=(0., 0., 1.)), Depth=height / scale)
        shape = model.create_entity('IfcShapeRepresentation', ContextOfItems=context, RepresentationIdentifier='Body', RepresentationType='SweptSolid', Items=[solid])
        product.Representation = model.create_entity('IfcProductDefinitionShape', Representations=[shape])
        if kind == 'IfcWindow':
            product.OverallWidth, product.OverallHeight = width / scale, height / scale
        return product
    wall = product('IfcWall', 0., 9., .2, 3.)
    windows = []
    for x in (2., 5.):
        opening = product('IfcOpeningElement', x, .9, .2, 1.2)
        window = product('IfcWindow', x, .9, .05, 1.2)
        model.create_entity('IfcRelVoidsElement', GlobalId=ifcopenshell.guid.new(), RelatingBuildingElement=wall, RelatedOpeningElement=opening)
        model.create_entity('IfcRelFillsElement', GlobalId=ifcopenshell.guid.new(), RelatingOpeningElement=opening, RelatedBuildingElement=window)
        windows.append(window)
    model.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), RelatedElements=[wall, *windows], RelatingStructure=storey)
    source = tmp_path / 'source.ifc'
    model.write(str(source))
    selection = {'asset_id': 'test-source', 'proposed_slot': 'formal-004', 'assessment_path': 'source.ifc', 'assessment_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'size_bytes': source.stat().st_size, 'schema': 'IFC2X3', 'license': 'MIT', 'source_family': 'shared-synthetic-family', 'building_identity': 'layout-01', 'building_identity_basis': 'Distinct synthetic layout, not verified real building.', 'independent_building_verified': False, 'native_pass_registered': True, 'assessment_native_evidence': 'native.json', 'prior_native_summary': {'completed': True, 'error_count': 0}, 'rights': {'public_release_policy': 'open_modification_with_notice', 'record': 'rights.jsonl', 'conditions': 'Retain notice', 'source_url': 'https://example.test/source', 'original_sha256': 'older-source-sha', 'repair_evidence': ['repair.json']}, 'proposals': [{'class': 'IfcWindow', 'targets': [{'step_id': windows[0].id()}], 'reference': {'step_id': windows[1].id()}}], 'recommended_target_count': 1}
    return tmp_path, source, selection, [w.GlobalId for w in windows]


def api():
    return importlib.import_module('scripts.ifc_repair.repair_comparison.authoring')


def test_authoring_binds_actual_units_geometry_floor_and_private_identity(author_source):
    root, source, selection, guids = author_source
    before = source.read_bytes()
    row = api().author_candidate(selection, repository_root=root)
    spec = row['task_proposal']['author_expectations']['target-1']
    assert spec['basis'] == 'public_author_intent'
    assert spec['width_mm'] == pytest.approx(900)
    assert spec['height_mm'] == pytest.approx(1200)
    assert 'opening_width_mm' not in spec
    assert row['task_proposal']['public_numeric_spec']['targets'][0]['opening_width_mm'] == pytest.approx(900)
    assert spec['opening_height_mm'] == pytest.approx(1200)
    assert spec['opening_center_xy_m'] == pytest.approx([2, 0])
    assert spec['opening_bottom_world_m'] == pytest.approx(1.8)
    assert spec['storey_world_elevation_m'] == pytest.approx(1)
    assert spec['sill_mm'] == pytest.approx(800)
    assert spec['reference_guid'] == guids[1]
    assert spec['target_guid'] == guids[0]
    assert spec['geometry_checks']['reference_mesh_equal'] is True
    assert spec['geometry_checks']['storey_elevation_attribute_agrees'] is False
    assert spec['target_center_offset_from_opening_m'] == pytest.approx([0, 0, 0])
    assert spec['target_center_offset_basis'] == 'retained_public_reference_geometry'
    assert spec['geometry_checks']['reference_derived_center_offset_matches_target'] is True
    public = row['task_proposal']['public_request']
    for forbidden in guids + ['SECRET', 'GlobalId', 'Python', 'STEP', 'IfcOpenShell']:
        assert forbidden not in public
    for expected in ['900', '1200', '800', '1.000', '2.000', '5.000']:
        assert expected in public
    assert row['scene_family'] == 'shared-synthetic-family'
    assert row['independent_building_verified'] is False
    assert row['source_role'] == 'preselected_reference_from_registered_repair_copy'
    assert row['human_viewed'] is False
    assert row['task_proposal']['frozen'] is False
    assert source.read_bytes() == before


def test_stale_source_is_rejected_before_measurement(author_source):
    root, source, selection, _ = author_source
    source.write_bytes(source.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='SOURCE_CHANGED'):
        api().author_candidate(selection, repository_root=root)


def test_equal_nominal_dimensions_do_not_admit_a_different_reference_mesh(author_source):
    root, source, selection, _ = author_source
    model = ifcopenshell.open(str(source))
    reference = model.by_id(selection['proposals'][0]['reference']['step_id'])
    reference.Representation.Representations[0].Items[0].SweptArea.YDim *= 2
    model.write(str(source))
    selection['assessment_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='REFERENCE_MESH_MISMATCH'):
        api().author_candidate(selection, repository_root=root)


def test_reference_cannot_be_a_deleted_target(author_source):
    root, _, selection, _ = author_source
    target = selection['proposals'][0]['targets'][0]['step_id']
    selection['proposals'][0]['reference']['step_id'] = target
    with pytest.raises(ValueError, match='REFERENCE_IS_TARGET'):
        api().author_candidate(selection, repository_root=root)


def test_unreviewed_rights_fail_closed(author_source):
    root, _, selection, _ = author_source
    selection['rights']['public_release_policy'] = 'unresolved'
    with pytest.raises(ValueError, match='RIGHTS_NOT_CLEAR'):
        api().author_candidate(selection, repository_root=root)


def test_registered_copyleft_policy_retains_conditions(author_source):
    root, _, selection, _ = author_source
    selection['rights']['public_release_policy'] = 'open_modification_with_copyleft'
    selection['rights']['conditions'] = 'GPL source and notice obligations'
    row = api().author_candidate(selection, repository_root=root)
    assert row['rights_policy'] == 'open_modification_with_copyleft'
    assert row['rights_conditions'] == 'GPL source and notice obligations'


def test_missing_requested_target_does_not_silently_shrink_task(author_source):
    root, _, selection, _ = author_source
    with pytest.raises(ValueError, match='TARGET_COUNT_UNAVAILABLE'):
        api().author_candidate(selection, repository_root=root, plan=[(0, 2)])


def test_reference_offset_is_rotated_between_actual_host_walls():
    # Independent 90 degree rotation: reference +X 0.04m becomes target +Y.
    measured = {'host_placement_world_m': [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], 'mesh_center_world_m': [2, 3.04, 4], 'opening_center_world_m': [2, 3, 4]}
    ref = {'host_placement_world_m': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], 'mesh_center_world_m': [.04, 0, 0], 'opening_center_world_m': [0, 0, 0]}
    result = api().reference_derived_offset(measured, ref)
    assert result['offset_m'] == pytest.approx([0, .04, 0])
    assert result['matches_target_within_1mm'] is True
    measured['mesh_center_world_m'][1] = 3.06
    result = api().reference_derived_offset(measured, ref)
    assert result['matches_target_within_1mm'] is False
    assert result['offset_m'] == pytest.approx([0, .04, 0])


def test_swapped_nominal_dimensions_are_not_silently_authored(author_source):
    root, source, selection, _ = author_source
    model = ifcopenshell.open(str(source))
    for entity in model.by_type('IfcWindow'):
        entity.OverallWidth, entity.OverallHeight = entity.OverallHeight, entity.OverallWidth
    model.write(str(source))
    selection['assessment_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='NOMINAL_OPENING_DIMENSIONS_SWAPPED'):
        api().author_candidate(selection, repository_root=root)


def test_batch_output_cannot_overwrite_source_or_selection(author_source):
    root, source, selection, _ = author_source
    inventory = root / 'selection.json'
    inventory.write_text(json.dumps({'candidates': [selection]}), encoding='utf-8')
    for output in [inventory, source, root / 'public' / 'authored.json']:
        before = source.read_bytes()
        with pytest.raises(ValueError, match='PRIVATE_JSON_OUTPUT_REQUIRED'):
            api().author_selection(inventory, output, repository_root=root)
        assert source.read_bytes() == before

