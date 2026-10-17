from __future__ import annotations

import copy
import json
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
import numpy as np
import pytest
from ifcopenshell.api.root.remove_product import remove_product

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, build_recipes
from scripts.ifc_repair.dataset_batch.prompt_check import audit_prompt
from scripts.ifc_repair.dataset_batch.prompts_v2 import PROFILE, prepare_inventory


def make_case(scene_factory, tmp_path, family="window", *, millimetres=True, rotated=True, configure=None):
    source = scene_factory(tmp_path / "source.ifc", millimetres=millimetres, rotated=rotated)
    if configure:
        model = ifcopenshell.open(str(source))
        configure(model)
        model.write(str(source))
    inv = prepare_inventory(source)
    if family == "mixed":
        deleted = [{**inv["targets"][key][0], "preserve_opening": key == "door"} for key in ("door", "window", "beam", "column")]
        ids = {row["guid"] for row in deleted}
        prop = next(row for row in inv["properties"] if row["guid"] not in ids)
        after = not prop["before"] if isinstance(prop["before"], bool) else prop["before"] + " damaged"
        recipe = {"family": family, "severity": "medium", "deletions": deleted, "property_changes": [{**prop, "after": after}]}
    elif family in {"attribute", "attribute_string"}:
        prop = next(row for row in inv["properties"] if row["ifc_class"] == ("IfcDoor" if family == "attribute" else "IfcWindow") and row["value_type"] == ("IfcBoolean" if family == "attribute" else "IfcIdentifier"))
        after = not prop["before"] if isinstance(prop["before"], bool) else prop["before"] + " damaged"
        recipe = {"family": family, "severity": "light", "deletions": [], "property_changes": [{**prop, "after": after}]}
    elif family == "peer":
        target = inv["targets"]["door"][0]
        peer = target["geometry"]["peers"][0]
        geometry = {**target["geometry"], "body_spec": {"method": "surviving_instance", "peer": peer}}
        recipe = {"family": family, "severity": "light", "deletions": [{**target, "geometry": geometry, "preserve_opening": True}], "property_changes": []}
    else:
        recipe = next(row for row in build_recipes(inv, count=25) if row["family"] == family)
    folder = tmp_path / "case"
    apply_recipe(source, recipe, folder, inventory=inv, prompt_profile=PROFILE)
    manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
    texts = {mode: path.read_text(encoding="utf-8") for mode in ("host_wall", "world") if (path := folder / f"public/request-{mode}.txt").exists()}
    return ifcopenshell.open(str(source)), ifcopenshell.open(str(folder / "public/model.ifc")), manifest, texts


def assert_failure(reference, damaged, manifest, mode, text, fragment):
    report = audit_prompt(reference, damaged, manifest, mode, text)
    assert not report["passed"], report
    assert any(fragment in error for error in report["errors"]), report
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("family", ["door", "window", "door_window", "beam", "column", "beam_column", "door_window_beam_column", "attribute", "attribute_string", "mixed"])
def test_actual_automatic_requests_cover_damage_families(scene_factory, tmp_path, family, monkeypatch):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, family)
    # Auditing may never regenerate the expected sentence from private metadata.
    monkeypatch.setattr("scripts.ifc_repair.dataset_batch.prompts_v2.render_prompts", lambda *_: pytest.fail("prompt regeneration"))
    for mode, text in texts.items():
        report = audit_prompt(reference, damaged, manifest, mode, text)
        assert report["passed"], report
        assert report["checks"]["target_meshes"] == len(manifest["deletions"])
        assert report["checks"]["openings"] == sum(row["ifc_class"] in {"IfcDoor", "IfcWindow"} for row in manifest["deletions"])
        assert report["checks"]["properties"] == len(manifest["property_changes"])
        json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("rotated,millimetres", [(False, False), (True, False), (True, True)])
def test_world_and_wall_distance_frames_resolve_actual_ifc_units(scene_factory, tmp_path, rotated, millimetres):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, rotated=rotated, millimetres=millimetres)
    for mode, text in texts.items():
        report = audit_prompt(reference, damaged, manifest, mode, text)
        assert report["passed"], report


