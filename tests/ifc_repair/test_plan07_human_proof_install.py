from pathlib import Path

from scripts.ifc_repair.install_plan07_human_proof import (
    DEFAULT_COLLECTION_ROOT,
    validate_plan07_layout,
)


def test_checked_in_plan07_human_proof_is_directly_reviewable() -> None:
    result = validate_plan07_layout(DEFAULT_COLLECTION_ROOT)

    assert result["status"] == "passed", result["errors"]
    assert result["case_count"] == 10
    assert result["repaired_case_count"] == 9
    assert result["no_repair_case_count"] == 1
    assert result["live_provider_calls"] == 11
    assert result["reopened_ifc_count"] == 28

    report = DEFAULT_COLLECTION_ROOT / "PLAN07-REPORT.md"
    assert report.is_file()
    assert "R1" in report.read_text(encoding="utf-8")

    sample_layout = (
        DEFAULT_COLLECTION_ROOT
        / "structural/batch/phase12-plan07-live-beam-column-complete"
    )
    assert (sample_layout / "01-original.ifc").is_file()
    assert (sample_layout / "02-damaged.ifc").is_file()
    assert (sample_layout / "03-repaired.ifc").is_file()
    assert (sample_layout / "input/request.txt").is_file()
    assert (sample_layout / "agent/repair-intent.json").is_file()
    assert (sample_layout / "changeset/bound-changeset.json").is_file()
    assert (sample_layout / "validation/evidence-decision.json").is_file()

    guard = (
        DEFAULT_COLLECTION_ROOT
        / "guard/unsupported/phase12-plan07-live-structural-program-guard"
    )
    assert (guard / "02-damaged.ifc").is_file()
    assert (guard / "NO-REPAIR.md").is_file()
    assert not (guard / "03-repaired.ifc").exists()
