from __future__ import annotations

import hashlib
import json

import ifcopenshell
import pytest

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, build_recipes, inventory_model
from scripts.ifc_repair.dataset_batch.prompts import render_prompts
from scripts.ifc_repair.dataset_batch.validation import native_validate, verify_case


def test_inventory_resolves_rotated_storey_and_millimetres(scene_factory, tmp_path):
    inv = inventory_model(scene_factory(tmp_path / "source.ifc", millimetres=True))
    door = next(row for row in inv["targets"]["door"] if row["name"] == "IfcDoor-1")
    assert door["geometry"]["origin_world_m"] == pytest.approx([10, 21, 3])
    assert door["geometry"]["origin_storey_m"] == pytest.approx([1, 0, 0])
    assert door["geometry"]["dimensions_local_m"] == pytest.approx([0.9, 0.15, 2.1])
    assert door["host"]["name"] == "Host wall"


def test_recipes_are_distinct_cover_families_and_reproducible(scene_factory, tmp_path):
    inv = inventory_model(scene_factory(tmp_path / "source.ifc"))
    recipes = build_recipes(inv, count=25, seed=42)
    assert recipes == build_recipes(inv, count=25, seed=42)
    assert len(recipes) == len({json.dumps(r, sort_keys=True) for r in recipes}) == 25
    assert {"door", "window", "door_window", "beam", "column", "beam_column", "door_window_beam_column", "attribute"} <= {r["family"] for r in recipes}
    assert any(r["deletions"] and r["property_changes"] for r in recipes)


def test_damage_is_legal_non_destructive_and_prompt_never_exports_deleted_guids(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    inv = inventory_model(source)
    recipe = next(r for r in build_recipes(inv, count=25, seed=12) if r["family"] == "door_window")
    result = apply_recipe(source, recipe, tmp_path / "case", inventory=inv)
    assert result["status"] == "passed"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    manifest = json.loads((tmp_path / "case/private/mutation.json").read_text(encoding="utf-8"))
    assert native_validate(tmp_path / "case/public/model.ifc")["passed"]
    assert verify_case(source, tmp_path / "case/public/model.ifc", manifest)["passed"]
    for text in render_prompts(manifest).values():
        if isinstance(text, str):
            assert all(item["guid"] not in text for item in manifest["deletions"])
    assert not result["human_reviewed"]


def test_shared_property_is_isolated_to_requested_occurrence(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc", shared_property=True)
    inv = inventory_model(source)
    prop = next(p for p in inv["properties"] if p["ifc_class"] == "IfcDoor")
    recipe = {"family": "attribute", "severity": "light", "deletions": [], "property_changes": [{**prop, "after": False}]}
    result = apply_recipe(source, recipe, tmp_path / "case", inventory=inv)
    assert result["status"] == "passed"
    model = ifcopenshell.open(str(tmp_path / "case/public/model.ifc"))
    values = {}
    for door in model.by_type("IfcDoor"):
        for rel in door.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                values[door.GlobalId] = rel.RelatingPropertyDefinition.HasProperties[0].NominalValue.wrappedValue
    assert values[prop["guid"]] is False
    assert sum(value is True for value in values.values()) == 1


def test_verifier_rejects_unrecorded_change(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    changed = ifcopenshell.open(str(source))
    changed.by_type("IfcWall")[0].Name = "Unrelated edit"
    damaged = tmp_path / "changed.ifc"
    changed.write(str(damaged))
    manifest = {"deletions": [], "property_changes": []}
    result = verify_case(source, damaged, manifest)
    assert not result["passed"]
    assert result["unrecorded_product_changes"]


def test_plain_boolean_can_not_supply_25_distinct_cases():
    inv = {"targets": {key: [] for key in ("door", "window", "beam", "column")}, "properties": [{"guid": "example", "ifc_class": "IfcDoor", "pset_name": "Pset_DoorCommon", "property_name": "IsExternal", "value_type": "IfcBoolean", "before": True}]}
    assert len(build_recipes(inv, count=25, seed=1)) == 1


def test_case_cannot_overwrite_previous_artifacts(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    inv = inventory_model(source)
    recipe = build_recipes(inv, count=1)[0]
    output = tmp_path / "case"
    apply_recipe(source, recipe, output, inventory=inv)
    before = hashlib.sha256((output / "public/model.ifc").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        apply_recipe(source, recipe, output, inventory=inv)
    assert hashlib.sha256((output / "public/model.ifc").read_bytes()).hexdigest() == before


def test_circle_column_prompt_specifies_radius_instead_of_only_bounding_box(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    column = model.by_type("IfcColumn")[0]
    solid = column.Representation.Representations[0].Items[0]
    position = model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((0.0, 0.0)), None)
    solid.SweptArea = model.createIfcCircleProfileDef("AREA", None, position, 0.15)
    model.write(str(source))
    inv = inventory_model(source)
    target = next(t for t in inv["targets"]["column"] if t["guid"] == column.GlobalId)
    recipe = {"family": "column", "severity": "light", "deletions": [{**target, "preserve_opening": False}], "property_changes": []}
    apply_recipe(source, recipe, tmp_path / "case", inventory=inv)
    text = (tmp_path / "case/public/request-world.txt").read_text(encoding="utf-8")
    assert "圆形截面" in text
    assert "半径150毫米" in text


def test_verifier_rejects_silent_property_type_and_project_units_change(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    changed = ifcopenshell.open(str(source))
    prop = next(p for p in changed.by_type("IfcPropertySingleValue") if p.Name == "Reference")
    prop.NominalValue = changed.createIfcLabel(prop.NominalValue.wrappedValue)
    assert not verify_case(source, changed, {"deletions": [], "property_changes": []})["passed"]
    changed = ifcopenshell.open(str(source))
    changed.by_type("IfcSIUnit")[0].Prefix = "MILLI"
    assert not verify_case(source, changed, {"deletions": [], "property_changes": []})["passed"]


def test_instance_pset_also_owned_by_type_does_not_mutate_inherited_value(scene_factory, tmp_path):
    import uuid
    from scripts.ifc_repair.dataset_batch.engine import _change_property
    import ifcopenshell.util.element
    source = scene_factory(tmp_path / "source.ifc", shared_property=False)
    model = ifcopenshell.open(str(source))
    door = model.by_type("IfcDoor")[0]
    pset = next(rel.RelatingPropertyDefinition for rel in door.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties"))
    kind = model.create_entity("IfcDoorStyle", GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory, Name="Shared type", HasPropertySets=[pset], OperationType="SINGLE_SWING_LEFT", ConstructionType="WOOD", ParameterTakesPrecedence=False, Sizeable=False)
    model.create_entity("IfcRelDefinesByType", GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory, RelatedObjects=model.by_type("IfcDoor"), RelatingType=kind)
    change = {"guid": door.GlobalId, "pset_name": pset.Name, "property_name": "IsExternal", "value_type": "IfcBoolean", "before": True, "after": False}
    _change_property(model, change, uuid.uuid4())
    assert kind.HasPropertySets[0].HasProperties[0].NominalValue.wrappedValue is True
    assert ifcopenshell.util.element.get_psets(door, should_inherit=False)[pset.Name]["IsExternal"] is False
