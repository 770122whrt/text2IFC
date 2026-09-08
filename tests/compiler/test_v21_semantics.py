"""Frozen deterministic material/type/property failure family; no Provider evidence."""
import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as util
import pytest

from text2ifc_compiler import compile_document


def document():
    value = json.loads((Path(__file__).parents[1] / "contract_v2/fixtures/complete.json").read_text(encoding="utf-8"))
    value["schema_version"] = "bim-json/2.1"
    return value


def record(value, entity_id):
    return next(r for r in value["entities"] if r["id"] == entity_id)


def by_id(model, entity_id):
    return next(e for e in model.by_type("IfcObjectDefinition") if util.get_psets(e, should_inherit=False).get("Pset_text2IFCIdentity", {}).get("BimJsonId") == entity_id)


@pytest.mark.parametrize("entity_id", ["wall-1", "slab-1", "beam-1", "column-1", "door-1", "window-1"])
def test_requested_single_material_survives_reopen(tmp_path, entity_id):
    value = document()
    record(value, entity_id)["materials"] = [{"kind": "single_material", "name": "Explicit material"}]
    out = tmp_path / "out.ifc"
    result = compile_document(value, out)
    assert result.success, result
    assert util.get_material(by_id(ifcopenshell.open(str(out)), entity_id)).Name == "Explicit material"


def layer_usage(thickness, axis="AXIS2"):
    return {"kind": "material_layer_set_usage", "layer_set_name": "assembly", "direction": axis, "direction_sense": "POSITIVE", "offset_from_reference_line": 0, "layers": [{"name": "Layer A", "thickness": thickness}]}


def test_legacy_layer_usage_cannot_silently_disappear(tmp_path):
    value = document()
    value["schema_version"] = "bim-json/2.0"
    wall = record(value, "wall-1")
    wall["materials"] = [layer_usage(wall["attributes"]["Representation"]["profile"]["y"])]
    result = compile_document(value, tmp_path / "legacy.ifc")
    assert result.success, result
    assert util.get_material(by_id(ifcopenshell.open(str(result.output_path)), "wall-1")) is not None


@pytest.mark.parametrize("entity_id,axis", [("wall-1", "AXIS2"), ("slab-1", "AXIS3")])
def test_layer_usage_survives_reopen(tmp_path, entity_id, axis):
    value = document()
    item = record(value, entity_id)
    rep = item["attributes"]["Representation"]
    thickness = rep["profile"]["y"] if axis == "AXIS2" else rep["depth"]
    item["materials"] = [layer_usage(thickness, axis)]
    result = compile_document(value, tmp_path / "layers.ifc")
    assert result.success, result
    material = util.get_material(by_id(ifcopenshell.open(str(result.output_path)), entity_id))
    assert material.is_a("IfcMaterialLayerSetUsage")
    assert material.LayerSetDirection == axis
    assert material.ForLayerSet.MaterialLayers[0].LayerThickness == thickness


def with_type(value):
    value["entities"].append({"id": "beam-type", "ifc_class": "IfcBeamType", "attributes": {"Name": "Shared beam", "PredefinedType": "BEAM"}, "property_sets": {"Pset_BeamCommon": {"FireRating": "60"}}, "materials": [{"kind": "single_material", "name": "Steel"}], "provenance": {"source": "user"}})
    value["relationships"].append({"id": "beam-typing", "ifc_class": "IfcRelDefinesByType", "attributes": {"RelatingType": "beam-type", "RelatedObjects": ["beam-1"]}, "provenance": {"source": "user"}})
    return value


def test_type_inheritance_and_direct_override_preserve_definition(tmp_path):
    value = with_type(document())
    original = copy.deepcopy(value)
    result = compile_document(value, tmp_path / "inherited.ifc")
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    beam = by_id(model, "beam-1")
    assert util.get_material(beam).Name == "Steel"
    assert util.get_psets(beam)["Pset_BeamCommon"]["FireRating"] == "60"
    record(value, "beam-1")["materials"] = [{"kind": "single_material", "name": "Timber"}]
    record(value, "beam-1")["property_sets"]["Pset_BeamCommon"] = {"FireRating": "90"}
    result = compile_document(value, tmp_path / "override.ifc")
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert util.get_material(by_id(model, "beam-1")).Name == "Timber"
    assert util.get_material(by_id(model, "beam-type")).Name == "Steel"
    assert util.get_psets(by_id(model, "beam-type"))["Pset_BeamCommon"]["FireRating"] == "60"
    assert original["entities"][-1] == value["entities"][-1]


