import json
import re
from pathlib import Path

from scripts.ifc_repair.validate_success_cases import (
    validate_success_case_collection,
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


def test_mixed_door_window_proof_preserves_guid_free_targeting_evidence() -> None:
    case = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases/door/offline"
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
