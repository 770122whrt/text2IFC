"""Parent-relative IfcLocalPlacement extraction."""

from __future__ import annotations

from typing import Any


def _direction(value, default: tuple[float, float, float]) -> list[float]:
    if value is None:
        return list(default)
    ratios = list(value.DirectionRatios)
    if len(ratios) == 2:
        ratios.append(0.0)
    return [float(item) for item in ratios]


def local_position(axis_placement, length_factor: float) -> dict[str, Any]:
    coordinates = list(axis_placement.Location.Coordinates)
    if len(coordinates) == 2:
        coordinates.append(0.0)
    return {
        "origin": [float(item) * length_factor for item in coordinates],
        "axis": _direction(
            getattr(axis_placement, "Axis", None), (0.0, 0.0, 1.0)
        ),
        "ref_direction": _direction(
            getattr(axis_placement, "RefDirection", None), (1.0, 0.0, 0.0)
        ),
    }


def aggregate_parent(entity):
    for relation in getattr(entity, "Decomposes", ()) or ():
        parent = getattr(relation, "RelatingObject", None)
        if parent is not None:
            return parent
    for relation in getattr(entity, "ContainedInStructure", ()) or ():
        parent = getattr(relation, "RelatingStructure", None)
        if parent is not None:
            return parent
    return None


def extract_object_placement(
    entity,
    placement_owners: dict[int, str],
    entity_ids: dict[int, str],
    length_factor: float,
) -> dict[str, Any] | None:
    placement = getattr(entity, "ObjectPlacement", None)
    if placement is None or not placement.is_a("IfcLocalPlacement"):
        return None
    parent_id = None
    parent_placement = placement.PlacementRelTo
    if parent_placement is not None:
        parent_id = placement_owners.get(parent_placement.id())
    if parent_id is None:
        parent = aggregate_parent(entity)
        if parent is not None:
            parent_id = entity_ids.get(parent.id())
    if parent_id is None:
        return None
    result = local_position(placement.RelativePlacement, length_factor)
    result["relative_to"] = parent_id
    return result
