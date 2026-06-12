from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def entity(value, entity_id):
    return next(item for item in value["entities"] if item["id"] == entity_id)


def pairs(value):
    return {(item.code, item.path) for item in validate_v2_document(value)}


def test_complete_fixture_covers_initial_profile_and_space_geometry() -> None:
    value = document()
    expected = {
        "IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey",
        "IfcWall", "IfcColumn", "IfcBeam", "IfcSlab", "IfcDoor",
        "IfcWindow", "IfcStair", "IfcStairFlight", "IfcRoof", "IfcSpace",
        "IfcOpeningElement", "IfcPlate", "IfcCovering", "IfcCurtainWall",
        "IfcMember", "IfcRailing",
    }

    assert {item["ifc_class"] for item in value["entities"]} == expected
    assert validate_v2_document(value) == []
    space = entity(value, "space-1")
    assert space["attributes"]["ObjectPlacement"]["relative_to"] == "storey-1"
    assert space["attributes"]["Representation"]["profile"]["kind"] == "polygon"


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda rep: rep.__setitem__("depth", 0), "INVALID_EXTRUSION_DEPTH"),
        (
            lambda rep: rep["profile"].__setitem__("points", [[0, 0], [1, 0], [1, 1]]),
            "OPEN_POLYGON_PROFILE",
        ),
        (
            lambda rep: rep["profile"].__setitem__(
                "points", [[float(index), 0] for index in range(258)]
            ),
            "PROFILE_POINT_LIMIT_EXCEEDED",
        ),
        (
            lambda rep: rep["profile"]["points"][1].__setitem__(0, 100000001),
            "COORDINATE_LIMIT_EXCEEDED",
        ),
    ],
)
def test_polygon_extrusion_is_positive_closed_and_bounded(mutation, code) -> None:
    value = document()
    representation = entity(value, "slab-1")["attributes"]["Representation"]
    mutation(representation)

    assert any(found == code for found, _ in pairs(value))


@pytest.mark.parametrize("kind", ["brep", "mapped", "surface", "boolean", "tessellated"])
def test_formal_rejects_raw_or_unsupported_geometry_kinds(kind) -> None:
    value = document()
    entity(value, "wall-1")["attributes"]["Representation"] = {
        "kind": kind,
        "raw": {},
    }

    assert (
        "UNSUPPORTED_GEOMETRY_KIND",
        "/entities/4/attributes/Representation/kind",
    ) in pairs(value)


def test_formal_semantic_product_requires_representation() -> None:
    value = document()
    entity(value, "wall-1")["attributes"].pop("Representation")

    assert (
        "MISSING_REPRESENTATION",
        "/entities/4/attributes/Representation",
    ) in pairs(value)


def test_representation_local_position_is_independent_and_validated() -> None:
    value = document()
    representation = entity(value, "wall-1")["attributes"]["Representation"]
    representation["position"] = {
        "origin": [125.0, 250.0, 0.0],
        "axis": [0.0, 0.0, 2.0],
        "ref_direction": [3.0, 0.0, 0.0],
    }
    assert validate_v2_document(value) == []

    representation["position"]["axis"] = [0.0, 0.0, 0.0]
    assert (
        "ZERO_REPRESENTATION_VECTOR",
        "/entities/4/attributes/Representation/position/axis",
    ) in pairs(value)


def test_unsupported_source_geometry_is_valid_only_as_explicit_draft_loss() -> None:
    partial = document()
    entity(partial, "wall-1")["attributes"].pop("Representation")
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": partial,
        "missing_facts": [],
        "losses": [
            {
                "source_ref": "source.ifc#wall-1",
                "path": "/entities/4/attributes/Representation",
                "kind": "UNSUPPORTED_BREP",
                "message": "Source BRep is not in the formal geometry profile."
            }
        ],
        "clarification_targets": [],
        "provenance": {"source": "test"}
    }

    assert validate_draft(draft) == []
