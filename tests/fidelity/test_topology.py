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


def _add_connected_wall_pair(value: dict) -> None:
    wall_1 = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall_2 = copy.deepcopy(wall_1)
    wall_2["id"] = "wall-2"
    wall_2["attributes"]["Name"] = "Connected wall"
    wall_2["attributes"]["ObjectPlacement"]["origin"] = [5100, 200, 0]
    value["entities"].append(wall_2)
    value["relationships"].append(
        {
            "id": "connect-wall-1",
            "ifc_class": "IfcRelConnectsPathElements",
            "attributes": {
                "RelatingElement": "wall-1",
                "RelatedElement": "wall-2",
                "RelatingPriorities": [],
                "RelatedPriorities": [],
                "RelatingConnectionType": "ATEND",
                "RelatedConnectionType": "ATSTART",
            },
            "provenance": {"source": "test"},
        }
    )


def test_v2_compiles_path_element_topology_relationship(
    tmp_path: Path,
) -> None:
    value = document()
    _add_connected_wall_pair(value)
    output = tmp_path / "connected-walls.ifc"

    result = compile_document(value, output)

    assert result.success
    model = open_ifc(output)
    relations = model.by_type("IfcRelConnectsPathElements")
    assert len(relations) == 1
    relation = relations[0]
    assert _bim_id(relation.RelatingElement) == "wall-1"
    assert _bim_id(relation.RelatedElement) == "wall-2"
    assert relation.RelatingConnectionType == "ATEND"
    assert relation.RelatedConnectionType == "ATSTART"
