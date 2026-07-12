"""Hash-bound local and global Gate plans for candidate revisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


LOCAL_GATE_ORDER = (
    "opening_filling_relationships",
    "opening_filling_geometry",
    "wall_host_geometry",
    "room_enclosure",
    "stair_vertical_connection",
    "slab_wall_vertical_alignment",
    "storey_ownership",
)
GLOBAL_GATE_ORDER = (
    "bim_json_schema",
    "bim_json_semantics",
    "relationship_integrity",
    "expected_fact_coverage",
    "unrelated_component_preservation",
    "ifc_compile",
    "ifc_reopen",
    "generated_ifc_geometry",
    "audit",
    "secret_scan",
)


def build_revision_gate_plan(
    *,
    candidate: Mapping[str, Any],
    revision: Mapping[str, Any],
    changed_ids: Sequence[str],
    dependency_ids: Sequence[str],
    preservation: Mapping[str, Any],
    final: bool,
) -> dict[str, Any]:
    """Select fast local Gates while keeping final global Gates mandatory."""

    classes = _classes_by_id(candidate)
    selected: set[str] = set()
    for component_id in changed_ids:
        selected.update(_changed_gates(classes.get(component_id, "")))
    for component_id in dependency_ids:
        selected.update(_dependency_gates(classes.get(component_id, "")))
    local_gates = [gate for gate in LOCAL_GATE_ORDER if gate in selected]
    return {
        "schema_version": "text2ifc/revision-gate-plan/1.0",
        "mode": "final_acceptance" if final else "local_feedback",
        "revision_binding": {
            "revision_id": revision.get("revision_id"),
            "candidate_hash": revision.get("candidate_hash"),
            "expected_facts_hash": revision.get("expected_facts_hash"),
        },
        "changed_ids": sorted(set(changed_ids)),
        "dependency_ids": sorted(set(dependency_ids)),
        "preservation": dict(preservation),
        "local_gates": local_gates,
        "skipped_local_gates": [gate for gate in LOCAL_GATE_ORDER if gate not in selected],
        "global_gates": list(GLOBAL_GATE_ORDER) if final else [],
        "global_gates_mandatory": bool(final),
    }


def write_revision_gate_evidence(
    *,
    output_path: Path | str,
    plan: Mapping[str, Any],
    gate_results: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist Gate evidence only after checking its revision/hash binding."""

    binding = plan.get("revision_binding", {})
    issues: list[dict[str, str]] = []
    if gate_results.get("revision_id") != binding.get("revision_id"):
        issues.append(
            _issue("REVISION_GATE_ID_MISMATCH", "/revision_id", "Gate result revision ID differs from the plan.")
        )
    if gate_results.get("candidate_hash") != binding.get("candidate_hash"):
        issues.append(
            _issue("REVISION_GATE_HASH_MISMATCH", "/candidate_hash", "Gate result candidate hash differs from the plan.")
        )
    preservation = plan.get("preservation", {})
    if preservation.get("unrelated_component_preservation_rate") != 1.0:
        issues.append(
            _issue(
                "REVISION_GATE_PRESERVATION_FAILED",
                "/preservation/unrelated_component_preservation_rate",
                "Unrelated component preservation must equal 1.0.",
            )
        )
    result = {
        "schema_version": "text2ifc/revision-gate-evidence/1.0",
        "valid": not issues,
        "plan": dict(plan),
        "gate_results": dict(gate_results),
        "issues": sorted(issues, key=lambda item: (item["path"], item["code"])),
    }
    _write_json(Path(output_path), result)
    return result


def _classes_by_id(candidate: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for collection in ("entities", "relationships"):
        records = candidate.get(collection, [])
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, Mapping) and isinstance(record.get("id"), str):
                result[record["id"]] = str(record.get("ifc_class", ""))
    return result


def _changed_gates(ifc_class: str) -> set[str]:
    if ifc_class in {"IfcDoor", "IfcWindow", "IfcOpeningElement"}:
        return {"opening_filling_relationships", "opening_filling_geometry"}
    if ifc_class in {"IfcWall", "IfcWallStandardCase"}:
        return {"wall_host_geometry", "room_enclosure"}
    if ifc_class == "IfcSpace":
        return {"room_enclosure", "storey_ownership"}
    if ifc_class in {"IfcStair", "IfcStairFlight"}:
        return {"stair_vertical_connection", "storey_ownership"}
    if ifc_class == "IfcSlab":
        return {"stair_vertical_connection", "slab_wall_vertical_alignment", "storey_ownership"}
    if ifc_class.startswith("IfcRel"):
        return {"opening_filling_relationships", "storey_ownership"}
    return set()


def _dependency_gates(ifc_class: str) -> set[str]:
    if ifc_class in {"IfcWall", "IfcWallStandardCase"}:
        return {"wall_host_geometry"}
    if ifc_class in {"IfcDoor", "IfcWindow", "IfcOpeningElement"}:
        return {"opening_filling_relationships", "opening_filling_geometry"}
    if ifc_class in {"IfcStair", "IfcStairFlight", "IfcSlab"}:
        return {"stair_vertical_connection"}
    return set()


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
