"""Summaries for Phase 6.4 route-level live UAT evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/phase6.4-route-live-uat/1.0"
CASE_SCHEMA_VERSION = "text2ifc/phase6.4-route-live-uat-case/1.0"

REQUIRED_ROUTES = (
    "ask_user",
    "regenerate_json",
    "revise_design_brief",
    "repair_json",
    "provider_retry",
    "blocked_as_unsupported",
    "gate_issue",
    "runtime_blocked",
)

AUTO_RESOLVED_STATUS = "auto_resolved_live"
CORRECT_TERMINAL_STATUS = "correct_terminal_live"
RETRY_CONTROL_STATUS = "retry_control_live"


def build_route_live_uat_summary(output_root: Path | str) -> dict[str, Any]:
    root = Path(output_root)
    cases = [_read_json(path) for path in sorted((root / "cases").glob("*.json"))]
    passed_cases = [
        case
        for case in cases
        if case.get("finish_reason") == "stop"
        and case.get("model_output_valid") is True
        and case.get("response_id")
    ]
    covered_routes = sorted({str(case.get("route")) for case in passed_cases if case.get("route")})
    missing = [route for route in REQUIRED_ROUTES if route not in covered_routes]
    auto_resolved = sorted(
        str(case["route"])
        for case in passed_cases
        if case.get("status") == AUTO_RESOLVED_STATUS
    )
    correct_terminal = sorted(
        str(case["route"])
        for case in passed_cases
        if case.get("status") == CORRECT_TERMINAL_STATUS
    )
    retry_control = sorted(
        str(case["route"])
        for case in passed_cases
        if case.get("status") == RETRY_CONTROL_STATUS
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "all_required_routes_live_checked": not missing,
        "required_routes": list(REQUIRED_ROUTES),
        "covered_routes": covered_routes,
        "missing_required_routes": missing,
        "auto_resolved_routes": auto_resolved,
        "correct_terminal_routes": correct_terminal,
        "retry_control_routes": retry_control,
        "case_count": len(cases),
        "passed_case_count": len(passed_cases),
        "cases": [
            {
                "case_id": case.get("case_id"),
                "route": case.get("route"),
                "status": case.get("status"),
                "response_id": case.get("response_id"),
                "finish_reason": case.get("finish_reason"),
                "evidence_paths": case.get("evidence_paths", []),
            }
            for case in cases
        ],
        "boundary": (
            "Routes with auto_resolved_live prove a live model correction action. "
            "Routes with correct_terminal_live prove the workflow should stop, ask the user, "
            "or require human/developer review instead of fabricating a fix. "
            "provider_retry proves retry-control evidence, not model self-repair."
        ),
    }
    _write_json(root / "route-live-uat-summary.json", summary)
    _write_report(root / "route-live-uat-report.md", summary)
    return summary


def _read_json(path: Path) -> dict[str, Any]:
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


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.4 Route-Level Live UAT",
        "",
        f"- all_required_routes_live_checked: `{summary['all_required_routes_live_checked']}`",
        f"- passed_case_count: `{summary['passed_case_count']}` / `{summary['case_count']}`",
        f"- missing_required_routes: `{summary['missing_required_routes']}`",
        "",
        "## Route Classes",
        "",
        f"- auto_resolved_routes: `{summary['auto_resolved_routes']}`",
        f"- correct_terminal_routes: `{summary['correct_terminal_routes']}`",
        f"- retry_control_routes: `{summary['retry_control_routes']}`",
        "",
        "## Boundary",
        "",
        summary["boundary"],
        "",
        "## Cases",
        "",
        "| Case | Route | Status | Response ID | Evidence |",
        "|---|---|---|---|---|",
    ]
    for case in summary["cases"]:
        paths = "<br>".join(f"`{path}`" for path in case.get("evidence_paths", [])) or "-"
        lines.append(
            f"| `{case.get('case_id')}` | `{case.get('route')}` | `{case.get('status')}` | "
            f"`{case.get('response_id')}` | {paths} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
