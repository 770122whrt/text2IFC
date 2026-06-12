from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from text2ifc_contract.placement import world_transform_for
from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def entity(value, entity_id):
    return next(item for item in value["entities"] if item["id"] == entity_id)


def pairs(value):
    return {(item.code, item.path) for item in validate_v2_document(value)}


def test_complete_fixture_normalizes_bases_and_composes_world_transform() -> None:
    value = document()

    assert validate_v2_document(value) == []
    first = world_transform_for(value, "opening-1")
    second = world_transform_for(value, "opening-1")

    assert first == second
    assert [row[3] for row in first[:3]] == pytest.approx(
        [1600.0, 2200.0, 3000.0], abs=1.0
    )
    assert [first[0][0], first[1][0], first[2][0]] == pytest.approx(
        [1.0, 0.0, 0.0], abs=1e-9
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("axis", [0, 0, 0], "ZERO_PLACEMENT_VECTOR"),
        ("ref_direction", [0, 0, 0], "ZERO_PLACEMENT_VECTOR"),
        ("ref_direction", [1, 0, 1], "NON_ORTHOGONAL_PLACEMENT"),
    ],
)
def test_placement_rejects_zero_or_nonorthogonal_basis(field, value, code) -> None:
    value_document = document()
    entity(value_document, "wall-1")["attributes"]["ObjectPlacement"][field] = value

    assert (
        code,
        f"/entities/4/attributes/ObjectPlacement/{field}",
    ) in pairs(value_document)


def test_placement_rejects_unresolved_parent_and_cycles() -> None:
    value = document()
    entity(value, "wall-1")["attributes"]["ObjectPlacement"][
        "relative_to"
    ] = "missing"
    assert (
        "UNRESOLVED_PLACEMENT_PARENT",
        "/entities/4/attributes/ObjectPlacement/relative_to",
    ) in pairs(value)

    value = document()
    entity(value, "building-1")["attributes"]["ObjectPlacement"][
        "relative_to"
    ] = "storey-1"
    assert any(code == "PLACEMENT_CYCLE" for code, _ in pairs(value))


def test_formal_product_requires_placement_and_allowed_parent_class() -> None:
    value = document()
    entity(value, "wall-1")["attributes"].pop("ObjectPlacement")
    assert (
        "MISSING_OBJECT_PLACEMENT",
        "/entities/4/attributes/ObjectPlacement",
    ) in pairs(value)

    value = document()
    entity(value, "storey-1")["attributes"]["ObjectPlacement"][
        "relative_to"
    ] = "wall-1"
    assert (
        "INVALID_PLACEMENT_PARENT_CLASS",
        "/entities/3/attributes/ObjectPlacement/relative_to",
    ) in pairs(value)


def test_placement_rejects_excessive_chain_depth() -> None:
    value = document()
    template = entity(value, "member-1")
    parent = "storey-1"
    for index in range(66):
        clone = copy.deepcopy(template)
        clone["id"] = f"member-depth-{index}"
        clone["attributes"]["ObjectPlacement"]["relative_to"] = parent
        value["entities"].append(clone)
        parent = clone["id"]

    assert any(code == "PLACEMENT_DEPTH_EXCEEDED" for code, _ in pairs(value))
