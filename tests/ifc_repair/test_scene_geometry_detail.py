"""Public placement/Body facts, independently authored in a synthetic IFC."""
from copy import deepcopy
import hashlib

import ifcopenshell.guid
import numpy as np
import pytest

from text2ifc_ifc_repair import scene_context
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.scene_context import PublicScene, SceneError
from tests.ifc_repair.test_scene_context import fixture_scene
from tests.ifc_repair.test_window_installation_anchor import scene as window_scene


def public_scene(tmp_path, **configuration):
    model, wall, opening, reference, _, unit = window_scene(**configuration)
    storey = model.by_type("IfcBuildingStorey")[0]
    storey.ObjectPlacement.RelativePlacement.Location.Coordinates = (
        3000 * unit, -500 * unit, 8000 * unit
    )
    storey.ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios = (0., 1., 0.)
    source = tmp_path / "public.ifc"
    model.write(str(source))
    before = source.read_bytes()
    index = tmp_path / "public.sqlite"
    metadata = build_ifc_index(source, index)
    scene = PublicScene.from_ifc(source, index, source_sha256=metadata.source_ifc_sha256)
    return scene, source, before, storey.GlobalId, wall.GlobalId, opening.GlobalId, reference.GlobalId


@pytest.mark.parametrize("millimetres", [False, True])
def test_storey_has_complete_world_placement_with_xy_rotation_and_si_units(tmp_path, millimetres):
    scene, source, before, storey_id, *_ = public_scene(tmp_path, millimetres=millimetres)
    expected = [[0., -1., 0., 3000.], [1., 0., 0., -500.],
                [0., 0., 1., 8000.], [0., 0., 0., 1.]]
    overview = scene.overview()
    assert np.asarray(overview["storeys"][0]["placement_world_mm"]) == pytest.approx(np.asarray(expected))
    detail = scene.geometry_detail(storey_id)
    assert np.asarray(detail["placement_world_mm"]) == pytest.approx(np.asarray(expected))
    assert detail["body_bounds_local_mm"] is None
    assert source.read_bytes() == before


@pytest.mark.parametrize("millimetres,sign,normal", [(False, 1., -45.), (True, -1., 35.)])
def test_queried_reference_keeps_actual_body_and_opening_offset_from_placement(tmp_path, millimetres, sign, normal):
    scene, source, before, _, wall_id, opening_id, reference_id = public_scene(
        tmp_path, millimetres=millimetres, sign=sign, normal=normal, base_gap=20.
    )
    page = scene.query({"ids": [reference_id]})
    record = page["records"][0]
    detail = scene.geometry_detail(reference_id)
    assert record["geometry_detail_status"] == "available"
    assert record["placement_world_mm"] == detail["placement_world_mm"]
    expected_world = [[0., -sign, 0., 1000. - normal],
                      [sign, 0., 0., 5500. if sign > 0 else 6400.],
                      [0., 0., 1., 8720.], [0., 0., 0., 1.]]
    assert np.asarray(detail["placement_world_mm"]) == pytest.approx(np.asarray(expected_world))
    assert detail["body_bounds_local_mm"]["x"] == pytest.approx([-25., 925.])
    assert detail["body_bounds_local_mm"]["y"] == pytest.approx([-30., 45.])
    assert detail["body_bounds_local_mm"]["z"] == pytest.approx([-10., 1200.])
    copied_opening = detail["opening"]
    assert copied_opening["id"] == opening_id and copied_opening["host_id"] == wall_id
    expected = [[sign, 0., 0., 0. if sign > 0 else 900.],
                [0., sign, 0., -sign * normal], [0., 0., 1., -20.], [0., 0., 0., 1.]]
    assert np.asarray(copied_opening["placement_in_product_mm"]) == pytest.approx(np.asarray(expected))
    assert copied_opening["body_bounds_local_mm"]["x"] == pytest.approx([0., 900.])
    assert copied_opening["body_bounds_local_mm"]["y"] == pytest.approx([-75., 75.])
    assert copied_opening["body_bounds_local_mm"]["z"] == pytest.approx([0., 1200.])
    assert opening_id not in scene.offered_ids and wall_id not in scene.offered_ids
    assert source.read_bytes() == before


