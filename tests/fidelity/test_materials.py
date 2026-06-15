from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc


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


def test_v2_compiles_explicit_wall_material_layer_set_usage(
    tmp_path: Path,
) -> None:
    value = document()
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
