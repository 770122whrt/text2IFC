from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell
import pytest

from scripts.ifc_repair.curate_phase12_structural_proof import curate
from scripts.ifc_repair.run_phase12_offline import run_offline_matrix
from scripts.ifc_repair.validate_success_cases import (
    validate_success_case_collection,
)


SUCCESS_CASE_IDS = {
    "phase12-d7n-beam-loadbearing",
    "phase12-d7n-column-loadbearing",
    "phase12-d7n-beam-column-atomic",
    "phase12-vvo-beam-material-present",
    "phase12-vvo-column-material-absent",
    "phase12-vvo-door-window-beam-column-atomic",
}
FAILURE_CASE_IDS = {
    "phase12-d7n-beam-column-rollback",
    "phase12-vvo-door-window-beam-column-rollback",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def phase12_offline_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("phase12-offline") / "run"
    result = run_offline_matrix(output)
    assert result["status"] == "passed"
    return output


def test_fixed_matrix_covers_frozen_structural_and_mixed_contract(
    phase12_offline_run: Path,
) -> None:
    summary = _read(phase12_offline_run / "run-summary.json")
    assert {item["case_id"] for item in summary["accepted_cases"]} == (
        SUCCESS_CASE_IDS
    )
    assert {item["case_id"] for item in summary["failed_cases"]} == (
        FAILURE_CASE_IDS
    )
    assert summary["coverage"] == {
        "beam_only": True,
        "column_only": True,
        "beam_column_atomic": True,
        "beam_loadbearing": True,
        "column_loadbearing": True,
        "material_present": True,
        "material_absent": True,
        "rollback": True,
        "door_window_beam_column_atomic": True,
        "door_window_beam_column_rollback": True,
    }
    assert summary["evidence_scope"] == "cross_scene_same_family_bimnet"


def test_every_accepted_source_case_is_hash_bound_reopened_and_public_only(
    phase12_offline_run: Path,
) -> None:
    summary = _read(phase12_offline_run / "run-summary.json")
    for record in summary["accepted_cases"]:
        case = phase12_offline_run / record["relative_path"]
        manifest = _read(case / "manifest.json")
        assert manifest["status"] == "passed"
        assert manifest["provider_evidence_mode"] == (
            "offline_bound_deterministic"
        )
        assert manifest["synthetic_fallback_used"] is False
        assert manifest["source"]["schema"] == "IFC2X3"
        for entry in manifest["artifacts"].values():
            artifact = case / entry["path"]
            assert artifact.is_file()
            assert artifact.stat().st_size == entry["bytes"]
            assert _sha256(artifact) == entry["sha256"]
        for name in ("original.ifc", "damaged.ifc", "repaired.ifc"):
            assert ifcopenshell.open(str(case / name)).schema == "IFC2X3"

        boundary = _read(case / "production-boundary.json")
        assert boundary["original_ifc_supplied"] is False
        assert boundary["mutation_manifest_supplied"] is False
        assert boundary["deleted_object_ids_supplied"] is False
        assert boundary["private_comparator_available_during_repair"] is False

        private = _read(case / "mutation_manifest.private.json")
        private_tokens = {
            str(target["entity"]["global_id"])
            for target in private["targets"]
        } | {
            str(target["entity"]["step_id"])
            for target in private["targets"]
            if target["entity"].get("step_id") is not None
        }
        public_text = "\n".join(
            (case / name).read_text(encoding="utf-8")
            for name in (
                "request.txt",
                "repair-intent.json",
                "target-resolution.json",
                "semantic-manifests.json",
                "changeset.json",
                "production-boundary.json",
            )
            if (case / name).is_file()
        )
        assert all(token not in public_text for token in private_tokens)


def test_four_family_case_is_one_success_and_one_real_rollback(
    phase12_offline_run: Path,
) -> None:
    success = (
        phase12_offline_run
        / "accepted"
        / "phase12-vvo-door-window-beam-column-atomic"
    )
    changeset = _read(success / "changeset.json")
    application = _read(success / "application.json")
    assert len(changeset["operations"]) == 6
    assert {
        item["operation_type"] for item in changeset["operations"]
    } == {
        "add_window_with_opening_to_wall",
        "fill_existing_opening_with_door",
        "add_beam",
        "add_column",
    }
    assert application["valid"] is True
    assert application["published"] is True

    failed = (
        phase12_offline_run
        / "failed"
        / "phase12-vvo-door-window-beam-column-rollback"
    )
    failure = _read(failed / "failure.json")
    assert failure["published"] is False
    assert failure["source_unchanged"] is True
    assert failure["blocking_code"]
    assert not (failed / "repaired.ifc").exists()


def test_fixed_structural_case_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    only = ("phase12-d7n-beam-loadbearing",)
    run_offline_matrix(first, case_ids=only)
    run_offline_matrix(second, case_ids=only)
    for name in ("damaged.ifc", "repaired.ifc", "changeset.json"):
        assert _sha256(first / "accepted" / only[0] / name) == _sha256(
            second / "accepted" / only[0] / name
        )


def test_curator_accepts_only_strict_cases_and_states_scope_honestly(
    tmp_path: Path,
    phase12_offline_run: Path,
) -> None:
    collection = tmp_path / "proof"
    collection.mkdir()
    (collection / "manifest.json").write_text(
        json.dumps({"case_count": 0, "cases": []}) + "\n",
        encoding="utf-8",
    )
    (collection / "README.md").write_text(
        "# IFC repair success cases\n",
        encoding="utf-8",
    )

    result = curate(phase12_offline_run, collection)

    assert result["status"] == "passed"
    assert result["case_count"] == len(SUCCESS_CASE_IDS)
    manifest = _read(collection / "manifest.json")
    structural = [
        item
        for item in manifest["cases"]
        if item.get("phase") == "12"
        and item.get("provider_evidence_mode")
        == "offline_bound_deterministic"
    ]
    assert {item["case_id"] for item in structural} == SUCCESS_CASE_IDS
    assert not FAILURE_CASE_IDS & {item["case_id"] for item in manifest["cases"]}
    assert manifest["evidence_scope"] == "cross_scene_same_family_bimnet"
    readme = (collection / "README.md").read_text(encoding="utf-8")
    assert (
        "Cross-scene, same-family BIMNet evidence only; "
        "not cross-dataset generalization."
    ) in readme

    validation = validate_success_case_collection(collection)
    assert validation.status == "passed", validation.errors
    assert validation.independently_recomputed_case_count == len(
        SUCCESS_CASE_IDS
    )
