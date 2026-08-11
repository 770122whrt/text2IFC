from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import ifcopenshell
import pytest

import scripts.ifc_repair.run_phase12_public_structural_repair as structural_runner
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
REQUIRED_COVERAGE = {
    "beam_only",
    "column_only",
    "beam_column_atomic",
    "beam_loadbearing",
    "column_loadbearing",
    "material_present",
    "material_absent",
    "rollback",
    "door_window_beam_column_atomic",
    "door_window_beam_column_rollback",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _public_beam_bundle() -> dict:
    return {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "case_id": "phase12-final-gate-failure",
        "request_id": "request-phase12-final-gate-failure",
        "changeset_id": "changeset-phase12-final-gate-failure",
        "request": "Add one horizontal rectangular Beam.",
        "operations": [
            {
                "operation_id": "phase12-final-gate-failure-beam-1",
                "operation_type": "add_beam",
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "global_id": "0K_MqVdrL0JOCMi_Gblgiw",
                },
                "parameters": {
                    "axis": {
                        "start": {
                            "x_mm": 140000,
                            "y_mm": 140000,
                            "z_mm": 0,
                        },
                        "end": {
                            "x_mm": 143000,
                            "y_mm": 144000,
                            "z_mm": 0,
                        },
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 300,
                        "height_mm": 500,
                    },
                },
                "property_intents": [],
                "attribute_intents": [],
            }
        ],
    }


def _minimal_failure_matrix(root: Path) -> Path:
    accepted = [
        {
            "case_id": case_id,
            "status": "passed",
            "relative_path": f"accepted/{case_id}",
            "operation_count": 1,
            "operation_types": ["add_beam"],
        }
        for case_id in sorted(SUCCESS_CASE_IDS)
    ]
    failed_cases = []
    for case_id in sorted(FAILURE_CASE_IDS):
        case_root = root / "failed" / case_id
        artifact_root = (
            case_root / "attempt"
            if case_id == "phase12-d7n-beam-column-rollback"
            else case_root
        )
        artifact_root.mkdir(parents=True)
        damaged = artifact_root / "damaged.ifc"
        damaged.write_bytes(b"actual damaged IFC bytes")
        fingerprint = _sha256(damaged)
        (artifact_root / "changeset.json").write_text(
            json.dumps({"base_model_fingerprint": fingerprint}) + "\n",
            encoding="utf-8",
        )
        application = {
            "valid": False,
            "published": False,
            "issues": [{"code": "STRUCTURAL_SAME_AXIS_OVERLAP"}],
        }
        (artifact_root / "application.json").write_text(
            json.dumps(application) + "\n",
            encoding="utf-8",
        )
        failure = {
            "case_id": case_id,
            "status": "failed_expected",
            "valid": False,
            "published": False,
            "blocking_code": "STRUCTURAL_SAME_AXIS_OVERLAP",
            "source_unchanged": True,
            "damaged_ifc_sha256": fingerprint,
        }
        (case_root / "failure.json").write_text(
            json.dumps(failure) + "\n",
            encoding="utf-8",
        )
        failed_cases.append(failure)
    summary = {
        "status": "passed",
        "matrix_complete": True,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "accepted_cases": accepted,
        "failed_cases": failed_cases,
        "coverage": {key: True for key in REQUIRED_COVERAGE},
    }
    (root / "run-summary.json").write_text(
        json.dumps(summary) + "\n",
        encoding="utf-8",
    )
    return root


def _single_case_collection(
    source: Path,
    destination: Path,
    *,
    case_id: str,
) -> Path:
    collection = _read(source / "manifest.json")
    entry = next(item for item in collection["cases"] if item["case_id"] == case_id)
    relative_case = Path(entry["files"]).parent
    destination.mkdir()
    shutil.copytree(source / relative_case, destination / relative_case)
    (destination / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": collection.get(
                    "schema_version",
                    "text2ifc/ifc-repair-success-collection/0.1",
                ),
                "case_count": 1,
                "cases": [entry],
                "evidence_scope": collection.get("evidence_scope"),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


@pytest.fixture(scope="module")
def phase12_offline_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("phase12-offline") / "run"
    result = run_offline_matrix(output)
    assert result["status"] == "passed"
    return output


@pytest.fixture(scope="module")
def phase12_curated(
    tmp_path_factory: pytest.TempPathFactory,
    phase12_offline_run: Path,
) -> Path:
    collection = tmp_path_factory.mktemp("phase12-curated") / "proof"
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
    return collection


