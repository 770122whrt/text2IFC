"""Deterministic Door-to-Opening placement and geometric L1 evidence."""

from __future__ import annotations

import math
from typing import Any, Mapping

import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import (
    product_geometry_bounds_in_host_mm,
    product_local_geometry_bounds_mm,
)


MIN_PROJECTED_OVERLAP_RATIO = 0.95
MAX_CENTER_DEVIATION_MM = 5.0
MAX_AXIS_DEVIATION_DEGREES = 0.1
MAX_DIMENSION_DEVIATION_MM = 1.0


def select_door_placement_in_opening(
    door: Any,
    opening: Any,
) -> dict[str, Any]:
    """Choose the canonical 0/180-degree placement that best fills Opening.

    Reused IFC2X3 DoorStyle maps do not share one geometry-origin convention.
    The choice is therefore derived from the surviving Opening and the mapped
    Door representation, never from a deleted occurrence or benchmark model.
    """

    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    local_bounds = product_local_geometry_bounds_mm(door)
    opening_center_y = _center(opening_bounds["y"])
    width_mm = _millimetres(door, float(door.OverallWidth))
    height_mm = _millimetres(door, float(door.OverallHeight))
    candidates = []
    for sign in (1.0, -1.0):
        rotated_center_y = sign * _center(local_bounds["y"])
        location_y = opening_center_y - rotated_center_y
        location_z = opening_bounds["z"][0] - local_bounds["z"][0]
        nominal_edge_x = (
            opening_bounds["x"][0]
            if sign > 0
            else opening_bounds["x"][1]
        )
        geometry_centered_x = (
            _center(opening_bounds["x"])
            - sign * _center(local_bounds["x"])
        )
        for placement_kind, location_x in (
            ("nominal_edge", nominal_edge_x),
            ("geometry_center", geometry_centered_x),
        ):
            actual_bounds = _placed_axis_aligned_bounds(
                local_bounds,
                sign=sign,
                location_mm=(location_x, location_y, location_z),
            )
            nominal_bounds = {
                "x": sorted((location_x, location_x + sign * width_mm)),
                "y": [location_y, location_y],
                "z": [location_z, location_z + height_mm],
            }
            diagnostics = _alignment_diagnostics(
                door_bounds=actual_bounds,
                opening_bounds=opening_bounds,
                nominal_bounds=nominal_bounds,
                axis_deviation_degrees=0.0,
            )
            candidates.append(
                {
                    "sign": sign,
                    "placement_kind": placement_kind,
                    "location_mm": (location_x, location_y, location_z),
                    "diagnostics": diagnostics,
                }
            )
    selected = max(
        candidates,
        key=lambda item: (
            item["diagnostics"]["valid"],
            item["diagnostics"]["projected_overlap_ratio"],
            -item["diagnostics"]["geometry_placement_excess_mm"],
            -item["diagnostics"]["geometry_center_deviation_mm"],
            item["placement_kind"] == "geometry_center",
            item["sign"],
        ),
    )
    return {
        "location": tuple(
            _project_units(opening, value)
            for value in selected["location_mm"]
        ),
        "ref_direction": (selected["sign"], 0.0, 0.0),
        "diagnostics": selected["diagnostics"],
    }


def measure_door_opening_alignment(
    door: Any,
    opening: Any,
) -> dict[str, Any]:
    """Measure actual and nominal Door envelopes in Opening-local axes."""

    door_bounds = product_geometry_bounds_in_host_mm(door, opening)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    relative = _relative_placement(door, opening)
    width_mm = _millimetres(door, float(door.OverallWidth))
    height_mm = _millimetres(door, float(door.OverallHeight))
    nominal_points = []
    for x in (0.0, _project_units(door, width_mm)):
        for z in (0.0, _project_units(door, height_mm)):
            point = relative @ [x, 0.0, z, 1.0]
            nominal_points.append(
                [
                    float(point[axis]) * _millimetres_per_project_unit(door)
                    for axis in range(3)
                ]
            )
    nominal_bounds = {
        axis_name: [
            min(point[axis] for point in nominal_points),
            max(point[axis] for point in nominal_points),
        ]
        for axis, axis_name in enumerate(("x", "y", "z"))
    }
    return _alignment_diagnostics(
        door_bounds=door_bounds,
        opening_bounds=opening_bounds,
        nominal_bounds=nominal_bounds,
        axis_deviation_degrees=_axis_deviation_degrees(relative),
    )


