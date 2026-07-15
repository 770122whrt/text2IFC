import json
from pathlib import Path


def test_live_chain_coverage_report_requires_real_model_and_gate_evidence(tmp_path):
    from text2ifc_agent.live_chain_coverage import build_live_chain_coverage

    root = tmp_path / "phase6.4-live"
    accepted = root / "runs" / "accepted-session"
    nonaccept = root / "runs" / "draft-session"
    _write_json(
        root / "smoke-json.json",
        {
            "status": "passed",
            "provider": "deepseek-openai-compatible",
            "response_id": "smoke-response",
            "finish_reason": "stop",
        },
    )
    _write_accepted_run(accepted)
    _write_nonaccept_run(nonaccept)

    result = build_live_chain_coverage(
        output_root=root,
        accepted_session_hash="accepted-session",
        nonaccept_session_hash="draft-session",
    )

    assert result["schema_version"] == "text2ifc/phase6.4-live-chain-coverage/1.0"
    assert result["provider"] == "deepseek-openai-compatible"
    assert result["all_required_links_passed"] is True
    assert result["missing_required_link_ids"] == []
    links = {link["link_id"]: link for link in result["links"]}
    assert links["provider_smoke_json"]["evidence_level"] == "live_model_verified"
    assert links["accepted_design_brief_to_bim_json"]["provider_response_ids"] == ["generator-response"]
    assert links["accepted_deterministic_gates_to_audit"]["provider_response_ids"] == ["audit-response"]
    assert links["accepted_audit_to_ifc"]["status"] == "passed"
    assert links["nonaccept_issues_to_ask_user"]["route"] == "ask_user"
    assert links["nonaccept_issues_to_ask_user"]["final_status"] == "draft"

    report_path = root / "live-chain-coverage-report.md"
    result_path = root / "live-chain-coverage-result.json"
    assert report_path.is_file()
    assert result_path.is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "accepted_design_brief_to_bim_json" in report
    assert "nonaccept_issues_to_ask_user" in report


def test_live_chain_coverage_fails_when_generator_live_metadata_is_missing(tmp_path):
    from text2ifc_agent.live_chain_coverage import build_live_chain_coverage

    root = tmp_path / "phase6.4-live"
    accepted = root / "runs" / "accepted-session"
    nonaccept = root / "runs" / "draft-session"
    _write_json(root / "smoke-json.json", {"status": "ok", "response_id": "smoke", "finish_reason": "stop"})
    _write_accepted_run(accepted)
    _write_nonaccept_run(nonaccept)
    (accepted / "generator" / "metrics.json").unlink()

    result = build_live_chain_coverage(
        output_root=root,
        accepted_session_hash="accepted-session",
        nonaccept_session_hash="draft-session",
    )

    assert result["all_required_links_passed"] is False
    assert "accepted_design_brief_to_bim_json" in result["missing_required_link_ids"]


def _write_accepted_run(run_dir: Path) -> None:
    _write_json(
        run_dir / "case-result.json",
        {
            "final_status": "accepted",
            "route": "accepted",
            "compile_reopen_passed": True,
            "deterministic_gates_passed": True,
            "audit_passed": True,
            "output_type": "ifc",
        },
    )
    _write_json(run_dir / "design-brief" / "design-brief.json", {"status": "ready"})
    _write_json(run_dir / "calls" / "01-design-brief" / "metrics.json", _metrics("design-response"))
    _write_json(run_dir / "calls" / "01-design-brief" / "response.raw.json", {"id": "design-response"})
    _write_json(run_dir / "generator" / "candidate.json", {"schema_version": "bim-json/2.0"})
    _write_json(run_dir / "generator" / "validation.json", {"valid": True})
    _write_json(run_dir / "generator" / "metrics.json", _metrics("generator-response"))
    _write_json(run_dir / "generator" / "trace" / "response.raw.json", {"id": "generator-response"})
    _write_json(run_dir / "gate-summary.json", {"overall_status": "passed"})
    _write_json(run_dir / "geometry-feedback.json", {"success": True})
    _write_json(run_dir / "ifc-verification.json", {"success": True})
    _write_json(run_dir / "audit" / "audit-report.json", {"recommendation": "accept"})
    _write_json(run_dir / "audit" / "metrics.json", _metrics("audit-response"))
    _write_json(run_dir / "audit" / "trace" / "response.raw.json", {"id": "audit-response"})
    _write_json(run_dir / "route-decision.json", {"final_status": "accepted", "route": "accepted"})
    _write_json(run_dir / "feedback-rounds.json", {"rounds": []})
    _write_text(run_dir / "output.ifc", "ISO-10303-21;\nEND-ISO-10303-21;\n")
    _write_text(run_dir / "report.md", "# accepted\n")


def _write_nonaccept_run(run_dir: Path) -> None:
    _write_json(
        run_dir / "case-result.json",
        {
            "final_status": "draft",
            "route": "ask_user",
            "compile_reopen_passed": False,
            "deterministic_gates_passed": False,
            "audit_passed": False,
            "output_type": "none",
        },
    )
    _write_json(run_dir / "calls" / "01-design-brief" / "metrics.json", _metrics("draft-response"))
    _write_json(run_dir / "calls" / "01-design-brief" / "response.raw.json", {"id": "draft-response"})
    _write_json(run_dir / "issues.json", {"issues": [{"issue_id": "missing-1"}]})
    _write_json(run_dir / "route-decision.json", {"final_status": "draft", "route": "ask_user"})
    _write_json(run_dir / "feedback-rounds.json", {"rounds": [{"route": "ask_user"}]})
    _write_text(run_dir / "report.md", "# draft\n")


def _metrics(response_id: str) -> dict:
    return {
        "response_id": response_id,
        "stop_reason": "stop",
        "model": "deepseek-v4-flash",
        "usage": {"total_tokens": 10},
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
