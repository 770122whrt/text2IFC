import json
import re
from pathlib import Path

from scripts.ifc_repair.validate_success_cases import (
    validate_success_case_collection,
)
from scripts.ifc_repair.curate_phase11_door_proof import (
    _proof_classification,
)


ROOT = Path(__file__).resolve().parents[2]


def test_checked_in_success_case_collection_is_self_consistent() -> None:
    result = validate_success_case_collection()

    assert result.status == "passed", result.errors
    assert result.case_count >= 5
    assert result.operation_count >= 17
    assert result.reopened_ifc_count == result.case_count * 3

    phase11 = {
        item["case_id"]
        for item in result.cases
        if item["case_id"]
        in {
            "largebuilding-door-preserve-opening",
            "vvo-door-preserve-opening",
            "advancedproject-door-preserve-opening",
            "largebuilding-generated-door-type",
            "vvo-five-door-preserve-opening",
            "vvo-two-door-two-window-mixed",
        }
    }
    assert len(phase11) == 6


def test_phase11_proofs_follow_family_and_case_kind_directories() -> None:
    collection = ROOT / "dataset/processed/proof/ifc-repair-success-cases"
    manifest = json.loads(
        (collection / "manifest.json").read_text(encoding="utf-8")
    )
    cases = {item["case_id"]: item for item in manifest["cases"]}

    single_door_ids = {
        "largebuilding-door-preserve-opening",
        "vvo-door-preserve-opening",
        "advancedproject-door-preserve-opening",
        "largebuilding-generated-door-type",
    }
    for case_id in single_door_ids:
        case = cases[case_id]
        assert case["operation_family"] == "door"
        assert case["case_kind"] == "single"
        assert case["report"] == f"door/single/{case_id}/REPORT.md"

    batch = cases["vvo-five-door-preserve-opening"]
    assert batch["operation_family"] == "door"
    assert batch["case_kind"] == "batch"
    assert batch["report"] == (
        "door/batch/vvo-five-door-preserve-opening/REPORT.md"
    )

    mixed = cases["vvo-two-door-two-window-mixed"]
    assert mixed["operation_family"] == "mixed"
    assert mixed["case_kind"] == "mixed"
    assert mixed["report"] == (
        "mixed/door-window/vvo-two-door-two-window-mixed/REPORT.md"
    )


def test_phase11_curation_routes_by_operation_family_not_operation_type() -> None:
    door_only = {
        "operations": [
            {"operation_type": "add_door_with_opening_to_wall"},
            {"operation_type": "fill_existing_opening_with_door"},
        ]
    }
    assert _proof_classification(door_only, operation_count=2)[:3] == (
        "door",
        "batch",
        "door/batch",
    )

    door_window = {
        "operations": [
            {"operation_type": "fill_existing_opening_with_door"},
            {"operation_type": "add_window_with_opening_to_wall"},
        ]
    }
    assert _proof_classification(door_window, operation_count=2)[:3] == (
        "mixed",
        "mixed",
        "mixed/door-window",
    )


def test_mixed_door_window_proof_preserves_guid_free_targeting_evidence() -> None:
    case = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases/mixed/door-window"
        / "vvo-two-door-two-window-mixed"
    )
    request = (case / "input/request.txt").read_text(encoding="utf-8")
    assert re.findall(
        r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])",
        request,
    ) == []

    intent = json.loads(
        (case / "agent/repair-intent.json").read_text(encoding="utf-8")
    )
    assert all(
        operation["target_query"].get("global_id") is None
        for operation in intent["operations"]
    )
    resolution = json.loads(
        (case / "agent/target-resolution.json").read_text(encoding="utf-8")
    )
    assert resolution["status"] == "resolved"
    assert len(resolution["operations"]) == 4
