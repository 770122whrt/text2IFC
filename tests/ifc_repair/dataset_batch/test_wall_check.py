from __future__ import annotations

import hashlib
import json

import ifcopenshell
import ifcopenshell.geom
import pytest
from ifcopenshell.api.root.remove_product import remove_product

from scripts.ifc_repair.dataset_batch.wall_check import check_wall_closure


def _target(model, kind, *, preserve=False, index=0):
    element = model.by_type(kind)[index]
    opening = element.FillsVoids[0].RelatingOpeningElement
    host = opening.VoidsElements[0].RelatingBuildingElement
    return {"guid": str(element.GlobalId), "opening_guid": str(opening.GlobalId), "host": {"guid": str(host.GlobalId)}, "preserve_opening": preserve}


def _damage(source, path, targets):
    model = ifcopenshell.open(str(source))
    for target in targets:
        opening = model.by_guid(target["opening_guid"])
        remove_product(model, product=model.by_guid(target["guid"]))
        if not target["preserve_opening"]:
            remove_product(model, product=opening)
    model.write(str(path))
    return path


@pytest.mark.parametrize("rotated,millimetres", [(False, False), (True, False), (True, True)])
def test_window_and_opening_deletion_really_fills_wall(scene_factory, tmp_path, rotated, millimetres):
    source = scene_factory(tmp_path / "source.ifc", rotated=rotated, millimetres=millimetres)
    target = _target(ifcopenshell.open(str(source)), "IfcWindow")
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert report["passed"], report
    assert report["applicable"]
    wall = report["walls"][0]
    assert wall["opening_count"] == {"before": 4, "after": 3, "expected": 3}
    assert wall["mesh_equal_expected"]
    assert wall["meshes"]["after"]["closed"]
    assert wall["meshes"]["after"]["volume_m3"] > wall["meshes"]["before"]["volume_m3"]
    assert wall["other_openings_preserved"]
    probe = wall["opening_checks"][0]
    assert probe["passed"] and len(probe["probes"]) >= 3
    assert all(row["inside_uncut_wall"] and not row["inside_wall_before"] and row["inside_wall_after"] for row in probe["probes"])
    json.dumps(report, allow_nan=False)


