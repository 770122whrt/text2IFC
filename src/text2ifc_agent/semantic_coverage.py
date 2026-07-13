"""Semantic coverage helpers for Design Brief to BIM JSON acceptance."""

from __future__ import annotations

from math import hypot
import re
from typing import Any, Mapping


ACCEPTED_COVERAGE_STATES = {"represented", "compiler_generated", "waived_by_user"}
BLOCKING_COVERAGE_STATES = {"unsupported_draft", "blocked_unknown_capability"}


def build_design_geometry_expectation(
    *,
    case_id: str,
    design_brief: Mapping[str, Any],
    expected_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive checkable geometry only from confirmed Design Brief facts."""
    known = design_brief.get("known_facts")
    known_facts = known if isinstance(known, Mapping) else {}
    building = known_facts.get("building")
    building_facts = building if isinstance(building, Mapping) else {}
    outer_bounds = (
        _plan_bounds(building_facts.get("outline"))
        or _polygon_plan_bounds_from_fact(building_facts.get("outline"))
        or _plan_bounds(building_facts.get("outer_bounds"))
    )
    wall_thickness = _number(building_facts.get("wall_thickness_mm"))
    slab_thickness = _number(building_facts.get("floor_slab_thickness_mm"))
    expected_storeys = {
        str(record.get("id")): record
        for record in _records(expected_facts.get("storeys"))
        if isinstance(record.get("id"), str)
    }
    raw_storeys = _records(known_facts.get("storeys"))
    design_storeys = {
        str(record.get("id")): record
        for record in raw_storeys
        if isinstance(record.get("id"), str)
    }
    design_space_paths: dict[str, str] = {}
    design_wall_paths: dict[str, str] = {}
    for storey_index, storey in enumerate(raw_storeys):
        for space_index, space in enumerate(_records(storey.get("spaces"))):
            space_id = _string(space.get("id"))
            if space_id is not None:
                design_space_paths[space_id] = (
                    f"/known_facts/storeys/{storey_index}/spaces/{space_index}"
                )
        for wall_index, wall in enumerate(_interior_walls(storey)):
            wall_id = _string(wall.get("id"))
            if wall_id is not None:
                design_wall_paths[wall_id] = (
                    f"/known_facts/storeys/{storey_index}/walls/interior/{wall_index}"
                )
    spaces: dict[str, dict[str, Any]] = {}
    space_sources: dict[
        str, tuple[tuple[float, float, float, float], str]
    ] = {}
    walls: dict[str, dict[str, Any]] = {}
    slabs: dict[str, dict[str, Any]] = {}
    roof: dict[str, dict[str, Any]] = {}
    stairs: dict[str, dict[str, Any]] = {}
    floor_openings: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []

    for space_index, space in enumerate(_records(expected_facts.get("spaces"))):
        space_id = _string(space.get("id"))
        storey_id = _string(space.get("storey"))
        bounds = _plan_bounds(space.get("bounds"))
        storey = expected_storeys.get(storey_id) if storey_id is not None else None
        design_storey = design_storeys.get(storey_id) if storey_id is not None else None
        elevation = _number(storey.get("elevation_mm")) if isinstance(storey, Mapping) else None
        height = _number(space.get("height_mm"))
        if height is None and isinstance(design_storey, Mapping):
            height = _number(design_storey.get("net_height_mm"))
        path = design_space_paths.get(space_id or "", f"/known_facts/spaces/{space_index}")
        if (
            space_id is None
            or storey_id is None
            or bounds is None
            or elevation is None
            or height is None
        ):
            unresolved.append(
                _unresolved_geometry(path=path, reason="space_geometry_missing")
            )
            continue
        spaces[space_id] = {
            "bbox": _bbox(
                bounds[0], bounds[1], bounds[2], bounds[3], elevation, elevation + height
            ),
            "storey_id": storey_id,
            "source_fact_refs": [path],
        }
        space_sources[space_id] = (bounds, path)

    explicit_slabs = _records(expected_facts.get("slabs"))
    for slab_index, slab in enumerate(explicit_slabs):
        slab_id = _string(slab.get("id"))
        top = _number(slab.get("top_elevation_mm"))
        thickness = _number(slab.get("thickness_mm"))
        storey_id = _string(slab.get("storey"))
        storey = expected_storeys.get(storey_id) if storey_id is not None else None
        if top is None and isinstance(storey, Mapping):
            top = _number(storey.get("elevation_mm"))
        if thickness is None:
            thickness = slab_thickness
        bounds = (
            _plan_bounds(slab.get("bounds"))
            or _polygon_plan_bounds_from_fact(slab.get("polygon"))
            or outer_bounds
        )
        path = f"/known_facts/floor_slabs/{slab_index}"
        if slab_id is None or top is None or thickness is None or bounds is None:
            unresolved.append(_unresolved_geometry(path=path, reason="floor_slab_geometry_missing"))
            continue
        slab_bbox = _bbox(
            bounds[0], bounds[1], bounds[2], bounds[3], top - thickness, top
        )
        slabs[slab_id] = {
            "bbox": slab_bbox,
            "datum": "slab_top",
            "source_fact_refs": [path],
        }
        openings = _records(slab.get("openings"))
        if isinstance(slab.get("opening"), Mapping):
            openings.insert(0, dict(slab["opening"]))
        for opening_index, opening in enumerate(openings):
            opening_bounds = _plan_bounds(opening.get("bounds"))
            if opening_bounds is not None:
                opening_id = _string(opening.get("id")) or (
                    f"opening-{slab_id}-stair"
                    if opening_index == 0
                    else f"opening-{slab_id}-stair-{opening_index + 1}"
                )
                floor_openings[opening_id] = {
                    "bbox": _bbox(
                        opening_bounds[0],
                        opening_bounds[1],
                        opening_bounds[2],
                        opening_bounds[3],
                        top - thickness,
                        top,
                    ),
                    "host_slab_id": slab_id,
                    "bbox_issue_code": "FLOOR_OPENING_BBOX_MISMATCH",
                    "source_fact_refs": [f"{path}/openings/{opening_index}"],
                }

    roof_record = expected_facts.get("roof")
    if isinstance(roof_record, Mapping):
        roof_id = _string(roof_record.get("id"))
        bottom = _number(roof_record.get("bottom_elevation_mm"))
        if bottom is None:
            bottom = _number(roof_record.get("elevation_mm"))
        thickness = _number(roof_record.get("thickness_mm"))
        bounds = (
            _plan_bounds(roof_record.get("bounds"))
            or _polygon_plan_bounds_from_fact(roof_record.get("polygon"))
            or outer_bounds
        )
        if roof_id is not None and bottom is not None and thickness is not None and bounds is not None:
            roof[roof_id] = {
                "bbox": _bbox(
                    bounds[0], bounds[1], bounds[2], bounds[3], bottom, bottom + thickness
                ),
                "datum": "roof_bottom",
                "source_fact_refs": ["/known_facts/roof_slab"],
            }

    for stair_index, stair in enumerate(_records(expected_facts.get("stairs"))):
        stair_id = _string(stair.get("id"))
        bounds = _plan_bounds(stair.get("bounds")) or _plan_bounds(
            stair.get("plan_bounds")
        )
        start = _number(stair.get("start_elevation_mm"))
        end = _number(stair.get("end_elevation_mm"))
        path = f"/known_facts/stairs/{stair_index}"
        if stair_id is None or bounds is None or start is None or end is None:
            unresolved.append(_unresolved_geometry(path=path, reason="stair_geometry_missing"))
            continue
        flight_ids = stair.get("flight_ids")
        if not isinstance(flight_ids, list) or not flight_ids:
            flight_ids = [stair_id.replace("stair-", "stair-flight-", 1)]
        stairs[stair_id] = {
            "flight_ids": [str(item) for item in flight_ids],
            "bbox": _bbox(bounds[0], bounds[1], bounds[2], bounds[3], start, end),
            "bbox_issue_code": "STAIR_BBOX_MISMATCH",
            "require_steps": True,
            "source_fact_refs": [path],
        }

    explicit_wall_ids: set[str] = set()
    for wall_index, wall in enumerate(_records(expected_facts.get("walls"))):
        wall_id = _string(wall.get("id"))
        if wall_id is not None:
            explicit_wall_ids.add(wall_id)
        storey_id = _string(wall.get("storey"))
        bounds = _wall_plan_bounds(wall)
        bbox_issue_code = "WALL_SEGMENT_MISMATCH"
        storey = expected_storeys.get(storey_id) if storey_id is not None else None
        elevation = _number(storey.get("elevation_mm")) if isinstance(storey, Mapping) else None
        height = _number(wall.get("height_mm"))
        if height is None and isinstance(storey, Mapping):
            height = _number(storey.get("net_height_mm"))
        path = design_wall_paths.get(wall_id or "", f"/known_facts/walls/{wall_index}")
        if wall_id is None or storey_id is None or elevation is None or height is None:
            unresolved.append(
                _unresolved_geometry(path=path, reason="explicit_wall_geometry_missing")
            )
            continue
        if bounds is None:
            connects = wall.get("connects")
            if isinstance(connects, list) and len(connects) == 2:
                source_a = space_sources.get(str(connects[0]))
                source_b = space_sources.get(str(connects[1]))
                segment = _shared_wall_segment(source_a, source_b)
                thickness = _number(wall.get("thickness_mm")) or wall_thickness
                if segment is not None and thickness is not None and thickness > 0:
                    bbox_issue_code = "INTERIOR_WALL_SHARED_BOUNDARY_MISMATCH"
                    axis, coordinate, start, end = segment
                    if axis == "x":
                        bounds = (
                            start,
                            end,
                            coordinate - thickness / 2,
                            coordinate + thickness / 2,
                        )
                    else:
                        bounds = (
                            coordinate - thickness / 2,
                            coordinate + thickness / 2,
                            start,
                            end,
                        )
                else:
                    unresolved.append(
                        _unresolved_geometry(
                            path=path,
                            reason="shared_boundary_not_unique_or_wall_thickness_missing",
                            source_fact_refs=[
                                source_a[1] if source_a is not None else "",
                                source_b[1] if source_b is not None else "",
                                path,
                            ],
                        )
                    )
                    continue
            else:
                continue
        x_span = bounds[1] - bounds[0]
        y_span = bounds[3] - bounds[2]
        walls[wall_id] = {
            "axis": "x" if x_span >= y_span else "y",
            "bbox": _bbox(
                bounds[0], bounds[1], bounds[2], bounds[3], elevation, elevation + height
            ),
            "bbox_issue_code": bbox_issue_code,
            "bbox_issue_path": f"/walls/{wall_id}",
            "source_fact_refs": [path],
        }

    for storey_index, storey in enumerate(raw_storeys):
        storey_id = _string(storey.get("id"))
        if storey_id is None or storey_id not in expected_storeys:
            unresolved.append(
                _unresolved_geometry(
                    path=f"/known_facts/storeys/{storey_index}",
                    reason="storey_id_not_confirmed_in_expected_facts",
                )
            )
            continue
        elevation = _number(storey.get("elevation_mm"))
        height = _number(storey.get("net_height_mm"))
        if elevation is None or height is None or height <= 0:
            unresolved.append(
                _unresolved_geometry(
                    path=f"/known_facts/storeys/{storey_index}",
                    reason="storey_elevation_or_net_height_missing",
                )
            )
            continue

        if not explicit_slabs and outer_bounds is not None and slab_thickness is not None and slab_thickness > 0:
            slabs[f"slab-{storey_id}-floor"] = {
                "bbox": _bbox(
                    outer_bounds[0],
                    outer_bounds[1],
                    outer_bounds[2],
                    outer_bounds[3],
                    elevation - slab_thickness,
                    elevation,
                ),
                "datum": "storey_slab_top",
                "source_fact_refs": [
                    "/known_facts/building/outer_bounds",
                    "/known_facts/building/floor_slab_thickness_mm",
                    f"/known_facts/storeys/{storey_index}/elevation_mm",
                ],
            }

        interior_walls = _interior_walls(storey)
        storey_spaces = _spaces_by_id(storey, storey_index=storey_index)
        for wall_index, wall in enumerate(interior_walls):
            wall_id = _string(wall.get("id"))
            if wall_id is not None and wall_id in explicit_wall_ids:
                continue
            connects = wall.get("connects")
            if isinstance(connects, list) and len(connects) == 2:
                from_id = _string(connects[0])
                to_id = _string(connects[1])
            else:
                from_id = _string(wall.get("from"))
                to_id = _string(wall.get("to"))
            path = f"/known_facts/storeys/{storey_index}/walls/interior/{wall_index}"
            if wall_id is None or from_id is None or to_id is None:
                unresolved.append(_unresolved_geometry(path=path, reason="interior_wall_identity_missing"))
                continue
            source_a = storey_spaces.get(from_id)
            source_b = storey_spaces.get(to_id)
            segment = _shared_wall_segment(source_a, source_b)
            if segment is None or wall_thickness is None or wall_thickness <= 0:
                unresolved.append(
                    _unresolved_geometry(
                        path=path,
                        reason="shared_boundary_not_unique_or_wall_thickness_missing",
                        source_fact_refs=[
                            source_a[1] if source_a is not None else "",
                            source_b[1] if source_b is not None else "",
                            path,
                        ],
                    )
                )
                continue
            axis, coordinate, start, end = segment
            if axis == "x":
                bbox = _bbox(start, end, coordinate - wall_thickness / 2, coordinate + wall_thickness / 2, elevation, elevation + height)
            else:
                bbox = _bbox(coordinate - wall_thickness / 2, coordinate + wall_thickness / 2, start, end, elevation, elevation + height)
            walls[wall_id] = {
                "axis": axis,
                "bbox": bbox,
                "bbox_issue_code": "INTERIOR_WALL_SHARED_BOUNDARY_MISMATCH",
                "bbox_issue_path": f"/walls/{wall_id}",
                "source_fact_refs": [source_a[1], source_b[1], path],
            }

    for slab in slabs.values():
        slab_bottom = slab["bbox"]["z"][0]
        slab["must_touch_walls"] = sorted(
            wall_id
            for wall_id, wall in walls.items()
            if abs(wall["bbox"]["z"][1] - slab_bottom) <= 0.000001
        )

    return {
        "schema_version": "text2ifc/design-geometry-expectation/1.0",
        "case_id": case_id,
        "source": "design_brief_expected_facts",
        "units": "METRE",
        "tolerance": 0.05,
        "complete": not unresolved,
        "spaces": spaces,
        "walls": walls,
        "slabs": slabs,
        "roof": roof,
        "stairs": stairs,
        "floor_openings": floor_openings,
        "unresolved": unresolved,
    }


def _records(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _plan_bounds(value: Any) -> tuple[float, float, float, float] | None:
    if isinstance(value, Mapping):
        x_range = value.get("x")
        y_range = value.get("y")
        if (
            isinstance(x_range, list)
            and len(x_range) == 2
            and isinstance(y_range, list)
            and len(y_range) == 2
        ):
            coordinates = tuple(
                _number(item) for item in (*x_range, *y_range)
            )
            if all(item is not None for item in coordinates):
                x_min, x_max, y_min, y_max = coordinates
                if x_min < x_max and y_min < y_max:
                    return (x_min, x_max, y_min, y_max)
        coordinates = tuple(
            _number(value.get(key)) for key in ("x_min", "x_max", "y_min", "y_max")
        )
        if all(item is not None for item in coordinates):
            x_min, x_max, y_min, y_max = coordinates
            if x_min < x_max and y_min < y_max:
                return (x_min, x_max, y_min, y_max)
    if not isinstance(value, str):
        return None
    match = re.fullmatch(
        r"\s*x\s*=\s*(-?\d+(?:\.\d+)?)\s*\.\.\s*(-?\d+(?:\.\d+)?)\s*,\s*y\s*=\s*(-?\d+(?:\.\d+)?)\s*\.\.\s*(-?\d+(?:\.\d+)?)\s*",
        value,
    )
    if match is None:
        return None
    x_min, x_max, y_min, y_max = (float(item) for item in match.groups())
    return (x_min, x_max, y_min, y_max) if x_min < x_max and y_min < y_max else None


def _polygon_plan_bounds_from_fact(
    value: Any,
) -> tuple[float, float, float, float] | None:
    if isinstance(value, Mapping):
        value = value.get("points")
    if not isinstance(value, list) or len(value) < 3:
        return None
    points: list[tuple[float, float]] = []
    for point in value:
        if not isinstance(point, list) or len(point) < 2:
            return None
        x = _number(point[0])
        y = _number(point[1])
        if x is None or y is None:
            return None
        points.append((x, y))
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    if x_min >= x_max or y_min >= y_max:
        return None
    return (x_min, x_max, y_min, y_max)


def _wall_plan_bounds(wall: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    explicit = _plan_bounds(wall.get("bounds"))
    if explicit is not None:
        return explicit
    start = wall.get("start_mm")
    end = wall.get("end_mm")
    thickness = _number(wall.get("thickness_mm"))
    if (
        not isinstance(start, list)
        or not isinstance(end, list)
        or len(start) < 2
        or len(end) < 2
        or thickness is None
        or thickness <= 0
    ):
        return None
    x1, y1 = _number(start[0]), _number(start[1])
    x2, y2 = _number(end[0]), _number(end[1])
    if None in {x1, y1, x2, y2}:
        return None
    half = thickness / 2
    if y1 == y2 and x1 != x2:
        return (min(x1, x2), max(x1, x2), y1 - half, y1 + half)
    if x1 == x2 and y1 != y2:
        return (x1 - half, x1 + half, min(y1, y2), max(y1, y2))
    return None


def _interior_walls(storey: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    walls = storey.get("walls")
    if not isinstance(walls, Mapping):
        return []
    return _records(walls.get("interior"))


def _spaces_by_id(
    storey: Mapping[str, Any],
    *,
    storey_index: int,
) -> dict[str, tuple[tuple[float, float, float, float], str]]:
    result: dict[str, tuple[tuple[float, float, float, float], str]] = {}
    for index, space in enumerate(_records(storey.get("spaces"))):
        space_id = _string(space.get("id"))
        bounds = _plan_bounds(space.get("bounds")) or _plan_bounds(
            space.get("bounding_box")
        )
        if space_id is not None and bounds is not None:
            result[space_id] = (
                bounds,
                f"/known_facts/storeys/{storey_index}/spaces/{index}",
            )
    return result


def _shared_wall_segment(
    left: tuple[tuple[float, float, float, float], str] | None,
    right: tuple[tuple[float, float, float, float], str] | None,
) -> tuple[str, float, float, float] | None:
    if left is None or right is None:
        return None
    left_bounds, _ = left
    right_bounds, _ = right
    left_x_min, left_x_max, left_y_min, left_y_max = left_bounds
    right_x_min, right_x_max, right_y_min, right_y_max = right_bounds
    if left_x_max == right_x_min or right_x_max == left_x_min:
        start, end = max(left_y_min, right_y_min), min(left_y_max, right_y_max)
        if start < end:
            coordinate = left_x_max if left_x_max == right_x_min else right_x_max
            return ("y", coordinate, start, end)
    if left_y_max == right_y_min or right_y_max == left_y_min:
        start, end = max(left_x_min, right_x_min), min(left_x_max, right_x_max)
        if start < end:
            coordinate = left_y_max if left_y_max == right_y_min else right_y_max
            return ("x", coordinate, start, end)
    return None


def _unresolved_geometry(
    *,
    path: str,
    reason: str,
    source_fact_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "path": path,
        "reason": reason,
        "source_fact_refs": [item for item in source_fact_refs or [] if item],
    }


def evaluate_semantic_coverage(
    *,
    case_id: str,
    design_brief: Mapping[str, Any],
    candidate: Mapping[str, Any],
    capability_profile: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify explicit Design Brief facts against current generation support."""
    facts: list[dict[str, Any]] = []
    unsupported = _unsupported_by_path(capability_profile)
    for path, value in _known_fact_leaves(design_brief):
        unsupported_record = unsupported.get(path)
        if _is_waived(design_brief, path):
            coverage_state = "waived_by_user"
            reason = "User explicitly waived this fact for the current run."
        elif unsupported_record is not None:
            coverage_state = "unsupported_draft"
            reason = str(unsupported_record.get("reason", "Unsupported fact."))
        else:
            coverage_state = "represented"
            reason = "Fact is inside the current supported semantic profile."
        facts.append(
            {
                "path": path,
                "value": value,
                "coverage_state": coverage_state,
                "reason": reason,
            }
        )
    blocking = [
        fact
        for fact in facts
        if fact["coverage_state"] in BLOCKING_COVERAGE_STATES
    ]
    return {
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "case_id": case_id,
        "valid": not blocking,
        "candidate_entity_count": len(candidate.get("entities", [])),
        "capability_profile_id": capability_profile.get("profile_id"),
        "capability_profile_hash": capability_profile.get("profile_hash"),
        "facts": facts,
        "blocking_facts": blocking,
        "custom_property_policy": capability_profile.get("custom_property_policy"),
    }


def build_semantic_geometry_expectation(
    *,
    case_id: str,
    design_brief: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Derive supported rectangular-room wall expectations from user facts."""
    known = design_brief.get("known_facts")
    if not isinstance(known, Mapping):
        return None
    space_facts = known.get("space")
    wall_facts = known.get("walls")
    if not isinstance(space_facts, Mapping) or not isinstance(wall_facts, Mapping):
        return None
    if space_facts.get("shape") != "rectangle":
        return None
    wall_placement = wall_facts.get("placement")
    canonical_wall_placement = _canonical_wall_placement(wall_placement)
    if canonical_wall_placement != "outside_boundary":
        return None
    if wall_facts.get("enclosure") not in {None, "closed"}:
        return None

    length_mm = _number(space_facts.get("length_mm"))
    width_mm = _number(space_facts.get("width_mm"))
    thickness_mm = _number(wall_facts.get("thickness_mm"))
    height_mm = _number(wall_facts.get("height_mm")) or _number(space_facts.get("height_mm"))
    if not all(value is not None and value > 0 for value in (length_mm, width_mm, thickness_mm, height_mm)):
        return None

    space = _find_space(candidate)
    if space is None:
        return None
    space_bounds = _space_inner_bounds(
        space,
        length_mm=length_mm,
        width_mm=width_mm,
    )
    if space_bounds is None:
        return None
    x_min, x_max, y_min, y_max, z_min = space_bounds
    z_max = z_min + height_mm

    walls = {
        "wall-south": {
            "axis": "x",
            "bbox": _bbox(x_min - thickness_mm, x_max + thickness_mm, y_min - thickness_mm, y_min, z_min, z_max),
        },
        "wall-north": {
            "axis": "x",
            "bbox": _bbox(x_min - thickness_mm, x_max + thickness_mm, y_max, y_max + thickness_mm, z_min, z_max),
        },
        "wall-west": {
            "axis": "y",
            "bbox": _bbox(x_min - thickness_mm, x_min, y_min, y_max, z_min, z_max),
        },
        "wall-east": {
            "axis": "y",
            "bbox": _bbox(x_max, x_max + thickness_mm, y_min, y_max, z_min, z_max),
        },
    }
    center_overlap_walls = {
        "wall-south": {
            "axis": "x",
            "bbox": _bbox(
                x_min - thickness_mm / 2,
                x_max + thickness_mm / 2,
                y_min - thickness_mm,
                y_min,
                z_min,
                z_max,
            ),
        },
        "wall-north": {
            "axis": "x",
            "bbox": _bbox(
                x_min - thickness_mm / 2,
                x_max + thickness_mm / 2,
                y_max,
                y_max + thickness_mm,
                z_min,
                z_max,
            ),
        },
        "wall-west": {
            "axis": "y",
            "bbox": _bbox(
                x_min - thickness_mm,
                x_min,
                y_min - thickness_mm / 2,
                y_max + thickness_mm / 2,
                z_min,
                z_max,
            ),
        },
        "wall-east": {
            "axis": "y",
            "bbox": _bbox(
                x_max,
                x_max + thickness_mm,
                y_min - thickness_mm / 2,
                y_max + thickness_mm / 2,
                z_min,
                z_max,
            ),
        },
    }
    for wall_id, wall in walls.items():
        wall["bbox_issue_code"] = "WALL_OUTSIDE_BOUNDARY_GAP"
        wall["bbox_issue_path"] = f"/walls/{wall_id}"
    for wall_id, wall in center_overlap_walls.items():
        wall["bbox_issue_code"] = "WALL_OUTSIDE_BOUNDARY_GAP"
        wall["bbox_issue_path"] = f"/walls/{wall_id}"
    return {
        "case_id": case_id,
        "derivation": "design_brief_rectangular_room_outside_boundary_v1",
        "source": "design_brief",
        "tolerance": 0.05,
        "units": "METRE",
        "source_facts": {
            "space": {
                "length_mm": length_mm,
                "width_mm": width_mm,
                "height_mm": height_mm,
            },
            "walls": {
                "placement": canonical_wall_placement,
                **(
                    {"placement_raw": wall_placement}
                    if wall_placement != canonical_wall_placement
                    else {}
                ),
                "thickness_mm": thickness_mm,
                "enclosure": wall_facts.get("enclosure"),
            },
        },
        "walls": walls,
        "accepted_wall_sets": [
            {
                "convention": "long_wall_through",
                "walls": walls,
            },
            {
                "convention": "center_overlap",
                "walls": center_overlap_walls,
            },
        ],
    }


def _canonical_wall_placement(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {
        "outside_boundary",
        "external_boundary",
        "outside",
        "outside_room_boundary",
        "exterior",
        "outer",
    }:
        return "outside_boundary"
    compact = value.strip()
    if compact in {
        "外侧",
        "外部",
        "房间边界外侧",
        "边界外侧",
        "室外侧",
        "澶栦晶",
        "НвІа",
    }:
        return "outside_boundary"
    return normalized if normalized else None


def _known_fact_leaves(design_brief: Mapping[str, Any]) -> list[tuple[str, Any]]:
    known_facts = design_brief.get("known_facts")
    if not isinstance(known_facts, Mapping):
        return []
    leaves: list[tuple[str, Any]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key in sorted(value):
                visit(value[key], f"{path}/{key}")
        elif isinstance(value, list):
            leaves.append((path, value))
        else:
            leaves.append((path, value))

    visit(known_facts, "/known_facts")
    return leaves


def _unsupported_by_path(capability_profile: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in capability_profile.get("unsupported_facts", []):
        if isinstance(item, Mapping) and isinstance(item.get("path"), str):
            result[str(item["path"])] = item
    return result


def _is_waived(design_brief: Mapping[str, Any], path: str) -> bool:
    waived_facts = design_brief.get("waived_facts", [])
    if isinstance(waived_facts, list) and path in waived_facts:
        return True
    for collection_name in ("user_corrections", "unsupported_requests"):
        collection = design_brief.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item in collection:
            if (
                isinstance(item, Mapping)
                and item.get("path") == path
                and item.get("waived") is True
            ):
                return True
    return False


def _find_space(candidate: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for entity in candidate.get("entities", []):
        if isinstance(entity, Mapping) and entity.get("ifc_class") == "IfcSpace":
            return entity
    return None


def _placement_origin(entity: Mapping[str, Any]) -> tuple[float, float, float] | None:
    attributes = entity.get("attributes")
    if not isinstance(attributes, Mapping):
        return None
    placement = attributes.get("ObjectPlacement")
    if not isinstance(placement, Mapping):
        return None
    origin = placement.get("origin")
    if not isinstance(origin, list) or len(origin) < 2:
        return None
    return (
        float(origin[0]),
        float(origin[1]),
        float(origin[2]) if len(origin) > 2 else 0.0,
    )


def _space_inner_bounds(
    entity: Mapping[str, Any],
    *,
    length_mm: float,
    width_mm: float,
) -> tuple[float, float, float, float, float] | None:
    origin = _placement_origin(entity)
    if origin is None:
        return None
    profile = _representation_profile(entity)
    if isinstance(profile, Mapping) and profile.get("kind") == "polygon":
        bounds = _polygon_plan_bounds(entity, profile)
        if bounds is None:
            return None
        x_min, _x_max, y_min, _y_max, z_min = bounds
        return (x_min, x_min + length_mm, y_min, y_min + width_mm, z_min)

    origin_x, origin_y, origin_z = origin
    return (
        origin_x - length_mm / 2,
        origin_x + length_mm / 2,
        origin_y - width_mm / 2,
        origin_y + width_mm / 2,
        origin_z,
    )


def _representation_profile(entity: Mapping[str, Any]) -> Mapping[str, Any] | None:
    attributes = entity.get("attributes")
    if not isinstance(attributes, Mapping):
        return None
    representation = attributes.get("Representation")
    if not isinstance(representation, Mapping):
        return None
    profile = representation.get("profile")
    return profile if isinstance(profile, Mapping) else None


def _polygon_plan_bounds(
    entity: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> tuple[float, float, float, float, float] | None:
    origin = _placement_origin(entity)
    if origin is None:
        return None
    local_x, local_y = _local_plan_axes(entity)
    if local_x is None or local_y is None:
        return None
    points = profile.get("points")
    if not isinstance(points, list) or not points:
        return None

    world_points: list[tuple[float, float]] = []
    origin_x, origin_y, origin_z = origin
    for point in points:
        if not isinstance(point, list) or len(point) < 2:
            return None
        local_point_x = _number(point[0])
        local_point_y = _number(point[1])
        if local_point_x is None or local_point_y is None:
            return None
        world_points.append(
            (
                origin_x + local_point_x * local_x[0] + local_point_y * local_y[0],
                origin_y + local_point_x * local_x[1] + local_point_y * local_y[1],
            )
        )
    x_values = [point[0] for point in world_points]
    y_values = [point[1] for point in world_points]
    return (min(x_values), max(x_values), min(y_values), max(y_values), origin_z)


def _local_plan_axes(
    entity: Mapping[str, Any],
) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    attributes = entity.get("attributes")
    if not isinstance(attributes, Mapping):
        return (None, None)
    placement = attributes.get("ObjectPlacement")
    if not isinstance(placement, Mapping):
        return (None, None)
    ref_direction = placement.get("ref_direction", [1, 0, 0])
    if not isinstance(ref_direction, list) or len(ref_direction) < 2:
        return (None, None)
    ref_x = _number(ref_direction[0])
    ref_y = _number(ref_direction[1])
    if ref_x is None or ref_y is None:
        return (None, None)
    norm = hypot(ref_x, ref_y)
    if norm == 0:
        return (None, None)
    local_x = (ref_x / norm, ref_y / norm)
    local_y = (-local_x[1], local_x[0])
    return (local_x, local_y)


def _bbox(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
) -> dict[str, list[float]]:
    return {
        "x": _metre_range(x_min, x_max),
        "y": _metre_range(y_min, y_max),
        "z": _metre_range(z_min, z_max),
    }


def _metre_range(start_mm: float, end_mm: float) -> list[float]:
    return [round(start_mm / 1000, 6), round(end_mm / 1000, 6)]


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None
