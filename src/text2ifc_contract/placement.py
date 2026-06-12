"""Validation and deterministic composition of parent-relative placements."""

from __future__ import annotations

import math
from numbers import Number
from typing import Any

from text2ifc_knowledge.registry import load_ifc2x3_registry

from .validation import ValidationIssue


MAX_PLACEMENT_DEPTH = 64
MAX_COORDINATE_MAGNITUDE = 100_000_000.0
VECTOR_TOLERANCE = 1e-9
ORTHOGONAL_TOLERANCE = 1e-9

_SPATIAL_PARENT_CLASSES = {
    "IfcSite": {"IfcProject"},
    "IfcBuilding": {"IfcProject", "IfcSite"},
    "IfcBuildingStorey": {"IfcProject", "IfcBuilding"},
    "IfcSpace": {"IfcBuildingStorey", "IfcSpace"},
}


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, Number)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _vector(value: Any, length: int) -> list[float] | None:
    if not isinstance(value, list) or len(value) != length:
        return None
    if not all(_is_number(item) for item in value):
        return None
    return [float(item) for item in value]


def _norm(value: list[float]) -> float:
    return math.sqrt(sum(item * item for item in value))


def _normalized(value: list[float]) -> list[float]:
    magnitude = _norm(value)
    if magnitude <= VECTOR_TOLERANCE:
        raise ValueError("placement direction vector is zero")
    return [item / magnitude for item in value]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _identity() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _matrix_multiply(
    left: list[list[float]], right: list[list[float]]
) -> list[list[float]]:
    return [
        [
            sum(left[row][inner] * right[inner][column] for inner in range(4))
            for column in range(4)
        ]
        for row in range(4)
    ]


