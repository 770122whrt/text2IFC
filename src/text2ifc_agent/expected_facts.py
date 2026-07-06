"""Dynamic expected-fact sidecars derived from Design Brief evidence."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


EXPECTED_FACTS_SCHEMA_VERSION = "text2ifc/expected-facts/1.0"


def build_expected_facts(
    *,
    case_id: str,
    design_brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Build dynamic expected facts without mutating the Design Brief."""
    known = design_brief.get("known_facts", {})
    known_facts = known if isinstance(known, Mapping) else {}
    nested_storeys = _nested_storeys(known_facts.get("storeys"))
    if nested_storeys:
        storeys = _storey_records_from_nested(nested_storeys)
        spaces = _space_records_from_nested(nested_storeys, storeys)
        doors = _opening_records_from_nested(nested_storeys, storeys, "doors")
        windows = _opening_records_from_nested(nested_storeys, storeys, "windows")
    elif _is_storey_list(known_facts.get("storeys")) and isinstance(
        known_facts.get("spaces"), Mapping
    ):
        storeys = _storey_records_from_list(_records(known_facts.get("storeys")))
        spaces = _space_records_from_storey_map(known_facts.get("spaces"), storeys)
        space_storeys = _space_name_storey_map(spaces)
        doors = _flat_opening_records(
            known_facts.get("doors"),
            storeys,
            "doors",
            space_storeys=space_storeys,
        )
        windows = _flat_opening_records(
            known_facts.get("windows"),
            storeys,
            "windows",
            space_storeys=space_storeys,
        )
    elif isinstance(known_facts.get("spaces"), Mapping):
        storeys = _storey_records_from_floor_map(
            known_facts.get("spaces"),
            known_facts.get("building"),
        )
        spaces = _space_records_from_storey_map(known_facts.get("spaces"), storeys)
        doors = _opening_records_from_storey_map(
            known_facts.get("doors"),
            storeys,
            "doors",
        )
        windows = _opening_records_from_storey_map(
            known_facts.get("windows"),
            storeys,
            "windows",
        )
    else:
        storeys = _records(known_facts.get("storeys"))
        spaces = _records(known_facts.get("spaces"))
        doors = _records(known_facts.get("doors"))
        windows = _records(known_facts.get("windows"))
    slabs = _slab_records(known_facts)
    stairs = (
        _records(known_facts.get("stairs"))
        or _singular_stair_record(known_facts, storeys)
        or _stair_records_from_nested(nested_storeys, storeys)
    )
    roof = _roof_record(known_facts)

    source_paths = _source_paths(design_brief.get("fact_sources", []))
    payload: dict[str, Any] = {
        "schema_version": EXPECTED_FACTS_SCHEMA_VERSION,
        "case_id": case_id,
        "source": {
            "design_brief_schema_version": design_brief.get("schema_version"),
            "status": design_brief.get("status"),
            "language": design_brief.get("language"),
        },
        "storeys": _copy_records(storeys),
        "storey_count": len(storeys),
        "spaces": _copy_records(spaces),
        "doors": _copy_records(doors),
        "windows": _copy_records(windows),
        "slabs": _copy_records(slabs),
        "roof": deepcopy(dict(roof)) if roof is not None else None,
        "stairs": _copy_records(stairs),
        "space_counts_by_storey": _counts_by_storey(spaces),
        "door_counts_by_storey": _counts_by_storey(doors),
        "window_counts_by_storey": _counts_by_storey(windows),
        "total_counts": {
            "IfcBuildingStorey": len(storeys),
            "IfcSpace": len(spaces),
            "IfcDoor": len(doors),
            "IfcWindow": len(windows),
        },
        "required_relationships": {
            "containment": {
                "storeys": len(storeys),
                "spaces": len(spaces),
                "doors": len(doors),
                "windows": len(windows),
            },
            "opening_fill": {
                "doors": len(doors),
                "windows": len(windows),
            },
        },
        "source_paths": source_paths,
        "unresolved_expectations": _unresolved_expectations(design_brief),
        "sidecar_role": "orchestration_expectations_not_bim_json_schema",
    }
    fixture_reuse = known_facts.get("fixture_reuse")
    if isinstance(fixture_reuse, Mapping):
        payload["fixture_reuse"] = deepcopy(dict(fixture_reuse))
    return payload


