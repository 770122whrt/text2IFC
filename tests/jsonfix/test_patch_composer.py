from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
BASE_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.composer")
    except ModuleNotFoundError as exc:
        pytest.fail(f"patch composer is not implemented: {exc}")
    return module.compose_patches


@pytest.fixture
def base_document() -> dict:
    document = json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))
    document["provenance"]["document_id"] = "composer-base"
    return document


def _patch(*operations: dict, target_document_id: str = "composer-base") -> dict:
    return {
        "patch_version": "bim-json-patch/1.0",
        "target_schema_version": "bim-json/2.0",
        "target_ifc_schema": "IFC2X3",
        "target_document_id": target_document_id,
        "layers": [
            {
                "id": "user-layer-1",
                "kind": "user",
                "provenance": {
                    "source": "test-user",
                    "request_id": "repair-1",
                },
                "operations": list(operations),
            }
        ],
    }


def _wall(wall_id: str = "wall-west") -> dict:
    return {
        "id": wall_id,
        "ifc_class": "IfcWallStandardCase",
        "attributes": {
            "Name": "West wall",
            "ObjectPlacement": {
                "relative_to": "storey-1",
                "origin": [0, 3000, 0],
                "axis": [0, 0, 1],
                "ref_direction": [0, 1, 0],
            },
            "Representation": {
                "kind": "extruded_profile",
                "profile": {"kind": "rectangle", "x": 4000, "y": 200},
                "depth": 2800,
                "direction": [0, 0, 1],
            },
        },
        "property_sets": {},
        "provenance": {
            "source": "user-patch",
            "layer_id": "user-layer-1",
        },
    }


def _codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_add_entity_produces_formal_candidate_without_mutating_base(
    base_document: dict,
) -> None:
    compose_patches = _api()
    before = copy.deepcopy(base_document)
    operation = {
        "op": "add_entity",
        "target": {"collection": "entities", "id": "wall-west"},
        "value": _wall(),
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert result.valid
    assert result.formal_valid
    assert base_document == before
    assert result.document is not base_document
    assert [item["id"] for item in result.document["entities"]][-1] == "wall-west"
    assert validate_v2_document(result.document) == []


def test_set_property_adds_missing_property_and_preserves_existing_facts(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "set_property",
        "target": {
            "collection": "entities",
            "id": "wall-1",
            "property_set": "Pset_WallCommon",
            "property": "FireRating",
        },
        "value": "R30",
    }

    result = compose_patches(base_document, [_patch(operation)])

    wall = next(
        item for item in result.document["entities"] if item["id"] == "wall-1"
    )
    assert result.valid
    assert wall["property_sets"]["Pset_WallCommon"] == {
        "IsExternal": True,
        "FireRating": "R30",
    }


def test_add_relationship_requires_resolved_semantic_endpoints(
    base_document: dict,
) -> None:
    compose_patches = _api()
    relationship = {
        "id": "connect-wall-column",
        "ifc_class": "IfcRelConnectsPathElements",
        "attributes": {
            "RelatingElement": "wall-1",
            "RelatedElement": "column-1",
            "RelatingPriorities": [],
            "RelatedPriorities": [],
            "RelatingConnectionType": "ATEND",
            "RelatedConnectionType": "ATSTART",
        },
        "provenance": {
            "source": "agent-patch",
            "layer_id": "user-layer-1",
        },
    }
    operation = {
        "op": "add_relationship",
        "target": {
            "collection": "relationships",
            "id": "connect-wall-column",
        },
        "value": relationship,
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert result.valid
    assert result.document["relationships"][-1] == relationship
    assert validate_v2_document(result.document) == []


def test_missing_target_rejects_patch_without_partial_application(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "set_property",
        "target": {
            "collection": "entities",
            "id": "wall-missing",
            "property_set": "Pset_WallCommon",
            "property": "FireRating",
        },
        "value": "R60",
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert not result.valid
    assert result.document == base_document
    assert _codes(result) == {"TARGET_NOT_FOUND"}


def test_duplicate_entity_id_is_rejected_as_ambiguous(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "add_entity",
        "target": {"collection": "entities", "id": "wall-1"},
        "value": _wall("wall-1"),
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert not result.valid
    assert result.document == base_document
    assert _codes(result) == {"DUPLICATE_TARGET_ID"}


def test_source_fact_conflict_requires_explicit_overwrite(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "set_property",
        "target": {
            "collection": "entities",
            "id": "wall-1",
            "property_set": "Pset_WallCommon",
            "property": "IsExternal",
        },
        "value": False,
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert not result.valid
    assert result.document == base_document
    assert _codes(result) == {"SOURCE_FACT_CONFLICT"}


def test_explicit_overwrite_is_applied_and_remains_auditable(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "set_property",
        "target": {
            "collection": "entities",
            "id": "wall-1",
            "property_set": "Pset_WallCommon",
            "property": "IsExternal",
        },
        "value": False,
        "overwrite": True,
    }

    result = compose_patches(base_document, [_patch(operation)])

    wall = next(
        item for item in result.document["entities"] if item["id"] == "wall-1"
    )
    assert result.valid
    assert wall["property_sets"]["Pset_WallCommon"]["IsExternal"] is False
    assert "SOURCE_FACT_OVERWRITTEN" in _codes(result)


def test_invalid_composed_candidate_fails_formal_gate(
    base_document: dict,
) -> None:
    compose_patches = _api()
    invalid_wall = _wall()
    invalid_wall["attributes"].pop("Representation")
    operation = {
        "op": "add_entity",
        "target": {"collection": "entities", "id": "wall-west"},
        "value": invalid_wall,
    }

    result = compose_patches(base_document, [_patch(operation)])

    assert not result.valid
    assert not result.formal_valid
    assert "COMPOSED_DOCUMENT_INVALID" in _codes(result)
    assert validate_v2_document(result.document)


def test_patch_target_document_id_must_match_base_identity(
    base_document: dict,
) -> None:
    compose_patches = _api()
    operation = {
        "op": "add_entity",
        "target": {"collection": "entities", "id": "wall-west"},
        "value": _wall(),
    }

    result = compose_patches(
        base_document,
        [_patch(operation, target_document_id="another-document")],
    )

    assert not result.valid
    assert result.document == base_document
    assert _codes(result) == {"TARGET_DOCUMENT_MISMATCH"}
