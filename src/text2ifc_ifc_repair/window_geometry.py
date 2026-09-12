"""Deterministic mapped Window placement inside a generated Opening."""

from __future__ import annotations

from collections import Counter
from typing import Any

import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import (
    product_geometry_bounds_in_host_mm,
    product_local_geometry_bounds_mm,
)


def select_window_placement_in_opening(
    window: Any,
    opening: Any,
    window_type: Any,
) -> dict[str, Any]:
    """Place reused mapped geometry using surviving same-Type orientation.

    IFC2X3 WindowStyle maps may be anchored to either wall face and may use a
    180-degree occurrence rotation. The Type map alone does not record that
    occurrence convention. Surviving occurrences of the same Type are public
    repair-input evidence, so their opening-relative rotation is used without
    consulting the deleted occurrence or pristine benchmark model.
    """

    local_bounds = product_local_geometry_bounds_mm(window)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    votes = _surviving_orientation_votes(window, window_type)
    if votes:
        counts = Counter(votes)
        highest = max(counts.values())
        winners = sorted(
            sign for sign, count in counts.items() if count == highest
        )
        if len(winners) != 1:
            raise ValueError("WINDOW_TYPE_PLACEMENT_ORIENTATION_AMBIGUOUS")
        sign = winners[0]
        source = "surviving_same_type_occurrences"
    else:
        # Preserve the historical deterministic orientation when no surviving
        # same-Type occurrence exposes the authoring convention.
        sign = 1.0
        source = "deterministic_positive_orientation_fallback"

    if source == "deterministic_positive_orientation_fallback":
        location_mm = (0.0, opening_bounds["y"][0], 0.0)
        return {
            "location": tuple(
                _project_units(opening, value) for value in location_mm
            ),
            "location_mm": location_mm,
            "ref_direction": (sign, 0.0, 0.0),
            "orientation_source": source,
            "orientation_votes": votes,
        }

    transformed_x = sorted(sign * value for value in local_bounds["x"])
    transformed_y = sorted(sign * value for value in local_bounds["y"])
    location_x = _center(opening_bounds["x"]) - _center(transformed_x)
    if sign > 0.0:
        location_y = opening_bounds["y"][1] - transformed_y[1]
    else:
        location_y = opening_bounds["y"][0] - transformed_y[0]
    location_z = opening_bounds["z"][0] - local_bounds["z"][0]
    location_mm = (location_x, location_y, location_z)
    return {
        "location": tuple(
            _project_units(opening, value) for value in location_mm
        ),
        "location_mm": location_mm,
        "ref_direction": (sign, 0.0, 0.0),
        "orientation_source": source,
        "orientation_votes": votes,
    }


def _surviving_orientation_votes(
    new_window: Any,
    window_type: Any,
) -> list[float]:
    votes: list[float] = []
    seen: set[int] = set()
    for relation in getattr(window_type, "ObjectTypeOf", ()) or ():
        for peer in relation.RelatedObjects:
            if (
                peer == new_window
                or not peer.is_a("IfcWindow")
                or peer.id() in seen
            ):
                continue
            fills = [
                item
                for item in getattr(peer, "FillsVoids", ()) or ()
                if item.is_a("IfcRelFillsElement")
            ]
            if len(fills) != 1:
                continue
            relative = _relative_placement(
                peer, fills[0].RelatingOpeningElement
            )
            sign = _canonical_half_turn_sign(relative)
            if sign is not None:
                seen.add(peer.id())
                votes.append(sign)
    return votes


def _relative_placement(product: Any, host: Any) -> Any:
    host_matrix = ifcopenshell.util.placement.get_local_placement(
        host.ObjectPlacement
    )
    product_matrix = ifcopenshell.util.placement.get_local_placement(
        product.ObjectPlacement
    )
    return _inverse_rigid_transform(host_matrix) @ product_matrix


def _canonical_half_turn_sign(relative: Any) -> float | None:
    tolerance = 1e-6
    sign = 1.0 if float(relative[0, 0]) >= 0.0 else -1.0
    expected = (
        (sign, 0.0, 0.0),
        (0.0, sign, 0.0),
        (0.0, 0.0, 1.0),
    )
    for row in range(3):
        for column in range(3):
            if (
                abs(float(relative[row, column]) - expected[row][column])
                > tolerance
            ):
                return None
    return sign


def _inverse_rigid_transform(matrix: Any) -> Any:
    inverse = matrix.copy()
    rotation = matrix[:3, :3]
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -(rotation.T @ matrix[:3, 3])
    inverse[3, :] = (0.0, 0.0, 0.0, 1.0)
    return inverse


def _center(interval: list[float]) -> float:
    return (float(interval[0]) + float(interval[1])) / 2.0


def _project_units(entity: Any, millimetres: float) -> float:
    millimetres_per_project_unit = (
        float(ifcopenshell.util.unit.calculate_unit_scale(entity.file))
        * 1000.0
    )
    return millimetres / millimetres_per_project_unit


__all__ = ["select_window_placement_in_opening"]
