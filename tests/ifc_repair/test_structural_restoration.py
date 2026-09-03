from __future__ import annotations

import json
import shutil
from pathlib import Path

import scripts.ifc_repair.run_phase12_offline as offline_runner
from scripts.ifc_repair.run_phase12_public_structural_repair import (
    run_public_repair,
)
from text2ifc_ifc_repair.mutation import remove_structural_members
from text2ifc_ifc_repair.structural_restoration import (
    audit_structural_restoration_case,
)


ROOT = Path(__file__).resolve().parents[2]
OLD_OFFSITE_CASE = (
    ROOT
    / "tests/fixtures/ifc_repair/phase12-plan07-offsite-known-failure"
)
VVO = ROOT / "dataset/ifc/train/vvo.ifc"
VVO_BEAM_ID = "17tPjyQtf2L9JnbXXmcTUF"
VVO_COLUMN_ID = "1rsYNObuDC4euALdw6WUK4"
VVO_ATOMIC_CASE_ID = "phase12-v2-vvo-beam-column-atomic-restoration"


def test_old_offsite_case_is_rejected_as_structural_restoration() -> None:
    audit = audit_structural_restoration_case(OLD_OFFSITE_CASE)

    assert audit["status"] == "failed"
    assert audit["restoration_eligible"] is False
    assert {
        "STRUCTURAL_RESTORATION_TARGET_NOT_RECONSTRUCTABLE",
        "STRUCTURAL_RESTORATION_STOREY_MISMATCH",
        "STRUCTURAL_RESTORATION_AXIS_MISMATCH",
    } <= {issue["code"] for issue in audit["issues"]}


def test_vvo_rectangular_pair_closes_the_structural_damage_delta(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    remove_structural_members(
        source_path=VVO,
        output_dir=fixture,
        beam_global_ids=(VVO_BEAM_ID,),
        column_global_ids=(VVO_COLUMN_ID,),
    )
    spec = offline_runner._structural_specs()[VVO_ATOMIC_CASE_ID]
    bundle = offline_runner._bundle(
        VVO_ATOMIC_CASE_ID,
        spec["request"],
        spec["operations"],
    )
    bundle_path = tmp_path / "request.json"
    bundle_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    case_root = tmp_path / "case"
    run_public_repair(
        damaged_ifc=fixture / "damaged.ifc",
        public_request_bundle=bundle_path,
        output_root=case_root,
    )
    shutil.copy2(VVO, case_root / "original.ifc")
    shutil.copy2(
        fixture / "mutation_manifest.private.json",
        case_root / "mutation_manifest.private.json",
    )

    audit = audit_structural_restoration_case(case_root)

    assert audit["status"] == "passed", audit["issues"]
    assert audit["restoration_eligible"] is True
    assert audit["axis_tolerance_mm"] == 0.01
    assert audit["section_tolerance_mm"] == 0.01
    assert len(audit["outcomes"]) == 2
    assert all(
        outcome["checks"]["target_reconstructable"]
        and outcome["checks"]["target_absent_in_damaged"]
        and outcome["checks"]["storey_matches"]
        and outcome["checks"]["repaired_storey_matches"]
        and outcome["checks"]["request_axis_error_mm"] <= 0.01
        and outcome["checks"]["request_section_error_mm"] <= 0.01
        and outcome["checks"]["repaired_axis_error_mm"] <= 0.01
        and outcome["checks"]["repaired_section_error_mm"] <= 0.01
        for outcome in audit["outcomes"]
    )


def test_request_scoped_audit_accepts_one_restored_member_without_hiding_other_damage(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture"
    remove_structural_members(
        source_path=VVO,
        output_dir=fixture,
        beam_global_ids=(VVO_BEAM_ID,),
        column_global_ids=(VVO_COLUMN_ID,),
    )
    spec = offline_runner._structural_specs()[
        "phase12-v2-vvo-column-material-absent-restoration"
    ]
    bundle = offline_runner._bundle(
        "request-scoped-column-restoration",
        spec["request"],
        spec["operations"],
    )
    bundle_path = tmp_path / "request.json"
    bundle_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    case_root = tmp_path / "case"
    run_public_repair(
        damaged_ifc=fixture / "damaged.ifc",
        public_request_bundle=bundle_path,
        output_root=case_root,
    )
    shutil.copy2(VVO, case_root / "original.ifc")
    shutil.copy2(
        fixture / "mutation_manifest.private.json",
        case_root / "mutation_manifest.private.json",
    )

    full_damage_audit = audit_structural_restoration_case(case_root)
    request_scoped_audit = audit_structural_restoration_case(
        case_root,
        coverage_mode="requested_operation_subset",
    )

    assert full_damage_audit["status"] == "failed"
    assert request_scoped_audit["status"] == "passed", request_scoped_audit["issues"]
    assert request_scoped_audit["restoration_eligible"] is True
    assert request_scoped_audit["coverage_mode"] == "requested_operation_subset"
    assert request_scoped_audit["unrequested_damage_families"] == ["beam"]
    assert [item["family"] for item in request_scoped_audit["outcomes"]] == [
        "column"
    ]
