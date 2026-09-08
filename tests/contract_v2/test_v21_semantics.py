"""Material support matrix and additive version boundaries frozen before implementation."""
import json
from pathlib import Path

import pytest


def document():
    value = json.loads((Path(__file__).parent / "fixtures/complete.json").read_text(encoding="utf-8"))
    value["schema_version"] = "bim-json/2.1"
    return value


def item(value, entity_id):
    return next(e for e in value["entities"] if e["id"] == entity_id)


def validate(value):
    from text2ifc_contract.validation_v21 import validate_v21_document
    return validate_v21_document(value)


def test_single_material_supported_and_old_schema_frozen():
    from text2ifc_contract.validation_v2 import validate_v2_document
    value = document()
    item(value, "beam-1")["materials"] = [{"kind": "single_material", "name": "Steel"}]
    assert validate(value) == []
    value["schema_version"] = "bim-json/2.0"
    assert validate_v2_document(value)


@pytest.mark.parametrize("entity_id", ["beam-1", "column-1", "door-1", "window-1", "project-1"])
def test_unsupported_layer_targets_fail_closed(entity_id):
    value = document()
    item(value, entity_id)["materials"] = [{"kind": "material_layer_set_usage", "layer_set_name": "layers", "direction": "AXIS2", "direction_sense": "POSITIVE", "offset_from_reference_line": 0, "layers": [{"name": "Steel", "thickness": 200}]}]
    assert any(i.code == "UNSUPPORTED_MATERIAL_ASSIGNMENT" for i in validate(value))


@pytest.mark.parametrize("change", ["multiple", "thickness", "axis"])
def test_ambiguous_or_inconsistent_assignments_block(change):
    value = document()
    wall = item(value, "wall-1")
    assignment = {"kind": "material_layer_set_usage", "layer_set_name": "layers", "direction": "AXIS2", "direction_sense": "POSITIVE", "offset_from_reference_line": 0, "layers": [{"name": "Brick", "thickness": wall["attributes"]["Representation"]["profile"]["y"]}]}
    wall["materials"] = [assignment]
    if change == "multiple":
        wall["materials"].append(assignment.copy())
    elif change == "thickness":
        assignment["layers"][0]["thickness"] += 1
    else:
        assignment["direction"] = "AXIS3"
    assert validate(value)


def test_project_single_material_is_not_silently_dropped():
    value = document()
    item(value, "project-1")["materials"] = [{"kind": "single_material", "name": "Steel"}]
    assert any(i.code == "UNSUPPORTED_MATERIAL_ASSIGNMENT" for i in validate(value))


def typed_wall(value, thickness):
    value["entities"].append({"id": "wall-type", "ifc_class": "IfcWallType", "attributes": {"Name": "Wall assembly", "PredefinedType": "STANDARD"}, "materials": [{"kind": "material_layer_set", "layer_set_name": "assembly", "layers": [{"name": "Brick", "thickness": thickness}]}], "property_sets": {"Pset_WallCommon": {"FireRating": "60"}}, "provenance": {"source": "user"}})
    value["relationships"].append({"id": "wall-typing", "ifc_class": "IfcRelDefinesByType", "attributes": {"RelatingType": "wall-type", "RelatedObjects": ["wall-1"]}, "provenance": {"source": "user"}})
    return value


def test_inherited_layers_must_fit_instance_unless_directly_overridden():
    value = typed_wall(document(), 1)
    assert any(i.code == "MATERIAL_LAYER_THICKNESS_MISMATCH" for i in validate(value))
    item(value, "wall-1")["materials"] = [{"kind": "single_material", "name": "Explicit override"}]
    assert validate(value) == []


def test_type_property_applicability_uses_occurrence_family():
    value = typed_wall(document(), 200)
    typ = item(value, "wall-type")
    assert not any(i.code == "PROPERTY_SET_NOT_APPLICABLE" for i in validate(value))
    typ["property_sets"] = {"Pset_BeamCommon": {"FireRating": "60"}}
    assert any(i.code == "PROPERTY_SET_NOT_APPLICABLE" for i in validate(value))


def test_null_performance_property_is_not_a_placeholder():
    value = document()
    item(value, "wall-1")["property_sets"]["Pset_WallCommon"]["FireRating"] = None
    assert any(i.code == "INVALID_PROPERTY_TYPE" for i in validate(value))
