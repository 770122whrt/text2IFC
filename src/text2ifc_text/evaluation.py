"""Provider-independent Text-to-BIM-JSON evaluation harness."""

from __future__ import annotations

import json
import math
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable

from jsonschema import Draft202012Validator

from text2ifc_compiler import compile_document
from text2ifc_contract.schema import load_schema_v2
from text2ifc_contract.validation import _normalize_error, _sort_issues
from text2ifc_contract.validation_v2 import validate_v2_document

from .splits import ROOT, atomic_write_text, render_json


ALLOWED_SPLITS = {"train", "validation", "test"}
DEFAULT_EVALUATION_FIXTURE_DIR = (
    ROOT / "dataset" / "processed" / "text2json" / "evaluation-fixtures"
)
DEFAULT_PAIRS_DIR = ROOT / "dataset" / "processed" / "text2json" / "pairs"
EVALUATION_SCHEMA_VERSION = "text2ifc/text2json-evaluation-v1"
CompilerHook = Callable[[dict[str, Any], Path], Any]


class EvaluationError(ValueError):
    """Raised when evaluation inputs are unsafe or inconsistent."""


def _issue_payload(issue: Any) -> dict[str, Any]:
    return {
        "code": issue.code,
        "path": issue.path,
        "message": issue.message,
    }


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_issues(document: Any) -> list[Any]:
    validator = Draft202012Validator(load_schema_v2())
    issues = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    return _sort_issues(issues)


def _entity_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entity["id"]: entity for entity in document.get("entities", [])}


def _relationship_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        relationship["id"]: relationship
        for relationship in document.get("relationships", [])
    }


def _property_triples(document: dict[str, Any]) -> set[tuple[str, str, str, str]]:
    triples: set[tuple[str, str, str, str]] = set()
    for entity in document.get("entities", []):
        for pset_name, properties in entity.get("property_sets", {}).items():
            for property_name, value in properties.items():
                triples.add(
                    (entity["id"], pset_name, property_name, _canonical(value))
                )
    return triples


def _relationship_endpoint_pairs(
    relationship: dict[str, Any],
) -> set[tuple[str, str, str]]:
    pairs: set[tuple[str, str, str]] = set()
    for key, value in relationship.get("attributes", {}).items():
        if isinstance(value, str):
            pairs.add((relationship["ifc_class"], key, value))
    return pairs


def _distance_mm(left: Iterable[Any], right: Iterable[Any]) -> float:
    left_values = [float(value) for value in left]
    right_values = [float(value) for value in right]
    return math.sqrt(
        sum((left_values[index] - right_values[index]) ** 2 for index in range(3))
    )


def _angle_degrees(left: Iterable[Any], right: Iterable[Any]) -> float:
    left_values = [float(value) for value in left]
    right_values = [float(value) for value in right]
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0 or right_norm == 0:
        return 180.0
    dot = sum(
        left_values[index] * right_values[index] for index in range(len(left_values))
    )
    cosine = max(-1.0, min(1.0, dot / (left_norm * right_norm)))
    return math.degrees(math.acos(cosine))


def _representation_signature(entity: dict[str, Any]) -> str | None:
    representation = entity.get("attributes", {}).get("Representation")
    if representation is None:
        return None
    return _canonical(representation)


