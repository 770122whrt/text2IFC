from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _manifest_module():
    name = "text2ifc_dataset.phase6_manifest"
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        spec = None
    assert spec is not None, "Phase 6 manifest module is missing"
    return importlib.import_module(name)


def _build():
    return _manifest_module().build_phase6_manifest()


def test_manifest_rejects_missing_license_status():
    module = _manifest_module()
    manifest = _build()
    del manifest["records"][0]["license_status"]

    with pytest.raises(module.Phase6ManifestError, match="license_status"):
        module.validate_phase6_manifest(manifest)


def test_manifest_rejects_scene_family_leakage():
    module = _manifest_module()
    manifest = _build()
    leaked = copy.deepcopy(manifest)
    train_record = next(
        record for record in leaked["records"] if record["split"] == "train"
    )
    train_record["split"] = "validation"
    train_record["training_eligible"] = False
    train_record["eligible_uses"] = ["model-evaluation"]

    with pytest.raises(module.Phase6ManifestError, match="scene_family"):
        module.validate_phase6_manifest(leaked)


def test_manifest_links_formal_targets_and_loss_sidecars():
    module = _manifest_module()
    manifest = _build()

    assert manifest["schema_version"] == "text2ifc/phase6-training-manifest-v1"
    assert manifest["counts"]["records"] == 100
    assert manifest["counts"]["by_split"] == {
        "test": 12,
        "train": 68,
        "validation": 20,
    }
    assert manifest["counts"]["training_eligible"] == 68
    assert manifest["counts"]["source_files"] == 25
    assert manifest["counts"]["scene_families"] == 19
    for record in manifest["records"]:
        assert len(record["source_sha256"]) == 64
        assert record["target_kind"] == "formal"
        assert (ROOT / record["formal_target_path"]).is_file()
        assert (ROOT / record["loss_sidecar_path"]).is_file()
        assert record["license_status"] == "user-authorized-local-use"
        assert record["training_eligible"] is (record["split"] == "train")
        if record["split"] == "train":
            assert "local-model-training" in record["eligible_uses"]
        else:
            assert record["eligible_uses"] == ["model-evaluation"]

    module.validate_phase6_manifest(manifest)


def test_manifest_rejects_missing_loss_sidecar_link():
    module = _manifest_module()
    manifest = _build()
    del manifest["records"][0]["loss_sidecar_path"]

    with pytest.raises(module.Phase6ManifestError, match="loss_sidecar_path"):
        module.validate_phase6_manifest(manifest)


def test_validation_and_test_records_cannot_be_training_eligible():
    module = _manifest_module()
    manifest = _build()
    record = next(
        item for item in manifest["records"] if item["split"] == "validation"
    )
    record["training_eligible"] = True
    record["eligible_uses"] = ["local-model-training", "model-evaluation"]

    with pytest.raises(module.Phase6ManifestError, match="training_eligible"):
        module.validate_phase6_manifest(manifest)
