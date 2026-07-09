import json
from pathlib import Path


def test_chain_completeness_combines_live_links_and_route_matrix(tmp_path):
    from text2ifc_agent.chain_completeness import build_chain_completeness

    root = tmp_path / "phase6.4"
    _write_json(
        root / "live-chain-coverage-result.json",
        {
            "all_required_links_passed": True,
            "passed_required_link_count": 8,
            "required_link_count": 8,
            "links": [
                {"link_id": "accepted_user_input_to_design_brief", "status": "passed", "evidence_level": "live_model_verified"},
                {"link_id": "accepted_design_brief_to_bim_json", "status": "passed", "evidence_level": "live_model_verified"},
                {"link_id": "accepted_bim_json_to_deterministic_gates", "status": "passed", "evidence_level": "deterministic_verified"},
                {"link_id": "accepted_deterministic_gates_to_audit", "status": "passed", "evidence_level": "live_model_verified"},
                {"link_id": "accepted_audit_to_ifc", "status": "passed", "evidence_level": "artifact_verified"},
                {"link_id": "nonaccept_issues_to_ask_user", "status": "passed", "evidence_level": "artifact_verified", "route": "ask_user"},
            ],
        },
    )
    matrix_root = tmp_path / "matrix"
    _write_json(
        matrix_root / "matrix-result.json",
        {
            "false_accept_count": 0,
            "cases": [
                {"case_id": "accepted", "route": "accepted", "final_status": "accepted"},
                {"case_id": "ask-user", "route": "ask_user", "final_status": "draft"},
                {"case_id": "regen", "route": "regenerate_json", "final_status": "blocked"},
                {"case_id": "design", "route": "revise_design_brief", "final_status": "blocked"},
                {"case_id": "provider", "route": "provider_retry", "final_status": "blocked"},
                {"case_id": "unsupported", "route": "blocked_as_unsupported", "final_status": "blocked"},
            ],
        },
    )

    result = build_chain_completeness(live_root=root, matrix_root=matrix_root)

    assert result["schema_version"] == "text2ifc/phase6.4-chain-completeness/1.0"
    assert result["overall_status"] == "phase6_4_evidence_complete_with_boundaries"
    assert result["live_core_chain_complete"] is True
    assert result["deterministic_route_matrix_complete"] is True
    assert result["false_accept_count"] == 0
    assert result["matrix_route_coverage"]["missing_routes"] == []
    assert "repair_json" in result["not_live_verified_routes"]
    assert (root / "chain-completeness-result.json").is_file()
    assert (root / "chain-completeness-report.md").is_file()


def test_chain_completeness_fails_if_matrix_misses_required_route(tmp_path):
    from text2ifc_agent.chain_completeness import build_chain_completeness

    live_root = tmp_path / "live"
    matrix_root = tmp_path / "matrix"
    _write_json(
        live_root / "live-chain-coverage-result.json",
        {"all_required_links_passed": True, "passed_required_link_count": 8, "required_link_count": 8, "links": []},
    )
    _write_json(
        matrix_root / "matrix-result.json",
        {"false_accept_count": 0, "cases": [{"case_id": "accepted", "route": "accepted"}]},
    )

    result = build_chain_completeness(live_root=live_root, matrix_root=matrix_root)

    assert result["overall_status"] == "incomplete"
    assert result["deterministic_route_matrix_complete"] is False
    assert "ask_user" in result["matrix_route_coverage"]["missing_routes"]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
