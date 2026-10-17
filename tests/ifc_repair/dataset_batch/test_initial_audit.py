from __future__ import annotations

import ifcopenshell
import pytest

from scripts.ifc_repair.audit_initial_dataset import _body_from_public, audit_case, audit_prompt, geometry_from_text
from scripts.ifc_repair.dataset_batch.engine import apply_recipe, build_recipes, inventory_model


def case_for(scene_factory, tmp_path, family):
    source = scene_factory(tmp_path / "source.ifc", millimetres=True)
    inventory = inventory_model(source)
    recipe = next(row for row in build_recipes(inventory, count=25) if row["family"] == family)
    folder = tmp_path / "case"
    apply_recipe(source, recipe, folder)
    return source, recipe, folder


def test_old_matching_opening_sentence_is_not_a_complete_specification(scene_factory, tmp_path):
    source, recipe, folder = case_for(scene_factory, tmp_path, "window")
    original = ifcopenshell.open(str(source))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    text = (folder / "public/request-world.txt").read_text(encoding="utf-8")
    # Remove the whole new opening specification, leaving the historic vague request.
    import re
    text = re.sub(r"洞口规格开始.*?洞口规格结束。", "同时建立匹配的墙洞口和门窗填充关系。", text)
    check = audit_prompt(original, damaged, recipe, "world", text)
    assert "removed_opening_spec_missing" in check["failures"]
    assert not check["sufficient"]


def test_public_extrusion_parser_reconstructs_circle_radius():
    text = "几何实体1采用圆形截面（IfcCircleProfileDef），半径150毫米。实体坐标原点在构件自身坐标中为（0，0，0）毫米，X/Y/Z轴分别为（1，0，0）、（0，1，0）、（0，0，1）；截面原点在实体坐标中为（0，0，0）毫米，X/Y轴分别为（1，0，0）、（0，1，0）；沿实体坐标方向（0，0，1）拉伸3000毫米。"
    model, product = geometry_from_text(text)
    solid = product.Representation.Representations[0].Items[0]
    assert solid.SweptArea.Radius == pytest.approx(0.15)
    assert solid.Depth == pytest.approx(3.0)


def test_opening_peer_axes_are_parsed_from_peer_clause_not_opening_placement(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc", rotated=False)
    model = ifcopenshell.open(str(source))
    text = "洞口世界原点为（16.5，20，4）米，洞口世界X/Y/Z轴分别为（1，0，0）、（0，1，0）、（0，0，1）。几何形状逐项复制模型中仍存在的IfcOpeningElement「Opening」，参考实例的世界基点为（15，20，4）米，世界X/Y/Z轴分别为（1，0，0）、（0，1，0）、（0，0，1）；复制其自身局部几何，再按本条指定原点和轴放置。"
    geometry_model, peer = _body_from_public(text, model, 1.0)
    assert geometry_model is None
    assert peer.ObjectPlacement.RelativePlacement.Location.Coordinates == pytest.approx([5, 0, 1])


def test_first_batch_audit_rejects_orientation_corruption(scene_factory, tmp_path):
    source, recipe, folder = case_for(scene_factory, tmp_path, "beam")
    original = ifcopenshell.open(str(source))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    text = (folder / "public/request-storey_local.txt").read_text(encoding="utf-8")
    check = audit_prompt(original, damaged, recipe, "storey_local", text)
    assert check["sufficient"], check
    text = text.replace("构件自身X、Y、Z轴在上述坐标系中的方向分别为（1，0，0）、（0，1，0）", "构件自身X、Y、Z轴在上述坐标系中的方向分别为（0，1，0）、（-1，0，0）")
    assert "placement_or_axes_mismatch" in audit_prompt(original, damaged, recipe, "storey_local", text)["failures"]


def test_opening_size_is_independently_compared_not_assumed_equal_to_window(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    opening = model.by_type("IfcWindow")[0].FillsVoids[0].RelatingOpeningElement
    solid = opening.Representation.Representations[0].Items[0]
    solid.SweptArea.YDim = 0.8  # opening depth differs from window geometry
    model.write(str(source))
    inventory = inventory_model(source)
    target = next(row for row in inventory["targets"]["window"] if row["opening_guid"] == opening.GlobalId)
    recipe = {"family": "window", "severity": "light", "deletions": [{**target, "preserve_opening": False}], "property_changes": []}
    folder = tmp_path / "case"
    apply_recipe(source, recipe, folder)
    text = (folder / "public/request-world.txt").read_text(encoding="utf-8")
    original = ifcopenshell.open(str(source))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    assert audit_prompt(original, damaged, recipe, "world", text)["sufficient"]
    text = text.replace("YDim=800毫米", "YDim=150毫米")
    assert "opening_geometry_mismatch" in audit_prompt(original, damaged, recipe, "world", text)["failures"]


@pytest.mark.parametrize("family", ["door", "window", "door_window", "beam", "column", "beam_column", "door_window_beam_column", "attribute"])
def test_bounded_fixture_covers_all_operation_families(scene_factory, tmp_path, family):
    source, recipe, folder = case_for(scene_factory, tmp_path, family)
    original = ifcopenshell.open(str(source))
    damaged = ifcopenshell.open(str(folder / "public/model.ifc"))
    for frame in ("world", "storey_local"):
        text = (folder / f"public/request-{frame}.txt").read_text(encoding="utf-8")
        check = audit_prompt(original, damaged, recipe, frame, text)
        assert check["sufficient"], check


def test_native_receipt_reuse_still_rechecks_changed_prompt_and_seal(scene_factory, tmp_path):
    source, recipe, folder = case_for(scene_factory, tmp_path, "beam")
    receipt = audit_case(folder, "beam", reference=source)
    request = folder / "public/request-world.txt"
    text = request.read_text(encoding="utf-8")
    request.write_text(text.replace("补建一根梁", "补建一根柱"), encoding="utf-8")
    checked = audit_case(folder, "beam", reference=source, reuse_native=receipt)
    assert checked["native_validation_mode"] == "reused_bound_receipt"
    assert checked["ifc_compliant"]
    assert not checked["prompt_information_sufficient"]
    assert not checked["damage_crosscheck_passed"]
    assert not checked["seal_passed"]


def test_native_receipt_reuse_rejects_changed_ifc(scene_factory, tmp_path):
    source, recipe, folder = case_for(scene_factory, tmp_path, "beam")
    receipt = audit_case(folder, "beam", reference=source)
    path = folder / "public/model.ifc"
    model = ifcopenshell.open(str(path))
    model.by_type("IfcWall")[0].Name = "Modified output"
    model.write(str(path))
    with pytest.raises(ValueError, match="native_receipt_byte_binding_failed"):
        audit_case(folder, "beam", reference=source, reuse_native=receipt)