def test_geometry_detail_is_lazy_cached_and_never_authorizes_unoffered_products(tmp_path, monkeypatch):
    scene, source, before, _, wall_id, opening_id, reference_id = public_scene(tmp_path)
    calls = []
    create_shape = scene_context.ifcopenshell.geom.create_shape
    def counted(settings, entity, *args, **kwargs):
        calls.append(entity.GlobalId)
        return create_shape(settings, entity, *args, **kwargs)
    monkeypatch.setattr(scene_context.ifcopenshell.geom, "create_shape", counted)
    with pytest.raises(SceneError, match="SCENE_ID_NOT_OFFERED"):
        scene.geometry_detail(reference_id)
    assert calls == []
    scene.query({"ids": [reference_id]})
    assert calls == [reference_id, opening_id]
    first = scene.geometry_detail(reference_id)
    first["placement_world_mm"][0][3] = 1e9
    assert scene.geometry_detail(reference_id)["placement_world_mm"][0][3] != 1e9
    scene.query({"ids": [reference_id]})
    assert calls == [reference_id, opening_id]
    with pytest.raises(SceneError, match="SCENE_ID_NOT_OFFERED"):
        scene.geometry_detail(wall_id)
    scene.query({"ids": [wall_id]})
    assert calls == [reference_id, opening_id, wall_id]
    assert scene.geometry_detail(wall_id)["body_bounds_local_mm"]["x"] == pytest.approx([0., 7000.])
    assert source.read_bytes() == before
    assert hashlib.sha256(before).digest() == hashlib.sha256(source.read_bytes()).digest()


def test_standalone_records_may_supply_detail_but_missing_facts_are_not_guessed():
    original = fixture_scene()
    records = deepcopy(original.records)
    records[0].update(placement_world_mm=[[0., -1., 0., 100.], [1., 0., 0., 200.],
                                          [0., 0., 1., 300.], [0., 0., 0., 1.]],
                      body_bounds_local_mm={"x": [0., 10000.], "y": [-100., 100.], "z": [0., 3000.]})
    scene = PublicScene(records, original.storeys, project_unit_scale=.001)
    scene.overview()
    before = deepcopy(scene.records)
    page = scene.query({"ids": ["wall", "window-0"]})
    wall = scene.geometry_detail("wall")
    assert wall["placement_world_mm"][0][3] == 100.
    assert scene.records == before
    assert next(row for row in page["records"] if row["id"] == "window-0")["geometry_detail_status"] == "unavailable"
    with pytest.raises(SceneError, match="SCENE_GEOMETRY_DETAIL_UNAVAILABLE"):
        scene.geometry_detail("window-0")
    with pytest.raises(SceneError, match="SCENE_GEOMETRY_DETAIL_UNAVAILABLE"):
        scene.geometry_detail("level")


@pytest.mark.parametrize("field", ["placement_world_mm", "body_bounds_local_mm"])
def test_invalid_or_partial_standalone_geometry_fails_closed(field):
    original = fixture_scene()
    records = deepcopy(original.records)
    records[0].update(placement_world_mm=np.eye(4).tolist(),
                      body_bounds_local_mm={"x": [0., 1.], "y": [0., 1.], "z": [0., 1.]})
    if field == "placement_world_mm":
        records[0][field][0][3] = float("nan")
    else:
        records[0][field].pop("z")
    scene = PublicScene(records, [], project_unit_scale=1.)
    scene.query({"ids": ["wall"]})
    with pytest.raises(SceneError, match="SCENE_GEOMETRY_DETAIL_UNAVAILABLE"):
        scene.geometry_detail("wall")