def test_only_door_deleted_preserves_opening_and_wall(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    target = _target(ifcopenshell.open(str(source)), "IfcDoor", preserve=True)
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert report["passed"], report
    wall = report["walls"][0]
    assert wall["opening_count"] == {"before": 4, "after": 4, "expected": 4}
    assert wall["mesh_equal_before"] and wall["mesh_equal_expected"]
    opening = wall["opening_checks"][0]
    assert opening["present_after"] and opening["void_relationship_preserved"] and opening["geometry_preserved"]
    assert all(not row["inside_wall_before"] and not row["inside_wall_after"] for row in opening["probes"])


def test_mixed_same_wall_deletions_close_only_requested_opening(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    targets = [_target(model, "IfcDoor", preserve=True), _target(model, "IfcWindow")]
    damaged = _damage(source, tmp_path / "damaged.ifc", targets)
    report = check_wall_closure(source, damaged, {"deletions": targets})
    assert report["passed"], report
    wall = report["walls"][0]
    assert wall["opening_count"] == {"before": 4, "after": 3, "expected": 3}
    assert len(wall["opening_checks"]) == 2
    assert all(row["passed"] for row in wall["opening_checks"])
    assert not wall["mesh_equal_before"]


def test_two_deleted_openings_on_one_wall_are_checked_together(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    targets = [_target(model, "IfcWindow", index=index) for index in (0, 1)]
    damaged = _damage(source, tmp_path / "damaged.ifc", targets)
    report = check_wall_closure(source, damaged, {"deletions": targets})
    assert report["passed"], report
    wall = report["walls"][0]
    assert wall["opening_count"] == {"before": 4, "after": 2, "expected": 2}
    assert all(row["occupancy_confirmed"] for row in wall["opening_checks"])


def test_preserved_opening_with_removed_void_relation_is_rejected(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    target = _target(ifcopenshell.open(str(source)), "IfcDoor", preserve=True)
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    changed = ifcopenshell.open(str(damaged))
    changed.remove(changed.by_guid(target["opening_guid"]).VoidsElements[0])
    changed.write(str(damaged))
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert not report["passed"]
    assert not report["walls"][0]["opening_checks"][0]["void_relationship_preserved"]


def test_unrelated_opening_removal_is_rejected(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    target = _target(model, "IfcWindow")
    extra = _target(model, "IfcDoor", index=1)
    damaged = _damage(source, tmp_path / "damaged.ifc", [target, extra])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert not report["passed"]
    assert not report["walls"][0]["other_openings_preserved"]


def _bake_cut_wall_into_brep(model):
    """Bake the already cut geometry into the wall's own IFC Body."""
    wall = model.by_type("IfcWall")[0]
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, wall)
    vertices = list(zip(*[iter(shape.geometry.verts)] * 3))
    triangles = list(zip(*[iter(shape.geometry.faces)] * 3))
    points = [model.createIfcCartesianPoint(vertex) for vertex in vertices]
    faces = [model.createIfcFace([model.createIfcFaceOuterBound(model.createIfcPolyLoop([points[index] for index in triangle]), True)]) for triangle in triangles]
    brep = model.createIfcFacetedBrep(model.createIfcClosedShell(faces))
    body = wall.Representation.Representations[0]
    body.RepresentationType = "Brep"
    body.Items = [brep]


def test_baked_wall_hole_is_rejected_even_if_expected_mesh_matches(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc", rotated=False)
    model = ifcopenshell.open(str(source))
    target = _target(model, "IfcWindow")
    _bake_cut_wall_into_brep(model)
    model.write(str(source))
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert not report["passed"]
    wall = report["walls"][0]
    assert wall["mesh_equal_expected"], "This is the confound the independent interior probes must reject"
    assert not wall["opening_checks"][0]["passed"]
    assert any(not row["inside_wall_after"] for row in wall["opening_checks"][0]["probes"])


def test_unavailable_opening_geometry_cannot_pass(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    target = _target(model, "IfcWindow")
    model.by_guid(target["opening_guid"]).Representation = None
    model.write(str(source))
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert not report["passed"] and report["errors"]


def test_opening_outside_host_cannot_claim_closure(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc", rotated=False)
    model = ifcopenshell.open(str(source))
    target = _target(model, "IfcWindow")
    model.by_guid(target["opening_guid"]).ObjectPlacement.RelativePlacement.Location.Coordinates = (5.0, 2.0, 1.0)
    model.write(str(source))
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    report = check_wall_closure(source, damaged, {"deletions": [target]})
    assert not report["passed"]
    assert report["walls"][0]["mesh_equal_expected"]
    assert any(row["code"] == "OPENING_INTERIOR_PROBES_UNCONFIRMED" for row in report["errors"])


def test_read_only_and_input_hash_binding(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    target = _target(ifcopenshell.open(str(source)), "IfcWindow")
    damaged = _damage(source, tmp_path / "damaged.ifc", [target])
    original_bytes, damaged_bytes = source.read_bytes(), damaged.read_bytes()
    hashes = {"source_sha256": hashlib.sha256(original_bytes).hexdigest(), "damaged_sha256": hashlib.sha256(damaged_bytes).hexdigest()}
    manifest = {"deletions": [target], **hashes}
    report = check_wall_closure(source, damaged, manifest)
    assert report["passed"] and report["input_unchanged"]
    assert source.read_bytes() == original_bytes and damaged.read_bytes() == damaged_bytes
    report = check_wall_closure(source, damaged, {**manifest, "source_sha256": "0" * 64})
    assert not report["passed"]


def test_structural_only_recipe_reports_not_applicable(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    report = check_wall_closure(source, source, {"deletions": [{"guid": "beam", "opening_guid": None, "host": {}, "preserve_opening": False}]})
    assert not report["applicable"] and report["walls"] == []


def test_missing_host_or_conflicting_opening_policy_fails_closed(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    target = _target(ifcopenshell.open(str(source)), "IfcWindow")
    assert not check_wall_closure(source, source, {"deletions": [{**target, "host": {}}]})["passed"]
    assert not check_wall_closure(source, source, {"deletions": [target, {**target, "preserve_opening": True}]})["passed"]
