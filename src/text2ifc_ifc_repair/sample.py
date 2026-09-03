"""Read-only inventory for hash-bound IFC repair samples."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import ifcopenshell

from .geometry import opening_position_in_wall_mm, straight_wall_axis


FROZEN_COUNT_CLASSES = (
    "IfcProject",
    "IfcSite",
    "IfcBuilding",
    "IfcBuildingStorey",
    "IfcSpace",
    "IfcWall",
    "IfcOpeningElement",
    "IfcWindow",
    "IfcDoor",
    "IfcRelFillsElement",
    "IfcRelVoidsElement",
)


def inspect_sample(path: Path | str) -> dict[str, Any]:
    """Return stable identity and structural counts for one IFC artifact."""

    source = Path(path)
    model = ifcopenshell.open(str(source))
    return {
        "schema": model.schema,
        "size_bytes": source.stat().st_size,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "counts": {
            ifc_class: len(model.by_type(ifc_class))
            for ifc_class in FROZEN_COUNT_CLASSES
        },
    }


def inspect_target_chain(
    path: Path | str,
    *,
    wall_global_id: str,
    opening_global_id: str,
    window_global_id: str,
) -> dict[str, Any]:
    """Resolve and describe one Window-Opening-Wall relationship chain."""

    model = ifcopenshell.open(str(Path(path)))
    wall = _by_guid_or_none(model, wall_global_id)
    opening = _by_guid_or_none(model, opening_global_id)
    window = _by_guid_or_none(model, window_global_id)
    if wall is None or opening is None or window is None:
        raise ValueError("TARGET_CHAIN_NOT_FOUND")
    if not wall.is_a("IfcWall") or not opening.is_a("IfcOpeningElement") or not window.is_a("IfcWindow"):
        raise ValueError("TARGET_CHAIN_CLASS_MISMATCH")

    fills = [
        relation
        for relation in window.FillsVoids
        if relation.RelatingOpeningElement == opening
    ]
    voids = [
        relation
        for relation in opening.VoidsElements
        if relation.RelatingBuildingElement == wall
    ]
    if len(fills) != 1 or len(voids) != 1:
        raise ValueError("TARGET_CHAIN_RELATIONSHIP_MISMATCH")

    axis_start, axis_end = straight_wall_axis(wall)
    millimetres_per_project_unit = (
        ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    )
    axis_start_mm = [
        value * millimetres_per_project_unit for value in axis_start
    ]
    axis_end_mm = [
        value * millimetres_per_project_unit for value in axis_end
    ]
    storeys = [
        relation.RelatingStructure
        for relation in wall.ContainedInStructure
        if relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    if len(storeys) != 1:
        raise ValueError("TARGET_WALL_STOREY_AMBIGUOUS")

    relative_placement = opening.ObjectPlacement
    if relative_placement is None or relative_placement.PlacementRelTo != wall.ObjectPlacement:
        raise ValueError("TARGET_OPENING_NOT_WALL_LOCAL")
    local_origin = [
        float(value) * millimetres_per_project_unit
        for value in relative_placement.RelativePlacement.Location.Coordinates
    ]
    while len(local_origin) < 3:
        local_origin.append(0.0)
    opening_position = opening_position_in_wall_mm(opening, wall)

    return {
        "wall": {
            "ifc_class": wall.is_a(),
            "step_id": wall.id(),
            "global_id": wall.GlobalId,
            "name": wall.Name,
            "storey": storeys[0].Name,
            "geometry_capability": "straight_wall",
            "axis_start_mm": axis_start_mm,
            "axis_end_mm": axis_end_mm,
            "length_mm": math.dist(axis_start_mm, axis_end_mm),
            "local_reference": "wall_local_start",
        },
        "opening": {
            "ifc_class": opening.is_a(),
            "step_id": opening.id(),
            "global_id": opening.GlobalId,
            "wall_local_origin_mm": local_origin,
            "wall_local_geometry_bounds_mm": opening_position["geometry_bounds_mm"],
            "geometric_center_offset_mm": opening_position["center_offset"],
            "sill_height_mm": opening_position["sill_height"],
        },
        "window": {
            "ifc_class": window.is_a(),
            "step_id": window.id(),
            "global_id": window.GlobalId,
            "name": window.Name,
            "width_mm": (
                float(window.OverallWidth) * millimetres_per_project_unit
            ),
            "height_mm": (
                float(window.OverallHeight) * millimetres_per_project_unit
            ),
        },
        "relationships": {
            "fills_step_id": fills[0].id(),
            "voids_step_id": voids[0].id(),
        },
    }


def inspect_sample_capabilities(path: Path | str) -> dict[str, int]:
    """Classify walls and count complete Window-Opening-Wall chains."""

    model = ifcopenshell.open(str(Path(path)))
    straight_wall_count = 0
    unsupported_wall_count = 0
    for wall in model.by_type("IfcWall"):
        try:
            straight_wall_axis(wall)
        except ValueError as error:
            if str(error) != "UNSUPPORTED_WALL_GEOMETRY":
                raise
            unsupported_wall_count += 1
        else:
            straight_wall_count += 1

    valid_chain_count = 0
    for window in model.by_type("IfcWindow"):
        fills = list(window.FillsVoids)
        if len(fills) != 1:
            continue
        opening = fills[0].RelatingOpeningElement
        voids = list(opening.VoidsElements)
        if (
            len(voids) == 1
            and voids[0].RelatingBuildingElement.is_a("IfcWall")
        ):
            valid_chain_count += 1
    return {
        "straight_wall_count": straight_wall_count,
        "unsupported_wall_count": unsupported_wall_count,
        "valid_window_opening_wall_chain_count": valid_chain_count,
    }


def _by_guid_or_none(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(global_id)
    except RuntimeError:
        return None
