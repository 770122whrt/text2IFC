"""Pure shared resolution and capability policy for structural operations."""

from __future__ import annotations

import math
from typing import Any, Mapping

from text2ifc_ifc_repair.operations.structural_member import (
    resolve_structural_member_frame,
)
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target


def structural_intent_capability(
    *,
    operation: Mapping[str, Any],
    family: str,
) -> dict[str, str]:
    parameters = operation.get("parameters")
    if not isinstance(parameters, Mapping):
        return {"status": "supported"}
    if any(
        key in parameters
        for key in ("analysis_member", "structural_analysis", "loads", "nodes")
    ):
        return {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        }
    if any(key in parameters for key in ("length_mm", "height_mm")):
        return {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_SCALAR_EXTENT_UNSUPPORTED",
        }
    axis = parameters.get("axis")
    if isinstance(axis, Mapping):
        if "grid" in axis:
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_GRID_PLACEMENT_UNSUPPORTED",
            }
        if any(key in axis for key in ("curve", "control_points", "polyline")):
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_CURVED_MEMBER_UNSUPPORTED",
            }
        reference = axis.get("reference")
        if isinstance(reference, Mapping) and reference.get("grid"):
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_GRID_PLACEMENT_UNSUPPORTED",
            }
    section = parameters.get("section")
    if isinstance(section, Mapping):
        if section.get("shape") not in {None, "rectangle"}:
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_SECTION_UNSUPPORTED",
            }
        if family == "beam" and any(
            key in section
            for key in ("orientation", "rotation", "rotation_degrees")
        ):
            return {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_SECTION_ROTATION_UNSUPPORTED",
            }
    if isinstance(axis, Mapping) and _has_explicit_axis(axis, family):
        try:
            resolve_structural_member_frame(
                occurrence_class=_occurrence_class(family),
                axis_start_mm=_point_tuple(axis[_axis_keys(family)[0]]),
                axis_end_mm=_point_tuple(axis[_axis_keys(family)[1]]),
                section=section,
            )
        except ValueError as error:
            return {"status": "unsupported", "reason_code": str(error)}
    return {"status": "supported"}


def resolve_structural_parameters(
    *,
    operation: Mapping[str, Any],
    target_record: Any,
    repository: Any,
    context: Mapping[str, Any],
    family: str,
) -> dict[str, Any]:
    del context
    if target_record.ifc_class != "IfcBuildingStorey":
        return {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_TARGET_STOREY_REQUIRED",
        }
    parameters = operation.get("parameters")
    if not isinstance(parameters, Mapping):
        return _missing(("/parameters/axis", "/parameters/section"))
    axis = parameters.get("axis")
    section = parameters.get("section")
    missing: list[str] = []
    if not isinstance(axis, Mapping):
        missing.append("/parameters/axis")
    if not isinstance(section, Mapping):
        missing.append("/parameters/section")
    if missing:
        return _missing(tuple(missing))
    assert isinstance(axis, Mapping) and isinstance(section, Mapping)
    start_key, end_key = _axis_keys(family)
    has_explicit = start_key in axis or end_key in axis
    has_reference = "reference" in axis
    if has_explicit and has_reference:
        return {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_AXIS_AUTHORITY_CONFLICT",
        }
    if has_explicit:
        missing = [
            f"/parameters/axis/{key}"
            for key in (start_key, end_key)
            if key not in axis
        ]
        if missing:
            return _missing(tuple(missing))
        try:
            canonical_axis = {
                start_key: _canonical_point(axis[start_key]),
                end_key: _canonical_point(axis[end_key]),
            }
            resolve_structural_member_frame(
                occurrence_class=_occurrence_class(family),
                axis_start_mm=_point_tuple(canonical_axis[start_key]),
                axis_end_mm=_point_tuple(canonical_axis[end_key]),
                section=section,
            )
        except ValueError as error:
            return {"status": "unsupported", "reason_code": str(error)}
        return {
            "status": "resolved",
            "parameters": {"axis": canonical_axis, "section": dict(section)},
        }
    if not has_reference:
        return _missing(
            (
                f"/parameters/axis/{start_key}",
                f"/parameters/axis/{end_key}",
            )
        )
    if repository is None or not isinstance(axis["reference"], Mapping):
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_INVALID",
            "candidates": (),
        }
    try:
        query = TargetQuery.from_dict(axis["reference"])
    except ValueError:
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_INVALID",
            "candidates": (),
        }
    if set(query.allowed_ifc_classes) != {_occurrence_class(family)}:
        return {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_CLASS_UNSUPPORTED",
        }
    result = resolve_target(repository, query)
    candidates = tuple(item.to_dict() for item in result.candidates)
    if result.status == "ambiguous":
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_AMBIGUOUS",
            "candidates": candidates,
        }
    if result.status != "resolved" or not result.candidates:
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_NOT_FOUND",
            "candidates": candidates,
        }
    reference = repository.get_by_global_id(result.candidates[0].ifc_global_id)
    if reference is None or reference.storey_global_id != target_record.ifc_global_id:
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_STOREY_MISMATCH",
            "candidates": candidates,
        }
    capability = reference.geometry_summary.get("axis_capability", {})
    if (
        capability.get("status") != "measured_current_ifc"
        or capability.get("storey_global_id") != target_record.ifc_global_id
        or not capability.get("storey_local_start_mm")
        or not capability.get("storey_local_end_mm")
    ):
        return {
            "status": "clarification_required",
            "reason_code": "STRUCTURAL_AXIS_REFERENCE_GEOMETRY_UNAVAILABLE",
            "candidates": candidates,
        }
    canonical_axis = {
        start_key: _point_document(capability["storey_local_start_mm"]),
        end_key: _point_document(capability["storey_local_end_mm"]),
    }
    try:
        resolve_structural_member_frame(
            occurrence_class=_occurrence_class(family),
            axis_start_mm=_point_tuple(canonical_axis[start_key]),
            axis_end_mm=_point_tuple(canonical_axis[end_key]),
            section=section,
        )
    except ValueError as error:
        return {"status": "unsupported", "reason_code": str(error)}
    return {
        "status": "resolved",
        "parameters": {"axis": canonical_axis, "section": dict(section)},
    }