@pytest.mark.parametrize("mode", ["world", "host_wall"])
@pytest.mark.parametrize("corruption", ["origin", "axes", "section", "no_body", "opening_origin", "opening_axes", "opening_section", "no_opening", "no_void", "no_fill"])
def test_actual_text_corruptions_are_rejected(scene_factory, tmp_path, mode, corruption):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path)
    text = texts[mode]
    expected = "mismatch"
    if corruption == "origin":
        if mode == "world":
            text = re.sub(r"放置原点的世界坐标为（[^）]+）", "放置原点的世界坐标为（999，999，999）", text, count=1)
        else:
            text = re.sub(r"沿墙自身X方向距离[-+0-9.eE]+米", "沿墙自身X方向距离999米", text, count=1)
    elif corruption == "axes":
        target_part, rest = text.split("洞口规格开始：", 1)
        prefix = "世界X/Y/Z轴分别为" if mode == "world" else "构件自身X/Y/Z轴相对墙自身坐标系的方向分别为"
        # The world row also has wall axes; edit the final (target) clause.
        matches = list(re.finditer(re.escape(prefix) + r"[^。]+。", target_part))
        match = matches[-1]
        target_part = target_part[:match.start()] + prefix + "（1，0，0）、（0，1，0）、（0，0，1）。" + target_part[match.end():]
        if mode == "host_wall":
            target_part = target_part.replace(prefix + "（1，0，0）、（0，1，0）", prefix + "（0，1，0）、（-1，0，0）")
        text = target_part + "洞口规格开始：" + rest
    elif corruption == "section":
        text = text.replace("XDim=1200毫米", "XDim=1100毫米", 1)
    elif corruption == "no_body":
        text = re.sub(r"几何实体1采用.*?拉伸[-+0-9.eE]+毫米。", "", text, count=1)
        expected = "complete_geometry_not_described"
    elif corruption.startswith("opening_"):
        before, opening = text.split("洞口规格开始：", 1)
        if corruption == "opening_origin":
            if mode == "world":
                opening = re.sub(r"洞口世界原点为（[^）]+）", "洞口世界原点为（999，999，999）", opening, count=1)
            else:
                opening = opening.replace("Y方向距离0.000000米", "Y方向距离1.000000米", 1)
        elif corruption == "opening_axes":
            prefix = "世界X/Y/Z轴分别为" if mode == "world" else "构件自身X/Y/Z轴相对墙自身坐标系的方向分别为"
            opening = re.sub(re.escape(prefix) + r"[^。]+。", prefix + "（1，0，0）、（0，0，1）、（0，-1，0）。", opening, count=1)
        else:
            opening = opening.replace("YDim=150毫米", "YDim=500毫米", 1)
        text = before + "洞口规格开始：" + opening
    elif corruption == "no_opening":
        text = re.sub(r"洞口规格开始：.*?洞口规格结束。", "建立匹配的洞口。", text)
        expected = "opening_spec_missing"
    elif corruption == "no_void":
        text = text.replace("在上述宿主墙上建立新洞口的void关系", "在墙上建立新洞口")
        expected = "void_relationship_missing"
    elif corruption == "no_fill":
        text = text.replace("门窗填充关系", "普通关联")
        expected = "fill_relationship_missing"
    assert text != texts[mode]
    assert_failure(reference, damaged, manifest, mode, text, expected)


def test_bbox_does_not_hide_missing_circle_or_wrong_radius(scene_factory, tmp_path):
    def circle(model):
        unit = ifcopenshell.util.unit.calculate_unit_scale(model)
        for column in model.by_type("IfcColumn"):
            solid = column.Representation.Representations[0].Items[0]
            position = model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((0.0, 0.0)), None)
            solid.SweptArea = model.createIfcCircleProfileDef("AREA", None, position, 0.15 / unit)
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "column", configure=circle)
    assert audit_prompt(reference, damaged, manifest, "world", texts["world"])["passed"]
    assert_failure(reference, damaged, manifest, "world", texts["world"].replace("半径150毫米", "半径149毫米"), "geometry_mismatch")


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_preserved_opening_is_selected_by_public_host_frame_and_axes(scene_factory, tmp_path, mode):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "door")
    assert manifest["deletions"][0]["preserve_opening"]
    report = audit_prompt(reference, damaged, manifest, mode, texts[mode])
    assert report["passed"], report
    opening = damaged.by_guid(manifest["deletions"][0]["opening_guid"])
    remove_product(damaged, product=opening)
    assert_failure(reference, damaged, manifest, mode, texts[mode], "retained_opening_not_unique_or_absent")


