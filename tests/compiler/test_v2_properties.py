from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _by_bim_id(model, bim_json_id: str):
    for entity in model.by_type("IfcProduct"):
        psets = ifcopenshell.util.element.get_psets(entity)
        if psets.get("Pset_text2IFCIdentity", {}).get("BimJsonId") == bim_json_id:
            return entity
    raise KeyError(bim_json_id)


def test_v2_native_attributes_and_property_sets_round_trip(tmp_path: Path) -> None:
    value = document()
    wall = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall["attributes"]["Description"] = "Load-bearing perimeter wall"
    wall["property_sets"]["custom:text2ifc.Example"] = {
        "Code": "W-01",
        "Reviewed": True,
    }
    output = tmp_path / "properties-v2.ifc"

    assert compile_document(value, output).success
    model = open_ifc(output)
    wall_ifc = _by_bim_id(model, "wall-1")
    psets = ifcopenshell.util.element.get_psets(wall_ifc)

    assert wall_ifc.Description == "Load-bearing perimeter wall"
    assert psets["Pset_WallCommon"]["IsExternal"] is True
    assert psets["custom:text2ifc.Example"]["Code"] == "W-01"
    assert psets["custom:text2ifc.Example"]["Reviewed"] is True

    door = _by_bim_id(model, "door-1")
    door_json = next(item for item in value["entities"] if item["id"] == "door-1")
    assert door.OverallWidth == door_json["attributes"]["OverallWidth"]
    assert door.OverallHeight == door_json["attributes"]["OverallHeight"]