def _alignment_diagnostics(
    *,
    door_bounds: Mapping[str, list[float]],
    opening_bounds: Mapping[str, list[float]],
    nominal_bounds: Mapping[str, list[float]],
    axis_deviation_degrees: float,
) -> dict[str, Any]:
    intersection_x = _intersection_length(
        door_bounds["x"], opening_bounds["x"]
    )
    intersection_y = _intersection_length(
        door_bounds["y"], opening_bounds["y"]
    )
    intersection_z = _intersection_length(
        door_bounds["z"], opening_bounds["z"]
    )
    door_face_area = _extent(door_bounds["x"]) * _extent(door_bounds["z"])
    opening_face_area = (
        _extent(opening_bounds["x"]) * _extent(opening_bounds["z"])
    )
    overlap_denominator = min(door_face_area, opening_face_area)
    projected_overlap = (
        0.0
        if overlap_denominator <= 0.0
        else intersection_x * intersection_z / overlap_denominator
    )
    nominal_center_deviation = math.hypot(
        _center(nominal_bounds["x"]) - _center(opening_bounds["x"]),
        _center(nominal_bounds["z"]) - _center(opening_bounds["z"]),
    )
    geometry_center_deviation = math.sqrt(
        sum(
            (
                _center(door_bounds[axis])
                - _center(opening_bounds[axis])
            )
            ** 2
            for axis in ("x", "y", "z")
        )
    )
    geometry_center_by_axis = {
        axis: abs(
            _center(door_bounds[axis])
            - _center(opening_bounds[axis])
        )
        for axis in ("x", "y", "z")
    }
    geometry_base_deviation = abs(
        float(door_bounds["z"][0]) - float(opening_bounds["z"][0])
    )
    geometry_placement_excess = max(
        0.0,
        geometry_center_by_axis["x"] - MAX_CENTER_DEVIATION_MM,
        geometry_center_by_axis["y"] - MAX_CENTER_DEVIATION_MM,
        geometry_base_deviation - MAX_CENTER_DEVIATION_MM,
    )
    width_deviation = abs(
        _extent(nominal_bounds["x"]) - _extent(opening_bounds["x"])
    )
    height_deviation = abs(
        _extent(nominal_bounds["z"]) - _extent(opening_bounds["z"])
    )
    valid = (
        projected_overlap >= MIN_PROJECTED_OVERLAP_RATIO
        and intersection_y > 0.0
        and geometry_placement_excess <= 0.0
        and axis_deviation_degrees <= MAX_AXIS_DEVIATION_DEGREES
        and width_deviation <= MAX_DIMENSION_DEVIATION_MM
        and height_deviation <= MAX_DIMENSION_DEVIATION_MM
    )
    return {
        "valid": valid,
        "projected_overlap_ratio": round(projected_overlap, 6),
        "normal_axis_intersection_mm": round(intersection_y, 6),
        "nominal_center_deviation_mm": round(
            nominal_center_deviation, 6
        ),
        "geometry_center_deviation_mm": round(
            geometry_center_deviation, 6
        ),
        "geometry_center_deviation_by_axis_mm": {
            axis: round(value, 6)
            for axis, value in geometry_center_by_axis.items()
        },
        "geometry_base_deviation_mm": round(
            geometry_base_deviation, 6
        ),
        "geometry_placement_excess_mm": round(
            geometry_placement_excess, 6
        ),
        "axis_deviation_degrees": round(axis_deviation_degrees, 6),
        "width_deviation_mm": round(width_deviation, 6),
        "height_deviation_mm": round(height_deviation, 6),
        "door_bounds_in_opening_mm": _rounded_bounds(door_bounds),
        "opening_bounds_mm": _rounded_bounds(opening_bounds),
        "nominal_door_bounds_mm": _rounded_bounds(nominal_bounds),
        "thresholds": {
            "minimum_projected_overlap_ratio": (
                MIN_PROJECTED_OVERLAP_RATIO
            ),
            "maximum_center_deviation_mm": MAX_CENTER_DEVIATION_MM,
            "maximum_axis_deviation_degrees": (
                MAX_AXIS_DEVIATION_DEGREES
            ),
            "maximum_dimension_deviation_mm": (
                MAX_DIMENSION_DEVIATION_MM
            ),
        },
    }


