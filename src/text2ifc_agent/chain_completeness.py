"""Phase 6.4 chain correctness and completeness summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/phase6.4-chain-completeness/1.0"

REQUIRED_MATRIX_ROUTES = (
    "accepted",
    "ask_user",
    "regenerate_json",
    "revise_design_brief",
    "provider_retry",
    "blocked_as_unsupported",
)

CONTRACT_ONLY_ROUTES = (
    "repair_json",
    "gate_issue",
    "runtime_blocked",
)


def build_chain_completeness(
    *,
    live_root: Path | str,
    matrix_root: Path | str,
) -> dict[str, Any]:
    live_dir = Path(live_root)
    matrix_dir = Path(matrix_root)
    live = _read_json(live_dir / "live-chain-coverage-result.json")
    matrix = _read_json(matrix_dir / "matrix-result.json")

    matrix_routes = sorted(
        {
            str(case.get("route"))
            for case in matrix.get("cases", [])
            if case.get("route")
        }
    )
    missing_matrix_routes = [
        route for route in REQUIRED_MATRIX_ROUTES if route not in matrix_routes
    ]
    live_routes = sorted(
        {
            str(link.get("route"))
            for link in live.get("links", [])
            if link.get("route") and link.get("status") == "passed"
        }
    )
    live_links_passed = bool(live.get("all_required_links_passed"))
    false_accept_count = int(matrix.get("false_accept_count", 0))
    matrix_complete = not missing_matrix_routes and false_accept_count == 0
    complete = live_links_passed and matrix_complete
    result = {
        "schema_version": SCHEMA_VERSION,
        "overall_status": "phase6_4_evidence_complete_with_boundaries"
        if complete
        else "incomplete",
        "live_core_chain_complete": live_links_passed,
        "live_required_links": {
            "passed": int(live.get("passed_required_link_count", 0)),
            "total": int(live.get("required_link_count", 0)),
            "missing_link_ids": list(live.get("missing_required_link_ids", [])),
        },
        "deterministic_route_matrix_complete": matrix_complete,
        "false_accept_count": false_accept_count,
        "matrix_route_coverage": {
            "required_routes": list(REQUIRED_MATRIX_ROUTES),
            "covered_routes": matrix_routes,
            "missing_routes": missing_matrix_routes,
        },
        "live_route_coverage": {
            "covered_routes": live_routes,
            "boundary": (
                "Live evidence proves the accepted IFC path and the non-accept "
                "ask_user path. Other failure routes are deterministic/unit "
                "coverage in Phase 6.4 unless separately live-tested."
            ),
        },
        "not_live_verified_routes": sorted(
            set(REQUIRED_MATRIX_ROUTES).union(CONTRACT_ONLY_ROUTES).difference(live_routes)
        ),
        "contract_only_routes": list(CONTRACT_ONLY_ROUTES),
        "evidence_inputs": {
            "live_chain_coverage": str(live_dir / "live-chain-coverage-result.json"),
            "feedback_matrix": str(matrix_dir / "matrix-result.json"),
        },
    }
    _write_json(live_dir / "chain-completeness-result.json", result)
    _write_report(live_dir / "chain-completeness-report.md", result)
    return result


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.4 Chain Correctness and Completeness",
        "",
        f"- overall_status: `{result['overall_status']}`",
        f"- live_core_chain_complete: `{result['live_core_chain_complete']}`",
        f"- deterministic_route_matrix_complete: `{result['deterministic_route_matrix_complete']}`",
        f"- false_accept_count: `{result['false_accept_count']}`",
        "",
        "## Live Required Links",
        "",
        f"- passed: `{result['live_required_links']['passed']}` / `{result['live_required_links']['total']}`",
        f"- missing_link_ids: `{result['live_required_links']['missing_link_ids']}`",
        "",
        "## Deterministic Route Matrix",
        "",
        f"- required_routes: `{result['matrix_route_coverage']['required_routes']}`",
        f"- covered_routes: `{result['matrix_route_coverage']['covered_routes']}`",
        f"- missing_routes: `{result['matrix_route_coverage']['missing_routes']}`",
        "",
        "## Live Route Boundary",
        "",
        result["live_route_coverage"]["boundary"],
        "",
        f"- live_covered_routes: `{result['live_route_coverage']['covered_routes']}`",
        f"- not_live_verified_routes: `{result['not_live_verified_routes']}`",
        f"- contract_only_routes: `{result['contract_only_routes']}`",
        "",
        "## Evidence Inputs",
        "",
        f"- live_chain_coverage: `{result['evidence_inputs']['live_chain_coverage']}`",
        f"- feedback_matrix: `{result['evidence_inputs']['feedback_matrix']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