@pytest.mark.parametrize("fault", ["no_placement", "no_body", "no_fill", "two_fills", "no_host", "two_hosts"])
def test_public_source_missing_or_ambiguous_reference_geometry_is_disclosed(tmp_path, fault):
    model, wall, opening, reference, _, _ = window_scene()
    if fault == "no_placement":
        reference.ObjectPlacement = None
    elif fault == "no_body":
        reference.Representation = None
    elif fault == "no_fill":
        model.remove(reference.FillsVoids[0])
    elif fault == "two_fills":
        model.createIfcRelFillsElement(ifcopenshell.guid.new(), reference.OwnerHistory, None, None, opening, reference)
    elif fault == "no_host":
        model.remove(opening.VoidsElements[0])
    elif fault == "two_hosts":
        model.createIfcRelVoidsElement(ifcopenshell.guid.new(), reference.OwnerHistory, None, None, wall, opening)
    source = tmp_path / "public.ifc"
    model.write(str(source))
    before = source.read_bytes()
    metadata = build_ifc_index(source, tmp_path / "public.sqlite")
    scene = PublicScene.from_ifc(source, tmp_path / "public.sqlite", source_sha256=metadata.source_ifc_sha256)
    page = scene.query({"ids": [reference.GlobalId]})
    assert page["records"][0]["geometry_detail_status"] == "unavailable"
    with pytest.raises(SceneError, match="SCENE_GEOMETRY_DETAIL_UNAVAILABLE"):
        scene.geometry_detail(reference.GlobalId)
    assert source.read_bytes() == before


def test_door_exposes_the_same_public_opening_relative_frame(tmp_path):
    model, wall, opening, reference, _, _ = window_scene(sign=-1., normal=35., base_gap=20.)
    door = model.createIfcDoor(GlobalId=ifcopenshell.guid.new(), OwnerHistory=reference.OwnerHistory,
        Name="Public reference door", ObjectPlacement=reference.ObjectPlacement,
        Representation=reference.Representation, OverallWidth=reference.OverallWidth,
        OverallHeight=reference.OverallHeight)
    reference.FillsVoids[0].RelatedBuildingElement = door
    containment = reference.ContainedInStructure[0]
    containment.RelatedElements = [*containment.RelatedElements, door]
    source = tmp_path / "public.ifc"
    model.write(str(source))
    before = source.read_bytes()
    metadata = build_ifc_index(source, tmp_path / "public.sqlite")
    scene = PublicScene.from_ifc(source, tmp_path / "public.sqlite", source_sha256=metadata.source_ifc_sha256)
    scene.query({"ids": [door.GlobalId]})
    detail = scene.geometry_detail(door.GlobalId)
    assert detail["opening"]["host_id"] == wall.GlobalId
    assert detail["body_bounds_local_mm"]["x"] == pytest.approx([-25., 925.])
    assert np.asarray(detail["opening"]["placement_in_product_mm"]) == pytest.approx(np.asarray(
        [[-1., 0., 0., 900.], [0., -1., 0., 35.], [0., 0., 1., -20.], [0., 0., 0., 1.]]))
    assert source.read_bytes() == before


def test_source_only_detail_recomputes_bound_geometry_without_an_index_or_offering(tmp_path):
    scene, source, before, storey_id, wall_id, opening_id, reference_id = public_scene(tmp_path)
    model = ifcopenshell.open(str(source))
    storey = scene_context.public_geometry_detail(model, storey_id)
    assert storey["placement_world_mm"][0][3] == 3000.
    assert storey["placement_world_mm"][1][3] == -500.
    assert storey["body_bounds_local_mm"] is None
    host = scene_context.public_geometry_detail(model, wall_id)
    assert host["body_bounds_local_mm"]["x"] == pytest.approx([0., 7000.])
    reference = scene_context.public_geometry_detail(model, reference_id)
    assert reference["opening"]["id"] == opening_id
    assert reference["opening"]["host_id"] == wall_id
    assert scene.offered_ids == set()
    with pytest.raises(SceneError, match="SCENE_ID_NOT_OFFERED"):
        scene.geometry_detail(reference_id)
    scene.query({"ids": [reference_id]})
    assert scene.geometry_detail(reference_id) == reference
    with pytest.raises(SceneError, match="SCENE_GEOMETRY_DETAIL_UNAVAILABLE"):
        scene_context.public_geometry_detail(model, "absent-public-identity")
    assert source.read_bytes() == before