def test_wall_modes_and_world_names_are_kept_separate(scene_factory, tmp_path):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path)
    for leak in ("宿主墙「Host wall」。", "构件名「" + manifest["deletions"][0]["name"] + "」。", "构件GUID=" + manifest["deletions"][0]["guid"]):
        assert_failure(reference, damaged, manifest, "world", texts["world"] + leak, "leak")
    assert_failure(reference, damaged, manifest, "host_wall", texts["host_wall"] + "世界坐标为（1，2，3）米。", "mixed_locator_modes")
    assert_failure(reference, damaged, manifest, "storey_local", texts["world"], "unsupported_mode")


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_ambiguous_wall_locator_is_rejected_without_private_guid_fallback(scene_factory, tmp_path, mode):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path)
    wall = damaged.by_type("IfcWall")[0]
    duplicate = damaged.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory, Name=wall.Name, ObjectPlacement=wall.ObjectPlacement, Representation=wall.Representation)
    containment = wall.ContainedInStructure[0]
    containment.RelatedElements = tuple(containment.RelatedElements) + (duplicate,)
    assert_failure(reference, damaged, manifest, mode, texts[mode], "wall_not_unique_or_absent")


def _brep_doors(model):
    _brep_products(model, model.by_type("IfcDoor"))


def _brep_products(model, products):
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    for door in products:
        shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), door)
        vertices = np.asarray(shape.geometry.verts).reshape(-1, 3) / unit
        triangles = np.asarray(shape.geometry.faces).reshape(-1, 3)
        points = [model.createIfcCartesianPoint(tuple(float(v) for v in vertex)) for vertex in vertices]
        faces = [model.createIfcFace([model.createIfcFaceOuterBound(model.createIfcPolyLoop([points[int(i)] for i in triangle]), True)]) for triangle in triangles]
        representation = door.Representation.Representations[0]
        representation.RepresentationType = "Brep"
        representation.Items = [model.createIfcFacetedBrep(model.createIfcClosedShell(faces))]


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_complex_peer_resolves_public_text_even_with_wrong_private_peer_guid(scene_factory, tmp_path, mode):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "peer", configure=_brep_doors)
    assert "几何形状逐项复制" in texts[mode]
    altered = copy.deepcopy(manifest)
    altered["deletions"][0]["geometry"]["body_spec"]["peer"]["guid"] = altered["deletions"][0]["guid"]
    report = audit_prompt(reference, damaged, altered, mode, texts[mode])
    assert report["passed"], report
    peer_id = manifest["deletions"][0]["geometry"]["body_spec"]["peer"]["guid"]
    remove_product(damaged, product=damaged.by_guid(peer_id))
    assert_failure(reference, damaged, manifest, mode, texts[mode], "public_peer_not_unique_or_absent")


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_property_target_restoration_value_and_type_are_checked(scene_factory, tmp_path, mode):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "attribute")
    text = texts[mode]
    assert_failure(reference, damaged, manifest, mode, text.replace("改为是", "改为否"), "property_restoration_value_mismatch")
    change = manifest["property_changes"][0]
    entity = damaged.by_guid(change["guid"])
    prop = next(prop for rel in entity.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.Name == change["pset_name"] for prop in rel.RelatingPropertyDefinition.HasProperties if prop.Name == change["property_name"])
    prop.NominalValue = damaged.createIfcLogical(False)
    assert_failure(reference, damaged, manifest, mode, text, "property_type_mismatch")