def _local_transform(placement: dict[str, Any]) -> list[list[float]]:
    origin = _vector(placement.get("origin"), 3)
    axis = _vector(placement.get("axis"), 3)
    ref_direction = _vector(placement.get("ref_direction"), 3)
    if origin is None or axis is None or ref_direction is None:
        raise ValueError("placement vectors must contain three finite numbers")
    if any(abs(item) > MAX_COORDINATE_MAGNITUDE for item in origin):
        raise ValueError("placement origin exceeds the coordinate limit")

    z_axis = _normalized(axis)
    x_axis = _normalized(ref_direction)
    if abs(_dot(z_axis, x_axis)) > ORTHOGONAL_TOLERANCE:
        raise ValueError("placement axis and reference direction are not orthogonal")
    y_axis = _normalized(_cross(z_axis, x_axis))
    return [
        [x_axis[0], y_axis[0], z_axis[0], origin[0]],
        [x_axis[1], y_axis[1], z_axis[1], origin[1]],
        [x_axis[2], y_axis[2], z_axis[2], origin[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _is_product(declaration) -> bool:
    return declaration is not None and "IfcProduct" in declaration["supertypes"]


def _parent_class_allowed(
    child_class: str,
    parent_class: str,
    registry,
) -> bool:
    allowed = _SPATIAL_PARENT_CLASSES.get(child_class)
    if allowed is not None:
        return parent_class in allowed
    if parent_class == "IfcProject":
        return True
    return _is_product(registry.declaration(parent_class))


def validate_placement_graph(
    document: dict[str, Any],
) -> list[ValidationIssue]:
    registry = load_ifc2x3_registry()
    entities = document.get("entities", [])
    indexed = {
        record.get("id"): (index, record)
        for index, record in enumerate(entities)
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    issues: list[ValidationIssue] = []

    for index, record in enumerate(entities):
        ifc_class = record["ifc_class"]
        declaration = registry.declaration(ifc_class)
        if not _is_product(declaration):
            continue

        base = f"/entities/{index}/attributes/ObjectPlacement"
        placement = record["attributes"].get("ObjectPlacement")
        if not isinstance(placement, dict):
            issues.append(
                _issue(
                    "MISSING_OBJECT_PLACEMENT",
                    base,
                    f"{ifc_class} requires parent-relative placement.",
                )
            )
            continue

        for field in ("origin", "axis", "ref_direction"):
            path = f"{base}/{field}"
            vector = _vector(placement.get(field), 3)
            if vector is None:
                issues.append(
                    _issue(
                        "INVALID_PLACEMENT_VECTOR",
                        path,
                        f"{field} must contain three finite numbers.",
                    )
                )
                continue
            if field == "origin":
                if any(
                    abs(item) > MAX_COORDINATE_MAGNITUDE for item in vector
                ):
                    issues.append(
                        _issue(
                            "COORDINATE_LIMIT_EXCEEDED",
                            path,
                            "Placement origin exceeds the coordinate limit.",
                        )
                    )
            elif _norm(vector) <= VECTOR_TOLERANCE:
                issues.append(
                    _issue(
                        "ZERO_PLACEMENT_VECTOR",
                        path,
                        f"{field} must be non-zero.",
                    )
                )

        axis = _vector(placement.get("axis"), 3)
        ref_direction = _vector(placement.get("ref_direction"), 3)
        if (
            axis is not None
            and ref_direction is not None
            and _norm(axis) > VECTOR_TOLERANCE
            and _norm(ref_direction) > VECTOR_TOLERANCE
            and abs(_dot(_normalized(axis), _normalized(ref_direction)))
            > ORTHOGONAL_TOLERANCE
        ):
            issues.append(
                _issue(
                    "NON_ORTHOGONAL_PLACEMENT",
                    f"{base}/ref_direction",
                    "axis and ref_direction must be orthogonal.",
                )
            )

        parent_id = placement.get("relative_to")
        parent_entry = indexed.get(parent_id)
        if parent_entry is None:
            issues.append(
                _issue(
                    "UNRESOLVED_PLACEMENT_PARENT",
                    f"{base}/relative_to",
                    f"Placement parent {parent_id!r} is not declared.",
                )
            )
        else:
            parent_class = parent_entry[1]["ifc_class"]
            if not _parent_class_allowed(ifc_class, parent_class, registry):
                issues.append(
                    _issue(
                        "INVALID_PLACEMENT_PARENT_CLASS",
                        f"{base}/relative_to",
                        f"{ifc_class} cannot be placed relative to {parent_class}.",
                    )
                )

    for start_id, (start_index, record) in indexed.items():
        declaration = registry.declaration(record["ifc_class"])
        if not _is_product(declaration):
            continue
        seen: set[str] = set()
        current_id = start_id
        depth = 0
        while current_id in indexed:
            if current_id in seen:
                issues.append(
                    _issue(
                        "PLACEMENT_CYCLE",
                        f"/entities/{start_index}/attributes/ObjectPlacement/relative_to",
                        f"Placement chain for {start_id!r} contains a cycle.",
                    )
                )
                break
            seen.add(current_id)
            current = indexed[current_id][1]
            placement = current["attributes"].get("ObjectPlacement")
            if not isinstance(placement, dict):
                break
            parent_id = placement.get("relative_to")
            if parent_id not in indexed:
                break
            depth += 1
            if depth > MAX_PLACEMENT_DEPTH:
                issues.append(
                    _issue(
                        "PLACEMENT_DEPTH_EXCEEDED",
                        f"/entities/{start_index}/attributes/ObjectPlacement/relative_to",
                        f"Placement chain exceeds {MAX_PLACEMENT_DEPTH} levels.",
                    )
                )
                break
            current_id = parent_id

    return issues


def world_transform_for(
    document: dict[str, Any], entity_id: str
) -> list[list[float]]:
    indexed = {
        record["id"]: record
        for record in document.get("entities", [])
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    if entity_id not in indexed:
        raise KeyError(entity_id)

    def compose(
        current_id: str, seen: set[str], depth: int
    ) -> list[list[float]]:
        if depth > MAX_PLACEMENT_DEPTH:
            raise ValueError("placement depth exceeded")
        if current_id in seen:
            raise ValueError("placement cycle")
        record = indexed[current_id]
        placement = record.get("attributes", {}).get("ObjectPlacement")
        if placement is None:
            return _identity()
        parent_id = placement.get("relative_to")
        if parent_id not in indexed:
            raise ValueError(f"unresolved placement parent: {parent_id!r}")
        parent = compose(parent_id, {*seen, current_id}, depth + 1)
        return _matrix_multiply(parent, _local_transform(placement))

    return compose(entity_id, set(), 0)
