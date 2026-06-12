from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _bim_id(entity) -> str:
    return ifcopenshell.util.element.get_psets(entity)[
        "Pset_text2IFCIdentity"
    ]["BimJsonId"]


def test_v2_generates_bookkeeping_and_explicit_void_fill_relations(
    tmp_path: Path,
) -> None:
    output = tmp_path / "relations-v2.ifc"
    assert compile_document(document(), output).success
    model = open_ifc(output)

    void = model.by_type("IfcRelVoidsElement")
    fill = model.by_type("IfcRelFillsElement")
    assert len(void) == 1
    assert len(fill) == 1
    assert _bim_id(void[0].RelatingBuildingElement) == "wall-1"
    assert _bim_id(void[0].RelatedOpeningElement) == "opening-1"
    assert _bim_id(fill[0].RelatingOpeningElement) == "opening-1"
    assert _bim_id(fill[0].RelatedBuildingElement) == "door-1"

    assert model.by_type("IfcRelAggregates")
    assert model.by_type("IfcRelContainedInSpatialStructure")
    assert model.by_type("IfcRelDefinesByProperties")
