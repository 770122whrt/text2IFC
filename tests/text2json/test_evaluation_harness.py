from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from text2ifc_text.evaluation import evaluate_prediction_cases


FIXTURE = Path("tests/contract_v2/fixtures/complete.json")


def _document() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _case(
    record_id: str,
    gold: dict[str, Any],
    prediction: dict[str, Any] | str,
    *,
    source_file_id: str = "fixture-ifc",
) -> dict[str, Any]:
    prediction_text = (
        prediction
        if isinstance(prediction, str)
        else json.dumps(prediction, sort_keys=True)
    )
    return {
        "record_id": record_id,
        "split": "validation",
        "source_file_id": source_file_id,
        "target_json": gold,
        "prediction_text": prediction_text,
    }


def _entity(document: dict[str, Any], entity_id: str) -> dict[str, Any]:
    return next(entity for entity in document["entities"] if entity["id"] == entity_id)


def _relationship(document: dict[str, Any], relation_id: str) -> dict[str, Any]:
    return next(
        relation for relation in document["relationships"] if relation["id"] == relation_id
    )


def _without_references(document: dict[str, Any], missing_id: str) -> dict[str, Any]:
    value = copy.deepcopy(document)
    value["entities"] = [
        entity for entity in value["entities"] if entity["id"] != missing_id
    ]
    value["relationships"] = [
        relation
        for relation in value["relationships"]
        if missing_id not in relation.get("attributes", {}).values()
    ]
    return value


def test_invalid_outputs_are_bucketed_before_semantic_scoring() -> None:
    gold = _document()
    schema_invalid = copy.deepcopy(gold)
    del schema_invalid["ifc_schema"]
    semantic_invalid = copy.deepcopy(gold)
    _entity(semantic_invalid, "wall-1")["ifc_class"] = "IfcBuildingElementProxy"

    result = evaluate_prediction_cases(
        [
            _case("invalid-json", gold, "{"),
            _case("schema-invalid", gold, schema_invalid),
            _case("semantic-invalid", gold, semantic_invalid),
        ]
    )

    assert result["metrics"]["record_count"] == 3
    assert result["metrics"]["validity"]["parse_success_rate"] == pytest.approx(2 / 3)
    assert result["metrics"]["validity"]["schema_valid_rate"] == pytest.approx(1 / 3)
    assert result["metrics"]["validity"]["semantic_valid_rate"] == pytest.approx(0.0)
    assert result["metrics"]["semantic"]["scored_record_count"] == 0
    assert result["records"]["invalid-json"]["stage"] == "parse"
    assert result["records"]["schema-invalid"]["stage"] == "schema"
    assert result["records"]["schema-invalid"]["validation_issues"]
    assert result["records"]["semantic-invalid"]["stage"] == "semantic"
    assert result["records"]["semantic-invalid"]["validation_issues"]
    assert [bucket["record_count"] for bucket in result["error_buckets"]] == [1, 1, 1]


def test_perfect_prediction_scores_all_metric_families() -> None:
    gold = _document()

    result = evaluate_prediction_cases([_case("perfect", gold, gold)])
    metrics = result["metrics"]

    assert metrics["validity"]["parse_success_rate"] == 1.0
    assert metrics["validity"]["schema_valid_rate"] == 1.0
    assert metrics["validity"]["semantic_valid_rate"] == 1.0
    assert metrics["semantic"]["ifc_class_accuracy"] == 1.0
    assert metrics["semantic"]["entity_count_error"] == 0
    assert metrics["semantic"]["relationship_count_error"] == 0
    assert metrics["semantic"]["property_precision"] == 1.0
    assert metrics["semantic"]["property_recall"] == 1.0
    assert metrics["semantic"]["property_f1"] == 1.0
    assert metrics["semantic"]["relationship_endpoint_accuracy"] == 1.0
    assert metrics["semantic"]["placement_origin_max_error_mm"] == 0
    assert metrics["semantic"]["geometry_exact_accuracy"] == 1.0
    assert result["records"]["perfect"]["stage"] == "ok"


def test_mismatches_change_targeted_metrics_without_invalidating_json() -> None:
    gold = _document()
    class_mismatch = copy.deepcopy(gold)
    _entity(class_mismatch, "column-1")["ifc_class"] = "IfcBeam"
    missing_entity = _without_references(gold, "plate-1")
    property_mismatch = copy.deepcopy(gold)
    _entity(property_mismatch, "wall-1")["property_sets"]["Pset_WallCommon"][
        "IsExternal"
    ] = False
    relation_mismatch = copy.deepcopy(gold)
    _relationship(relation_mismatch, "fill-1")["attributes"][
        "RelatedBuildingElement"
    ] = "window-1"
    placement_mismatch = copy.deepcopy(gold)
    _entity(placement_mismatch, "wall-1")["attributes"]["ObjectPlacement"][
        "origin"
    ][0] += 25

    result = evaluate_prediction_cases(
        [
            _case("class", gold, class_mismatch),
            _case("missing", gold, missing_entity),
            _case("property", gold, property_mismatch),
            _case("relationship", gold, relation_mismatch),
            _case("placement", gold, placement_mismatch),
        ]
    )
    metrics = result["metrics"]

    assert metrics["validity"]["semantic_valid_rate"] == 1.0
    assert metrics["semantic"]["ifc_class_accuracy"] < 1.0
    assert metrics["semantic"]["entity_count_error"] > 0
    assert metrics["semantic"]["property_precision"] < 1.0
    assert metrics["semantic"]["property_recall"] < 1.0
    assert metrics["semantic"]["property_f1"] < 1.0
    assert metrics["semantic"]["relationship_endpoint_accuracy"] < 1.0
    assert metrics["semantic"]["placement_origin_max_error_mm"] == pytest.approx(25.0)


def test_compile_and_reopen_failures_are_separate_from_json_validity() -> None:
    gold = _document()

    def compiler(_: dict[str, Any], __: Path) -> Any:
        return {
            "compile_success": False,
            "reopen_success": False,
            "issues": [{"code": "IFC_REOPEN_ERROR", "message": "fixture failure"}],
        }

    result = evaluate_prediction_cases(
        [_case("compile-failure", gold, gold)],
        compiler=compiler,
    )

    assert result["metrics"]["validity"]["semantic_valid_rate"] == 1.0
    assert result["metrics"]["compiler"]["compile_success_rate"] == 0.0
    assert result["metrics"]["compiler"]["reopen_success_rate"] == 0.0
    assert result["records"]["compile-failure"]["stage"] == "compile"
    assert result["records"]["compile-failure"]["compiler_issues"][0]["code"] == (
        "IFC_REOPEN_ERROR"
    )
