"""Frozen S0 family: new filling contract, geometry and independent IFC readback.

These deterministic examples are regression evidence, not Provider capability
evidence. They exercise all four templates, units, placement and parameter bounds.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np
import pytest

TEMPLATES = ("window-single", "window-double-vertical", "door-left", "door-right")


def representation(template="window-single", **updates):
    result = {
        "kind": "basic_filling", "template_id": template,
        "template_version": "text2ifc/basic-filling/1.0",
        "width": 1200.0, "height": 1500.0, "depth": 200.0,
        "parameters": {},
    }
    if template.startswith("door"):
        result.update(width=900.0, height=2100.0)
    result.update(updates)
    return result


def ifc_class(template):
    return "IfcDoor" if template.startswith("door") else "IfcWindow"


def model_for(rep, *, millimetres=True):
    from ifcopenshell.api.context import add_context
    from ifcopenshell.api.unit import assign_unit
    from text2ifc_compiler.bootstrap import _create_owner_metadata
    from ifcopenshell.api.root import create_entity

    model = ifcopenshell.file(schema="IFC2X3")
    _create_owner_metadata(model)
    create_entity(model, ifc_class="IfcProject", name="Geometry regression")
    unit = model.createIfcSIUnit(None, "LENGTHUNIT", "MILLI" if millimetres else None, "METRE")
    assign_unit(model, units=[unit])
    context = add_context(model, context_type="Model")
    body = add_context(model, context_type="Model", context_identifier="Body",
                       target_view="MODEL_VIEW", parent=context)
    product = create_entity(model, ifc_class=ifc_class(rep["template_id"]), name="Filling")
    return model, product, body


def vertices(entity, *, world=False):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, world)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = getattr(shape, "geometry", shape)
    return np.array(geometry.verts).reshape((-1, 3))


def roles(product):
    return {
        aspect.Name: [item for rep in aspect.ShapeRepresentations for item in rep.Items]
        for aspect in product.Representation.HasShapeAspects
    }


def public_document(template="door-left"):
    fixture = Path(__file__).resolve().parents[1] / "contract_v2" / "fixtures" / "complete.json"
    value = json.loads(fixture.read_text(encoding="utf-8"))
    value["schema_version"] = "bim-json/2.1"
    door = next(record for record in value["entities"] if record["id"] == "door-1")
    door["attributes"]["Representation"] = representation(template)
    return value


@pytest.mark.parametrize("template", TEMPLATES)
def test_frozen_parameter_defaults_sources_and_no_semantic_invention(template):
    from text2ifc_contract.basic_filling import resolve_basic_filling

    source = representation(template)
    before = copy.deepcopy(source)
    result = resolve_basic_filling(source, ifc_class(template))
    assert source == before
    assert result["parameters"]["frame_width"] == 50
    assert result["parameters"]["frame_depth"] == 60
    assert result["parameters"]["panel_thickness"] == (40 if template.startswith("door") else 6)
    assert set(result["parameter_sources"].values()) == {"text2ifc/basic-filling/1.0:" + template}
    assert "materials" not in result and "property_sets" not in result


@pytest.mark.parametrize("updates", [
    {"template_version": "text2ifc/basic-filling/9.0"},
    {"template_id": "window-sliding"}, {"width": 100}, {"depth": 59},
    {"parameters": {"frame_width": 9}}, {"parameters": {"frame_depth": 201}},
    {"parameters": {"panel_thickness": 31}}, {"parameters": {"casing_depth": 20}},
    {"parameters": {"split_ratio": 0.5}}, {"width": float("nan")},
])
def test_invalid_or_inapplicable_parameters_fail_closed(updates):
    from text2ifc_contract.basic_filling import validate_basic_filling

    assert validate_basic_filling(representation(**updates), "IfcWindow", "/Representation")


def test_double_window_bounds_and_user_sources_are_not_clamped():
    from text2ifc_contract.basic_filling import resolve_basic_filling, validate_basic_filling

    value = representation("window-double-vertical", parameters={"split_ratio": 0.2, "frame_width": 10})
    resolved = resolve_basic_filling(value, "IfcWindow")
    assert resolved["parameters"]["split_ratio"] == 0.2
    assert resolved["parameter_sources"]["split_ratio"] == "user"
    assert resolved["parameter_sources"]["frame_width"] == "user"
    value["parameters"]["split_ratio"] = 0.199
    assert validate_basic_filling(value, "IfcWindow", "/Representation")
    assert validate_basic_filling(representation("door-left"), "IfcWindow", "/Representation")


@pytest.mark.parametrize("template", TEMPLATES)
@pytest.mark.parametrize("millimetres", [True, False])
def test_reopened_mesh_parts_dimensions_depth_and_clean_apertures(template, millimetres):
    from text2ifc_compiler.basic_filling import add_basic_filling_geometry

    rep = representation(template)
    model, product, body = model_for(rep, millimetres=millimetres)
    add_basic_filling_geometry(model, product, rep, body)
    reopened = ifcopenshell.file.from_string(model.to_string())
    product = reopened.by_guid(product.GlobalId)
    mesh = vertices(product)
    assert mesh.min(axis=0) == pytest.approx([-rep["width"] / 2000, -0.03, 0])
    assert mesh.max(axis=0) == pytest.approx([rep["width"] / 2000, 0.03, rep["height"] / 1000])
    assert product.OverallWidth == pytest.approx(rep["width"] * (1 if millimetres else .001))
    component_roles = roles(product)
    is_door = template.startswith("door")
    assert set(component_roles) == ({"Lining", "Panel"} if is_door else {"Framing", "Glazing"})
    panel_items = component_roles["Panel" if is_door else "Glazing"]
    assert len(panel_items) == (2 if template == "window-double-vertical" else 1)
    # Independent readback of each solid proves glass/leaf thickness and aperture
    # contents. No overall bounding-box substitute for panel/clear-opening checks.
    for item in panel_items:
        verts = vertices(item)
        extent = np.ptp(verts, axis=0)
        assert extent[1] == pytest.approx(.04 if is_door else .006)
        assert extent[2] == pytest.approx((rep["height"] - (50 if is_door else 100)) / 1000)
        assert verts[:, 0].min() >= -rep["width"] / 2000 + .05 - 1e-8
        assert verts[:, 0].max() <= rep["width"] / 2000 - .05 + 1e-8
    # No glazing material or performance claim can be manufactured by geometry.
    assert not reopened.by_type("IfcMaterial")
    assert not any("FireRating" in values for values in ifcopenshell.util.element.get_psets(product).values())


@pytest.mark.parametrize("angle", [0, 37, 90, 180])
def test_rotation_and_user_placement_unchanged(angle):
    from ifcopenshell.api.geometry import edit_object_placement
    from text2ifc_compiler.basic_filling import add_basic_filling_geometry

    rep = representation("door-right", depth=300, parameters={"frame_depth": 100})
    model, product, body = model_for(rep)
    theta = np.deg2rad(angle)
    matrix = np.eye(4)
    matrix[:2, :2] = [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
    matrix[:3, 3] = [2.5, 3.2, .15]
    edit_object_placement(model, product=product, matrix=matrix, is_si=True)
    placement = product.ObjectPlacement.to_string()
    add_basic_filling_geometry(model, product, rep, body)
    assert product.ObjectPlacement.to_string() == placement
    reopened = ifcopenshell.file.from_string(model.to_string())
    product = reopened.by_guid(product.GlobalId)
    local = (vertices(product, world=True) - matrix[:3, 3]) @ matrix[:3, :3]
    assert local.min(axis=0) == pytest.approx([-.45, -.05, 0], abs=1e-8)
    assert local.max(axis=0) == pytest.approx([.45, .05, 2.1], abs=1e-8)


def test_public_compile_new_contract_preserves_opening_and_encodes_handedness(tmp_path):
    from text2ifc_compiler import compile_document, open_ifc

    value = public_document()
    output = tmp_path / "basic-left.ifc"
    result = compile_document(value, output)
    assert result.success, (result.input_issues, result.ifc_issues)
    model = open_ifc(output)
    product = model.by_type("IfcDoor")[0]
    assert ifcopenshell.util.element.get_type(product).OperationType == "SINGLE_SWING_LEFT"
    opening = product.FillsVoids[0].RelatingOpeningElement
    assert np.ptp(vertices(opening), axis=0) == pytest.approx([.9, .2, 2.1])
    assert ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement) == pytest.approx(
        ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement))


@pytest.mark.parametrize("mutation", ["width", "height", "opening", "host", "depth", "placement", "missing-fill", "type-conflict", "outside-host"])
def test_public_document_rejects_conflicting_dimensions_hosts_and_type(mutation):
    from text2ifc_contract.basic_filling import validate_basic_filling_document

    value = public_document()
    records = {record["id"]: record for record in value["entities"]}
    door = records["door-1"]["attributes"]
    if mutation in {"width", "height"}:
        door["OverallWidth" if mutation == "width" else "OverallHeight"] += 1
    elif mutation == "opening":
        records["opening-1"]["attributes"]["Representation"]["profile"]["x"] = 899
    elif mutation == "host":
        records["wall-1"]["attributes"]["Representation"]["profile"]["y"] = 100
    elif mutation == "depth":
        door["Representation"]["depth"] = 201
    elif mutation == "placement":
        door["ObjectPlacement"]["origin"][0] = 1
    elif mutation == "missing-fill":
        value["relationships"] = [relation for relation in value["relationships"] if relation["ifc_class"] != "IfcRelFillsElement"]
    elif mutation == "outside-host":
        records["opening-1"]["attributes"]["ObjectPlacement"]["origin"][0] = 2500
    else:
        value["entities"].append({"id": "style-conflict", "ifc_class": "IfcDoorStyle", "attributes": {"OperationType": "SINGLE_SWING_RIGHT"}})
        value["relationships"].append({"id": "type-conflict", "ifc_class": "IfcRelDefinesByType", "attributes": {"RelatingType": "style-conflict", "RelatedObjects": ["door-1"]}})
    assert validate_basic_filling_document(value)


def test_valid_document_and_old_geometry_are_unchanged():
    from text2ifc_contract.basic_filling import validate_basic_filling_document

    value = public_document()
    before = copy.deepcopy(value)
    assert validate_basic_filling_document(value) == []
    assert value == before


@pytest.mark.parametrize("tamper", ["none", "panel-depth", "frame-width", "role", "metadata", "nominal", "placement", "handedness"])
def test_independent_readback_rejects_tampered_parts_even_with_intact_provenance(tamper):
    from text2ifc_compiler.basic_filling import verify_basic_filling
    from text2ifc_compiler.bootstrap import build_ifc_v2

    value = public_document()
    model = build_ifc_v2(value).ifc_file
    product = model.by_type("IfcDoor")[0]
    if tamper == "panel-depth":
        roles(product)["Panel"][0].SweptArea.YDim += 1
    elif tamper == "frame-width":
        roles(product)["Lining"][0].SweptArea.XDim += 1
    elif tamper == "role":
        product.Representation.HasShapeAspects[0].Name = "Unknown"
    elif tamper == "metadata":
        pset = next(r.RelatingPropertyDefinition for r in product.IsDefinedBy if r.is_a("IfcRelDefinesByProperties") and r.RelatingPropertyDefinition.Name == "Pset_text2IFCBasicFilling")
        next(prop for prop in pset.HasProperties if prop.Name == "TemplateId").NominalValue = model.createIfcLabel("door-right")
    elif tamper == "nominal":
        product.OverallWidth += 1
    elif tamper == "placement":
        product.ObjectPlacement.RelativePlacement.Location.Coordinates = (1., 0., 0.)
    elif tamper == "handedness":
        ifcopenshell.util.element.get_type(product).OperationType = "SINGLE_SWING_RIGHT"
    reopened = ifcopenshell.file.from_string(model.to_string())
    issues = verify_basic_filling(reopened, value)
    assert bool(issues) == (tamper != "none")