def test_identical_material_names_do_not_merge_groups(tmp_path):
    value = document()
    for entity_id in ("beam-1", "column-1"):
        record(value, entity_id)["materials"] = [{"kind": "single_material", "name": "same label"}]
    result = compile_document(value, tmp_path / "groups.ifc")
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert util.get_material(by_id(model, "beam-1")).id() != util.get_material(by_id(model, "column-1")).id()


def test_independent_reopen_checker_rejects_wrong_and_missing_values(tmp_path):
    from text2ifc_compiler.semantic_verification import verify_document_semantics
    value = with_type(document())
    result = compile_document(value, tmp_path / "source.ifc")
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert verify_document_semantics(model, value) == ()
    util.get_material(by_id(model, "beam-type")).Name = "Wrong"
    assert any(i.code == "IFC_SEMANTIC_MISMATCH" for i in verify_document_semantics(model, value))
    model.remove(util.get_type(by_id(model, "beam-1")).ObjectTypeOf[0])
    assert any(i.attribute == "type" for i in verify_document_semantics(model, value))


def test_frozen_request_expectations_block_publication(tmp_path):
    out = tmp_path / "sentinel.ifc"
    out.write_bytes(b"unchanged")
    result = compile_document(document(), out, semantic_expectations=[{"entity_id": "beam-1", "kind": "material", "scope": "effective", "value": {"kind": "single_material", "name": "Steel"}}])
    assert not result.success
    assert out.read_bytes() == b"unchanged"


def test_standard_case_inherits_explicit_type_material_in_legal_usage(tmp_path):
    value = document()
    record(value, "wall-1")["ifc_class"] = "IfcWallStandardCase"
    value["entities"].append({"id": "wall-type", "ifc_class": "IfcWallType", "attributes": {"Name": "Explicit type", "PredefinedType": "STANDARD"}, "property_sets": {}, "materials": [{"kind": "single_material", "name": "Brick"}], "provenance": {"source": "user"}})
    value["relationships"].append({"id": "wall-typing", "ifc_class": "IfcRelDefinesByType", "attributes": {"RelatingType": "wall-type", "RelatedObjects": ["wall-1"]}, "provenance": {"source": "user"}})
    result = compile_document(value, tmp_path / "standard.ifc", semantic_expectations=[{"entity_id": "wall-1", "kind": "material", "value": {"kind": "single_material", "name": "Brick"}}])
    assert result.success, result


def test_absent_performance_rejects_present_null(tmp_path):
    from ifcopenshell.api.pset.add_pset import add_pset
    from text2ifc_compiler.semantic_verification import verify_semantic_expectations
    result = compile_document(document(), tmp_path / "null.ifc")
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    pset = add_pset(model, product=by_id(model, "beam-1"), name="Pset_BeamCommon")
    pset.HasProperties = (model.create_entity("IfcPropertySingleValue", Name="FireRating", NominalValue=None),)
    assert verify_semantic_expectations(model, [{"entity_id": "beam-1", "kind": "property", "pset": "Pset_BeamCommon", "property": "FireRating", "absent": True}])


def test_type_layer_set_remains_type_scoped_after_reopen(tmp_path):
    value = document()
    thickness = record(value, "wall-1")["attributes"]["Representation"]["profile"]["y"]
    assignment = {"kind": "material_layer_set", "layer_set_name": "Layer type", "layers": [{"name": "Brick", "thickness": thickness}]}
    value["entities"].append({"id": "wall-type", "ifc_class": "IfcWallType", "attributes": {"Name": "Type layers", "PredefinedType": "STANDARD"}, "property_sets": {}, "materials": [assignment], "provenance": {"source": "user"}})
    value["relationships"].append({"id": "wall-typing", "ifc_class": "IfcRelDefinesByType", "attributes": {"RelatingType": "wall-type", "RelatedObjects": ["wall-1"]}, "provenance": {"source": "user"}})
    result = compile_document(value, tmp_path / "type-layer.ifc", semantic_expectations=[{"entity_id": "wall-1", "kind": "material", "scope": "inherited", "value": assignment}])
    assert result.success, result
    model = ifcopenshell.open(str(result.output_path))
    assert util.get_material(by_id(model, "wall-1"), should_inherit=False) is None
    assert util.get_material(by_id(model, "wall-type")).is_a("IfcMaterialLayerSet")
