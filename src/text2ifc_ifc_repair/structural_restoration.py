"""Independent original/damaged/repaired structural restoration audit."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import ifcopenshell

from .geometry import measure_straight_rectangular_member
from .index_adapters import BeamIndexAdapter, ColumnIndexAdapter
from .mutation import _structural_geometry_is_reconstructable


SCHEMA_VERSION = "text2ifc/structural-restoration-audit/0.2"
AXIS_TOLERANCE_MM = 0.01
SECTION_TOLERANCE_MM = 0.01
ORIENTATION_TOLERANCE_DEGREES = 0.1
COVERAGE_MODES = frozenset(
    {"complete_damage_set", "requested_operation_subset"}
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"STRUCTURAL_RESTORATION_DOCUMENT_INVALID:{path.name}")
    return value


def _optional_guid(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None


def _point(value: Mapping[str, Any]) -> tuple[float, float, float]:
    return tuple(float(value[key]) for key in ("x_mm", "y_mm", "z_mm"))


def _point_distance(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    return math.sqrt(
        sum((float(a) - float(b)) ** 2 for a, b in zip(left, right, strict=True))
    )


def _axis_error_mm(
    family: str,
    operation: Mapping[str, Any],
    target_axis: Mapping[str, Any],
) -> float:
    axis = operation["parameters"]["axis"]
    if family == "beam":
        actual = (_point(axis["start"]), _point(axis["end"]))
        expected = (
            tuple(float(value) for value in target_axis["storey_local_start_mm"]),
            tuple(float(value) for value in target_axis["storey_local_end_mm"]),
        )
        direct = max(
            _point_distance(actual[0], expected[0]),
            _point_distance(actual[1], expected[1]),
        )
        reversed_error = max(
            _point_distance(actual[0], expected[1]),
            _point_distance(actual[1], expected[0]),
        )
        return min(direct, reversed_error)
    actual = (_point(axis["base"]), _point(axis["top"]))
    expected_points = sorted(
        (
            tuple(float(value) for value in target_axis["storey_local_start_mm"]),
            tuple(float(value) for value in target_axis["storey_local_end_mm"]),
        ),
        key=lambda point: point[2],
    )
    return max(
        _point_distance(actual[0], expected_points[0]),
        _point_distance(actual[1], expected_points[1]),
    )


def _target_section_dimensions(
    family: str,
    section: Mapping[str, Any],
) -> tuple[float, float]:
    profile_x = float(section["profile_x_mm"])
    profile_y = float(section["profile_y_mm"])
    if family == "column":
        return profile_x, profile_y
    profile_x_direction = tuple(
        float(value) for value in section["world_profile_x_direction"]
    )
    if abs(profile_x_direction[2]) >= math.cos(math.radians(0.1)):
        return profile_y, profile_x
    return profile_x, profile_y


def _section_error_mm(
    family: str,
    operation: Mapping[str, Any],
    target_section: Mapping[str, Any],
) -> float:
    expected_first, expected_second = _target_section_dimensions(
        family,
        target_section,
    )
    section = operation["parameters"]["section"]
    actual_first = float(section["width_mm"])
    actual_second = float(
        section["height_mm"] if family == "beam" else section["depth_mm"]
    )
    return max(
        abs(actual_first - expected_first),
        abs(actual_second - expected_second),
    )


def _undirected_orientation_error_degrees(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    left_values = tuple(float(value) for value in left)
    right_values = tuple(float(value) for value in right)
    if len(left_values) != 3 or len(right_values) != 3:
        raise ValueError("STRUCTURAL_RESTORATION_ORIENTATION_INVALID")
    left_magnitude = math.sqrt(sum(value * value for value in left_values))
    right_magnitude = math.sqrt(sum(value * value for value in right_values))
    if left_magnitude <= 0.0 or right_magnitude <= 0.0:
        raise ValueError("STRUCTURAL_RESTORATION_ORIENTATION_INVALID")
    dot = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left_values,
            right_values,
            strict=True,
        )
    ) / (left_magnitude * right_magnitude)
    return math.degrees(math.acos(max(-1.0, min(1.0, abs(dot)))))


def _repaired_orientation_error_degrees(
    *,
    family: str,
    target_section: Mapping[str, Any],
    measurement: Mapping[str, Any],
) -> float | None:
    if family != "column":
        return None
    profile_x = float(target_section["profile_x_mm"])
    profile_y = float(target_section["profile_y_mm"])
    if abs(profile_x - profile_y) <= SECTION_TOLERANCE_MM:
        return None
    actual = measurement.get("orientation")
    expected = target_section.get("storey_local_profile_x_direction")
    if actual is None or not isinstance(expected, Sequence):
        return math.inf
    return _undirected_orientation_error_degrees(expected, actual)


def _created_member(
    *,
    repaired: Any,
    application: Mapping[str, Any],
    operation_id: str,
    family: str,
) -> Any | None:
    expected_class = "IfcBeam" if family == "beam" else "IfcColumn"
    operations = [
        item
        for item in application.get("operations", ())
        if str(item.get("operation_id") or "") == operation_id
    ]
    if len(operations) != 1:
        return None
    matches = [
        item
        for item in operations[0].get("changes", {}).get("created", ())
        if item.get("role") == family
        and item.get("ifc_class") == expected_class
        and item.get("global_id")
    ]
    if len(matches) != 1:
        return None
    entity = _optional_guid(repaired, str(matches[0]["global_id"]))
    if entity is None or not entity.is_a(expected_class):
        return None
    return entity


def audit_structural_restoration_case(
    case_root: Path | str,
    *,
    coverage_mode: str = "complete_damage_set",
) -> dict[str, Any]:
    if coverage_mode not in COVERAGE_MODES:
        raise ValueError("STRUCTURAL_RESTORATION_COVERAGE_MODE_INVALID")
    root = Path(case_root).resolve()
    original = ifcopenshell.open(str(root / "original.ifc"))
    damaged = ifcopenshell.open(str(root / "damaged.ifc"))
    repaired = ifcopenshell.open(str(root / "repaired.ifc"))
    private = _read_json(root / "mutation_manifest.private.json")
    changeset = _read_json(root / "changeset.json")
    application = _read_json(root / "application.json")
    case_id = str(changeset.get("case_id") or root.name)
    issues: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    unrequested_damage_families: list[str] = []

    targets_by_family: dict[str, list[Mapping[str, Any]]] = {
        "beam": [],
        "column": [],
    }
    for target in private.get("targets", ()):
        if not isinstance(target, Mapping):
            continue
        ifc_class = str(target.get("entity", {}).get("ifc_class") or "")
        family = {"IfcBeam": "beam", "IfcColumn": "column"}.get(ifc_class)
        if family is not None:
            targets_by_family[family].append(target)

    operations_by_family: dict[str, list[Mapping[str, Any]]] = {
        "beam": [],
        "column": [],
    }
    for operation in changeset.get("operations", ()):
        if not isinstance(operation, Mapping):
            continue
        family = {
            "add_beam": "beam",
            "add_column": "column",
        }.get(str(operation.get("operation_type") or ""))
        if family is not None:
            operations_by_family[family].append(operation)

    for family in ("beam", "column"):
        targets = targets_by_family[family]
        operations = operations_by_family[family]
        if not targets and not operations:
            continue
        if (
            coverage_mode == "requested_operation_subset"
            and targets
            and not operations
        ):
            unrequested_damage_families.append(family)
            continue
        if len(targets) != 1 or len(operations) != 1:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_BINDING_AMBIGUOUS",
                    "family": family,
                    "target_count": len(targets),
                    "operation_count": len(operations),
                }
            )
            continue

        target = targets[0]
        operation = operations[0]
        operation_id = str(operation.get("operation_id") or "")
        target_id = str(target["entity"]["global_id"])
        target_entity = _optional_guid(original, target_id)
        target_storey_id = str(target["storey"]["global_id"])
        operation_storey_id = str(
            operation.get("target", {}).get("storey_global_id") or ""
        )
        outcome = {
            "family": family,
            "operation_id": operation_id,
            "target_role": str(target.get("role") or ""),
            "target_global_id": target_id,
            "checks": {},
        }
        outcomes.append(outcome)

        if target_entity is None:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_ORIGINAL_TARGET_MISSING",
                    "family": family,
                }
            )
            continue
        adapter = BeamIndexAdapter() if family == "beam" else ColumnIndexAdapter()
        target_geometry = adapter.extract(target_entity).geometry_summary
        reconstructable = _structural_geometry_is_reconstructable(
            family=family,
            geometry_summary=target_geometry,
            storey_global_id=target_storey_id,
        )
        outcome["checks"]["target_reconstructable"] = reconstructable
        if not reconstructable:
            issues.append(
                {
                    "code": (
                        "STRUCTURAL_RESTORATION_TARGET_NOT_RECONSTRUCTABLE"
                    ),
                    "family": family,
                }
            )

        target_absent = _optional_guid(damaged, target_id) is None
        outcome["checks"]["target_absent_in_damaged"] = target_absent
        if not target_absent:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_DAMAGE_TARGET_PRESENT",
                    "family": family,
                }
            )

        storey_matches = operation_storey_id == target_storey_id
        outcome["checks"]["storey_matches"] = storey_matches
        if not storey_matches:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_STOREY_MISMATCH",
                    "family": family,
                    "expected": target_storey_id,
                    "actual": operation_storey_id,
                }
            )

        target_axis = target_geometry.get("axis_capability", {})
        try:
            axis_error = _axis_error_mm(family, operation, target_axis)
        except (KeyError, TypeError, ValueError):
            axis_error = math.inf
        outcome["checks"]["request_axis_error_mm"] = axis_error
        if not math.isfinite(axis_error) or axis_error > AXIS_TOLERANCE_MM:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_AXIS_MISMATCH",
                    "family": family,
                    "error_mm": axis_error,
                }
            )

        target_section = target_geometry.get("section_capability", {})
        try:
            section_error = _section_error_mm(
                family,
                operation,
                target_section,
            )
        except (KeyError, TypeError, ValueError):
            section_error = math.inf
        outcome["checks"]["request_section_error_mm"] = section_error
        if (
            not math.isfinite(section_error)
            or section_error > SECTION_TOLERANCE_MM
        ):
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_SECTION_MISMATCH",
                    "family": family,
                    "error_mm": section_error,
                }
            )

        created = _created_member(
            repaired=repaired,
            application=application,
            operation_id=operation_id,
            family=family,
        )
        outcome["checks"]["created_member_present"] = created is not None
        if created is None:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_CREATED_MEMBER_MISSING",
                    "family": family,
                }
            )
            continue
        repaired_storeys = [
            relation.RelatingStructure
            for relation in getattr(created, "ContainedInStructure", ())
            if relation.RelatingStructure.is_a("IfcBuildingStorey")
        ]
        if len(repaired_storeys) != 1:
            issues.append(
                {
                    "code": (
                        "STRUCTURAL_RESTORATION_REPAIRED_STOREY_INVALID"
                    ),
                    "family": family,
                }
            )
            continue
        repaired_storey_id = str(repaired_storeys[0].GlobalId)
        repaired_storey_matches = repaired_storey_id == target_storey_id
        outcome["checks"]["repaired_storey_matches"] = (
            repaired_storey_matches
        )
        if not repaired_storey_matches:
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_REPAIRED_STOREY_MISMATCH",
                    "family": family,
                    "expected": target_storey_id,
                    "actual": repaired_storey_id,
                }
            )
        measurement = measure_straight_rectangular_member(
            created,
            relative_to=repaired_storeys[0],
        )
        try:
            repaired_axis_error = _axis_error_mm(
                family,
                {
                    "parameters": {
                        "axis": {
                            ("start" if family == "beam" else "base"): dict(
                                zip(
                                    ("x_mm", "y_mm", "z_mm"),
                                    measurement["axis_start_mm"],
                                    strict=True,
                                )
                            ),
                            ("end" if family == "beam" else "top"): dict(
                                zip(
                                    ("x_mm", "y_mm", "z_mm"),
                                    measurement["axis_end_mm"],
                                    strict=True,
                                )
                            ),
                        }
                    }
                },
                target_axis,
            )
        except (KeyError, TypeError, ValueError):
            repaired_axis_error = math.inf
        outcome["checks"]["repaired_axis_error_mm"] = repaired_axis_error
        if (
            not math.isfinite(repaired_axis_error)
            or repaired_axis_error > AXIS_TOLERANCE_MM
        ):
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_REPAIRED_AXIS_MISMATCH",
                    "family": family,
                    "error_mm": repaired_axis_error,
                }
            )

        try:
            repaired_section_error = _section_error_mm(
                family,
                {"parameters": {"section": measurement["section"]}},
                target_section,
            )
        except (KeyError, TypeError, ValueError):
            repaired_section_error = math.inf
        outcome["checks"]["repaired_section_error_mm"] = (
            repaired_section_error
        )
        if (
            not math.isfinite(repaired_section_error)
            or repaired_section_error > SECTION_TOLERANCE_MM
        ):
            issues.append(
                {
                    "code": "STRUCTURAL_RESTORATION_REPAIRED_SECTION_MISMATCH",
                    "family": family,
                    "error_mm": repaired_section_error,
                }
            )

        try:
            repaired_orientation_error = _repaired_orientation_error_degrees(
                family=family,
                target_section=target_section,
                measurement=measurement,
            )
        except (KeyError, TypeError, ValueError):
            repaired_orientation_error = math.inf
        outcome["checks"]["repaired_orientation_error_degrees"] = (
            repaired_orientation_error
        )
        if (
            repaired_orientation_error is not None
            and (
                not math.isfinite(repaired_orientation_error)
                or repaired_orientation_error > ORIENTATION_TOLERANCE_DEGREES
            )
        ):
            issues.append(
                {
                    "code": (
                        "STRUCTURAL_RESTORATION_REPAIRED_ORIENTATION_MISMATCH"
                    ),
                    "family": family,
                    "error_degrees": repaired_orientation_error,
                }
            )

    eligible = bool(outcomes) and not issues
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "status": "passed" if not issues else "failed",
        "restoration_eligible": eligible,
        "coverage_mode": coverage_mode,
        "unrequested_damage_families": unrequested_damage_families,
        "axis_tolerance_mm": AXIS_TOLERANCE_MM,
        "section_tolerance_mm": SECTION_TOLERANCE_MM,
        "orientation_tolerance_degrees": ORIENTATION_TOLERANCE_DEGREES,
        "outcomes": outcomes,
        "issues": issues,
    }


__all__ = ["audit_structural_restoration_case"]
