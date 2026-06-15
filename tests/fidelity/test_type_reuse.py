from __future__ import annotations

import copy
import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _bim_id(entity) -> str:
    return ifcopenshell.util.element.get_psets(entity)[
        "Pset_text2IFCIdentity"
    ]["BimJsonId"]


def _add_wall_type_reuse(value: dict) -> None:
    wall_1 = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall_2 = copy.deepcopy(wall_1)
    wall_2["id"] = "wall-2"
    wall_2["attributes"]["Name"] = "Wall 2"
    wall_2["attributes"]["ObjectPlacement"]["origin"] = [100, 800, 0]
    value["entities"].append(wall_2)
    value["entities"].append(
        {
            "id": "wall-type-1",
            "ifc_class": "IfcWallType",
            "attributes": {
                "Name": "Interior partition type",
                "PredefinedType": "STANDARD",
            },
            "property_sets": {},
            "provenance": {"source": "test"},
        }
    )
    value["relationships"].append(
        {
            "id": "type-wall-1",
            "ifc_class": "IfcRelDefinesByType",
            "attributes": {
                "RelatedObjects": ["wall-1", "wall-2"],
                "RelatingType": "wall-type-1",
            },
            "provenance": {"source": "test"},
        }
    )


def test_v2_compiles_wall_type_reuse_relationship(tmp_path: Path) -> None:
    value = document()
    _add_wall_type_reuse(value)
    output = tmp_path / "wall-type-reuse.ifc"

    result = compile_document(value, output)

    assert result.success
    model = open_ifc(output)
    type_relations = [
        relation
        for relation in model.by_type("IfcRelDefinesByType")
        if relation.RelatingType.is_a("IfcWallType")
    ]
    assert len(type_relations) == 1
    relation = type_relations[0]
    assert relation.RelatingType.Name == "Interior partition type"
    assert {_bim_id(item) for item in relation.RelatedObjects} == {
        "wall-1",
        "wall-2",
    }