def write_expected_facts(
    *,
    case_dir: Path | str,
    case_id: str,
    design_brief: Mapping[str, Any] | None = None,
) -> Path:
    """Write `expected-facts.json` for a case and return its path."""
    root = Path(case_dir)
    root.mkdir(parents=True, exist_ok=True)
    active_brief = design_brief if design_brief is not None else _load_design_brief(root)
    payload = build_expected_facts(case_id=case_id, design_brief=active_brief)
    output = root / "expected-facts.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def _load_design_brief(root: Path) -> dict[str, Any]:
    candidates = [
        root / "design-brief.json",
        root / "design-brief" / "design-brief.json",
    ]
    calls = sorted((root / "calls").glob("*-design-brief"))
    candidates.extend(call / "design-brief.json" for call in calls)
    for path in candidates:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
    raise ValueError("expected facts require design-brief.json")


def _records(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _is_storey_list(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(item, Mapping)
        and ("elevation" in item or "elevation_mm" in item or "name" in item)
        for item in value
    )


def _nested_storeys(value: Any) -> list[tuple[str, Mapping[str, Any]]]:
    if not isinstance(value, Mapping):
        return []
    records: list[tuple[int, str, Mapping[str, Any]]] = []
    for index, (source_key, payload) in enumerate(value.items(), start=1):
        if not isinstance(source_key, str) or not isinstance(payload, Mapping):
            continue
        elevation = payload.get("elevation_mm")
        sort_key = int(elevation) if isinstance(elevation, int) else index * 1_000_000
        records.append((sort_key, source_key, payload))
    return [(source_key, payload) for _sort, source_key, payload in sorted(records)]


def _storey_records_from_nested(
    nested_storeys: list[tuple[str, Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, (source_key, payload) in enumerate(nested_storeys, start=1):
        record: dict[str, Any] = {
            "id": _string(payload.get("id")) or f"storey-{index}",
            "source_key": source_key,
        }
        if isinstance(payload.get("elevation_mm"), int):
            record["elevation_mm"] = payload["elevation_mm"]
        records.append(record)
    return records


def _storey_records_from_list(storey_records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, payload in enumerate(storey_records, start=1):
        source_key = _string(payload.get("source_key")) or _string(payload.get("name")) or f"storey-{index}"
        record: dict[str, Any] = {
            "id": _string(payload.get("id")) or f"storey-{index}",
            "source_key": source_key,
        }
        if _string(payload.get("name")):
            record["name"] = payload["name"]
        elevation = _number_alias(payload, ("elevation_mm", "elevation"))
        if elevation is not None:
            record["elevation_mm"] = elevation
        records.append(record)
    return records


def _storey_records_from_floor_map(value: Any, building: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return []
    building_facts = building if isinstance(building, Mapping) else {}
    storey_height = _number_alias(building_facts, ("storey_height_mm", "height_mm")) or 3000
    slab_thickness = _number_alias(building_facts, ("slab_thickness_mm",)) or 150
    records: list[dict[str, Any]] = []
    for index, source_key in enumerate(_ordered_floor_keys(value), start=1):
        records.append(
            {
                "id": f"storey-{index}",
                "source_key": source_key,
                "elevation_mm": int((index - 1) * (storey_height + slab_thickness)),
            }
        )
    return records


def _ordered_floor_keys(value: Mapping[str, Any]) -> list[str]:
    def sort_key(item: tuple[str, Any]) -> tuple[int, str]:
        key = item[0]
        normalized = key.lower()
        if normalized in {"ground_floor", "first_storey", "storey_1", "storey-1"}:
            return (0, key)
        if normalized in {"first_floor", "second_storey", "storey_2", "storey-2"}:
            return (1, key)
        if "ground" in normalized or "首" in key:
            return (0, key)
        if "first" in normalized or "二" in key:
            return (1, key)
        return (10, key)

    return [
        key
        for key, payload in sorted(value.items(), key=sort_key)
        if isinstance(key, str) and isinstance(payload, list)
    ]


def _space_records_from_nested(
    nested_storeys: list[tuple[str, Mapping[str, Any]]],
    storeys: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for (source_key, payload), storey in zip(nested_storeys, storeys):
        spaces = payload.get("spaces")
        if not isinstance(spaces, Mapping):
            continue
        for space_key, space_payload in spaces.items():
            if not isinstance(space_key, str):
                continue
            record = _copy_payload(space_payload)
            record["storey"] = storey["id"]
            record["source_key"] = f"{source_key}.spaces.{space_key}"
            records.append(record)
    return records


def _space_records_from_storey_map(value: Any, storeys: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return _copy_records(_records(value))
    storey_by_source = {
        str(storey.get("source_key")): str(storey.get("id"))
        for storey in storeys
        if storey.get("source_key") and storey.get("id")
    }
    records: list[dict[str, Any]] = []
    for source_key, spaces in value.items():
        if not isinstance(source_key, str) or not isinstance(spaces, list):
            continue
        storey_id = storey_by_source.get(source_key)
        if storey_id is None:
            continue
        for index, space in enumerate(spaces, start=1):
            if not isinstance(space, Mapping):
                continue
            record = _copy_payload(space)
            record["storey"] = storey_id
            record["source_key"] = f"{source_key}.spaces[{index}]"
            rectangle = space.get("rectangle")
            if isinstance(rectangle, Mapping):
                min_x = _number_alias(rectangle, ("min_x",))
                min_y = _number_alias(rectangle, ("min_y",))
                max_x = _number_alias(rectangle, ("max_x",))
                max_y = _number_alias(rectangle, ("max_y",))
                if None not in {min_x, min_y, max_x, max_y}:
                    record["dimensions_mm"] = [max_x - min_x, max_y - min_y]
                    record["origin_mm"] = [min_x, min_y, 0]
            width = _number_alias(space, ("width_mm", "width"))
            if width is not None:
                record["width_mm"] = width
            depth = _number_alias(space, ("depth_mm", "depth"))
            if depth is not None:
                record["depth_mm"] = depth
            records.append(record)
    return records


def _opening_records_from_nested(
    nested_storeys: list[tuple[str, Mapping[str, Any]]],
    storeys: list[Mapping[str, Any]],
    collection: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    singular = collection[:-1]
    for (source_key, payload), storey in zip(nested_storeys, storeys):
        openings = payload.get(collection)
        if not isinstance(openings, list):
            continue
        sequence = 0
        for opening in openings:
            if not isinstance(opening, Mapping):
                continue
            count = _positive_count(_first_present(opening, ("count", "quantity")))
            for _ in range(count):
                sequence += 1
                record = _normalize_opening_payload(opening)
                record["storey"] = storey["id"]
                record["source_key"] = f"{source_key}.{singular}[{sequence}]"
                records.append(record)
    return records


def _flat_opening_records(
    value: Any,
    storeys: list[Mapping[str, Any]],
    collection: str,
    *,
    space_storeys: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    sequence_by_id: dict[str, int] = {}
    for opening in _records(value):
        count = _positive_count(_first_present(opening, ("count", "quantity")))
        for _ in range(count):
            record = _normalize_opening_payload(opening)
            if _string(record.get("id")):
                record["source_id"] = record.pop("id")
            record["storey"] = _infer_opening_storey(
                record,
                storeys,
                space_storeys=space_storeys or {},
            )
            base = _string(opening.get("id")) or f"{collection[:-1]}_{len(records) + 1}"
            sequence_by_id[base] = sequence_by_id.get(base, 0) + 1
            record["source_key"] = f"{base}[{sequence_by_id[base]}]"
            records.append(record)
    return records


def _opening_records_from_storey_map(
    value: Any,
    storeys: list[Mapping[str, Any]],
    collection: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return _flat_opening_records(value, storeys, collection)
    storey_by_source = {
        str(storey.get("source_key")): str(storey.get("id"))
        for storey in storeys
        if storey.get("source_key") and storey.get("id")
    }
    records: list[dict[str, Any]] = []
    singular = collection[:-1]
    for source_key in _ordered_floor_keys(value):
        openings = value.get(source_key)
        if not isinstance(openings, list):
            continue
        storey_id = storey_by_source.get(source_key)
        if storey_id is None:
            continue
        sequence = 0
        for opening in openings:
            if not isinstance(opening, Mapping):
                continue
            count = _positive_count(_first_present(opening, ("count", "quantity")))
            for _ in range(count):
                sequence += 1
                record = _normalize_opening_payload(opening)
                record["storey"] = storey_id
                record["source_key"] = f"{source_key}.{singular}[{sequence}]"
                records.append(record)
    return records


def _normalize_opening_payload(opening: Mapping[str, Any]) -> dict[str, Any]:
    record = _copy_payload(opening)
    for key in ("count", "quantity", "width", "height", "sill_height", "host"):
        record.pop(key, None)
    host = _string(_first_present(opening, ("host_wall", "host")))
    if host:
        record["host_wall"] = host
    width = _number_alias(opening, ("width_mm", "width"))
    height = _number_alias(opening, ("height_mm", "height"))
    sill = _number_alias(opening, ("sill_height_mm", "sill_height"))
    if width is not None:
        record["width_mm"] = width
    if height is not None:
        record["height_mm"] = height
    if sill is not None:
        record["sill_height_mm"] = sill
    return record


def _space_name_storey_map(spaces: list[Mapping[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for space in spaces:
        name = _string(space.get("name"))
        storey = _string(space.get("storey"))
        if name and storey:
            mapping[name] = storey
    return mapping


def _infer_opening_storey(
    record: Mapping[str, Any],
    storeys: list[Mapping[str, Any]],
    *,
    space_storeys: Mapping[str, str],
) -> str:
    text = " ".join(str(record.get(key, "")) for key in ("host_wall", "source_key", "id"))
    for storey in reversed(storeys):
        name = _string(storey.get("name")) or _string(storey.get("source_key"))
        if name and name in text:
            return str(storey["id"])
    for space_name, storey_id in space_storeys.items():
        if space_name in text:
            return storey_id
    if "二层" in text or "second" in text.lower():
        return str(storeys[min(1, len(storeys) - 1)]["id"])
    return str(storeys[0]["id"]) if storeys else ""


def _slab_records(known_facts: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    flat = _records(known_facts.get("slabs"))
    if flat:
        return flat
    slabs = known_facts.get("slabs")
    if not isinstance(slabs, Mapping):
        return []
    records: list[dict[str, Any]] = []
    for source_key, payload in slabs.items():
        if source_key == "roof" or not isinstance(source_key, str):
            continue
        record = _copy_payload(payload)
        record = _normalize_dimension_aliases(record)
        record["source_key"] = source_key
        records.append(record)
    records.sort(key=lambda record: record.get("elevation_mm", 1_000_000))
    return records


def _roof_record(known_facts: Mapping[str, Any]) -> dict[str, Any] | None:
    roof = known_facts.get("roof")
    if isinstance(roof, Mapping):
        record = _normalize_dimension_aliases(deepcopy(dict(roof)))
        if not _string(record.get("id")):
            record.setdefault("source_key", "roof")
        return record
    slabs = known_facts.get("slabs")
    roof_payload = None
    if isinstance(slabs, Mapping):
        roof_payload = slabs.get("roof") or slabs.get("roof_slab")
    if isinstance(roof_payload, Mapping):
        record = _normalize_dimension_aliases(_copy_payload(roof_payload))
        record["source_key"] = "roof"
        return record
    return None


def _stair_records_from_nested(
    nested_storeys: list[tuple[str, Mapping[str, Any]]],
    storeys: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for (source_key, payload), storey in zip(nested_storeys, storeys):
        stair = payload.get("stair")
        if not isinstance(stair, Mapping):
            continue
        record = _copy_payload(stair)
        record["storey"] = storey["id"]
        record["source_key"] = f"{source_key}.stair"
        records.append(record)
    return records


def _singular_stair_record(
    known_facts: Mapping[str, Any],
    storeys: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    stair = known_facts.get("stair") or known_facts.get("stairs")
    if not isinstance(stair, Mapping):
        return []
    record = _copy_payload(stair)
    record["storey"] = str(storeys[0]["id"]) if storeys else "storey-1"
    record["source_key"] = "stair"
    for target, names in {
        "start_elevation_mm": ("start_elevation_mm", "start_elevation"),
        "end_elevation_mm": ("end_elevation_mm", "end_elevation"),
        "start_z_mm": ("start_z_mm",),
        "end_z_mm": ("end_z_mm",),
    }.items():
        value = _number_alias(record, names)
        if value is not None:
            record[target] = value
    return [record]


def _copy_payload(value: Any) -> dict[str, Any]:
    return deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def _normalize_dimension_aliases(record: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "elevation_mm": ("elevation_mm", "elevation", "bottom_elevation", "elevation_bottom"),
        "thickness_mm": ("thickness_mm", "thickness"),
    }
    for target, names in aliases.items():
        value = _number_alias(record, names)
        if value is not None:
            record[target] = value
    return record


def _number_alias(record: Mapping[str, Any], names: tuple[str, ...]) -> int | float | None:
    value = _first_present(record, names)
    if isinstance(value, (int, float)):
        return value
    return None


def _first_present(record: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in record:
            return record[name]
    return None


def _positive_count(value: Any) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 1


def _copy_records(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [deepcopy(dict(record)) for record in records]


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _counts_by_storey(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        storey = record.get("storey")
        if isinstance(storey, str) and storey:
            counts[storey] = counts.get(storey, 0) + 1
    return dict(sorted(counts.items()))


def _source_paths(records: Any) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not isinstance(records, list):
        return result
    for record in records:
        if not isinstance(record, Mapping):
            continue
        path = record.get("path")
        turns = record.get("source_turns", [])
        if isinstance(path, str) and isinstance(turns, list):
            result[path] = [str(turn) for turn in turns]
    return result


def _unresolved_expectations(design_brief: Mapping[str, Any]) -> list[dict[str, Any]]:
    unresolved: list[dict[str, Any]] = []
    for key in ("missing_facts", "ambiguities", "unsupported_requests"):
        records = design_brief.get(key, [])
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, Mapping):
                unresolved.append(
                    {
                        "kind": key,
                        "id": record.get("id"),
                        "path": record.get("path"),
                        "blocking": record.get("blocking"),
                    }
                )
    return unresolved
