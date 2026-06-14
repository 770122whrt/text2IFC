from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_text.projection import project_supported_scope_target


ROOT = Path(__file__).resolve().parents[2]
COMPLETE_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _load_complete() -> dict[str, Any]:
    return json.loads(COMPLETE_FIXTURE.read_text(encoding="utf-8"))


def _entity(document: dict[str, Any], entity_id: str) -> dict[str, Any]:
    return next(item for item in document["entities"] if item["id"] == entity_id)


def _source_record() -> dict[str, Any]:
    return {
        "id": "bimnet-ifc2x3-test",
        "local_path": "dataset/ifc/train/test.ifc",
        "scene_family": "test",
        "sha256": "a" * 64,
    }


def test_projection_removes_only_validator_rejected_facts_and_records_omissions() -> None:
    document = _load_complete()
    original = copy.deepcopy(document)

    site = _entity(document, "site-1")
    site["attributes"]["RefLatitude"] = "not-a-compound-angle"

    wall = _entity(document, "wall-1")
    wall["property_sets"]["Pset_WallCommon"]["IsExternal"] = "yes"

    standard_case_wall = copy.deepcopy(wall)
    standard_case_wall["id"] = "stdwall-1"
    standard_case_wall["ifc_class"] = "IfcWallStandardCase"
    standard_case_wall["property_sets"]["Pset_WallCommon"]["IsExternal"] = True
    standard_case_wall["attributes"]["ObjectPlacement"]["relative_to"] = "storey-1"
    standard_case_wall["attributes"]["Representation"]["profile"] = {
        "kind": "polygon",
        "points": [[0, 0], [5000, 0], [5000, 200], [0, 200], [0, 0]],
    }
    document["entities"].append(standard_case_wall)

    door = _entity(document, "door-1")
    door["attributes"].pop("Representation")

    proxy = copy.deepcopy(_entity(document, "column-1"))
    proxy["id"] = "proxy-1"
    proxy["ifc_class"] = "IfcBuildingElementProxy"
    document["entities"].append(proxy)

    pre_issues = validate_v2_document(document)
    assert {issue.code for issue in pre_issues} >= {
        "CLASS_NOT_GENERATABLE",
        "INVALID_IFC_ATTRIBUTE_TYPE",
        "INVALID_PROPERTY_TYPE",
        "MISSING_REPRESENTATION",
        "WALL_STANDARD_CASE_REQUIRES_RECTANGLE",
    }

    input_before_projection = copy.deepcopy(document)
    result = project_supported_scope_target(document, source_record=_source_record())

    assert validate_v2_document(result["target"]) == []
    assert document == input_before_projection
    assert document != original
    assert document["entities"][-1]["id"] == "proxy-1"

    projected_ids = {record["id"] for record in result["target"]["entities"]}
    assert "site-1" in projected_ids
    assert "wall-1" in projected_ids
    assert "stdwall-1" not in projected_ids
    assert "door-1" not in projected_ids
    assert "proxy-1" not in projected_ids

    site_projected = _entity(result["target"], "site-1")
    assert "RefLatitude" not in site_projected["attributes"]
    wall_projected = _entity(result["target"], "wall-1")
    assert "IsExternal" not in wall_projected["property_sets"]["Pset_WallCommon"]

    serialized = json.dumps(result["target"], sort_keys=True)
    assert "not-a-compound-angle" not in serialized
    assert "yes" not in serialized

    omission_codes = {item["issue_code"] for item in result["omissions"]}
    assert {
        "CLASS_NOT_GENERATABLE",
        "INVALID_IFC_ATTRIBUTE_TYPE",
        "INVALID_PROPERTY_TYPE",
        "MISSING_REPRESENTATION",
        "WALL_STANDARD_CASE_REQUIRES_RECTANGLE",
        "UNRESOLVED_RELATIONSHIP_ENDPOINT",
    }.issubset(omission_codes)
    for omission in result["omissions"]:
        assert omission["source_file_id"] == "bimnet-ifc2x3-test"
        assert omission["path"].startswith("/")
        assert omission["reason"]
        assert "omitted_value" in omission


def test_projection_does_not_downcast_wall_standard_case_or_invent_geometry() -> None:
    document = _load_complete()
    wall = _entity(document, "wall-1")
    wall["ifc_class"] = "IfcWallStandardCase"
    wall["attributes"]["Representation"]["profile"] = {
        "kind": "polygon",
        "points": [[0, 0], [5000, 0], [5000, 200], [0, 200], [0, 0]],
    }

    result = project_supported_scope_target(document, source_record=_source_record())

    assert validate_v2_document(result["target"]) == []
    retained_classes = {
        record["id"]: record["ifc_class"] for record in result["target"]["entities"]
    }
    assert retained_classes.get("wall-1") is None
    assert "IfcWall" not in [
        omission.get("replacement_value") for omission in result["omissions"]
    ]
    assert any(
        omission["issue_code"] == "WALL_STANDARD_CASE_REQUIRES_RECTANGLE"
        and omission["entity_id"] == "wall-1"
        for omission in result["omissions"]
    )
