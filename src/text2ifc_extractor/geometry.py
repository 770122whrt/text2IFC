"""Semantic extrusion extraction with explicit unsupported geometry losses."""

from __future__ import annotations

import math
from typing import Any

from .placement import local_position


_LOSS_KIND = {
    "IfcMappedItem": "MAPPED_GEOMETRY",
    "IfcBooleanClippingResult": "BOOLEAN_GEOMETRY",
    "IfcBooleanResult": "BOOLEAN_GEOMETRY",
    "IfcFacetedBrep": "FACETED_BREP_GEOMETRY",
    "IfcFaceBasedSurfaceModel": "SURFACE_GEOMETRY",
    "IfcShellBasedSurfaceModel": "SURFACE_GEOMETRY",
}


def geometry_loss_kind(ifc_class: str) -> str:
    return _LOSS_KIND.get(ifc_class, "UNSUPPORTED_GEOMETRY")


def _profile_point(point, factor: float) -> list[float]:
    coordinates = list(point.Coordinates)
    return [float(coordinates[0]) * factor, float(coordinates[1]) * factor]


def _profile_basis(position) -> tuple[list[float], list[float]]:
    if position is None:
        return [0.0, 0.0], [1.0, 0.0]
    origin = list(position.Location.Coordinates)
    ref = (
        list(position.RefDirection.DirectionRatios)
        if position.RefDirection is not None
        else [1.0, 0.0]
    )
    magnitude = math.hypot(ref[0], ref[1])
    return [float(origin[0]), float(origin[1])], [
        float(ref[0]) / magnitude,
        float(ref[1]) / magnitude,
    ]


def _transform_profile_points(
    points: list[list[float]], position, factor: float
) -> list[list[float]]:
    origin, x_axis = _profile_basis(position)
    y_axis = [-x_axis[1], x_axis[0]]
    return [
        [
            (origin[0] + x_axis[0] * x + y_axis[0] * y) * factor,
            (origin[1] + x_axis[1] * x + y_axis[1] * y) * factor,
        ]
        for x, y in points
    ]


def _profile(area, factor: float) -> dict[str, Any] | None:
    position = getattr(area, "Position", None)
    if area.is_a("IfcRectangleProfileDef"):
        x_dim = float(area.XDim)
        y_dim = float(area.YDim)
        origin, x_axis = _profile_basis(position)
        if (
            abs(origin[0]) < 1e-12
            and abs(origin[1]) < 1e-12
            and abs(x_axis[0] - 1.0) < 1e-12
            and abs(x_axis[1]) < 1e-12
        ):
            return {
                "kind": "rectangle",
                "x": x_dim * factor,
                "y": y_dim * factor,
            }
        corners = [
            [-x_dim / 2.0, -y_dim / 2.0],
            [x_dim / 2.0, -y_dim / 2.0],
            [x_dim / 2.0, y_dim / 2.0],
            [-x_dim / 2.0, y_dim / 2.0],
            [-x_dim / 2.0, -y_dim / 2.0],
        ]
        return {
            "kind": "polygon",
            "points": _transform_profile_points(corners, position, factor),
        }
    if area.is_a("IfcArbitraryClosedProfileDef"):
        curve = area.OuterCurve
        if not curve.is_a("IfcPolyline"):
            return None
        raw = [
            [float(point.Coordinates[0]), float(point.Coordinates[1])]
            for point in curve.Points
        ]
        return {
            "kind": "polygon",
            "points": _transform_profile_points(raw, position, factor),
        }
    return None


def extract_extrusion(item, length_factor: float) -> dict[str, Any] | None:
    if not item.is_a("IfcExtrudedAreaSolid"):
        return None
    profile = _profile(item.SweptArea, length_factor)
    if profile is None:
        return None
    direction = [float(value) for value in item.ExtrudedDirection.DirectionRatios]
    if len(direction) == 2:
        direction.append(0.0)
    return {
        "kind": "extruded_profile",
        "profile": profile,
        "depth": float(item.Depth) * length_factor,
        "direction": direction,
        "position": local_position(item.Position, length_factor),
    }


def representation_items(entity) -> list:
    representation = getattr(entity, "Representation", None)
    if representation is None:
        return []
    body_items = []
    for shape in representation.Representations or ():
        if shape.RepresentationIdentifier == "Body":
            body_items.extend(shape.Items or ())
    return body_items
