from scripts.ifc_repair.validate_success_cases import (
    validate_success_case_collection,
)


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
