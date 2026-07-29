"""IFC-native geometry facts shared by repair operation adapters."""

from __future__ import annotations

import math
from typing import Any

import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit


UNSUPPORTED_WALL_GEOMETRY = "UNSUPPORTED_WALL_GEOMETRY"


def straight_wall_axis(wall: Any) -> tuple[list[float], list[float]]:
    """Return one two-point wall Axis or reject unsupported geometry."""

    representations = getattr(
        getattr(wall, "Representation", None), "Representations", ()
    )
    axes = [
        representation
        for representation in representations
        if representation.RepresentationIdentifier == "Axis"
    ]
    if len(axes) != 1 or len(axes[0].Items) != 1:
        raise ValueError(UNSUPPORTED_WALL_GEOMETRY)
    curve = axes[0].Items[0]
    if not curve.is_a("IfcPolyline") or len(curve.Points) != 2:
        raise ValueError(UNSUPPORTED_WALL_GEOMETRY)
    points: list[list[float]] = []
    for point in curve.Points:
        coordinates = [float(value) for value in point.Coordinates]
        while len(coordinates) < 3:
            coordinates.append(0.0)
        points.append(coordinates)
    if math.dist(points[0], points[1]) <= 0:
        raise ValueError(UNSUPPORTED_WALL_GEOMETRY)
    return points[0], points[1]


def wall_dimensions_mm(wall: Any) -> dict[str, float]:
    """Measure length, normal thickness and vertical height in wall-local axes."""

    start, end = straight_wall_axis(wall)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_project_units = math.hypot(dx, dy)
    millimetres_per_project_unit = (
        ifcopenshell.util.unit.calculate_unit_scale(wall.file) * 1000.0
    )
    length = length_project_units * millimetres_per_project_unit
    direction = (dx / length_project_units, dy / length_project_units)
    normal = (-direction[1], direction[0])
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), wall)
    vertices = shape.geometry.verts
    points_mm = [
        (
            float(vertices[index]) * 1000.0,
            float(vertices[index + 1]) * 1000.0,
            float(vertices[index + 2]) * 1000.0,
        )
        for index in range(0, len(vertices), 3)
    ]
    normal_coordinates = [
        point[0] * normal[0] + point[1] * normal[1] for point in points_mm
    ]
    z_coordinates = [point[2] for point in points_mm]
    return {
        "length": length,
        "thickness": max(normal_coordinates) - min(normal_coordinates),
        "height": max(z_coordinates) - min(z_coordinates),
    }


def opening_dimensions_mm(opening: Any) -> dict[str, float]:
    """Measure an axis-aligned opening in its object-local coordinates."""

    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), opening)
    vertices = shape.geometry.verts
    axes = (vertices[0::3], vertices[1::3], vertices[2::3])
    extents = [
        _clean_mm((max(axis) - min(axis)) * 1000.0)
        for axis in axes
    ]
    return {"width": extents[0], "depth": extents[1], "height": extents[2]}


def opening_position_in_wall_mm(
    opening: Any,
    wall: Any,
) -> dict[str, Any]:
    """Measure the opening geometry in the host wall's local coordinate frame.

    IFC authoring tools may place an opening at an arbitrary geometry anchor.  In
    particular, the LargeBuilding sample places the target at its right edge, so
    the placement origin is not the opening centre.  Public repair coordinates
    therefore come from transformed geometry bounds, never from that origin.
    """

    unit_scale = ifcopenshell.util.unit.calculate_unit_scale(opening.file)
    millimetres_per_project_unit = unit_scale * 1000.0
    bounds = product_geometry_bounds_in_host_mm(opening, wall)
    center = [
        (bounds[axis_name][0] + bounds[axis_name][1]) / 2.0
        for axis_name in ("x", "y", "z")
    ]
    start, end = straight_wall_axis(wall)
    start = [value * millimetres_per_project_unit for value in start]
    end = [value * millimetres_per_project_unit for value in end]
    direction = [end[index] - start[index] for index in range(3)]
    length = math.sqrt(sum(value * value for value in direction))
    unit = [value / length for value in direction]
    delta = [center[index] - start[index] for index in range(3)]
    return {
        "center_offset": _clean_mm(
            sum(delta[index] * unit[index] for index in range(3))
        ),
        "normal_offset": _clean_mm(-delta[0] * unit[1] + delta[1] * unit[0]),
        "sill_height": bounds["z"][0],
        "geometry_bounds_mm": bounds,
    }


def product_geometry_bounds_in_host_mm(product: Any, host: Any) -> dict[str, list[float]]:
    """Transform one product's tessellated bounds into a host-local frame."""

    host_matrix = ifcopenshell.util.placement.get_local_placement(
        host.ObjectPlacement
    )
    product_matrix = ifcopenshell.util.placement.get_local_placement(
        product.ObjectPlacement
    )
    relative = _inverse_rigid_transform(host_matrix) @ product_matrix
    unit_scale = ifcopenshell.util.unit.calculate_unit_scale(product.file)
    millimetres_per_project_unit = unit_scale * 1000.0
    shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), product)
    vertices = shape.geometry.verts
    points_in_host_mm: list[list[float]] = []
    for index in range(0, len(vertices), 3):
        # IfcOpenShell tessellation coordinates are SI metres, while placement
        # matrices use project units. Convert before applying the placement.
        object_point = [
            float(vertices[index]) / unit_scale,
            float(vertices[index + 1]) / unit_scale,
            float(vertices[index + 2]) / unit_scale,
            1.0,
        ]
        host_point = relative @ object_point
        points_in_host_mm.append(
            [
                float(host_point[axis]) * millimetres_per_project_unit
                for axis in range(3)
            ]
        )
    if not points_in_host_mm:
        raise ValueError("PRODUCT_GEOMETRY_EMPTY")
    return {
        axis_name: [
            _clean_mm(min(point[axis] for point in points_in_host_mm)),
            _clean_mm(max(point[axis] for point in points_in_host_mm)),
        ]
        for axis, axis_name in enumerate(("x", "y", "z"))
    }


def _clean_mm(value: float) -> float:
    """Remove tessellation noise while preserving sub-millimetre coordinates."""

    rounded = round(float(value), 6)
    return 0.0 if rounded == -0.0 else rounded


def _inverse_rigid_transform(matrix: Any) -> Any:
    # Ifc placements are rigid transforms. Using the transpose avoids a general
    # matrix dependency and keeps project-unit coordinates unchanged.
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse
