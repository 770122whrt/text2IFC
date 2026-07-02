import json
from pathlib import Path

from text2ifc_agent.gate_audit_bundle import (
    hash_json_file,
    validate_gate_summary_binding,
    write_gate_summary,
)


def test_gate_summary_binds_candidate_expected_facts_and_gate_evidence(tmp_path):
    case_dir = _write_gate_case(tmp_path)

    summary = write_gate_summary(case_dir=case_dir, case_id="gate-bundle")

    summary_path = case_dir / "gate-summary.json"
    assert summary_path.is_file()
    assert summary["schema_version"] == "text2ifc/gate-summary/1.0"
    assert summary["candidate_path"] == "generator/candidate.json"
    assert summary["candidate_hash"] == hash_json_file(
        case_dir / "generator" / "candidate.json"
    )
    assert summary["expected_facts_path"] == "expected-facts.json"
    assert summary["expected_facts_hash"] == hash_json_file(
        case_dir / "expected-facts.json"
    )
    assert summary["artifact_hashes"]["generator/candidate.json"] == summary[
        "candidate_hash"
    ]
    assert summary["artifact_hashes"]["expected-facts.json"] == summary[
        "expected_facts_hash"
    ]

    gates = {gate["name"]: gate for gate in summary["gates"]}
    assert gates["bim_json_validation"]["status"] == "passed"
    assert gates["semantic_coverage"]["status"] == "failed"
    assert gates["semantic_coverage"]["issue_codes"] == ["UNSUPPORTED_FACT"]
    assert gates["ifc_compile_reopen"]["status"] == "passed"
    assert gates["geometry"]["status"] == "failed"
    assert gates["geometry"]["issue_codes"] == ["ROOM_ENCLOSURE_OPEN"]
    assert summary["overall_status"] == "failed"


def test_gate_summary_binding_rejects_stale_candidate_hash(tmp_path):
    case_dir = _write_gate_case(tmp_path)
    summary = write_gate_summary(case_dir=case_dir, case_id="stale-bundle")
    _write_json(case_dir / "generator" / "candidate.json", {"changed": True})

    issues = validate_gate_summary_binding(case_dir=case_dir, summary=summary)

    assert issues == [
        {
            "code": "CANDIDATE_HASH_MISMATCH",
            "path": "/candidate_hash",
            "expected": hash_json_file(case_dir / "generator" / "candidate.json"),
            "actual": summary["candidate_hash"],
        }
    ]


def _write_gate_case(tmp_path: Path) -> Path:
    case_dir = tmp_path / "case"
    generator = case_dir / "generator"
    repair = case_dir / "repair"
    generator.mkdir(parents=True)
    repair.mkdir()
    _write_json(
        generator / "candidate.json",
        {
            "schema_version": "text2ifc/bim-json/2.0",
            "entities": [],
            "relationships": [],
        },
    )
    _write_json(generator / "validation.json", {"valid": True, "issues": []})
    _write_json(
        case_dir / "expected-facts.json",
        {
            "schema_version": "text2ifc/expected-facts/1.0",
            "storeys": [{"id": "storey-1"}],
        },
    )
    _write_json(
        case_dir / "semantic-coverage.json",
        {
            "valid": False,
            "blocking_facts": [
                {
                    "path": "/known_facts/door/opening_direction",
                    "coverage_state": "unsupported_draft",
                    "reason": "Unsupported fact.",
                }
            ],
        },
    )
    _write_json(case_dir / "ifc-verification.json", {"success": True, "input_issues": [], "ifc_issues": []})
    _write_json(
        case_dir / "geometry-feedback.json",
        {
            "success": False,
            "issues": [
                {
                    "code": "ROOM_ENCLOSURE_OPEN",
                    "path": "/spaces/space-1",
                    "message": "Room enclosure is open.",
                }
            ],
        },
    )
    _write_json(repair / "route.json", {"route": "no_repair_needed"})
    return case_dir


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
