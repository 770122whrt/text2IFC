import json
from pathlib import Path

from scripts.ifc_repair.audit_door_repair_triplet import audit_case


ROOT = Path(__file__).resolve().parents[2]
CASE = (
    ROOT
    / "dataset"
    / "processed"
    / "proof"
    / "ifc-repair-success-cases"
    / "mixed"
    / "door-window"
    / "vvo-authority-triplet-public-repair"
)
FIVE_DOOR_CASE = (
    ROOT
    / "dataset"
    / "processed"
    / "proof"
    / "ifc-repair-success-cases"
    / "door"
    / "batch"
    / "vvo-five-door-authority-public-repair"
)


def test_checked_in_vvo_triplet_has_authoritative_l0_l1_l2_release() -> None:
    evidence = audit_case(CASE, write=False)
    frozen = json.loads(
        (
            CASE / "validation" / "three-way-audit.json"
        ).read_text(encoding="utf-8")
    )
    release = json.loads(
        (
            CASE / "validation" / "release-decision.json"
        ).read_text(encoding="utf-8")
    )

    assert evidence["release_decision"] == release
    assert frozen["release_decision"] == release
    assert release["l0_pass"] is True
    assert release["l1_pass"] is True
    assert release["l2_pass"] is True
    assert release["publishable"] is True
    assert release["blocking_findings"] == []


def test_private_comparator_runs_after_repair_and_does_not_claim_exactness() -> None:
    evidence = audit_case(CASE, write=False)

    isolation = evidence["production_ground_truth_isolation"]
    private = evidence["private_original_to_repaired"]
    assert isolation["passed"] is True
    assert isolation["leaked_deleted_object_ids"] == []
    assert isolation["checked_private_deleted_object_count"] == 4
    assert isolation["private_comparator_started_after_repair"] is True
    assert private["private_exact_fidelity_pass"] is False
    assert evidence["release_decision"]["warnings"]
    assert {item["object_class"] for item in private["objects"]} == {
        "IfcDoor",
        "IfcWindow",
    }
    assert len(private["objects"]) == 4
    assert all(
        item["semantics"]["host_match"]
        and item["semantics"]["storey_match"]
        for item in private["objects"]
    )
    assert all(
        item["semantics"]["type_match"] is False
        for item in private["objects"]
    )


def test_vvo_mutation_and_production_views_keep_exact_business_counts() -> None:
    evidence = audit_case(CASE, write=False)

    mutation = evidence["private_original_to_damaged"]
    production = evidence["production_damaged_to_repaired"]["model_diff"]
    assert mutation["door_count_delta"] == -2
    assert mutation["window_count_delta"] == -2
    assert mutation["opening_count_delta"] == -2
    assert production["door_count_delta"] == 2
    assert production["window_count_delta"] == 2
    assert production["opening_count_delta"] == 2
    assert production["undeclared_added_roots"] == []


def test_vvo_five_door_public_repair_fills_every_retained_opening() -> None:
    evidence = audit_case(FIVE_DOOR_CASE, write=False)
    release = evidence["release_decision"]
    production = evidence["production_damaged_to_repaired"]

    assert release["l0_pass"] is True
    assert release["l1_pass"] is True
    assert release["l2_pass"] is True
    assert release["publishable"] is True
    assert release["blocking_findings"] == []
    assert production["model_diff"]["door_count_delta"] == 5
    assert production["model_diff"]["opening_count_delta"] == 0
    assert production["model_diff"]["undeclared_added_roots"] == []
    assert len(production["operation_checks"]) == 5
    assert all(
        item["valid"]
        and item["evidence"]["geometry_alignment"][
            "projected_overlap_ratio"
        ]
        >= 0.95
        for item in production["operation_checks"]
    )