def test_property_ambiguity_and_damaged_value_are_not_covered_by_source_manifest(scene_factory, tmp_path):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "attribute")
    text = texts["world"]
    change = manifest["property_changes"][0]
    entity = damaged.by_guid(change["guid"])
    duplicate = damaged.create_entity(entity.is_a(), GlobalId=ifcopenshell.guid.new(), OwnerHistory=entity.OwnerHistory, Name="Different name", ObjectPlacement=entity.ObjectPlacement, Representation=entity.Representation)
    containment = entity.ContainedInStructure[0]
    containment.RelatedElements = tuple(containment.RelatedElements) + (duplicate,)
    damaged.create_entity("IfcRelFillsElement", GlobalId=ifcopenshell.guid.new(), OwnerHistory=entity.OwnerHistory, RelatingOpeningElement=entity.FillsVoids[0].RelatingOpeningElement, RelatedBuildingElement=duplicate)
    assert_failure(reference, damaged, manifest, "world", text, "property_target_not_unique_or_absent")


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_opening_peer_resolves_from_coordinates_or_the_named_surviving_fill(scene_factory, tmp_path, mode):
    def opening_breps(model):
        _brep_products(model, [window.FillsVoids[0].RelatingOpeningElement for window in model.by_type("IfcWindow")])
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "window", configure=opening_breps)
    text = texts[mode]
    assert "几何形状逐项复制" in text
    if mode == "host_wall":
        assert "所填充的洞口" in text
    report = audit_prompt(reference, damaged, manifest, mode, text)
    assert report["passed"], report
    peer_id = manifest["deletions"][0]["opening"]["geometry"]["body_spec"]["peer"]["guid"]
    remove_product(damaged, product=damaged.by_guid(peer_id))
    assert_failure(reference, damaged, manifest, mode, text, "public_peer_not_unique_or_absent")


def test_property_damaged_value_is_independently_read(scene_factory, tmp_path):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, "attribute")
    change = manifest["property_changes"][0]
    entity = damaged.by_guid(change["guid"])
    prop = next(prop for rel in entity.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.Name == change["pset_name"] for prop in rel.RelatingPropertyDefinition.HasProperties if prop.Name == change["property_name"])
    prop.NominalValue = damaged.createIfcBoolean(change["before"])
    assert_failure(reference, damaged, manifest, "world", texts["world"], "property_before_or_after_mismatch")


def test_units_and_missing_rows_fail_closed(scene_factory, tmp_path):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path)
    assert_failure(reference, damaged, manifest, "world", texts["world"].replace("距离和放置坐标单位为米，几何尺寸单位为毫米。", ""), "units_missing")
    empty = "\n".join(line for line in texts["world"].splitlines() if not re.match(r"\d+\. ", line))
    assert_failure(reference, damaged, manifest, "world", empty, "target_count_mismatch")


def _cross_storey_windows(model):
    """Two upper-floor windows cut a tall wall contained on the lower floor."""
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    lower = model.by_type("IfcBuildingStorey")[0]
    owner = lower.OwnerHistory
    upper_axis = model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((0.0, 0.0, 3.0 / unit)), None, None)
    upper = model.create_entity("IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, Name="Upper level", CompositionType="ELEMENT", Elevation=6.0 / unit, ObjectPlacement=model.createIfcLocalPlacement(lower.ObjectPlacement, upper_axis))
    aggregate = next(rel for rel in model.by_type("IfcRelAggregates") if lower in rel.RelatedObjects)
    aggregate.RelatedObjects = tuple(aggregate.RelatedObjects) + (upper,)
    windows = model.by_type("IfcWindow")
    lower_containment = windows[0].ContainedInStructure[0]
    lower_containment.RelatedElements = tuple(item for item in lower_containment.RelatedElements if item not in windows)
    model.create_entity("IfcRelContainedInSpatialStructure", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, RelatingStructure=upper, RelatedElements=windows)
    for window in windows:
        window.ObjectPlacement.PlacementRelTo = upper.ObjectPlacement
        window.FillsVoids[0].RelatingOpeningElement.ObjectPlacement.PlacementRelTo = upper.ObjectPlacement
    wall = model.by_type("IfcWall")[0]
    wall.Representation.Representations[0].Items[0].Depth = 9.0 / unit
    other_axis = model.createIfcAxis2Placement3D(model.createIfcCartesianPoint((12.0 / unit, 0.0, 0.0)), None, None)
    other = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, Name="Other host", ObjectPlacement=model.createIfcLocalPlacement(lower.ObjectPlacement, other_axis), Representation=wall.Representation)
    lower_containment.RelatedElements = tuple(lower_containment.RelatedElements) + (other,)