@pytest.mark.parametrize(
    ("failed_gate", "error_code", "error_type"),
    (
        (
            "evaluation",
            "PUBLIC_STRUCTURAL_EVALUATION_FAILED",
            RuntimeError,
        ),
        (
            "preservation",
            "PUBLIC_STRUCTURAL_PRESERVATION_FAILED",
            RuntimeError,
        ),
        (
            "finalization",
            "PUBLIC_STRUCTURAL_FINALIZATION_FAILED",
            OSError,
        ),
    ),
)
def test_public_runner_does_not_publish_before_all_final_gates_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_gate: str,
    error_code: str,
    error_type: type[Exception],
) -> None:
    bundle = tmp_path / "request.json"
    bundle.write_text(
        json.dumps(_public_beam_bundle(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "output"
    if failed_gate == "evaluation":
        monkeypatch.setattr(
            structural_runner,
            "evaluation_to_dict",
            lambda _evaluation: {"complete_repair_success": False},
        )
    elif failed_gate == "preservation":
        monkeypatch.setattr(
            structural_runner,
            "compare_ifc_models",
            lambda *_args, **_kwargs: {
                "complete_preservation_success": False
            },
        )
    else:
        real_write = structural_runner._write
        failure_injected = False

        def fail_final_application_write(path: Path, value: object) -> None:
            nonlocal failure_injected
            output_path = (
                value.get("output", {}).get("path", "")
                if isinstance(value, dict)
                and isinstance(value.get("output"), dict)
                else ""
            )
            if (
                path.name == "application.json"
                and str(output_path).endswith("repaired.ifc")
                and not str(output_path).endswith("repaired.candidate.ifc")
                and not failure_injected
            ):
                failure_injected = True
                raise OSError("injected final application write failure")
            real_write(path, value)

        monkeypatch.setattr(
            structural_runner,
            "_write",
            fail_final_application_write,
        )

    with pytest.raises(error_type):
        structural_runner.run_public_repair(
            damaged_ifc=Path("dataset/ifc/test/d7n.ifc"),
            public_request_bundle=bundle,
            output_root=output,
        )

    assert not (output / "repaired.ifc").exists()
    assert not list(output.glob("*.candidate.ifc"))
    application = _read(output / "application.json")
    assert application["valid"] is True
    assert application["published"] is False
    assert application["output"] is None
    assert application["issues"][0]["code"] == error_code


@pytest.mark.parametrize("tamper", ("damaged", "blocking_code"))
def test_curator_independently_binds_failure_input_and_first_cause(
    tmp_path: Path,
    tamper: str,
) -> None:
    source = _minimal_failure_matrix(tmp_path / "source")
    failure_root = (
        source
        / "failed"
        / "phase12-d7n-beam-column-rollback"
    )
    artifact_root = failure_root / "attempt"
    summary_path = source / "run-summary.json"
    summary = _read(summary_path)
    failure_path = failure_root / "failure.json"
    failure = _read(failure_path)
    application_path = artifact_root / "application.json"
    application = _read(application_path)
    if tamper == "damaged":
        (artifact_root / "damaged.ifc").write_bytes(b"tampered damaged IFC")
        expected_error = "PHASE12_FAILURE_INPUT_FINGERPRINT_MISMATCH"
    else:
        failure["blocking_code"] = "UNRELATED_FAILURE"
        application["issues"][0]["code"] = "UNRELATED_FAILURE"
        expected_error = "PHASE12_FAILURE_CAUSE_MISMATCH"
        failure_path.write_text(json.dumps(failure) + "\n", encoding="utf-8")
        application_path.write_text(
            json.dumps(application) + "\n",
            encoding="utf-8",
        )
        for record in summary["failed_cases"]:
            if record["case_id"] == failure["case_id"]:
                record.update(failure)
        summary_path.write_text(json.dumps(summary) + "\n", encoding="utf-8")

    collection = tmp_path / "collection"
    collection.mkdir()
    (collection / "manifest.json").write_text(
        json.dumps({"case_count": 0, "cases": []}) + "\n",
        encoding="utf-8",
    )
    (collection / "README.md").write_text("# Proof\n", encoding="utf-8")
    with pytest.raises(ValueError, match=expected_error):
        curate(source, collection)


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

    expected_psets = {
        "phase12-d7n-beam-loadbearing": (
            "beam is load bearing",
            "Pset_BeamCommon.LoadBearing",
        ),
        "phase12-d7n-column-loadbearing": (
            "column is load bearing",
            "Pset_ColumnCommon.LoadBearing",
        ),
    }
    for case_id, (phrase, canonical_path) in expected_psets.items():
        case = phase12_offline_run / "accepted" / case_id
        intent = _read(case / "repair-intent.json")
        claim = intent["operations"][0]["property_intents"][0]
        assert claim == {
            "intent_kind": "natural_language_property",
            "property_phrase": phrase,
            "raw_value": True,
            "raw_unit": None,
            "scope": "occurrence_direct",
            "source": claim["source"],
        }
        resolution = _read(case / "target-resolution.json")
        evidence = resolution["property_resolutions"][0]
        assert evidence["decision"]["status"] == "standard_resolved"
        assert evidence["decision"]["reason_code"] == "REVIEWED_ALIAS_EXACT"
        exact = evidence["decision"]["exact_intent"]
        assert f"{exact['set_name']}.{exact['property_name']}" == canonical_path
        assert exact["requested_value_type"] == "IfcBoolean"
        assert exact["value"] is True


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

    for case_id in FAILURE_CASE_IDS:
        failed = phase12_offline_run / "failed" / case_id
        failure = _read(failed / "failure.json")
        application_path = (
            failed / "attempt" / "application.json"
            if case_id == "phase12-d7n-beam-column-rollback"
            else failed / "application.json"
        )
        application = _read(application_path)
        assert failure["valid"] is False
        assert failure["published"] is False
        assert failure["source_unchanged"] is True
        assert failure["blocking_code"] == application["issues"][0]["code"]
        assert application["valid"] is False
        assert application["published"] is False
        assert not list(failed.rglob("repaired.ifc"))
        if case_id == "phase12-vvo-door-window-beam-column-rollback":
            intent = _read(failed / "repair-intent.json")
            assert intent["operations"][-1]["provenance"][0]["reference"] == (
                "request:/operations/6"
            )


def test_fixed_structural_case_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    only = ("phase12-d7n-beam-loadbearing",)
    first_result = run_offline_matrix(first, case_ids=only)
    second_result = run_offline_matrix(second, case_ids=only)
    assert first_result["status"] == second_result["status"] == "partial"
    assert first_result["matrix_complete"] is False
    assert first_result["coverage"]["beam_loadbearing"] is True
    assert first_result["coverage"]["rollback"] is False
    for name in ("damaged.ifc", "repaired.ifc", "changeset.json"):
        assert _sha256(first / "accepted" / only[0] / name) == _sha256(
            second / "accepted" / only[0] / name
        )
    partial_collection = tmp_path / "partial-proof"
    partial_collection.mkdir()
    (partial_collection / "manifest.json").write_text(
        json.dumps({"case_count": 0, "cases": []}) + "\n",
        encoding="utf-8",
    )
    (partial_collection / "README.md").write_text(
        "# IFC repair success cases\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="PHASE12_SOURCE_RUN_NOT_PASSED"):
        curate(first, partial_collection)


def test_curator_accepts_only_strict_cases_and_states_scope_honestly(
    phase12_curated: Path,
) -> None:
    manifest = _read(phase12_curated / "manifest.json")
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
    readme = (phase12_curated / "README.md").read_text(encoding="utf-8")
    assert (
        "Cross-scene, same-family BIMNet evidence only; "
        "not cross-dataset generalization."
    ) in readme

    validation = validate_success_case_collection(phase12_curated)
    assert validation.status == "passed", validation.errors
    assert validation.independently_recomputed_case_count == len(
        SUCCESS_CASE_IDS
    )


def test_phase12_damage_source_hash_is_recomputed_after_manifest_rehash(
    tmp_path: Path,
    phase12_curated: Path,
) -> None:
    tampered = _single_case_collection(
        phase12_curated,
        tmp_path / "tampered",
        case_id="phase12-d7n-beam-loadbearing",
    )
    manifest = _read(tampered / "manifest.json")
    entry = next(
        item
        for item in manifest["cases"]
        if item["case_id"] == "phase12-d7n-beam-loadbearing"
    )
    case_root = (tampered / entry["files"]).parent
    private_path = case_root / "mutation_manifest.private.json"
    private = _read(private_path)
    private["source"]["sha256"] = "sha256:" + "0" * 64
    private_path.write_text(
        json.dumps(private, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    source_manifest_path = case_root / "manifest.json"
    source_manifest = _read(source_manifest_path)
    private_entry = next(
        item
        for item in source_manifest["artifacts"].values()
        if item["path"] == private_path.name
    )
    private_entry["bytes"] = private_path.stat().st_size
    private_entry["sha256"] = _sha256(private_path)
    source_manifest_path.write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    files_path = case_root / "FILES.json"
    files = _read(files_path)
    for record in files["files"]:
        artifact = case_root / record["path"]
        if record["path"] in {
            private_path.name,
            source_manifest_path.name,
        }:
            record["size_bytes"] = artifact.stat().st_size
            record["sha256"] = _sha256(artifact)
    files_path.write_text(
        json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    validation = validate_success_case_collection(tampered)
    assert validation.status == "failed"
    assert any(
        "l0.structural.damage:source_hash" in error
        for error in validation.errors
    )


def test_phase12_damage_audit_cannot_be_disabled_by_schema_downgrade(
    tmp_path: Path,
    phase12_curated: Path,
) -> None:
    tampered = _single_case_collection(
        phase12_curated,
        tmp_path / "schema-tampered",
        case_id="phase12-d7n-beam-loadbearing",
    )
    manifest = _read(tampered / "manifest.json")
    entry = manifest["cases"][0]
    case_root = (tampered / entry["files"]).parent
    source_manifest_path = case_root / "manifest.json"
    source_manifest = _read(source_manifest_path)
    source_manifest["schema_version"] = "text2ifc/legacy-proof/0.1"
    source_manifest_path.write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    files_path = case_root / "FILES.json"
    files = _read(files_path)
    source_entry = next(
        item for item in files["files"] if item["path"] == "manifest.json"
    )
    source_entry["size_bytes"] = source_manifest_path.stat().st_size
    source_entry["sha256"] = _sha256(source_manifest_path)
    files_path.write_text(
        json.dumps(files, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    validation = validate_success_case_collection(tampered)
    assert validation.status == "failed"
    assert any(
        "l0.structural.damage:source_manifest_schema" in error
        for error in validation.errors
    )
