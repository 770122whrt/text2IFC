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
            "dental-clinic-two-door-two-window-geometry-targeted",
        }
    }
    assert len(phase11) == 7
    phase11_summaries = [
        item
        for item in result.cases
        if "fill_existing_opening_with_door" in item["operation_types"]
        or "add_door_with_opening_to_wall" in item["operation_types"]
        if not item["case_id"].startswith("phase12-")
    ]
    assert len(phase11_summaries) >= 7
    assert all(
        item["independent_triplet_audit_publishable"] is True
        for item in phase11_summaries
    )
    assert all(
        item["audit_coverage"] == "strict_recomputed"
        and item["independent_l1_operation_count"] == item["operation_count"]
        and item["independent_l2_operation_count"] == item["operation_count"]
        and item["structural_audit_coverage"] == "not_applicable"
        for item in phase11_summaries
    )
    assert result.independently_recomputed_case_count >= len(phase11_summaries)
    assert result.legacy_unverifiable_case_count == 5
    assert len(result.limitations) == result.legacy_unverifiable_case_count
    legacy_windows = [
        item for item in result.cases if item["audit_coverage"] == "legacy_artifact_only"
    ]
    assert legacy_windows
    assert all(
        item["structural_audit_coverage"] == "not_applicable"
        for item in legacy_windows
    )


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

    for case_id in {
        "vvo-two-door-two-window-mixed",
        "dental-clinic-two-door-two-window-geometry-targeted",
    }:
        mixed = cases[case_id]
        assert mixed["operation_family"] == "mixed"
        assert mixed["case_kind"] == "mixed"
        assert mixed["report"] == (
            f"mixed/door-window/{case_id}/REPORT.md"
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


def test_dental_mixed_proof_uses_name_free_geometry_and_recreates_openings() -> None:
    case = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases/mixed/door-window"
        / "dental-clinic-two-door-two-window-geometry-targeted"
    )
    request = (case / "input/request.txt").read_text(encoding="utf-8")
    assert re.findall(
        r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])",
        request,
    ) == []

    intent = json.loads(
        (case / "agent/repair-intent.json").read_text(encoding="utf-8")
    )
    for operation in intent["operations"]:
        query = operation["target_query"]
        assert query.get("global_id") is None
        assert query.get("names") in (None, [])
        assert query.get("storey_name") is None
        assert len(query["geometry_constraints"]) == 4

    changeset = json.loads(
        (case / "changeset/bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    operation_types = [
        operation["operation_type"] for operation in changeset["operations"]
    ]
    assert operation_types.count("add_window_with_opening_to_wall") == 2
    assert operation_types.count("add_door_with_opening_to_wall") == 2
    assert "fill_existing_opening_with_door" not in operation_types

    source_manifest = json.loads(
        (case / "validation/source-run-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert source_manifest["damage"]["door_openings_removed"] is True
    assert source_manifest["damage"]["window_openings_removed"] is True
    assert len(source_manifest["damage"]["removed_windows"]) == 2
    assert all(
        item.get("name")
        for item in source_manifest["damage"]["removed_windows"]
    )