def _relative_placement(product: Any, host: Any) -> Any:
    host_matrix = ifcopenshell.util.placement.get_local_placement(
        host.ObjectPlacement
    )
    product_matrix = ifcopenshell.util.placement.get_local_placement(
        product.ObjectPlacement
    )
    return _inverse_rigid_transform(host_matrix) @ product_matrix


def _axis_deviation_degrees(relative: Any) -> float:
    x_axis = [float(relative[index, 0]) for index in range(3)]
    z_axis = [float(relative[index, 2]) for index in range(3)]
    x_norm = math.sqrt(sum(value * value for value in x_axis))
    z_norm = math.sqrt(sum(value * value for value in z_axis))
    if x_norm <= 0.0 or z_norm <= 0.0:
        return 180.0
    x_deviation = math.degrees(
        math.acos(min(1.0, max(-1.0, abs(x_axis[0] / x_norm))))
    )
    z_deviation = math.degrees(
        math.acos(min(1.0, max(-1.0, z_axis[2] / z_norm)))
    )
    return max(x_deviation, z_deviation)


def _placed_axis_aligned_bounds(
    bounds: Mapping[str, list[float]],
    *,
    sign: float,
    location_mm: tuple[float, float, float],
) -> dict[str, list[float]]:
    transformed = []
    for x in bounds["x"]:
        for y in bounds["y"]:
            for z in bounds["z"]:
                transformed.append(
                    (
                        location_mm[0] + sign * x,
                        location_mm[1] + sign * y,
                        location_mm[2] + z,
                    )
                )
    return {
        axis_name: [
            min(point[axis] for point in transformed),
            max(point[axis] for point in transformed),
        ]
        for axis, axis_name in enumerate(("x", "y", "z"))
    }


def _inverse_rigid_transform(matrix: Any) -> Any:
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse


def _intersection_length(
    first: list[float], second: list[float]
) -> float:
    return max(0.0, min(first[1], second[1]) - max(first[0], second[0]))


def _extent(interval: list[float]) -> float:
    return max(0.0, float(interval[1]) - float(interval[0]))


def _center(interval: list[float]) -> float:
    return (float(interval[0]) + float(interval[1])) / 2.0


def _millimetres_per_project_unit(entity: Any) -> float:
    return (
        float(ifcopenshell.util.unit.calculate_unit_scale(entity.file))
        * 1000.0
    )


def _millimetres(entity: Any, project_units: float) -> float:
    return project_units * _millimetres_per_project_unit(entity)


def _project_units(entity: Any, millimetres: float) -> float:
    return millimetres / _millimetres_per_project_unit(entity)


def _rounded_bounds(
    bounds: Mapping[str, list[float]],
) -> dict[str, list[float]]:
    return {
        axis: [round(float(value), 6) for value in bounds[axis]]
        for axis in ("x", "y", "z")
    }


__all__ = [
    "MAX_AXIS_DEVIATION_DEGREES",
    "MAX_CENTER_DEVIATION_MM",
    "MAX_DIMENSION_DEVIATION_MM",
    "MIN_PROJECTED_OVERLAP_RATIO",
    "measure_door_opening_alignment",
    "select_door_placement_in_opening",
]
