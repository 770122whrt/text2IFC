"""Semantic coverage helpers for Design Brief to BIM JSON acceptance."""

from __future__ import annotations

from typing import Any, Mapping


ACCEPTED_COVERAGE_STATES = {"represented", "compiler_generated", "waived_by_user"}
BLOCKING_COVERAGE_STATES = {"unsupported_draft", "blocked_unknown_capability"}


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
    if wall_facts.get("placement") != "outside_boundary":
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
    origin = _placement_origin(space)
    if origin is None:
        return None
    origin_x, origin_y, origin_z = origin
    x_min = origin_x - length_mm / 2
    x_max = origin_x + length_mm / 2
    y_min = origin_y - width_mm / 2
    y_max = origin_y + width_mm / 2
    z_min = origin_z
    z_max = origin_z + height_mm

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
    for wall_id, wall in walls.items():
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
                "placement": "outside_boundary",
                "thickness_mm": thickness_mm,
                "enclosure": wall_facts.get("enclosure"),
            },
        },
        "walls": walls,
    }


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
