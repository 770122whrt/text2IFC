"""Run the Phase 6.3 Gate/Audit final verification matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_agent.complex_fixture import (  # noqa: E402
    assess_no_false_accept_baseline,
    load_complex_fixture,
)
from text2ifc_agent.expected_facts import build_expected_facts  # noqa: E402
from text2ifc_agent.gate_audit_bundle import write_gate_summary  # noqa: E402
from text2ifc_agent.route_decision import write_route_decision  # noqa: E402


DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.3-gate-audit"
)
SOURCE_FIXTURE_ROOT = DEFAULT_OUTPUT_ROOT
MATRIX_SCHEMA_VERSION = "text2ifc/phase6.3-matrix/1.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    summary = run_matrix(args.output_root)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["false_accept_count"] == 0 else 2


def run_matrix(output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cases = [
        _write_complex_two_storey_case(output_root / "complex-two-storey"),
        _write_three_storey_case(output_root / "non-two-storey-three-level"),
        _write_smoke_case(
            output_root / "simple-room-smoke",
            case_id="simple-room-smoke",
            storeys=["storey-1"],
            spaces=[("space-1", "storey-1")],
        ),
        _write_smoke_case(
            output_root / "two-room-smoke",
            case_id="two-room-smoke",
            storeys=["storey-1"],
            spaces=[("space-1", "storey-1"), ("space-2", "storey-1")],
        ),
    ]
    false_accepts = [
        case
        for case in cases
        if case["route"] == "accept" and case["gate_overall_status"] != "passed"
    ]
    non_two_storey_covered = any(
        case["case_id"] == "non-two-storey-three-level"
        and case["non_two_storey_gate_route_covered"]
        for case in cases
    )
    summary = {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "case_count": len(cases),
        "cases": cases,
        "complex_two_storey_status": _case_by_id(cases, "complex-two-storey")[
            "status"
        ],
        "false_accept_count": len(false_accepts),
        "non_two_storey_gate_route_covered": non_two_storey_covered,
        "matrix_report": "matrix-report.md",
        "root": str(output_root),
    }
    _write_json(output_root / "matrix-summary.json", summary)
    _write_matrix_report(output_root / "matrix-report.md", summary)
    return summary


def _write_complex_two_storey_case(case_dir: Path) -> dict[str, Any]:
    source_dir = SOURCE_FIXTURE_ROOT / "complex-two-storey"
    fixture = load_complex_fixture(source_dir)
    input_text = fixture["input_text"]
    expectations = fixture["expectations"]
    readme_path = source_dir / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else None
    _reset_case_dir(case_dir)
    (case_dir / "input.txt").write_text(input_text, encoding="utf-8")
    if readme_text is not None:
        (case_dir / "README.md").write_text(readme_text, encoding="utf-8")
    _write_json(case_dir / "expected-manual-review.json", fixture["metadata"])
    expected_facts = _expected_from_manual_review(
        case_id="complex-two-storey",
        input_text=input_text,
        expectations=expectations,
    )
    _write_json(case_dir / "expected-facts.json", expected_facts)
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        spaces=_spaces_from_expectations(expectations),
        walls=_walls_for_storeys(["storey-1", "storey-2"]),
        doors=[
            (f"door-{index}", "storey-1", "storey-1-south-wall")
            for index in range(1, 6)
        ],
        windows=[
            (
                f"window-{index}",
                "storey-1" if index <= 4 else "storey-2",
                "storey-1-north-wall" if index <= 4 else "storey-2-north-wall",
            )
            for index in range(1, 10)
        ],
        include_opening_relationships_for_doors=True,
        include_opening_relationships_for_windows=False,
    )
    return _finalize_case(
        case_dir=case_dir,
        case_id="complex-two-storey",
        input_text=input_text,
        expected_facts=expected_facts,
        candidate=candidate,
        baseline=assess_no_false_accept_baseline(
            expectations,
            {
                "compile_reopen_success": True,
                "counts": {
                    "IfcBuildingStorey": 2,
                    "IfcSpace": 9,
                    "IfcDoor": 5,
                    "IfcWindow": 9,
                },
                "doors_by_storey": {"storey-1": 5, "storey-2": 0},
                "windows_with_opening_fill_count": 0,
                "containment_success": False,
            },
        ),
    )


def _write_three_storey_case(case_dir: Path) -> dict[str, Any]:
    source = SOURCE_FIXTURE_ROOT / "non-two-storey-three-level" / "design-brief.json"
    design_brief = json.loads(source.read_text(encoding="utf-8"))
    input_text = str(design_brief.get("original_request", "three-storey fixture"))
    _reset_case_dir(case_dir)
    _write_json(case_dir / "design-brief.json", design_brief)
    (case_dir / "input.txt").write_text(input_text + "\n", encoding="utf-8")
    expected_facts = build_expected_facts(
        case_id="non-two-storey-three-level",
        design_brief=design_brief,
    )
    _write_json(case_dir / "expected-facts.json", expected_facts)
    candidate = _candidate(
        storeys=["storey-1", "storey-2"],
        spaces=[("level-1-room", "storey-1"), ("level-2-room", "storey-2")],
        walls=[
            ("level-1-south-wall", "storey-1"),
            ("level-1-north-wall", "storey-1"),
            ("level-2-south-wall", "storey-2"),
            ("level-2-north-wall", "storey-2"),
        ],
        doors=[
            ("level-1-door", "storey-1", "level-1-south-wall"),
            ("level-2-door", "storey-2", "level-2-south-wall"),
        ],
        windows=[
            ("level-1-window", "storey-1", "level-1-north-wall"),
            ("level-2-window", "storey-2", "level-2-north-wall"),
        ],
        include_opening_relationships_for_doors=True,
        include_opening_relationships_for_windows=True,
    )
    return _finalize_case(
        case_dir=case_dir,
        case_id="non-two-storey-three-level",
        input_text=input_text,
        expected_facts=expected_facts,
        candidate=candidate,
    )


def _write_smoke_case(
    case_dir: Path,
    *,
    case_id: str,
    storeys: list[str],
    spaces: list[tuple[str, str]],
) -> dict[str, Any]:
    _reset_case_dir(case_dir)
    input_text = f"{case_id} regression smoke"
    (case_dir / "input.txt").write_text(input_text + "\n", encoding="utf-8")
    expected_facts = {
        "schema_version": "text2ifc/expected-facts/1.0",
        "case_id": case_id,
        "storeys": [{"id": storey} for storey in storeys],
        "storey_count": len(storeys),
        "spaces": [{"id": space, "storey": storey} for space, storey in spaces],
        "doors": [],
        "windows": [],
        "slabs": [],
        "roof": None,
        "stairs": [],
        "space_counts_by_storey": _counts_by_storey(
            [{"storey": storey} for _space, storey in spaces]
        ),
        "door_counts_by_storey": {},
        "window_counts_by_storey": {},
        "total_counts": {
            "IfcBuildingStorey": len(storeys),
            "IfcSpace": len(spaces),
            "IfcDoor": 0,
            "IfcWindow": 0,
        },
        "required_relationships": {
            "containment": {
                "storeys": len(storeys),
                "spaces": len(spaces),
                "doors": 0,
                "windows": 0,
            },
            "opening_fill": {"doors": 0, "windows": 0},
        },
    }
    _write_json(case_dir / "expected-facts.json", expected_facts)
    candidate = _candidate(
        storeys=storeys,
        spaces=spaces,
        walls=[],
        doors=[],
        windows=[],
        include_opening_relationships_for_doors=True,
        include_opening_relationships_for_windows=True,
    )
    return _finalize_case(
        case_dir=case_dir,
        case_id=case_id,
        input_text=input_text,
        expected_facts=expected_facts,
        candidate=candidate,
    )


def _finalize_case(
    *,
    case_dir: Path,
    case_id: str,
    input_text: str,
    expected_facts: Mapping[str, Any],
    candidate: Mapping[str, Any],
    baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    generator = case_dir / "generator"
    repair = case_dir / "repair"
    generator.mkdir(parents=True, exist_ok=True)
    repair.mkdir(parents=True, exist_ok=True)
    _write_json(generator / "candidate.json", dict(candidate))
    _write_json(generator / "validation.json", {"valid": True, "issues": []})
    _write_json(case_dir / "ifc-verification.json", {"success": True, "input_issues": [], "ifc_issues": []})
    _write_json(case_dir / "geometry-feedback.json", {"success": True, "issues": []})
    _write_json(repair / "route.json", {"route": "no_repair_needed"})
    gate_summary = write_gate_summary(case_dir=case_dir, case_id=case_id)
    route_decision = write_route_decision(
        case_dir=case_dir,
        audit={"recommendation": "accept", "blocking": False, "findings": []},
    )
    status = "accepted" if route_decision["route"] == "accept" else "blocked"
    case_summary = {
        "schema_version": "text2ifc/phase6.3-case-summary/1.0",
        "case_id": case_id,
        "input_text": input_text,
        "expected_counts": expected_facts.get("total_counts", {}),
        "gate_overall_status": gate_summary["overall_status"],
        "gate_applicability": {
            gate["name"]: gate["applicability"] for gate in gate_summary["gates"]
        },
        "gate_issue_codes": sorted(
            {
                code
                for gate in gate_summary["gates"]
                for code in gate.get("issue_codes", [])
            }
        ),
        "route": route_decision["route"],
        "owner_stage": route_decision["owner_stage"],
        "status": status,
        "baseline_status": baseline.get("status") if baseline else None,
        "non_two_storey_gate_route_covered": bool(
            route_decision["route_basis"].get("non_two_storey_evidence")
        ),
        "artifact_paths": [
            "expected-facts.json",
            "gate-summary.json",
            "route-decision.json",
            "report.md",
            "trace-manifest.json",
        ],
    }
    _write_json(case_dir / "case-summary.json", case_summary)
    _write_case_report(case_dir / "report.md", case_summary, gate_summary, route_decision)
    _write_trace_manifest(case_dir)
    return case_summary


def _expected_from_manual_review(
    *,
    case_id: str,
    input_text: str,
    expectations: Mapping[str, Any],
) -> dict[str, Any]:
    storeys = [
        {"id": storey, "elevation_mm": elevation}
        for storey, elevation in sorted(
            expectations.get("storey_elevations_mm", {}).items()
        )
    ]
    spaces = [
        {"id": space_id, "storey": storey}
        for storey, ids in expectations.get("space_ids_by_storey", {}).items()
        for space_id in ids
    ]
    doors = [
        {
            "id": f"door-{index}",
            "storey": "storey-1" if index <= 5 else "storey-2",
            "host_wall": "storey-1-south-wall" if index <= 5 else "storey-2-south-wall",
        }
        for index in range(1, int(expectations["door_counts"]["total"]) + 1)
    ]
    windows = [
        {
            "id": f"window-{index}",
            "storey": "storey-1" if index <= 4 else "storey-2",
            "host_wall": "storey-1-north-wall" if index <= 4 else "storey-2-north-wall",
        }
        for index in range(1, int(expectations["window_counts"]["total"]) + 1)
    ]
    return {
        "schema_version": "text2ifc/expected-facts/1.0",
        "case_id": case_id,
        "source": {"original_request_sha256": _text_hash(input_text)},
        "storeys": storeys,
        "storey_count": len(storeys),
        "spaces": spaces,
        "doors": doors,
        "windows": windows,
        "slabs": [{"id": "ground-slab"}, {"id": "second-floor-slab"}],
        "roof": {"id": "roof-slab"},
        "stairs": [{"id": "stair-1"}],
        "space_counts_by_storey": dict(expectations.get("space_counts", {})),
        "door_counts_by_storey": {
            key: value
            for key, value in expectations.get("door_counts", {}).items()
            if key != "total"
        },
        "window_counts_by_storey": {
            key: value
            for key, value in expectations.get("window_counts", {}).items()
            if key != "total"
        },
        "total_counts": {
            "IfcBuildingStorey": len(storeys),
            "IfcSpace": len(spaces),
            "IfcDoor": int(expectations["door_counts"]["total"]),
            "IfcWindow": int(expectations["window_counts"]["total"]),
        },
        "required_relationships": {
            "containment": {
                "storeys": len(storeys),
                "spaces": len(spaces),
                "doors": int(expectations["door_counts"]["total"]),
                "windows": int(expectations["window_counts"]["total"]),
            },
            "opening_fill": {
                "doors": int(expectations["door_counts"]["total"]),
                "windows": int(expectations["window_counts"]["total"]),
            },
        },
        "sidecar_role": "orchestration_expectations_not_bim_json_schema",
    }


def _candidate(
    *,
    storeys: list[str],
    spaces: list[tuple[str, str]],
    walls: list[tuple[str, str]],
    doors: list[tuple[str, str, str]],
    windows: list[tuple[str, str, str]],
    include_opening_relationships_for_doors: bool,
    include_opening_relationships_for_windows: bool,
) -> dict[str, Any]:
    entities = [_entity("building-1", "IfcBuilding", "project-1")]
    entities.extend(_entity(storey, "IfcBuildingStorey", "building-1") for storey in storeys)
    entities.extend(_entity(space, "IfcSpace", storey) for space, storey in spaces)
    entities.extend(_entity(wall, "IfcWall", storey) for wall, storey in walls)
    relationships = []
    for storey in storeys:
        contained = [
            entity["id"]
            for entity in entities
            if entity["id"] != storey
            and _placement_parent(entity) == storey
        ]
        if contained:
            relationships.append(_containment_relationship(storey, contained))
    for door_id, _storey, host_wall in doors:
        opening_id = f"opening-{door_id}"
        entities.append(_entity(opening_id, "IfcOpeningElement", host_wall))
        entities.append(_entity(door_id, "IfcDoor", opening_id))
        if include_opening_relationships_for_doors:
            relationships.extend(_opening_relationships(door_id, opening_id, host_wall))
    for window_id, _storey, host_wall in windows:
        opening_id = f"opening-{window_id}"
        entities.append(_entity(opening_id, "IfcOpeningElement", host_wall))
        entities.append(_entity(window_id, "IfcWindow", opening_id))
        if include_opening_relationships_for_windows:
            relationships.extend(_opening_relationships(window_id, opening_id, host_wall))
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": entities,
        "relationships": relationships,
        "provenance": {"source": "phase6.3-matrix"},
    }


def _entity(entity_id: str, ifc_class: str, relative_to: str) -> dict[str, Any]:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": {
            "ObjectPlacement": {
                "relative_to": relative_to,
                "origin": [0, 0, 0],
                "axis": [0, 0, 1],
                "ref_direction": [1, 0, 0],
            }
        },
        "property_sets": {},
        "provenance": {"source": "phase6.3-matrix"},
    }


def _containment_relationship(storey: str, contained: list[str]) -> dict[str, Any]:
    return {
        "id": f"contain-{storey}",
        "ifc_class": "IfcRelContainedInSpatialStructure",
        "attributes": {
            "RelatingStructure": storey,
            "RelatedElements": contained,
        },
        "provenance": {"source": "phase6.3-matrix"},
    }


def _opening_relationships(element_id: str, opening_id: str, host_wall: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"void-{opening_id}",
            "ifc_class": "IfcRelVoidsElement",
            "attributes": {
                "RelatingBuildingElement": host_wall,
                "RelatedOpeningElement": opening_id,
            },
            "provenance": {"source": "phase6.3-matrix"},
        },
        {
            "id": f"fill-{opening_id}",
            "ifc_class": "IfcRelFillsElement",
            "attributes": {
                "RelatingOpeningElement": opening_id,
                "RelatedBuildingElement": element_id,
            },
            "provenance": {"source": "phase6.3-matrix"},
        },
    ]


def _spaces_from_expectations(expectations: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [
        (space_id, storey)
        for storey, ids in expectations.get("space_ids_by_storey", {}).items()
        for space_id in ids
    ]


def _walls_for_storeys(storeys: list[str]) -> list[tuple[str, str]]:
    return [
        (f"{storey}-south-wall", storey)
        for storey in storeys
    ] + [
        (f"{storey}-north-wall", storey)
        for storey in storeys
    ]


def _counts_by_storey(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        storey = str(record["storey"])
        counts[storey] = counts.get(storey, 0) + 1
    return counts


def _placement_parent(entity: Mapping[str, Any]) -> str | None:
    attributes = entity.get("attributes", {})
    placement = attributes.get("ObjectPlacement", {}) if isinstance(attributes, Mapping) else {}
    return placement.get("relative_to") if isinstance(placement, Mapping) else None


def _case_by_id(cases: list[Mapping[str, Any]], case_id: str) -> Mapping[str, Any]:
    for case in cases:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def _write_case_report(
    path: Path,
    case_summary: Mapping[str, Any],
    gate_summary: Mapping[str, Any],
    route_decision: Mapping[str, Any],
) -> None:
    lines = [
        f"# {case_summary['case_id']}",
        "",
        f"- Original input: {case_summary['input_text']}",
        f"- Expected counts: `{json.dumps(case_summary['expected_counts'], sort_keys=True)}`",
        f"- Gate overall status: `{case_summary['gate_overall_status']}`",
        f"- Route: `{case_summary['route']}` owned by `{case_summary['owner_stage']}`",
        f"- Final status: `{case_summary['status']}`",
        f"- Gate issue codes: `{', '.join(case_summary['gate_issue_codes']) or 'none'}`",
        f"- Candidate hash: `{gate_summary['candidate_hash']}`",
        f"- Expected facts hash: `{gate_summary.get('expected_facts_hash')}`",
        f"- Gate summary hash source: `gate-summary.json`",
        f"- Route source issue codes: `{', '.join(route_decision['source_issue_codes']) or 'none'}`",
        f"- Non-two-storey route evidence: `{route_decision['route_basis'].get('non_two_storey_evidence')}`",
        "",
        "## Artifacts",
        "",
        "- expected-facts.json",
        "- generator/candidate.json",
        "- gate-summary.json",
        "- route-decision.json",
        "- trace-manifest.json",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_matrix_report(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# Phase 6.3 Matrix Report",
        "",
        f"- Case count: `{summary['case_count']}`",
        f"- False accept count: `{summary['false_accept_count']}`",
        f"- Non-two-storey gate/route covered: `{summary['non_two_storey_gate_route_covered']}`",
        "",
        "| Case | Status | Gate | Route | Expected counts |",
        "|---|---|---|---|---|",
    ]
    for case in summary["cases"]:
        counts = json.dumps(case["expected_counts"], sort_keys=True)
        lines.append(
            f"| {case['case_id']} | {case['status']} | {case['gate_overall_status']} | {case['route']} | `{counts}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_trace_manifest(root: Path) -> None:
    artifacts = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "trace-manifest.json":
            continue
        artifacts[path.relative_to(root).as_posix()] = "sha256:" + hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    manifest = {
        "schema_version": "text2ifc/run-trace-manifest/1.0",
        "trace_level": "compact",
        "artifact_count": len(artifacts),
        "artifact_hashes": artifacts,
    }
    _write_json(root / "trace-manifest.json", manifest)


def _reset_case_dir(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