def structural_operation_conflict_checker(
    previous: Mapping[str, Any],
    current: Mapping[str, Any],
) -> list[dict[str, str]]:
    if previous.get("target") != current.get("target"):
        return []
    first = previous.get("parameters", {}).get("axis", {})
    second = current.get("parameters", {}).get("axis", {})
    family = str(current.get("operation_type", "")).removeprefix("add_")
    start_key, end_key = _axis_keys(family)
    if not all(key in first and key in second for key in (start_key, end_key)):
        return []
    first_points = (_point_tuple(first[start_key]), _point_tuple(first[end_key]))
    second_points = (_point_tuple(second[start_key]), _point_tuple(second[end_key]))
    if not _collinear_overlap(first_points, second_points):
        return []
    return [
        {
            "code": "STRUCTURAL_SAME_AXIS_OVERLAP",
            "path": f"/parameters/axis/{start_key}",
            "message": "Structural member overlaps an operation on the same axis.",
        }
    ]


def _collinear_overlap(
    first: tuple[tuple[float, float, float], tuple[float, float, float]],
    second: tuple[tuple[float, float, float], tuple[float, float, float]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    a, b = first
    c, d = second
    vector = tuple(b[index] - a[index] for index in range(3))
    length = math.sqrt(sum(value * value for value in vector))
    if length <= tolerance:
        return False
    unit = tuple(value / length for value in vector)
    for point in (c, d):
        delta = tuple(point[index] - a[index] for index in range(3))
        projection = sum(delta[index] * unit[index] for index in range(3))
        residual = tuple(
            delta[index] - projection * unit[index] for index in range(3)
        )
        if math.sqrt(sum(value * value for value in residual)) > tolerance:
            return False
    second_interval = sorted(
        sum((point[index] - a[index]) * unit[index] for index in range(3))
        for point in (c, d)
    )
    return min(length, second_interval[1]) - max(0.0, second_interval[0]) > tolerance


def _missing(paths: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "clarification_required",
        "reason_code": "STRUCTURAL_FACTS_REQUIRED",
        "candidates": tuple(
            {"path": path, "fact": "required"} for path in sorted(paths)
        ),
    }


def _axis_keys(family: str) -> tuple[str, str]:
    if family == "beam":
        return "start", "end"
    if family == "column":
        return "base", "top"
    raise ValueError("STRUCTURAL_FAMILY_UNSUPPORTED")


def _occurrence_class(family: str) -> str:
    return {"beam": "IfcBeam", "column": "IfcColumn"}.get(
        family, "IfcStructuralItem"
    )


def _has_explicit_axis(axis: Mapping[str, Any], family: str) -> bool:
    return all(key in axis for key in _axis_keys(family))


def _canonical_point(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping) or set(value) != {"x_mm", "y_mm", "z_mm"}:
        raise ValueError("STRUCTURAL_AXIS_INVALID")
    result: dict[str, float] = {}
    for key in ("x_mm", "y_mm", "z_mm"):
        raw = value[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("STRUCTURAL_AXIS_INVALID")
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError("STRUCTURAL_AXIS_INVALID")
        result[key] = number
    return result


def _point_tuple(value: Any) -> tuple[float, float, float]:
    point = _canonical_point(value)
    return point["x_mm"], point["y_mm"], point["z_mm"]


def _point_document(value: Any) -> dict[str, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("STRUCTURAL_AXIS_INVALID")
    return {
        key: float(item)
        for key, item in zip(("x_mm", "y_mm", "z_mm"), value, strict=True)
    }


__all__ = [
    "resolve_structural_parameters",
    "structural_intent_capability",
    "structural_operation_conflict_checker",
]
