from __future__ import annotations

import copy
import json
from pathlib import Path

import ifcopenshell.util.element

from text2ifc_compiler import compile_document, open_ifc, verify_ifc


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _bim_id(entity) -> str:
    return ifcopenshell.util.element.get_psets(entity)[
        "Pset_text2IFCIdentity"
    ]["BimJsonId"]


def test_v2_compiles_exact_profile_classes_without_proxy(tmp_path: Path) -> None:
    value = document()
    original = copy.deepcopy(value)
    output = tmp_path / "complete-v2.ifc"

    result = compile_document(value, output)

    assert result.success
    assert value == original
    model = open_ifc(output)
    assert model.schema == "IFC2X3"
    assert verify_ifc(model) == ()
    assert len(model.by_type("IfcBuildingElementProxy")) == 0
    expected = {
        item["ifc_class"]
        for item in value["entities"]
        if item["ifc_class"] != "IfcProject"
    }
    assert {
        item.is_a()
        for item in model.by_type("IfcProduct")
        if _bim_id(item) in {record["id"] for record in value["entities"]}
    } == expected


def test_v2_preserves_exact_wall_standard_case(tmp_path: Path) -> None:
    value = document()
    wall = next(item for item in value["entities"] if item["id"] == "wall-1")
    wall["ifc_class"] = "IfcWallStandardCase"
    output = tmp_path / "wall-standard-case.ifc"

    result = compile_document(value, output)

    assert result.success
    model = open_ifc(output)
    exact = [
        item
        for item in model.by_type("IfcWall")
        if item.is_a() == "IfcWallStandardCase"
    ]
    assert len(exact) == 1
    assert _bim_id(exact[0]) == "wall-1"


def test_v2_invalid_or_draft_input_preserves_destination(tmp_path: Path) -> None:
    output = tmp_path / "sentinel.ifc"
    output.write_bytes(b"sentinel")

    invalid = document()
    invalid["entities"][4]["attributes"].pop("ObjectPlacement")
    result = compile_document(invalid, output)
    assert not result.success
    assert output.read_bytes() == b"sentinel"

    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": document(),
        "missing_facts": [],
        "losses": [
            {
                "source_ref": "test#wall",
                "path": "/entities/4/attributes/Representation",
                "kind": "MAPPED_GEOMETRY",
                "message": "Unsupported source geometry.",
            }
        ],
        "clarification_targets": [],
        "provenance": {"source": "test"},
    }
    result = compile_document(draft, output)
    assert not result.success
    assert output.read_bytes() == b"sentinel"
