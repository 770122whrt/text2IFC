from __future__ import annotations

import json
from pathlib import Path

from scripts.ifc_repair import assemble_phase12_live_evidence_v2 as curator


ROOT = Path(__file__).resolve().parents[2]
LIVE_RUN = (
    ROOT
    / "dataset/processed/ifc-repair-runs/phase12-live-v2"
    / "uat-20260903T095045509630Z"
)


def test_persisted_v2_genuine_transcript_is_independently_auditable() -> None:
    result = json.loads(
        (LIVE_RUN / "live-uat-result.json").read_text(encoding="utf-8")
    )

    audit = curator.audit_live_uat_result_v2(result)

    assert audit["status"] == "passed"
    assert audit["transport_calls"] == 11
    assert audit["transport_calls_by_stage"] == {
        "stage1": 4,
        "property_resolution": 4,
        "stage2": 3,
    }
    assert audit["success_case_ids"] == [
        "complete",
        "clarification-resume",
        "window-semantic-canary",
    ]
    assert audit["no_repair_case_ids"] == ["program-guard"]


def test_v2_curator_builds_human_first_success_and_no_repair_cases(
    tmp_path: Path,
) -> None:
    payload = curator.curate(LIVE_RUN, tmp_path)
    bundle = Path(payload["proof_bundle"])

    assert payload["evidence_validation_status"] == "passed"
    assert payload["phase_acceptance_eligible"] is False
    assert payload["proof_validation_status"] == "pending_plan_12_14"
    assert payload["success_case_count"] == 3
    assert payload["no_repair_case_count"] == 1
    assert (bundle / "REPORT.md").is_file()
    assert (bundle / "provider-evidence/live-uat-result.json").is_file()

    complete = bundle / "cases/complete"
    clarification = bundle / "cases/clarification-resume"
    window = bundle / "cases/window-semantic-canary"
    guard = bundle / "cases/program-guard"
    for case_root in (complete, clarification, window):
        assert (case_root / "REPORT.md").is_file()
        assert (case_root / "request.txt").is_file()
        assert (case_root / "damaged.ifc").is_file()
        assert (case_root / "repaired.ifc").is_file()
        assert not (case_root / "NO-REPAIR.md").exists()
    assert (complete / "original.ifc").is_file()
    assert (clarification / "original.ifc").is_file()
    assert (window / "original.ifc").is_file()
    assert (guard / "REPORT.md").is_file()
    assert (guard / "request.txt").is_file()
    assert (guard / "damaged.ifc").is_file()
    assert (guard / "NO-REPAIR.md").is_file()
    assert not (guard / "repaired.ifc").exists()

    complete_proof = json.loads(
        (complete / "proof-result.json").read_text(encoding="utf-8")
    )
    clarification_proof = json.loads(
        (clarification / "proof-result.json").read_text(encoding="utf-8")
    )
    assert complete_proof["structural_restoration"]["coverage_mode"] == (
        "complete_damage_set"
    )
    assert clarification_proof["structural_restoration"]["coverage_mode"] == (
        "requested_operation_subset"
    )
    assert clarification_proof["structural_restoration"][
        "unrequested_damage_families"
    ] == ["beam"]