def _replace_world_wall(text, wall, unit):
    frame = np.asarray(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement), dtype=float)
    frame[:3, 3] *= unit
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    settings.set("disable-opening-subtractions", True)
    shape = ifcopenshell.geom.create_shape(settings, wall)
    vertices = np.asarray(shape.geometry.verts).reshape(-1, 3)

    def xyz(value):
        return "（" + "，".join(f"{x:.6f}".rstrip("0").rstrip(".") for x in value) + "）"

    locator = "宿主墙世界原点为" + xyz(frame[:3, 3]) + "米，世界X/Y/Z轴分别为" + "、".join(xyz(axis) for axis in frame[:3, :3].T) + "。宿主墙未扣洞口的世界外包范围下角点为" + xyz(vertices.min(axis=0)) + "米，上角点为" + xyz(vertices.max(axis=0)) + "米。"
    return re.sub(r"宿主墙世界原点为.*?宿主墙未扣洞口的世界外包范围下角点为.*?米，上角点为.*?米。", locator, text, count=1)


@pytest.mark.parametrize("family", ["window", "attribute_string"])
def test_world_cross_storey_window_and_property_keep_their_own_floor(scene_factory, tmp_path, family):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, family, configure=_cross_storey_windows)
    assert "host_wall" not in texts  # Name + target floor cannot identify the lower-floor wall.
    assert "归属楼层「Upper level」" in texts["world"]
    report = audit_prompt(reference, damaged, manifest, "world", texts["world"])
    assert report["passed"], report
    assert report["checks"]["host_locators"] == 1
    assert report["checks"]["floor_memberships"] == 1


@pytest.mark.parametrize("family,expected", [("window", "floor_membership_mismatch"), ("attribute_string", "property_target_not_unique_or_absent")])
def test_world_cross_storey_target_floor_cannot_be_replaced_by_wall_floor(scene_factory, tmp_path, family, expected):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, family, configure=_cross_storey_windows)
    text = texts["world"].replace("归属楼层「Upper level」", "归属楼层「Level A」")
    assert_failure(reference, damaged, manifest, "world", text, expected)


@pytest.mark.parametrize("family,expected", [("window", "wall_host_mismatch"), ("attribute_string", "property_target_not_unique_or_absent")])
def test_world_cross_storey_existing_but_wrong_host_is_rejected(scene_factory, tmp_path, family, expected):
    reference, damaged, manifest, texts = make_case(scene_factory, tmp_path, family, configure=_cross_storey_windows)
    other = next(wall for wall in damaged.by_type("IfcWall") if wall.Name == "Other host")
    text = _replace_world_wall(texts["world"], other, ifcopenshell.util.unit.calculate_unit_scale(damaged))
    assert text != texts["world"]
    assert_failure(reference, damaged, manifest, "world", text, expected)


def test_cross_storey_host_mode_still_requires_wall_name_on_target_floor(scene_factory, tmp_path):
    reference, damaged, manifest, _ = make_case(scene_factory, tmp_path, configure=_cross_storey_windows)
    # Render the invalid host request explicitly to exercise the independent audit.
    from scripts.ifc_repair.dataset_batch.prompts_v2 import render_prompts
    invalid = copy.deepcopy(manifest)
    invalid["deletions"][0]["host"]["name_storey_unique"] = True
    text = render_prompts(invalid)["host_wall"]
    assert text is not None
    assert_failure(reference, damaged, manifest, "host_wall", text, "wall_not_unique_or_absent")


def test_checker_receipt_names_the_version_even_for_unsupported_mode():
    report = audit_prompt(None, None, {}, "storey_local", "ignored")
    assert report["checker_version"] == "text2ifc/dataset-prompt-check/1.1"
    assert not report["passed"]
