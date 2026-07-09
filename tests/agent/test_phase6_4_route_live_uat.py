import json
from pathlib import Path


def test_route_live_uat_summary_separates_resolved_and_terminal_routes(tmp_path):
    from text2ifc_agent.route_live_uat import build_route_live_uat_summary

    output_root = tmp_path / "route-live-uat"
    _write_case(output_root, "regenerate_json", route="regenerate_json", status="auto_resolved_live")
    _write_case(output_root, "revise_design_brief", route="revise_design_brief", status="auto_resolved_live")
    _write_case(output_root, "repair_json", route="repair_json", status="auto_resolved_live")
    _write_case(output_root, "ask_user", route="ask_user", status="correct_terminal_live")
    _write_case(output_root, "blocked_as_unsupported", route="blocked_as_unsupported", status="correct_terminal_live")
    _write_case(output_root, "gate_issue", route="gate_issue", status="correct_terminal_live")
    _write_case(output_root, "runtime_blocked", route="runtime_blocked", status="correct_terminal_live")
    _write_case(output_root, "provider_retry", route="provider_retry", status="retry_control_live")

    summary = build_route_live_uat_summary(output_root)

    assert summary["schema_version"] == "text2ifc/phase6.4-route-live-uat/1.0"
    assert summary["all_required_routes_live_checked"] is True
    assert summary["auto_resolved_routes"] == ["regenerate_json", "repair_json", "revise_design_brief"]
    assert summary["correct_terminal_routes"] == [
        "ask_user",
        "blocked_as_unsupported",
        "gate_issue",
        "runtime_blocked",
    ]
    assert summary["retry_control_routes"] == ["provider_retry"]
    assert summary["missing_required_routes"] == []
    assert (output_root / "route-live-uat-summary.json").is_file()
    assert (output_root / "route-live-uat-report.md").is_file()


def test_route_live_uat_summary_reports_missing_required_routes(tmp_path):
    from text2ifc_agent.route_live_uat import build_route_live_uat_summary

    output_root = tmp_path / "route-live-uat"
    _write_case(output_root, "ask_user", route="ask_user", status="correct_terminal_live")

    summary = build_route_live_uat_summary(output_root)

    assert summary["all_required_routes_live_checked"] is False
    assert "regenerate_json" in summary["missing_required_routes"]


def _write_case(output_root: Path, case_id: str, *, route: str, status: str) -> None:
    payload = {
        "schema_version": "text2ifc/phase6.4-route-live-uat-case/1.0",
        "case_id": case_id,
        "route": route,
        "status": status,
        "provider": "deepseek-openai-compatible",
        "response_id": f"resp-{case_id}",
        "finish_reason": "stop",
        "model_output_valid": True,
        "evidence_paths": [f"{case_id}.json"],
    }
    path = output_root / "cases" / f"{case_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
