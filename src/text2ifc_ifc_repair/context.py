"""Operation-aware compact public context for IFC repair Providers."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import ifcopenshell
from jsonschema import Draft202012Validator

from text2ifc_contract.validation import ValidationIssue

from .geometry import (
    UNSUPPORTED_WALL_GEOMETRY,
    opening_dimensions_mm,
    opening_position_in_wall_mm,
    straight_wall_axis,
    wall_dimensions_mm,
)
from .registry import OperationRegistry, OperationRegistryError


CONTEXT_SCHEMA_VERSION = "text2ifc/ifc-repair-context/0.1"
WINDOW_OPERATION = "add_window_with_opening_to_wall"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-context-0.1.schema.json"
)


@lru_cache(maxsize=1)
def _cached_context_schema() -> dict[str, Any]:
    schema = json.loads(CONTEXT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_context_schema() -> dict[str, Any]:
    return copy.deepcopy(_cached_context_schema())


def validate_repair_context(context: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(_cached_context_schema())
    issues = [
        ValidationIssue(
            code="SCHEMA_VALIDATION_ERROR",
            path=_json_pointer(error.absolute_path),
            message=error.message,
        )
        for error in validator.iter_errors(context)
    ]
    return sorted(set(issues), key=lambda issue: (issue.path, issue.message))


def build_repair_context(
    damaged_ifc_path: Path | str,
    public_spec: Mapping[str, Any],
    *,
    registry: OperationRegistry,
    max_candidates: int = 8,
    max_bytes: int = 12_000,
) -> dict[str, Any]:
    """Build a bounded context while retaining the requested target wall."""

    if max_candidates < 1 or max_bytes < 1:
        raise ValueError("INVALID_CONTEXT_BUDGET")
    operation_type = str(public_spec.get("requested_operation_type", ""))
    try:
        definition = registry.require(operation_type)
    except OperationRegistryError as error:
        raise ValueError(error.code) from error

    source = Path(damaged_ifc_path)
    model = ifcopenshell.open(str(source))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    requested_storey = str(public_spec["storey"]["name"])
    requested_description = str(public_spec["target"]["description"])

    candidates = []
    unsupported_count = 0
    seen_step_ids: set[int] = set()
    targets = []
    for ifc_class in definition.target_ifc_classes:
        for target in model.by_type(ifc_class):
            if target.id() not in seen_step_ids:
                seen_step_ids.add(target.id())
                targets.append(target)
    for target in targets:
        storey = _target_storey_name(target)
        if storey != requested_storey:
            continue
        try:
            candidate = registry.dispatch(
                "context_adapter",
                {"operation_type": operation_type},
                target=target,
                storey=storey,
            )
        except ValueError as error:
            if str(error) != UNSUPPORTED_WALL_GEOMETRY:
                raise
            unsupported_count += 1
            continue
        candidate["_selection_rank"] = (
            0 if target.Name == requested_description else 1,
            str(target.Name or ""),
            str(target.GlobalId),
        )
        candidates.append(candidate)
    candidates.sort(key=lambda item: item["_selection_rank"])
    if not candidates or candidates[0]["_selection_rank"][0] != 0:
        raise ValueError("CONTEXT_TARGET_NOT_FOUND")
    if sum(candidate["_selection_rank"][0] == 0 for candidate in candidates) != 1:
        raise ValueError("CONTEXT_TARGET_AMBIGUOUS")
    for candidate in candidates:
        del candidate["_selection_rank"]

    selected = candidates[:max_candidates]
    context = {
        "schema_version": CONTEXT_SCHEMA_VERSION,
        "base_model_fingerprint": "sha256:" + _sha256(source),
        "request_operation_hints": [operation_type],
        "candidate_targets": selected,
        "model_constraints": {
            "ifc_schema": "IFC2X3",
            "length_unit": "millimetre",
            "supported_wall_geometry": ["straight_wall"],
            "unsupported_wall_error": UNSUPPORTED_WALL_GEOMETRY,
            "unsupported_candidate_count": unsupported_count,
        },
        "context_budget": {
            "max_candidates": max_candidates,
            "max_bytes": max_bytes,
            "selected_candidate_count": len(selected),
            "omitted_candidate_count": len(candidates) - len(selected),
            "actual_bytes": 0,
            "estimated_tokens": 0,
            "token_estimator": "ceil(utf8_bytes/4)",
        },
    }
    _fit_byte_budget(context, candidate_count=len(candidates))
    return context


def canonical_context_json(context: Mapping[str, Any]) -> str:
    return json.dumps(
        context,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def build_window_wall_candidate(wall: Any, *, storey: str) -> dict[str, Any]:
    start, end = straight_wall_axis(wall)
    delta = [end[index] - start[index] for index in range(3)]
    length = sum(value * value for value in delta) ** 0.5
    direction = [value / length for value in delta]
    existing_openings = []
    for relationship in wall.HasOpenings:
        opening = relationship.RelatedOpeningElement
        dimensions = opening_dimensions_mm(opening)
        position = opening_position_in_wall_mm(opening, wall)
        center = position["center_offset"]
        width = dimensions["width"]
        existing_openings.append(
            {
                "center_offset_mm": center,
                "interval_mm": [center - width / 2.0, center + width / 2.0],
                "sill_height_mm": position["sill_height"],
                "width_mm": width,
                "height_mm": dimensions["height"],
            }
        )
    existing_openings.sort(key=lambda item: item["center_offset_mm"])
    return {
        "target_id": f"ifc:{wall.GlobalId}",
        "ifc_global_id": str(wall.GlobalId),
        "ifc_class": wall.is_a(),
        "name": str(wall.Name or ""),
        "storey": storey,
        "geometry_capability": "straight_wall",
        "details": {
            "coordinate_basis": {
                "reference": "wall_local_start",
                "axis_start_mm": start,
                "axis_end_mm": end,
                "axis_direction": direction,
                "vertical_direction": [0.0, 0.0, 1.0],
            },
            "dimensions_mm": wall_dimensions_mm(wall),
            "existing_openings": existing_openings,
        },
    }


def _target_storey_name(target: Any) -> str | None:
    storeys = [
        relationship.RelatingStructure
        for relationship in getattr(target, "ContainedInStructure", ())
        if relationship.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if len(storeys) != 1:
        return None
    return str(storeys[0].Name or "")


def _fit_byte_budget(context: dict[str, Any], *, candidate_count: int) -> None:
    budget = context["context_budget"]
    while True:
        _stabilize_budget_measurements(context)
        if budget["actual_bytes"] <= budget["max_bytes"]:
            return
        if len(context["candidate_targets"]) == 1:
            raise ValueError("CONTEXT_BUDGET_EXCEEDED")
        context["candidate_targets"].pop()
        budget["selected_candidate_count"] = len(context["candidate_targets"])
        budget["omitted_candidate_count"] = (
            candidate_count - budget["selected_candidate_count"]
        )


def _stabilize_budget_measurements(context: dict[str, Any]) -> None:
    budget = context["context_budget"]
    for _ in range(8):
        actual_bytes = len(canonical_context_json(context).encode("utf-8"))
        estimated_tokens = (actual_bytes + 3) // 4
        if (
            budget["actual_bytes"] == actual_bytes
            and budget["estimated_tokens"] == estimated_tokens
        ):
            return
        budget["actual_bytes"] = actual_bytes
        budget["estimated_tokens"] = estimated_tokens
    raise RuntimeError("context budget measurement did not stabilize")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_pointer(parts: Any) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"
