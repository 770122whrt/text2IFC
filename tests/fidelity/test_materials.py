from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc
from text2ifc_extractor import extract_ifc2x3


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _by_bim_id(model, bim_json_id: str):
    for entity in model.by_type("IfcProduct"):
        psets = ifcopenshell.util.element.get_psets(entity)
        if psets.get("Pset_text2IFCIdentity", {}).get("BimJsonId") == bim_json_id:
            return entity
    raise KeyError(bim_json_id)


def _add_explicit_wall_material(value: dict) -> dict:
    wall = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall["ifc_class"] = "IfcWallStandardCase"
    wall["materials"] = [
        {
            "kind": "material_layer_set_usage",
            "layer_set_name": "Exterior wall layers",
            "direction": "AXIS2",
            "direction_sense": "POSITIVE",
            "offset_from_reference_line": 0,
            "layers": [
                {"name": "Gypsum board", "thickness": 12.5},
                {"name": "Concrete", "thickness": 175.0},
            ],
        }
    ]
    return wall["materials"][0]


def test_v2_compiles_explicit_wall_material_layer_set_usage(
    tmp_path: Path,
) -> None:
    value = document()
    _add_explicit_wall_material(value)
    output = tmp_path / "explicit-wall-material.ifc"

    result = compile_document(value, output)

    assert result.success
    model = open_ifc(output)
    compiled_wall = _by_bim_id(model, "wall-1")
    associations = [
        relation.RelatingMaterial
        for relation in compiled_wall.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    assert len(associations) == 1
    usage = associations[0]
    assert usage.is_a("IfcMaterialLayerSetUsage")
    assert usage.LayerSetDirection == "AXIS2"
    assert usage.DirectionSense == "POSITIVE"
    assert usage.OffsetFromReferenceLine == 0
    layer_set = usage.ForLayerSet
    assert layer_set.LayerSetName == "Exterior wall layers"
    layers = list(layer_set.MaterialLayers)
    assert [layer.Material.Name for layer in layers] == ["Gypsum board", "Concrete"]
    assert [layer.LayerThickness for layer in layers] == [12.5, 175.0]


def test_extractor_preserves_supported_wall_material_layers(
    tmp_path: Path,
) -> None:
    value = document()
    expected = _add_explicit_wall_material(value)
    source_ifc = tmp_path / "source-material.ifc"
    assert compile_document(value, source_ifc).success

    extraction = extract_ifc2x3(source_ifc)
    extracted = extraction.document or extraction.draft["partial_document"]
    wall = next(
        entity
        for entity in extracted["entities"]
        if entity["ifc_class"] == "IfcWallStandardCase"
        and entity["attributes"].get("Name") == "Wall"
    )

    assert wall["materials"] == [expected]
    assert all(loss["kind"] != "MATERIAL_ASSOCIATION" for loss in extraction.losses)
