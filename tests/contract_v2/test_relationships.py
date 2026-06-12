from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def pairs(value):
    return {(item.code, item.path) for item in validate_v2_document(value)}


def test_void_and_fill_chain_is_explicit_and_bookkeeping_is_absent() -> None:
    value = document()

    assert validate_v2_document(value) == []
    assert [item["ifc_class"] for item in value["relationships"]] == [
        "IfcRelVoidsElement",
        "IfcRelFillsElement",
    ]
    forbidden = {
        "IfcRelAggregates",
        "IfcRelContainedInSpatialStructure",
        "IfcRelDefinesByProperties",
    }
    assert not forbidden.intersection(
        item["ifc_class"] for item in value["relationships"]
    )


@pytest.mark.parametrize(
    ("relation_index", "attribute", "replacement", "code"),
    [
        (0, "RelatedOpeningElement", "missing", "UNRESOLVED_RELATIONSHIP_ENDPOINT"),
        (0, "RelatedOpeningElement", "door-1", "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH"),
        (1, "RelatingOpeningElement", "wall-1", "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH"),
        (1, "RelatedBuildingElement", "space-1", "RELATIONSHIP_ENDPOINT_TYPE_MISMATCH"),
    ],
)
def test_relationship_endpoints_are_resolved_and_type_checked(
    relation_index, attribute, replacement, code
) -> None:
    value = document()
    value["relationships"][relation_index]["attributes"][attribute] = replacement

    assert (
        code,
        f"/relationships/{relation_index}/attributes/{attribute}",
    ) in pairs(value)


def test_duplicate_relation_id_and_unsupported_connection_are_rejected() -> None:
    value = document()
    value["relationships"][1]["id"] = "void-1"
    assert ("DUPLICATE_ID", "/relationships/1/id") in pairs(value)

    value = document()
    value["relationships"][0]["ifc_class"] = "IfcRelConnectsElements"
    assert (
        "UNSUPPORTED_RELATIONSHIP_CLASS",
        "/relationships/0/ifc_class",
    ) in pairs(value)
