import json
from pathlib import Path

from text2ifc_agent.gate_audit_bundle import gate_summary_hash, hash_json_file
from text2ifc_agent.route_decision import (
    ROUTE_DECISION_SCHEMA_VERSION,
    validate_route_decision_binding,
    write_route_decision,
)


def test_route_decision_accepts_when_gates_and_audit_pass(tmp_path):
    case_dir = _write_case(
        tmp_path,
        gates=[_gate("dynamic_entity_completeness", "passed", [])],
        overall_status="passed",
    )

    decision = write_route_decision(
        case_dir=case_dir,
        audit={"recommendation": "accept", "blocking": False, "findings": []},
    )

    assert decision["schema_version"] == ROUTE_DECISION_SCHEMA_VERSION
    assert decision["route"] == "accept"
    assert decision["owner_stage"] == "none"
    assert decision["allowed_next_action"] == "compile_or_report_acceptance"
    assert decision["candidate_hash"] == hash_json_file(
        case_dir / "generator" / "candidate.json"
    )
    assert decision["gate_summary_hash"] == gate_summary_hash(
        case_dir / "gate-summary.json"
    )


def test_route_decision_sends_design_brief_omission_back_to_design(tmp_path):
    case_dir = _write_case(
        tmp_path,
        gates=[
            _gate(
                "dynamic_entity_completeness",
                "failed",
                [
                    {
                        "code": "DESIGN_BRIEF_FACT_OMITTED",
                        "path": "/windows/storey-2",
                        "message": "Original input included a second-floor window but Design Brief omitted it.",
                    }
                ],
            )
        ],
    )

    decision = write_route_decision(case_dir=case_dir)

    assert decision["route"] == "design_revision_required"
    assert decision["owner_stage"] == "design_brief"
    assert decision["allowed_next_action"] == "rerun_design_brief_with_feedback"
    assert "DESIGN_BRIEF_FACT_OMITTED" in decision["source_issue_codes"]


def test_route_decision_sends_missing_entities_to_generator(tmp_path):
    case_dir = _write_case(
        tmp_path,
        gates=[
            _gate(
                "dynamic_entity_completeness",
                "failed",
                [
                    {
                        "code": "EXPECTED_ENTITY_MISSING",
                        "path": "/doors",
                        "expected_storey": "storey-2",
                    }
                ],
            )
        ],
    )

    decision = write_route_decision(case_dir=case_dir)

    assert decision["route"] == "generator_regeneration_required"
    assert decision["owner_stage"] == "generator"
    assert decision["allowed_next_action"] == "rerun_generator_with_gate_feedback"


def test_route_decision_sends_repairable_relationship_mismatch_to_local_repair(tmp_path):
    case_dir = _write_case(
        tmp_path,
        gates=[
            _gate(
                "dynamic_storey_containment",
                "failed",
                [
                    {
                        "code": "HOST_WALL_MISMATCH",
                        "path": "/windows/window-3/host_wall",
                        "expected_host_wall": "wall-l3-north",
                        "actual_host_wall": "wall-l1-north",
                    }
                ],
            )
        ],
    )

    decision = write_route_decision(case_dir=case_dir)

    assert decision["route"] == "local_repair_required"
    assert decision["owner_stage"] == "repair"
    assert decision["allowed_next_action"] == "run_local_repair_with_gate_feedback"


def test_route_decision_uses_non_two_storey_issue_evidence_without_special_case(tmp_path):
    case_dir = _write_case(
        tmp_path,
        gates=[
            _gate(
                "dynamic_storey_containment",
                "failed",
                [
                    {
                        "code": "EXPECTED_ENTITY_MISSING",
                        "path": "/doors/level-3-door",
                        "expected_storey": "storey-3",
                    }
                ],
            )
        ],
    )

    decision = write_route_decision(case_dir=case_dir)

    assert decision["route"] == "generator_regeneration_required"
    assert decision["owner_stage"] == "generator"
    assert decision["route_basis"]["non_two_storey_evidence"] is True


def test_route_decision_blocks_stale_hash_and_non_improving_attempt(tmp_path):
    stale_case = _write_case(
        tmp_path / "stale",
        gates=[_gate("dynamic_entity_completeness", "passed", [])],
        overall_status="passed",
    )
    decision = write_route_decision(case_dir=stale_case)
    _write_json(stale_case / "generator" / "candidate.json", {"changed": True})

    issues = validate_route_decision_binding(case_dir=stale_case, decision=decision)

    assert issues[0]["code"] == "ROUTE_CANDIDATE_HASH_MISMATCH"

    stalled_case = _write_case(
        tmp_path / "stalled",
        gates=[
            _gate(
                "dynamic_entity_completeness",
                "failed",
                [{"code": "EXPECTED_ENTITY_MISSING", "path": "/windows"}],
            )
        ],
    )
    stalled = write_route_decision(
        case_dir=stalled_case,
        attempt_index=1,
        previous_issue_count=1,
    )

    assert stalled["route"] == "blocked_failure"
    assert stalled["owner_stage"] == "orchestrator"
    assert "NON_IMPROVING_ROUTE_ATTEMPT" in stalled["source_issue_codes"]


def _write_case(
    root: Path,
    *,
    gates: list[dict],
    overall_status: str = "failed",
) -> Path:
    case_dir = root / "case"
    (case_dir / "generator").mkdir(parents=True)
    _write_json(
        case_dir / "generator" / "candidate.json",
        {
            "schema_version": "bim-json/2.0",
            "ifc_schema": "IFC2X3",
            "units": {"length": "MILLIMETRE"},
            "entities": [],
            "relationships": [],
            "provenance": {"source": "test-fixture"},
        },
    )
    _write_json(
        case_dir / "expected-facts.json",
        {
            "schema_version": "text2ifc/expected-facts/1.0",
            "case_id": "route-test",
        },
    )
    gate_summary = {
        "schema_version": "text2ifc/gate-summary/1.0",
        "case_id": "route-test",
        "candidate_path": "generator/candidate.json",
        "candidate_hash": hash_json_file(case_dir / "generator" / "candidate.json"),
        "expected_facts_path": "expected-facts.json",
        "expected_facts_hash": hash_json_file(case_dir / "expected-facts.json"),
        "artifact_hashes": {},
        "evidence": {},
        "gates": gates,
        "overall_status": overall_status,
    }
    _write_json(case_dir / "gate-summary.json", gate_summary)
    return case_dir


def _gate(name: str, status: str, issues: list[dict]) -> dict:
    return {
        "name": name,
        "applicability": "applicable",
        "status": status,
        "basis": "test fixture",
        "issue_count": len(issues),
        "issues": issues,
        "issue_codes": sorted({issue["code"] for issue in issues}),
        "source_paths": ["expected-facts.json", "generator/candidate.json"],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
