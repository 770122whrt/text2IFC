"""Run the deterministic Phase 6.4 feedback-routing matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.feedback_loop import write_feedback_artifacts
from text2ifc_agent.issues import Issue, write_issues
from text2ifc_agent.run_report import build_phase6_4_review_report


MATRIX_SCHEMA_VERSION = "text2ifc/phase6.4-feedback-matrix/1.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT
        / "dataset"
        / "processed"
        / "agent-demo"
        / "phase6.4-feedback-routing-matrix",
    )
    args = parser.parse_args(argv)
    summary = run_matrix(args.output_root)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def run_matrix(output_root: Path | str) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    case_results = [_write_case(root, case) for case in _cases()]
    false_accepts = [
        case
        for case in case_results
        if case["final_status"] == "accepted"
        and (not case["deterministic_gates_passed"] or not case["audit_passed"])
    ]
    summary = {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "case_count": len(case_results),
        "accepted_count": sum(1 for case in case_results if case["final_status"] == "accepted"),
        "blocked_count": sum(1 for case in case_results if case["final_status"] == "blocked"),
        "draft_count": sum(1 for case in case_results if case["final_status"] == "draft"),
        "failed_count": sum(1 for case in case_results if case["final_status"] == "failed"),
        "false_accept_count": len(false_accepts),
        "cases": case_results,
        "matrix_report": "matrix-report.md",
    }
    _write_json(root / "matrix-result.json", summary)
    _write_matrix_report(root / "matrix-report.md", summary)
    return summary


def _write_case(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    case_dir = root / case["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "design-brief").mkdir(exist_ok=True)
    (case_dir / "generator").mkdir(exist_ok=True)
    (case_dir / "audit").mkdir(exist_ok=True)
    _write_text(case_dir / "input.txt", case["input"])
    _write_json(case_dir / "conversation.json", [{"role": "user", "content": case["input"]}])
    _write_json(
        case_dir / "design-brief" / "design-brief.json",
        {"status": "ready" if case["route"] != "ask_user" else "needs_clarification"},
    )
    _write_json(
        case_dir / "generator" / "candidate.json",
        {"schema_version": "bim-json/2.0", "case_id": case["case_id"]},
    )
    _write_json(case_dir / "generator" / "validation.json", {"valid": case["schema_passed"], "issues": []})
    _write_json(case_dir / "ifc-verification.json", {"success": case["compile_reopen_passed"]})
    _write_json(case_dir / "geometry-feedback.json", {"success": case["geometry_passed"], "issues": []})
    _write_json(
        case_dir / "gate-summary.json",
        {
            "overall_status": "passed" if case["deterministic_gates_passed"] else "failed",
            "gates": [],
        },
    )
    _write_json(
        case_dir / "audit" / "audit-report.json",
        {
            "recommendation": "accept" if case["audit_passed"] else "revise",
            "blocking": not case["audit_passed"],
            "findings": [],
        },
    )
    if case["route"] == "accepted":
        _write_text(case_dir / "output.ifc", "ISO-10303-21;\nEND-ISO-10303-21;")

    issues = [_case_issue(case)] if case["route"] != "accepted" else []
    write_issues(case_dir / "issues.json", issues)
    round_record = write_feedback_artifacts(
        case_dir,
        source_stage=case["source_stage"],
        issues=issues,
    )
    route_decision = round_record["route_decision"]
    case_result = {
        "schema_version": "text2ifc/phase6.4-case-result/1.0",
        "case_id": case["case_id"],
        "input_language": "zh-CN",
        "workflow_language": "en-US-control",
        "prompt_language": "zh-CN",
        "output_type": "ifc" if route_decision["final_status"] == "accepted" else "none",
        "schema_passed": bool(case["schema_passed"]),
        "compile_reopen_passed": bool(case["compile_reopen_passed"]),
        "deterministic_gates_passed": bool(case["deterministic_gates_passed"]),
        "audit_passed": bool(case["audit_passed"]),
        "final_status": route_decision["final_status"],
        "route": route_decision["route"],
        "failure_owner": issues[0].owner if issues else None,
        "blocking_issue_count": len(issues),
        "evidence_paths": [
            "input.txt",
            "conversation.json",
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "generator/validation.json",
            "ifc-verification.json",
            "geometry-feedback.json",
            "audit/audit-report.json",
            "issues.json",
            "route-decision.json",
            "feedback-rounds.json",
        ],
    }
    _write_json(case_dir / "case-result.json", case_result)
    build_phase6_4_review_report(case_dir=case_dir)
    return {
        "case_id": case_result["case_id"],
        "final_status": case_result["final_status"],
        "route": case_result["route"],
        "failure_owner": case_result["failure_owner"],
        "blocking_issue_count": case_result["blocking_issue_count"],
        "deterministic_gates_passed": case_result["deterministic_gates_passed"],
        "audit_passed": case_result["audit_passed"],
        "report": f"{case['case_id']}/report.md",
    }


def _case_issue(case: dict[str, Any]) -> Issue:
    return Issue(
        issue_id=f"issue_{case['case_id'].replace('-', '_')}_0001",
        source=case["source"],
        severity=case.get("severity", "blocking"),
        owner=case["owner"],
        issue_type=case["issue_type"],
        evidence=case["evidence"],
        suggested_route=case["route"],
        retryable=case.get("retryable", True),
    )


def _cases() -> list[dict[str, Any]]:
    accepted = {
        "source": "audit",
        "owner": "audit",
        "issue_type": "semantic_mismatch",
        "route": "accepted",
        "evidence": "No issue.",
        "source_stage": "final",
        "schema_passed": True,
        "compile_reopen_passed": True,
        "geometry_passed": True,
        "deterministic_gates_passed": True,
        "audit_passed": True,
    }
    return [
        {"case_id": "simple-accepted-ifc", "input": "创建一个完整简单房间。", **accepted},
        {"case_id": "two-room-smoke", "input": "创建两个相邻房间。", **accepted},
        {
            "case_id": "controlled-two-storey-route",
            "input": "创建两层住宅并保持楼层关系。",
            "source": "audit",
            "owner": "generator",
            "issue_type": "missing_vertical_connection",
            "route": "regenerate_json",
            "evidence": "Stair or vertical connection is missing.",
            "source_stage": "audit",
            "schema_passed": True,
            "compile_reopen_passed": True,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
        },
        {
            "case_id": "clarification-two-storey-route",
            "input": "创建两层建筑，但楼梯位置不知道。",
            "source": "semantic_validation",
            "owner": "user",
            "issue_type": "missing_required_fact",
            "route": "ask_user",
            "evidence": "Stair location is required from the user.",
            "source_stage": "design_brief",
            "schema_passed": False,
            "compile_reopen_passed": False,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
        },
        {
            "case_id": "ambiguous-two-storey-route",
            "input": "创建一个两层空间，布局随意。",
            "source": "audit",
            "owner": "design_brief",
            "issue_type": "changed_original_request",
            "route": "revise_design_brief",
            "evidence": "Design Brief over-specified ambiguous layout.",
            "source_stage": "audit",
            "schema_passed": True,
            "compile_reopen_passed": False,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
        },
        {
            "case_id": "provider-truncation",
            "input": "创建一个超长复杂建筑。",
            "source": "provider",
            "owner": "provider",
            "issue_type": "provider_truncation",
            "route": "provider_retry",
            "evidence": "Provider returned finish_reason=length.",
            "source_stage": "provider",
            "schema_passed": False,
            "compile_reopen_passed": False,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
        },
        {
            "case_id": "unsupported-compiler-feature",
            "input": "创建当前编译器不支持的复杂楼梯。",
            "source": "compiler",
            "owner": "compiler",
            "issue_type": "compiler_unsupported_feature",
            "route": "blocked_as_unsupported",
            "evidence": "Compiler cannot emit this feature yet.",
            "source_stage": "compiler",
            "schema_passed": True,
            "compile_reopen_passed": False,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
            "retryable": False,
        },
        {
            "case_id": "three-storey-dynamic-route",
            "input": "创建三层建筑并包含楼梯连接。",
            "source": "deterministic_gate",
            "owner": "generator",
            "issue_type": "missing_storey_assignment",
            "route": "regenerate_json",
            "evidence": "A non-two-storey assignment is missing without hard-coded room names.",
            "source_stage": "gate",
            "schema_passed": True,
            "compile_reopen_passed": True,
            "geometry_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
        },
    ]


def _write_matrix_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.4 Feedback Routing Matrix",
        "",
        f"- case_count: `{summary['case_count']}`",
        f"- accepted_count: `{summary['accepted_count']}`",
        f"- blocked_count: `{summary['blocked_count']}`",
        f"- draft_count: `{summary['draft_count']}`",
        f"- false_accept_count: `{summary['false_accept_count']}`",
        "",
        "## Cases",
        "",
    ]
    for case in summary["cases"]:
        lines.append(
            f"- `{case['case_id']}`: final_status=`{case['final_status']}`, "
            f"route=`{case['route']}`, report=[report.md]({case['report']})"
        )
    _write_text(path, "\n".join(lines))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
