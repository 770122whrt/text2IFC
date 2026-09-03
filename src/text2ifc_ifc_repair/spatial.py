"""IFC spatial facts derived without benchmark or mutation ground truth."""

from __future__ import annotations

import math
from typing import Any

import ifcopenshell.util.placement
import ifcopenshell.util.unit

from .geometry import product_geometry_bounds_in_host_mm


MAX_OPENING_CONTEXT_STOREY_OFFSET_MM = 1000.0


def resolve_opening_storey(opening: Any, wall: Any) -> Any:
    """Resolve the host-wall spatial context at the retained Opening height.

    A normal single-storey wall inherits its one direct container.  Some IFC2X3
    authoring tools model one wall across several storeys while keeping only a
    base-storey containment relation.  When the retained Opening base is within
    one metre of another same-building Storey elevation, that elevation is the
    more specific host context.  Missing, conflicting, or equidistant evidence
    fails closed.
    """

    wall_storeys = [
        relation.RelatingStructure
        for relation in wall.ContainedInStructure
        if relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if not wall_storeys:
        raise ValueError(f"OPENING_HOST_STOREY_NOT_FOUND:{wall.GlobalId}")
    if len(wall_storeys) != 1:
        raise ValueError(f"OPENING_HOST_STOREY_AMBIGUOUS:{wall.GlobalId}")
    parent = _aggregate_parent(wall_storeys[0])
    candidates = [
        storey
        for storey in opening.file.by_type("IfcBuildingStorey")
        if _aggregate_parent(storey) == parent
    ]
    if not candidates:
        raise ValueError(f"OPENING_STOREY_NOT_FOUND:{opening.GlobalId}")
    scale_mm = _millimetres_per_project_unit(opening)
    opening_matrix = ifcopenshell.util.placement.get_local_placement(
        opening.ObjectPlacement
    )
    opening_local_bounds = product_geometry_bounds_in_host_mm(
        opening, opening
    )
    opening_base_mm = (
        float(opening_matrix[2, 3]) * scale_mm
        + float(opening_local_bounds["z"][0])
    )
    ranked = sorted(
        (
            (
                abs(
                    _storey_world_elevation_mm(storey)
                    - opening_base_mm
                ),
                str(storey.GlobalId),
                storey,
            )
            for storey in candidates
        ),
        key=lambda item: (item[0], item[1]),
    )
    if len(ranked) > 1 and math.isclose(
        ranked[0][0], ranked[1][0], abs_tol=1e-6
    ):
        raise ValueError(f"OPENING_STOREY_AMBIGUOUS:{opening.GlobalId}")
    direct_storey = wall_storeys[0]
    nearest_offset, _, nearest_storey = ranked[0]
    if (
        nearest_storey != direct_storey
        and nearest_offset > MAX_OPENING_CONTEXT_STOREY_OFFSET_MM
    ):
        return direct_storey
    return nearest_storey


def _aggregate_parent(element: Any) -> Any | None:
    parents = [
        relation.RelatingObject
        for relation in getattr(element, "Decomposes", ())
    ]
    return parents[0] if len(parents) == 1 else None


def _storey_world_elevation_mm(storey: Any) -> float:
    matrix = ifcopenshell.util.placement.get_local_placement(
        storey.ObjectPlacement
    )
    return float(matrix[2, 3]) * _millimetres_per_project_unit(storey)


def _millimetres_per_project_unit(entity: Any) -> float:
    return (
        float(ifcopenshell.util.unit.calculate_unit_scale(entity.file))
        * 1000.0
    )


__all__ = [
    "MAX_OPENING_CONTEXT_STOREY_OFFSET_MM",
    "resolve_opening_storey",
]
