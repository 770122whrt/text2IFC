"""GUID-independent IFC2Text roundtrip comparator.

This comparator evaluates reconstructable building observations rather than IFC
entity identity.  A single building-wide translation may be estimated; no
component receives its own alignment transform.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .facts import extract_building_facts


COMPARE_SCHEMA_VERSION = "text2ifc/ifc2text-compare/0.1"


@dataclass(frozen=True)
class CompareTolerances:
    storey_elevation_mm: float = 50.0
    wall_center_mm: float = 100.0
    wall_length_mm: float = 50.0
    wall_thickness_mm: float = 20.0
    wall_height_mm: float = 50.0
    wall_angle_deg: float = 2.0
    filling_center_mm: float = 100.0
    filling_size_mm: float = 20.0
    opening_center_mm: float = 100.0
    opening_size_mm: float = 20.0


def _distance(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None or len(a) != len(b):
        return None
    return math.dist(a, b)


def _center(item: dict[str, Any]) -> list[float] | None:
    if item.get("centroid_mm"):
        return list(item["centroid_mm"])
    start = item.get("axis_start_mm")
    end = item.get("axis_end_mm")
    if start and end:
        return [(start[index] + end[index]) / 2.0 for index in range(3)]
    return None


def _translated(point: list[float] | None, offset: list[float]) -> list[float] | None:
    if point is None:
        return None
    return [point[index] + offset[index] for index in range(3)]


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _building_anchor(facts: dict[str, Any]) -> list[float] | None:
    centers = [
        _center(wall)
        for storey in facts["storeys"]
        for wall in storey["walls"]
    ]
    usable = [center for center in centers if center is not None]
    if not usable:
        return None
    return [_median([point[axis] for point in usable]) for axis in range(3)]


def _translation(source: dict[str, Any], candidate: dict[str, Any], enabled: bool) -> list[float]:
    if not enabled:
        return [0.0, 0.0, 0.0]
    source_anchor = _building_anchor(source)
    candidate_anchor = _building_anchor(candidate)
    if source_anchor is None or candidate_anchor is None:
        return [0.0, 0.0, 0.0]
    return [source_anchor[index] - candidate_anchor[index] for index in range(3)]


def _orientation_deg(wall: dict[str, Any]) -> float | None:
    direction = wall.get("axis_direction")
    if not direction:
        start = wall.get("axis_start_mm")
        end = wall.get("axis_end_mm")
        if not start or not end:
            return None
        direction = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
    return math.degrees(math.atan2(direction[1], direction[0])) % 180.0


def _angle_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    delta = abs(a - b) % 180.0
    return min(delta, 180.0 - delta)


def _greedy_match(
    source: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
    cost: Callable[[dict[str, Any], dict[str, Any]], float],
    *,
    max_cost: float,
) -> tuple[list[tuple[dict[str, Any], dict[str, Any], float]], list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: list[tuple[float, int, int]] = []
    for source_index, source_item in enumerate(source):
        for candidate_index, candidate_item in enumerate(candidate):
            value = cost(source_item, candidate_item)
            if math.isfinite(value):
                pairs.append((value, source_index, candidate_index))
    used_source: set[int] = set()
    used_candidate: set[int] = set()
    matched: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    for value, source_index, candidate_index in sorted(pairs, key=lambda item: (item[0], item[1], item[2])):
        if value > max_cost or source_index in used_source or candidate_index in used_candidate:
            continue
        used_source.add(source_index)
        used_candidate.add(candidate_index)
        matched.append((source[source_index], candidate[candidate_index], value))
    missing = [item for index, item in enumerate(source) if index not in used_source]
    extra = [item for index, item in enumerate(candidate) if index not in used_candidate]
    return matched, missing, extra


def _match_storeys(source: dict[str, Any], candidate: dict[str, Any], offset: list[float], tolerance: float) -> tuple[list[tuple[dict[str, Any], dict[str, Any], float]], list[dict[str, Any]], list[dict[str, Any]]]:
    def cost(left: dict[str, Any], right: dict[str, Any]) -> float:
        a = left.get("elevation_mm")
        b = right.get("elevation_mm")
        if a is None or b is None:
            return 0.0 if left["label"] == right["label"] else math.inf
        return abs(a - (b + offset[2]))

    return _greedy_match(source["storeys"], candidate["storeys"], cost, max_cost=tolerance)


def _wall_cost(source: dict[str, Any], candidate: dict[str, Any], offset: list[float], tolerance: CompareTolerances) -> float:
    source_center = _center(source)
    candidate_center = _translated(_center(candidate), offset)
    center_delta = _distance(source_center, candidate_center)
    angle_delta = _angle_delta(_orientation_deg(source), _orientation_deg(candidate))
    if center_delta is None or angle_delta is None:
        return math.inf
    length_delta = abs(float(source.get("length_mm", 0.0)) - float(candidate.get("length_mm", 0.0)))
    return (
        center_delta / tolerance.wall_center_mm
        + angle_delta / tolerance.wall_angle_deg
        + length_delta / tolerance.wall_length_mm
    )


def _item_cost(source: dict[str, Any], candidate: dict[str, Any], offset: list[float], center_tolerance: float, size_tolerance: float, *, opening: bool = False) -> float:
    center_delta = _distance(_center(source), _translated(_center(candidate), offset))
    if center_delta is None:
        return math.inf
    if opening:
        source_dims = source.get("dimensions_mm", {})
        candidate_dims = candidate.get("dimensions_mm", {})
        fields = ("width", "height", "depth")
        deltas = [abs(float(source_dims[field]) - float(candidate_dims[field])) for field in fields if source_dims.get(field) is not None and candidate_dims.get(field) is not None]
    else:
        deltas = [
            abs(float(source[field]) - float(candidate[field]))
            for field in ("overall_width_mm", "overall_height_mm")
            if source.get(field) is not None and candidate.get(field) is not None
        ]
    size_cost = max(deltas, default=0.0) / size_tolerance
    return center_delta / center_tolerance + size_cost


def _delta_record(source: dict[str, Any], candidate: dict[str, Any], offset: list[float], category: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source": source["label"],
        "candidate": candidate["label"],
        "source_name": source.get("name"),
        "candidate_name": candidate.get("name"),
        "center_delta_mm": _distance(_center(source), _translated(_center(candidate), offset)),
    }
    if category == "walls":
        record.update(
            {
                "length_delta_mm": None if source.get("length_mm") is None or candidate.get("length_mm") is None else abs(source["length_mm"] - candidate["length_mm"]),
                "thickness_delta_mm": None if source.get("thickness_mm") is None or candidate.get("thickness_mm") is None else abs(source["thickness_mm"] - candidate["thickness_mm"]),
                "height_delta_mm": None if source.get("height_mm") is None or candidate.get("height_mm") is None else abs(source["height_mm"] - candidate["height_mm"]),
                "angle_delta_deg": _angle_delta(_orientation_deg(source), _orientation_deg(candidate)),
            }
        )
    elif category == "openings":
        for field in ("width", "height", "depth"):
            left = source.get("dimensions_mm", {}).get(field)
            right = candidate.get("dimensions_mm", {}).get(field)
            record[f"{field}_delta_mm"] = None if left is None or right is None else abs(left - right)
    else:
        record["width_delta_mm"] = None if source.get("overall_width_mm") is None or candidate.get("overall_width_mm") is None else abs(source["overall_width_mm"] - candidate["overall_width_mm"])
        record["height_delta_mm"] = None if source.get("overall_height_mm") is None or candidate.get("overall_height_mm") is None else abs(source["overall_height_mm"] - candidate["overall_height_mm"])
    return record


def _over_limit(record: dict[str, Any], category: str, tolerance: CompareTolerances) -> bool:
    def exceeds(name: str, limit: float) -> bool:
        value = record.get(name)
        return value is not None and value > limit

    if category == "walls":
        return any(
            (
                exceeds("center_delta_mm", tolerance.wall_center_mm),
                exceeds("length_delta_mm", tolerance.wall_length_mm),
                exceeds("thickness_delta_mm", tolerance.wall_thickness_mm),
                exceeds("height_delta_mm", tolerance.wall_height_mm),
                exceeds("angle_delta_deg", tolerance.wall_angle_deg),
            )
        )
    if category == "openings":
        return exceeds("center_delta_mm", tolerance.opening_center_mm) or any(
            exceeds(f"{field}_delta_mm", tolerance.opening_size_mm) for field in ("width", "height", "depth")
        )
    return exceeds("center_delta_mm", tolerance.filling_center_mm) or any(
        exceeds(f"{field}_delta_mm", tolerance.filling_size_mm) for field in ("width", "height")
    )


def compare_fact_documents(
    source: dict[str, Any],
    candidate: dict[str, Any],
    *,
    tolerances: CompareTolerances | None = None,
    allow_global_translation: bool = True,
) -> dict[str, Any]:
    tolerance = tolerances or CompareTolerances()
    offset = _translation(source, candidate, allow_global_translation)
    storey_pairs, missing_storeys, extra_storeys = _match_storeys(
        source, candidate, offset, tolerance.storey_elevation_mm
    )
    category_reports: dict[str, Any] = {}
    relationship_differences: list[dict[str, Any]] = []
    wall_label_map: dict[str, str] = {}

    for category in ("walls", "doors", "windows", "openings"):
        matches: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []
        extra: list[dict[str, Any]] = []
        deviations: list[dict[str, Any]] = []
        for source_storey, candidate_storey, _ in storey_pairs:
            left = source_storey[category]
            right = candidate_storey[category]
            if category == "walls":
                cost = lambda a, b: _wall_cost(a, b, offset, tolerance)
                max_cost = 6.0
            elif category == "openings":
                cost = lambda a, b: _item_cost(a, b, offset, tolerance.opening_center_mm, tolerance.opening_size_mm, opening=True)
                # Matching and acceptance are separate decisions: a substantially
                # resized opening at the same location should be reported as a
                # dimensional deviation, not misclassified as missing+extra.
                max_cost = 50.0
            else:
                cost = lambda a, b: _item_cost(a, b, offset, tolerance.filling_center_mm, tolerance.filling_size_mm)
                max_cost = 50.0
            paired, storey_missing, storey_extra = _greedy_match(left, right, cost, max_cost=max_cost)
            for source_item, candidate_item, match_cost in paired:
                delta = _delta_record(source_item, candidate_item, offset, category)
                delta["match_cost"] = round(match_cost, 6)
                delta["storey_source"] = source_storey["label"]
                delta["storey_candidate"] = candidate_storey["label"]
                matches.append(delta)
                if _over_limit(delta, category, tolerance):
                    deviations.append(delta)
                if category == "walls":
                    wall_label_map[source_item["label"]] = candidate_item["label"]
            missing.extend(storey_missing)
            extra.extend(storey_extra)
        category_reports[category] = {
            "matched": matches,
            "missing": [{"label": item["label"], "name": item.get("name")} for item in missing],
            "extra": [{"label": item["label"], "name": item.get("name")} for item in extra],
            "deviations": deviations,
        }

    # Check host-wall topology only after geometry establishes a cross-file wall map.
    for category in ("doors", "windows", "openings"):
        source_by_label = {item["label"]: item for storey in source["storeys"] for item in storey[category]}
        candidate_by_label = {item["label"]: item for storey in candidate["storeys"] for item in storey[category]}
        for match in category_reports[category]["matched"]:
            left = source_by_label[match["source"]]
            right = candidate_by_label[match["candidate"]]
            expected_host = wall_label_map.get(left.get("host_wall")) if left.get("host_wall") else None
            actual_host = right.get("host_wall")
            if expected_host != actual_host and (expected_host is not None or actual_host is not None):
                relationship_differences.append(
                    {
                        "category": category,
                        "source": left["label"],
                        "candidate": right["label"],
                        "relationship": "host_wall",
                        "expected_candidate_host": expected_host,
                        "actual_candidate_host": actual_host,
                    }
                )

    missing_count = len(missing_storeys) + sum(len(report["missing"]) for report in category_reports.values())
    extra_count = len(extra_storeys) + sum(len(report["extra"]) for report in category_reports.values())
    deviation_count = sum(len(report["deviations"]) for report in category_reports.values())
    consistent = missing_count == 0 and extra_count == 0 and deviation_count == 0 and not relationship_differences
    geometry_processable = all(
        item.get("measurement_status") == "measured" or item.get("centroid_mm") is not None
        for facts in (source, candidate)
        for storey in facts["storeys"]
        for category in ("walls", "doors", "windows", "openings")
        for item in storey[category]
    )
    return {
        "schema_version": COMPARE_SCHEMA_VERSION,
        "status": {
            "files_readable": True,
            "geometry_processable": geometry_processable,
            "reconstruction_consistent": consistent,
        },
        "scope": ["storeys", "walls", "doors", "windows", "openings", "host_wall_relationships"],
        "identity_policy": "geometry_and_relationship_matching_without_guid_equality",
        "alignment": {
            "kind": "single_global_translation" if allow_global_translation else "none",
            "candidate_to_source_translation_mm": [round(value, 3) for value in offset],
            "per_component_alignment": False,
        },
        "tolerances": asdict(tolerance),
        "storeys": {
            "matched": [
                {"source": left["label"], "candidate": right["label"], "elevation_delta_mm": round(delta, 3)}
                for left, right, delta in storey_pairs
            ],
            "missing": [item["label"] for item in missing_storeys],
            "extra": [item["label"] for item in extra_storeys],
        },
        "components": category_reports,
        "relationship_differences": relationship_differences,
        "summary": {
            "missing_count": missing_count,
            "extra_count": extra_count,
            "deviation_count": deviation_count,
            "relationship_difference_count": len(relationship_differences),
        },
    }


def compare_ifc_buildings(
    source_path: str | Path,
    candidate_path: str | Path,
    *,
    tolerances: CompareTolerances | None = None,
    allow_global_translation: bool = True,
) -> dict[str, Any]:
    """Open two IFCs independently and compare their description-level facts."""
    source = extract_building_facts(source_path, infer_spaces=False)
    candidate = extract_building_facts(candidate_path, infer_spaces=False)
    result = compare_fact_documents(
        source,
        candidate,
        tolerances=tolerances,
        allow_global_translation=allow_global_translation,
    )
    result["source"] = source["source"]
    result["candidate"] = candidate["source"]
    result["source_measurement_issues"] = source["issues"]
    result["candidate_measurement_issues"] = candidate["issues"]
    return result
