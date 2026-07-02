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
    storeys = _records(known_facts.get("storeys"))
    spaces = _records(known_facts.get("spaces"))
    doors = _records(known_facts.get("doors"))
    windows = _records(known_facts.get("windows"))
    slabs = _records(known_facts.get("slabs"))
    stairs = _records(known_facts.get("stairs"))
    roof = known_facts.get("roof") if isinstance(known_facts.get("roof"), Mapping) else None

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


def _copy_records(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [deepcopy(dict(record)) for record in records]


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
