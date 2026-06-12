"""Bounded semantic geometry validation for BIM JSON 2.0."""

from __future__ import annotations

import math
from numbers import Number
from typing import Any

from text2ifc_knowledge.registry import load_ifc2x3_registry

from .validation import ValidationIssue


MAX_COORDINATE_MAGNITUDE = 100_000_000.0
MAX_PROFILE_POINTS = 257
VECTOR_TOLERANCE = 1e-9


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path=path, message=message)


def _number(value: Any) -> float | None:
    if (
        not isinstance(value, Number)
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        return None
    return float(value)


def _requires_representation(ifc_class: str, declaration) -> bool:
    if declaration is None:
        return False
    return ifc_class == "IfcSpace" or "IfcElement" in declaration["supertypes"]


def _validate_rectangle(
    profile: dict[str, Any], path: str
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in sorted(set(profile) - {"kind", "x", "y"}):
        issues.append(
            _issue(
                "UNSUPPORTED_PROFILE_FIELD",
                f"{path}/{field}",
                f"Rectangle profile does not support {field!r}.",
            )
        )
    for field in ("x", "y"):
        value = _number(profile.get(field))
        field_path = f"{path}/{field}"
        if value is None or value <= 0:
            issues.append(
                _issue(
                    "INVALID_PROFILE_DIMENSION",
                    field_path,
                    f"Rectangle {field} must be a positive finite number.",
                )
            )
        elif abs(value) > MAX_COORDINATE_MAGNITUDE:
            issues.append(
                _issue(
                    "COORDINATE_LIMIT_EXCEEDED",
                    field_path,
                    "Rectangle dimension exceeds the coordinate limit.",
                )
            )
    return issues


def _validate_polygon(
    profile: dict[str, Any], path: str
) -> list[ValidationIssue]:
    issues = [
        _issue(
            "UNSUPPORTED_PROFILE_FIELD",
            f"{path}/{field}",
            f"Polygon profile does not support {field!r}.",
        )
        for field in sorted(set(profile) - {"kind", "points"})
    ]
    points = profile.get("points")
    if not isinstance(points, list):
        issues.append(
            _issue(
                "INVALID_POLYGON_PROFILE",
                f"{path}/points",
                "Polygon points must be an array.",
            )
        )
        return issues
    if len(points) > MAX_PROFILE_POINTS:
        issues.append(
            _issue(
                "PROFILE_POINT_LIMIT_EXCEEDED",
                f"{path}/points",
                f"Polygon profile exceeds {MAX_PROFILE_POINTS} points.",
            )
        )
    if len(points) < 4 or points[0] != points[-1]:
        issues.append(
            _issue(
                "OPEN_POLYGON_PROFILE",
                f"{path}/points",
                "Polygon profile must contain a closed ring.",
            )
        )
    for index, point in enumerate(points):
        point_path = f"{path}/points/{index}"
        if not isinstance(point, list) or len(point) != 2:
            issues.append(
                _issue(
                    "INVALID_POLYGON_POINT",
                    point_path,
                    "Polygon point must contain two finite coordinates.",
                )
            )
            continue
        for coordinate_index, coordinate in enumerate(point):
            value = _number(coordinate)
            coordinate_path = f"{point_path}/{coordinate_index}"
            if value is None:
                issues.append(
                    _issue(
                        "INVALID_POLYGON_POINT",
                        coordinate_path,
                        "Polygon coordinate must be finite.",
                    )
                )
            elif abs(value) > MAX_COORDINATE_MAGNITUDE:
                issues.append(
                    _issue(
                        "COORDINATE_LIMIT_EXCEEDED",
                        coordinate_path,
                        "Polygon coordinate exceeds the coordinate limit.",
                    )
                )
    return issues


def validate_geometry(
    document: dict[str, Any],
) -> list[ValidationIssue]:
    registry = load_ifc2x3_registry()
    issues: list[ValidationIssue] = []

    for index, record in enumerate(document.get("entities", [])):
        ifc_class = record["ifc_class"]
        declaration = registry.declaration(ifc_class)
        base = f"/entities/{index}/attributes/Representation"
        representation = record["attributes"].get("Representation")
        if representation is None:
            if _requires_representation(ifc_class, declaration):
                issues.append(
                    _issue(
                        "MISSING_REPRESENTATION",
                        base,
                        f"{ifc_class} requires semantic geometry.",
                    )
                )
            continue
        if not isinstance(representation, dict):
            issues.append(
                _issue(
                    "INVALID_REPRESENTATION",
                    base,
                    "Representation must be an object.",
                )
            )
            continue
        if representation.get("kind") != "extruded_profile":
            issues.append(
                _issue(
                    "UNSUPPORTED_GEOMETRY_KIND",
                    f"{base}/kind",
                    "Formal BIM JSON supports only extruded_profile geometry.",
                )
            )
            continue
        for field in sorted(
            set(representation) - {"kind", "profile", "depth", "direction"}
        ):
            issues.append(
                _issue(
                    "UNSUPPORTED_GEOMETRY_FIELD",
                    f"{base}/{field}",
                    f"Extruded profile does not support {field!r}.",
                )
            )

        depth = _number(representation.get("depth"))
        if depth is None or depth <= 0:
            issues.append(
                _issue(
                    "INVALID_EXTRUSION_DEPTH",
                    f"{base}/depth",
                    "Extrusion depth must be a positive finite number.",
                )
            )
        elif depth > MAX_COORDINATE_MAGNITUDE:
            issues.append(
                _issue(
                    "COORDINATE_LIMIT_EXCEEDED",
                    f"{base}/depth",
                    "Extrusion depth exceeds the coordinate limit.",
                )
            )

        direction = representation.get("direction")
        if (
            not isinstance(direction, list)
            or len(direction) != 3
            or any(_number(item) is None for item in direction)
            or math.sqrt(sum(float(item) ** 2 for item in direction))
            <= VECTOR_TOLERANCE
        ):
            issues.append(
                _issue(
                    "INVALID_EXTRUSION_DIRECTION",
                    f"{base}/direction",
                    "Extrusion direction must be a non-zero finite 3D vector.",
                )
            )

        profile = representation.get("profile")
        profile_path = f"{base}/profile"
        if not isinstance(profile, dict):
            issues.append(
                _issue(
                    "INVALID_PROFILE",
                    profile_path,
                    "Extrusion profile must be an object.",
                )
            )
            continue
        profile_kind = profile.get("kind")
        if profile_kind == "rectangle":
            issues.extend(_validate_rectangle(profile, profile_path))
        elif profile_kind == "polygon":
            issues.extend(_validate_polygon(profile, profile_path))
        else:
            issues.append(
                _issue(
                    "UNSUPPORTED_PROFILE_KIND",
                    f"{profile_path}/kind",
                    "Profile kind must be rectangle or polygon.",
                )
            )

    return issues
