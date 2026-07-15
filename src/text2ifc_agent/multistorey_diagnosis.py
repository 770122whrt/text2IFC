"""Summarize Phase 6.4 multistorey route-loop diagnosis runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/phase6.4-multistorey-diagnosis/1.0"

SYSTEM_CAPABILITY_OWNERS = {"compiler", "schema"}
SYSTEM_CAPABILITY_ROUTES = {"blocked_as_unsupported"}
ROUTE_LOOP_ROUTES = {"regenerate_json", "repair_json", "revise_design_brief"}


def build_multistorey_diagnosis_summary(root: Path | str) -> dict[str, Any]:
    output_root = Path(root)
    case_summaries = [_summarize_case(case_dir) for case_dir in _case_dirs(output_root)]
    capability_issue_types = sorted(
        {
            issue["issue_type"]
            for case in case_summaries
            for issue in case["issues"]
            if case["diagnosis_class"] == "system_capability_gap" and issue.get("issue_type")
        }
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "case_count": len(case_summaries),
        "accepted_ifc_count": sum(1 for case in case_summaries if case["accepted_ifc"]),
        "route_loop_fixable_count": sum(
            1 for case in case_summaries if case["diagnosis_class"] == "route_loop_fixable"
        ),
        "system_capability_gap_count": sum(
            1 for case in case_summaries if case["diagnosis_class"] == "system_capability_gap"
        ),
        "capability_gap_issue_types": capability_issue_types,
        "cases": case_summaries,
    }
    _write_json(output_root / "multistorey-diagnosis-summary.json", summary)
    _write_report(output_root / "multistorey-diagnosis-report.md", summary)
    return summary


def _case_dirs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "case-result.json").is_file()
    )


def _summarize_case(case_dir: Path) -> dict[str, Any]:
    case_result = _read_json(case_dir / "case-result.json")
    route_decision = _read_json(case_dir / "route-decision.json")
    issues_payload = _read_json(case_dir / "issues.json")
    issues = list(issues_payload.get("issues", [])) if isinstance(issues_payload.get("issues"), list) else []
    route = str(route_decision.get("route") or case_result.get("route") or "")
    final_status = str(route_decision.get("final_status") or case_result.get("final_status") or "")
    accepted_ifc = final_status == "accepted" and (case_dir / "output.ifc").is_file()
    return {
        "case_id": str(case_result.get("case_id") or case_dir.name),
        "final_status": final_status,
        "route": route,
        "accepted_ifc": accepted_ifc,
        "diagnosis_class": _diagnosis_class(route, issues, accepted_ifc),
        "issue_count": len(issues),
        "issue_owners": sorted({str(issue.get("owner")) for issue in issues if issue.get("owner")}),
        "issue_types": sorted({str(issue.get("issue_type")) for issue in issues if issue.get("issue_type")}),
        "issues": issues,
        "artifacts": {
            "report": str(case_dir / "report.md") if (case_dir / "report.md").is_file() else "",
            "ifc": str(case_dir / "output.ifc") if (case_dir / "output.ifc").is_file() else "",
            "case_result": str(case_dir / "case-result.json"),
            "route_decision": str(case_dir / "route-decision.json") if (case_dir / "route-decision.json").is_file() else "",
            "issues": str(case_dir / "issues.json") if (case_dir / "issues.json").is_file() else "",
        },
    }


def _diagnosis_class(route: str, issues: list[Any], accepted_ifc: bool) -> str:
    if accepted_ifc:
        return "accepted_ifc"
    owners = {str(issue.get("owner")) for issue in issues if isinstance(issue, dict)}
    if route in SYSTEM_CAPABILITY_ROUTES or owners & SYSTEM_CAPABILITY_OWNERS:
        return "system_capability_gap"
    if route in ROUTE_LOOP_ROUTES:
        return "route_loop_fixable"
    if route == "ask_user":
        return "user_fact_missing"
    return "blocked_or_unclear"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.4 Multistorey Route Loop Diagnosis",
        "",
        f"- case_count: `{summary['case_count']}`",
        f"- accepted_ifc_count: `{summary['accepted_ifc_count']}`",
        f"- route_loop_fixable_count: `{summary['route_loop_fixable_count']}`",
        f"- system_capability_gap_count: `{summary['system_capability_gap_count']}`",
        f"- capability_gap_issue_types: `{summary['capability_gap_issue_types']}`",
        "",
        "## Cases",
        "",
        "| Case | Final | Route | Diagnosis | Issues | Report | IFC |",
        "|---|---|---|---|---:|---|---|",
    ]
    for case in summary["cases"]:
        lines.append(
            f"| `{case['case_id']}` | `{case['final_status']}` | `{case['route']}` | "
            f"`{case['diagnosis_class']}` | `{case['issue_count']}` | "
            f"`{case['artifacts']['report']}` | `{case['artifacts']['ifc']}` |"
        )
    lines.extend(["", "## Findings", ""])
    for case in summary["cases"]:
        lines.append(f"### {case['case_id']}")
        lines.append("")
        lines.append(f"- diagnosis_class: `{case['diagnosis_class']}`")
        lines.append(f"- issue_owners: `{case['issue_owners']}`")
        lines.append(f"- issue_types: `{case['issue_types']}`")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
