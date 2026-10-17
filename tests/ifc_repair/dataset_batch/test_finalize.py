from __future__ import annotations

import json

import ifcopenshell
import ifcopenshell.guid

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, inventory_model
from scripts.ifc_repair.dataset_batch.validation import native_validate, sha256
from scripts.ifc_repair.finalize_batch_dataset import normalize_case


def test_empty_classification_is_cleaned_only_after_recorded_deletion(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    door = model.by_type("IfcDoor")[0]
    classification = model.create_entity("IfcClassification", Source="Offline fixture", Edition="1", Name="Uniformat")
    reference = model.createIfcClassificationReference(None, "D1010", "Doors", classification)
    relation = model.create_entity("IfcRelAssociatesClassification", GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory, Name="Door classification", RelatedObjects=[door], RelatingClassification=reference)
    shared = model.create_entity("IfcRelAssociatesClassification", GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory, Name="Shared classification", RelatedObjects=model.by_type("IfcDoor"), RelatingClassification=reference)
    shared_id = shared.GlobalId
    relation_id, door_id = relation.GlobalId, door.GlobalId
    model.write(str(source))
    source_hash = sha256(source)
    assert native_validate(source)["passed"]
    inv = inventory_model(source)
    target = next(p for p in inv["targets"]["door"] if p["guid"] == door_id)
    recipe = {"family": "door", "severity": "light", "deletions": [{**target, "preserve_opening": True}], "property_changes": []}
    folder = tmp_path / "case"
    initial = apply_recipe(source, recipe, folder, inventory=inv)
    assert initial["status"] == "failed"
    result = normalize_case(source, folder)
    assert result["status"] == "passed"
    assert sha256(source) == source_hash
    changed = ifcopenshell.open(str(folder / "public/model.ifc"))
    assert len(changed.by_type("IfcRelAssociatesClassification")) == 1
    assert len(changed.by_guid(shared_id).RelatedObjects) == 1
    manifest = json.loads((folder / "private/mutation.json").read_text(encoding="utf-8"))
    assert manifest["normalization"]["removed_empty_relationships"] == [relation_id]
    history = folder / "private/normalization/001"
    assert (history / "model.ifc").exists()
    assert not json.loads((history / "validation.json").read_text(encoding="utf-8"))["passed"]


def test_normalizer_keeps_existing_valid_case_bytes(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    inv = inventory_model(source)
    target = inv["targets"]["door"][0]
    folder = tmp_path / "case"
    recipe = {"family": "door", "severity": "light", "deletions": [{**target, "preserve_opening": True}], "property_changes": []}
    initial = apply_recipe(source, recipe, folder, inventory=inv)
    assert initial["status"] == "passed"
    before = sha256(folder / "public/model.ifc")
    result = normalize_case(source, folder)
    assert result["status"] == "passed"
    assert sha256(folder / "public/model.ifc") == before
    assert not (folder / "private/normalization").exists()