def _score_valid_prediction(
    gold: dict[str, Any], prediction: dict[str, Any]
) -> dict[str, Any]:
    gold_entities = _entity_map(gold)
    prediction_entities = _entity_map(prediction)
    gold_relationships = _relationship_map(gold)
    prediction_relationships = _relationship_map(prediction)

    class_total = len(gold_entities)
    class_correct = sum(
        1
        for entity_id, gold_entity in gold_entities.items()
        if prediction_entities.get(entity_id, {}).get("ifc_class")
        == gold_entity["ifc_class"]
    )

    gold_properties = _property_triples(gold)
    prediction_properties = _property_triples(prediction)
    property_true_positive = len(gold_properties.intersection(prediction_properties))

    relationship_endpoint_total = 0
    relationship_endpoint_correct = 0
    for relation_id, gold_relation in gold_relationships.items():
        gold_pairs = _relationship_endpoint_pairs(gold_relation)
        prediction_relation = prediction_relationships.get(relation_id)
        prediction_pairs = (
            _relationship_endpoint_pairs(prediction_relation)
            if prediction_relation is not None
            else set()
        )
        relationship_endpoint_total += len(gold_pairs)
        relationship_endpoint_correct += len(gold_pairs.intersection(prediction_pairs))

    placement_origin_errors: list[float] = []
    placement_axis_errors: list[float] = []
    placement_ref_direction_errors: list[float] = []
    for entity_id, gold_entity in gold_entities.items():
        prediction_entity = prediction_entities.get(entity_id)
        if prediction_entity is None:
            continue
        gold_placement = gold_entity.get("attributes", {}).get("ObjectPlacement")
        prediction_placement = prediction_entity.get("attributes", {}).get(
            "ObjectPlacement"
        )
        if not gold_placement or not prediction_placement:
            continue
        placement_origin_errors.append(
            _distance_mm(gold_placement["origin"], prediction_placement["origin"])
        )
        placement_axis_errors.append(
            _angle_degrees(gold_placement["axis"], prediction_placement["axis"])
        )
        placement_ref_direction_errors.append(
            _angle_degrees(
                gold_placement["ref_direction"],
                prediction_placement["ref_direction"],
            )
        )

    geometry_total = 0
    geometry_correct = 0
    for entity_id, gold_entity in gold_entities.items():
        gold_signature = _representation_signature(gold_entity)
        if gold_signature is None:
            continue
        geometry_total += 1
        prediction_entity = prediction_entities.get(entity_id)
        prediction_signature = (
            _representation_signature(prediction_entity)
            if prediction_entity is not None
            else None
        )
        if prediction_signature == gold_signature:
            geometry_correct += 1

    return {
        "class_correct": class_correct,
        "class_total": class_total,
        "entity_count_error": abs(len(prediction_entities) - len(gold_entities)),
        "relationship_count_error": abs(
            len(prediction_relationships) - len(gold_relationships)
        ),
        "property_true_positive": property_true_positive,
        "property_predicted": len(prediction_properties),
        "property_gold": len(gold_properties),
        "relationship_endpoint_correct": relationship_endpoint_correct,
        "relationship_endpoint_total": relationship_endpoint_total,
        "placement_origin_max_error_mm": max(placement_origin_errors, default=0.0),
        "placement_axis_max_error_degrees": max(placement_axis_errors, default=0.0),
        "placement_ref_direction_max_error_degrees": max(
            placement_ref_direction_errors, default=0.0
        ),
        "geometry_correct": geometry_correct,
        "geometry_total": geometry_total,
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _compiler_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return {
            "compile_success": bool(result.get("compile_success")),
            "reopen_success": bool(result.get("reopen_success")),
            "issues": result.get("issues", []),
        }
    success = bool(getattr(result, "success", False))
    issues: list[dict[str, Any]] = []
    for issue in getattr(result, "input_issues", ()):
        issues.append(_issue_payload(issue))
    for issue in getattr(result, "ifc_issues", ()):
        issues.append(
            {
                "code": issue.code,
                "path": f"{issue.entity}/{issue.attribute}",
                "message": issue.message,
            }
        )
    return {
        "compile_success": success,
        "reopen_success": success,
        "issues": issues,
    }


def _default_compiler(document: dict[str, Any], output_path: Path) -> Any:
    return compile_document(document, output_path)


def _prediction_text(case: dict[str, Any]) -> str:
    if "prediction_text" in case:
        return str(case["prediction_text"])
    if "prediction_json" in case:
        return _canonical(case["prediction_json"])
    if "prediction_path" in case:
        return Path(case["prediction_path"]).read_text(encoding="utf-8")
    raise EvaluationError(f"{case.get('record_id', '<unknown>')} has no prediction")


def _target_json(case: dict[str, Any]) -> dict[str, Any]:
    if "target_json" in case:
        target = case["target_json"]
    elif "target_json_path" in case:
        target = _load_json(ROOT / case["target_json_path"])
    else:
        raise EvaluationError(f"{case.get('record_id', '<unknown>')} has no target")
    if not isinstance(target, dict):
        raise EvaluationError(
            f"{case.get('record_id', '<unknown>')} target is not an object"
        )
    return target


def evaluate_prediction_cases(
    cases: list[dict[str, Any]],
    *,
    compiler: CompilerHook | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    parse_success = 0
    schema_valid = 0
    semantic_valid = 0
    scored_records = 0
    semantic_totals = Counter()
    origin_max = 0.0
    axis_max = 0.0
    ref_direction_max = 0.0
    compile_checked = 0
    compile_success = 0
    reopen_success = 0
    bucket_counter: Counter[tuple[str, str, str, str]] = Counter()
    compiler_root = output_dir or Path(tempfile.mkdtemp(prefix="text2ifc-eval-"))

    for case in cases:
        record_id = case["record_id"]
        split = case.get("split")
        if split not in ALLOWED_SPLITS:
            raise EvaluationError(f"{record_id} has unsupported split: {split!r}")
        source_file_id = case.get("source_file_id", "")
        record = {
            "record_id": record_id,
            "split": split,
            "source_file_id": source_file_id,
            "stage": "ok",
            "validation_issues": [],
            "compiler_issues": [],
        }
        records[record_id] = record
        target = _target_json(case)

        try:
            prediction = json.loads(_prediction_text(case))
        except json.JSONDecodeError as exc:
            record["stage"] = "parse"
            record["parse_error"] = f"{exc.msg} at line {exc.lineno} column {exc.colno}"
            bucket_counter[(split, source_file_id, "parse", "JSON_DECODE_ERROR")] += 1
            continue
        parse_success += 1
        if not isinstance(prediction, dict):
            record["stage"] = "schema"
            record["validation_issues"] = [
                {
                    "code": "INVALID_JSON_ROOT",
                    "path": "",
                    "message": "Prediction root must be a JSON object.",
                }
            ]
            bucket_counter[(split, source_file_id, "schema", "INVALID_JSON_ROOT")] += 1
            continue

        structural_issues = _schema_issues(prediction)
        if structural_issues:
            record["stage"] = "schema"
            record["validation_issues"] = [
                _issue_payload(issue) for issue in structural_issues
            ]
            bucket_counter[
                (split, source_file_id, "schema", structural_issues[0].code)
            ] += 1
            continue
        schema_valid += 1

        semantic_issues = validate_v2_document(prediction)
        if semantic_issues:
            record["stage"] = "semantic"
            record["validation_issues"] = [
                _issue_payload(issue) for issue in semantic_issues
            ]
            bucket_counter[
                (split, source_file_id, "semantic", semantic_issues[0].code)
            ] += 1
            continue
        semantic_valid += 1

        score = _score_valid_prediction(target, prediction)
        scored_records += 1
        for key, value in score.items():
            if key.endswith("_max_error_mm") or key.endswith("_max_error_degrees"):
                continue
            semantic_totals[key] += value
        origin_max = max(origin_max, score["placement_origin_max_error_mm"])
        axis_max = max(axis_max, score["placement_axis_max_error_degrees"])
        ref_direction_max = max(
            ref_direction_max, score["placement_ref_direction_max_error_degrees"]
        )

        if compiler is not None:
            compile_checked += 1
            output_path = compiler_root / "compiled" / f"{_safe_filename(record_id)}.ifc"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            compiler_result = _compiler_payload(compiler(prediction, output_path))
            if compiler_result["compile_success"]:
                compile_success += 1
            if compiler_result["reopen_success"]:
                reopen_success += 1
            if not compiler_result["compile_success"] or not compiler_result[
                "reopen_success"
            ]:
                record["stage"] = "compile"
                record["compiler_issues"] = compiler_result["issues"]
                first_code = (
                    compiler_result["issues"][0].get("code")
                    if compiler_result["issues"]
                    else "COMPILE_FAILURE"
                )
                bucket_counter[(split, source_file_id, "compile", first_code)] += 1

    total = len(cases)
    precision = _rate(
        semantic_totals["property_true_positive"],
        semantic_totals["property_predicted"],
    )
    recall = _rate(
        semantic_totals["property_true_positive"],
        semantic_totals["property_gold"],
    )
    property_f1 = (
        0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    )
    metrics = {
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "record_count": total,
        "validity": {
            "parse_success_rate": _rate(parse_success, total),
            "schema_valid_rate": _rate(schema_valid, total),
            "semantic_valid_rate": _rate(semantic_valid, total),
        },
        "semantic": {
            "scored_record_count": scored_records,
            "ifc_class_accuracy": _rate(
                semantic_totals["class_correct"],
                semantic_totals["class_total"],
            ),
            "entity_count_error": semantic_totals["entity_count_error"],
            "relationship_count_error": semantic_totals["relationship_count_error"],
            "property_precision": precision,
            "property_recall": recall,
            "property_f1": property_f1,
            "relationship_endpoint_accuracy": _rate(
                semantic_totals["relationship_endpoint_correct"],
                semantic_totals["relationship_endpoint_total"],
            ),
            "placement_origin_max_error_mm": origin_max,
            "placement_axis_max_error_degrees": axis_max,
            "placement_ref_direction_max_error_degrees": ref_direction_max,
            "geometry_exact_accuracy": _rate(
                semantic_totals["geometry_correct"],
                semantic_totals["geometry_total"],
            ),
        },
        "compiler": {
            "compile_checked_record_count": compile_checked,
            "compile_success_rate": (
                None if compile_checked == 0 else _rate(compile_success, compile_checked)
            ),
            "reopen_success_rate": (
                None if compile_checked == 0 else _rate(reopen_success, compile_checked)
            ),
        },
    }
    return {
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "metrics": metrics,
        "records": records,
        "error_buckets": _error_buckets(bucket_counter),
    }


def _safe_filename(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", value)


def _error_buckets(
    bucket_counter: Counter[tuple[str, str, str, str]]
) -> list[dict[str, Any]]:
    return [
        {
            "split": split,
            "source_file_id": source_file_id,
            "stage": stage,
            "code": code,
            "record_count": count,
        }
        for (split, source_file_id, stage, code), count in sorted(
            bucket_counter.items()
        )
    ]


def load_pair_records(
    path: Path | str, *, split: str | None = None
) -> list[dict[str, Any]]:
    root = Path(path)
    records: list[dict[str, Any]] = []
    paths = sorted(root.glob("*.jsonl")) if root.is_dir() else [root]
    for item in paths:
        for line in item.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if split is None or record.get("split") == split:
                records.append(record)
    return sorted(records, key=lambda record: record["record_id"])


def load_prediction_records(path: Path | str) -> dict[str, str]:
    root = Path(path)
    predictions: dict[str, str] = {}
    if root.is_file():
        for line in root.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            prediction_text = record.get("prediction_text")
            if prediction_text is None and "prediction_json" in record:
                prediction_text = _canonical(record["prediction_json"])
            if prediction_text is None:
                raise EvaluationError(f"{record.get('record_id')} has no prediction")
            predictions[record["record_id"]] = str(prediction_text)
        return predictions
    for item in sorted(root.glob("*.json")):
        predictions[item.stem] = item.read_text(encoding="utf-8")
    for item in sorted(root.glob("*.txt")):
        predictions[item.stem] = item.read_text(encoding="utf-8")
    return predictions


def build_prediction_cases(
    pair_records: list[dict[str, Any]], prediction_records: dict[str, str]
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for pair in pair_records:
        record_id = pair["record_id"]
        if record_id not in prediction_records:
            raise EvaluationError(f"missing prediction for {record_id}")
        cases.append(
            {
                "record_id": record_id,
                "split": pair["split"],
                "source_file_id": pair["source_file_id"],
                "target_json_path": pair["target_json_path"],
                "prediction_text": prediction_records[record_id],
            }
        )
    return cases


def evaluate_pair_predictions(
    *,
    pairs_path: Path | str,
    predictions_path: Path | str,
    output_dir: Path | str,
    split: str | None = None,
    run_compiler: bool = False,
) -> dict[str, Any]:
    pairs = load_pair_records(pairs_path, split=split)
    predictions = load_prediction_records(predictions_path)
    return evaluate_prediction_cases(
        build_prediction_cases(pairs, predictions),
        compiler=_default_compiler if run_compiler else None,
        output_dir=Path(output_dir),
    )


def write_evaluation_outputs(result: dict[str, Any], output_dir: Path | str) -> None:
    root = Path(output_dir)
    atomic_write_text(root / "metrics.json", render_json(result["metrics"]))
    atomic_write_text(root / "records.json", render_json(result["records"]))
    atomic_write_text(root / "error-buckets.json", render_json(result["error_buckets"]))
    atomic_write_text(root / "report.md", render_report(result))


def render_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# Text-to-BIM-JSON Evaluation Report",
        "",
        "## Metrics",
        "",
        f"- Records: {metrics['record_count']}",
        f"- Parse success: {metrics['validity']['parse_success_rate']:.6f}",
        f"- Schema valid: {metrics['validity']['schema_valid_rate']:.6f}",
        f"- Semantic valid: {metrics['validity']['semantic_valid_rate']:.6f}",
        f"- IFC class accuracy: {metrics['semantic']['ifc_class_accuracy']:.6f}",
        f"- Property F1: {metrics['semantic']['property_f1']:.6f}",
        f"- Relationship endpoint accuracy: {metrics['semantic']['relationship_endpoint_accuracy']:.6f}",
        f"- Placement max error mm: {metrics['semantic']['placement_origin_max_error_mm']:.6f}",
        f"- Geometry exact accuracy: {metrics['semantic']['geometry_exact_accuracy']:.6f}",
        "",
        "## Error Buckets",
        "",
        "| split | source_file_id | stage | code | record_count |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for bucket in result["error_buckets"]:
        lines.append(
            "| {split} | {source_file_id} | {stage} | {code} | {record_count} |".format(
                **bucket
            )
        )
    if not result["error_buckets"]:
        lines.append("| - | - | - | - | 0 |")
    return "\n".join(lines) + "\n"


def build_fixture_cases() -> list[dict[str, Any]]:
    gold = _load_json(ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json")
    schema_invalid = json.loads(_canonical(gold))
    del schema_invalid["ifc_schema"]
    semantic_invalid = json.loads(_canonical(gold))
    semantic_invalid["entities"][4]["ifc_class"] = "IfcBuildingElementProxy"
    return [
        {
            "record_id": "fixture-perfect",
            "split": "validation",
            "source_file_id": "fixture-ifc",
            "target_json": gold,
            "prediction_text": _canonical(gold),
        },
        {
            "record_id": "fixture-invalid-json",
            "split": "validation",
            "source_file_id": "fixture-ifc",
            "target_json": gold,
            "prediction_text": "{",
        },
        {
            "record_id": "fixture-schema-invalid",
            "split": "validation",
            "source_file_id": "fixture-ifc",
            "target_json": gold,
            "prediction_text": _canonical(schema_invalid),
        },
        {
            "record_id": "fixture-semantic-invalid",
            "split": "validation",
            "source_file_id": "fixture-ifc",
            "target_json": gold,
            "prediction_text": _canonical(semantic_invalid),
        },
    ]


def run_fixture_evaluation(
    output_dir: Path | str = DEFAULT_EVALUATION_FIXTURE_DIR,
) -> dict[str, Any]:
    result = evaluate_prediction_cases(
        build_fixture_cases(),
        compiler=_default_compiler,
        output_dir=Path(output_dir),
    )
    write_evaluation_outputs(result, output_dir)
    return result
