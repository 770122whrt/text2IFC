import json
from pathlib import Path

from text2ifc_agent.complex_fixture import (
    assess_no_false_accept_baseline,
    load_complex_fixture,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    ROOT / "dataset/processed/agent-demo/phase6.3-gate-audit/complex-two-storey"
)


def test_complex_two_storey_fixture_records_manual_review_truth():
    fixture = load_complex_fixture(FIXTURE_DIR)

    assert "IfcBuildingStorey" in fixture["input_text"]
    expectations = fixture["expectations"]
    assert expectations["storey_count"] == 2
    assert expectations["space_ids_by_storey"] == {
        "storey-1": ["living", "kitchen", "bathroom-1", "stair-room"],
        "storey-2": [
            "main-bedroom",
            "secondary-bedroom",
            "study",
            "bathroom-2",
            "corridor",
        ],
    }
    assert expectations["door_counts"] == {
        "total": 9,
        "storey-1": 5,
        "storey-2": 4,
    }
    assert expectations["window_counts"] == {
        "total": 9,
        "storey-1": 4,
        "storey-2": 5,
    }
    assert expectations["opening_fill_obligations"] == {
        "doors_require_opening_and_fill": True,
        "windows_require_opening_and_fill": True,
    }
    assert "second-floor missing doors" in expectations["known_gate_limitations"]


def test_reopenable_complex_candidate_with_missing_requested_facts_blocks():
    fixture = load_complex_fixture(FIXTURE_DIR)
    broken_candidate_evidence = {
        "compile_reopen_success": True,
        "counts": {
            "IfcBuildingStorey": 2,
            "IfcSpace": 9,
            "IfcDoor": 5,
            "IfcWindow": 9,
        },
        "doors_by_storey": {
            "storey-1": 5,
            "storey-2": 0,
        },
        "windows_with_opening_fill_count": 0,
        "containment_success": False,
    }

    result = assess_no_false_accept_baseline(
        fixture["expectations"],
        broken_candidate_evidence,
    )

    assert result["accepted"] is False
    assert result["compile_reopen_success"] is True
    assert result["status"] == "blocked"
    assert {
        issue["code"]
        for issue in result["issues"]
    } >= {
        "REQUESTED_DOORS_MISSING",
        "OPENING_FILL_RELATIONSHIPS_MISSING",
        "CONTAINMENT_INCOMPLETE",
    }


def test_fixture_manual_review_json_is_not_production_logic():
    fixture = load_complex_fixture(FIXTURE_DIR)
    metadata_path = FIXTURE_DIR / "expected-manual-review.json"
    raw = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert raw["usage"] == "manual_review_truth_for_phase6_3_wave0_only"
    assert fixture["expectations"]["production_rule"] is False
