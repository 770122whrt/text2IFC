"""Normalized semantic and geometric preservation comparison for IFC files."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.placement

from .registry import OperationRegistry


COMPARISON_SCHEMA_VERSION = "text2ifc/ifc-repair-comparison/0.1"


def evaluate_repair_application(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    changeset: Mapping[str, Any],
    application_result: Mapping[str, Any],
    registry: OperationRegistry,
) -> dict[str, Any]:
    """Retain the 0.1 dictionary surface while gating it with independent L1."""

    from .evaluation import evaluate_independent_l1
    from .evaluation_models import EvaluationStatus

    allowed_changed_ids = {
        str(item["global_id"])
        for operation_result in application_result.get("operations", [])
        for change_kind in ("created", "modified", "removed")
        for item in operation_result.get("changes", {}).get(change_kind, [])
        if item.get("global_id")
    }
    common = compare_ifc_models(
        damaged_ifc_path,
        repaired_ifc_path,
        allowed_changed_ids=allowed_changed_ids,
    )
    before_model = ifcopenshell.open(str(Path(damaged_ifc_path)))
    after_model = ifcopenshell.open(str(Path(repaired_ifc_path)))
    operation_results_by_id = {
        str(item["operation_id"]): item
        for item in application_result.get("operations", [])
    }
    operation_evaluations = []
    for operation in changeset["operations"]:
        application = operation_results_by_id.get(str(operation["operation_id"]), {})
        operation_evaluations.append(
            {
                "operation_id": operation["operation_id"],
                "operation_type": operation["operation_type"],
                **registry.dispatch(
                    "comparison_adapter",
                    operation,
                    before_model=before_model,
                    after_model=after_model,
                    application=application.get("changes", {}),
                ),
            }
        )
    application_postconditions_valid = all(
        item.get("valid", False)
        for item in application_result.get("postconditions", [])
    )
    l1_result = evaluate_independent_l1(
        damaged_ifc_path=damaged_ifc_path,
        repaired_ifc_path=repaired_ifc_path,
        changeset=changeset,
        application_result=application_result,
        registry=registry,
    )
    complete = (
        bool(application_result.get("valid"))
        and bool(application_result.get("published"))
        and application_postconditions_valid
        and common["complete_preservation_success"]
        and all(item.get("valid", False) for item in operation_evaluations)
        and l1_result.status is EvaluationStatus.PASSED
    )
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation/0.1",
        "complete_repair_success": complete,
        "successful_artifact_publishable": complete,
        "application_postconditions_valid": application_postconditions_valid,
        "tolerances": {
            "linear_mm": 0.1,
            "orientation_degrees": 0.1,
            "volume_m3": 1e-5,
        },
        "common": common,
        "operations": operation_evaluations,
        "l1": _l1_compatibility_projection(l1_result),
    }


def _l1_compatibility_projection(level: Any) -> dict[str, Any]:
    """Project Evaluation 0.2 checks without changing legacy comparator fields."""

    return {
        "status": level.status.value,
        "reason": level.reason,
        "checks": [
            {
                "check_id": check.check_id,
                "status": check.status.value,
                "reason": check.reason,
            }
            for check in level.checks
        ],
    }


def compare_ifc_models(
    before_path: Path | str,
    after_path: Path | str,
    *,
    allowed_changed_ids: Iterable[str],
) -> dict[str, Any]:
    """Compare IFC semantics by GlobalId without relying on STEP order."""

    before = ifcopenshell.open(str(Path(before_path)))
    after = ifcopenshell.open(str(Path(after_path)))
    actual_changes = normalized_model_diff(before, after)
    added = [item["global_id"] for item in actual_changes["created"]]
    removed = [item["global_id"] for item in actual_changes["removed"]]
    modified = [item["global_id"] for item in actual_changes["modified"]]
    changed = set(added) | set(removed) | set(modified)
    allowed = set(allowed_changed_ids)
    unexpected = sorted(changed - allowed)
    drift = {
        item["global_id"]: {"before": item["before"], "after": item["after"]}
        for item in actual_changes["modified"]
    }
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "before_readable": True,
        "after_readable": True,
        "before_schema": before.schema,
        "after_schema": after.schema,
        "schema_preserved": before.schema == after.schema,
        "added_ids": added,
        "removed_ids": removed,
        "modified_ids": modified,
        "allowed_changed_ids": sorted(allowed),
        "unexpected_changed_ids": unexpected,
        "drift": drift,
        "complete_preservation_success": (
            before.schema == after.schema and not unexpected
        ),
    }


def normalized_model_diff(before_model: Any, after_model: Any) -> dict[str, Any]:
    """Return deterministic actual IfcRoot changes from independently opened models."""

    before_snapshot = _model_snapshot(before_model)
    after_snapshot = _model_snapshot(after_model)
    before_ids = set(before_snapshot)
    after_ids = set(after_snapshot)
    created = [
        _diff_fact("created", global_id, None, after_snapshot[global_id])
        for global_id in sorted(after_ids - before_ids)
    ]
    removed = [
        _diff_fact("removed", global_id, before_snapshot[global_id], None)
        for global_id in sorted(before_ids - after_ids)
    ]
    modified = [
        _diff_fact(
            "modified",
            global_id,
            before_snapshot[global_id],
            after_snapshot[global_id],
        )
        for global_id in sorted(before_ids & after_ids)
        if before_snapshot[global_id] != after_snapshot[global_id]
    ]
    return {"created": created, "modified": modified, "removed": removed}


def _diff_fact(
    change_kind: str,
    global_id: str,
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> dict[str, Any]:
    snapshot = after if after is not None else before
    assert snapshot is not None
    ifc_class = str(snapshot["ifc_class"])
    return {
        "change_kind": change_kind,
        "global_id": global_id,
        "ifc_class": ifc_class,
        "is_relationship": ifc_class.startswith("IfcRel"),
        "before": before,
        "after": after,
    }


def _model_snapshot(model: Any) -> dict[str, Any]:
    return {
        str(entity.GlobalId): _root_snapshot(entity)
        for entity in model.by_type("IfcRoot")
    }


def _root_snapshot(entity: Any) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "ifc_class": entity.is_a(),
        "name": getattr(entity, "Name", None),
        "attributes": _root_attributes(entity),
    }
    if entity.is_a("IfcProduct"):
        snapshot["placement"] = _placement_snapshot(entity)
        snapshot["containers"] = sorted(
            str(relation.RelatingStructure.GlobalId)
            for relation in getattr(entity, "ContainedInStructure", ())
        )
        snapshot["types"] = _type_ids(entity)
        snapshot["geometry"] = _geometry_snapshot(entity)
    return snapshot


def _root_attributes(entity: Any) -> dict[str, Any]:
    excluded = {
        "GlobalId",
        "OwnerHistory",
        "Name",
        "Description",
        "ObjectPlacement",
        "Representation",
        "RepresentationMaps",
    }
    attributes: dict[str, Any] = {}
    for index in range(len(entity)):
        name = entity.attribute_name(index)
        if name in excluded:
            continue
        attributes[name] = _normalize_value(entity[index], depth=0, seen=set())
    return attributes


def _normalize_value(value: Any, *, depth: int, seen: set[int]) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        normalized = [
            _normalize_value(child, depth=depth, seen=seen) for child in value
        ]
        return sorted(normalized, key=_canonical_sort_key)
    if hasattr(value, "is_a") and hasattr(value, "id"):
        global_id = getattr(value, "GlobalId", None)
        if global_id:
            return {"ifc_class": value.is_a(), "global_id": str(global_id)}
        if depth >= 2 or value.id() in seen:
            return {
                "ifc_class": value.is_a(),
                "name": getattr(value, "Name", None),
            }
        child_seen = set(seen)
        child_seen.add(value.id())
        attributes = {}
        for index in range(len(value)):
            name = value.attribute_name(index)
            if name in {"OwnerHistory", "Representation", "RepresentationMaps"}:
                continue
            attributes[name] = _normalize_value(
                value[index], depth=depth + 1, seen=child_seen
            )
        return {"ifc_class": value.is_a(), "attributes": attributes}
    return str(value)


def _placement_snapshot(entity: Any) -> list[list[float]] | None:
    if getattr(entity, "ObjectPlacement", None) is None:
        return None
    matrix = ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)
    return [
        [round(float(value), 6) for value in row]
        for row in matrix.tolist()
    ]


def _type_ids(entity: Any) -> list[str]:
    ids = []
    for relation in getattr(entity, "IsDefinedBy", ()):
        if relation.is_a("IfcRelDefinesByType"):
            ids.append(str(relation.RelatingType.GlobalId))
    for relation in getattr(entity, "IsTypedBy", ()):
        ids.append(str(relation.RelatingType.GlobalId))
    return sorted(set(ids))


def _geometry_snapshot(entity: Any) -> dict[str, Any] | None:
    representation = getattr(entity, "Representation", None)
    if representation is None:
        return None
    normalized = _normalize_representation_value(
        representation, depth=0, seen=set()
    )
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "available": True,
        "representation_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def _normalize_representation_value(
    value: Any,
    *,
    depth: int,
    seen: set[int],
) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return [
            _normalize_representation_value(child, depth=depth, seen=seen)
            for child in value
        ]
    if hasattr(value, "is_a") and hasattr(value, "id"):
        global_id = getattr(value, "GlobalId", None)
        if global_id:
            return {"ifc_class": value.is_a(), "global_id": str(global_id)}
        if depth >= 12 or value.id() in seen:
            return {"ifc_class": value.is_a(), "cycle": True}
        child_seen = set(seen)
        child_seen.add(value.id())
        return {
            "ifc_class": value.is_a(),
            "attributes": {
                value.attribute_name(index): _normalize_representation_value(
                    value[index], depth=depth + 1, seen=child_seen
                )
                for index in range(len(value))
            },
        }
    return str(value)


def _canonical_sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
