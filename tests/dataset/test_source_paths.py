"""Archived source references must resolve by an explicit, byte-bound migration."""

import hashlib
import json

import pytest

from text2ifc_dataset.source_paths import resolve_source_path


def _layout(root, records=None):
    target = root / "dataset/external/example.ifc"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"frozen IFC bytes")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = root / "dataset/manifests/bimnet-migration-map.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"records": records if records is not None else [{
        "old_path": "dataset/ifc/train/example.ifc",
        "new_path": "dataset/external/example.ifc", "sha256": digest,
    }]}), encoding="utf-8")
    return target, manifest, digest


def test_migrated_reference_uses_verified_canonical_bytes(tmp_path):
    target, _, digest = _layout(tmp_path)
    assert resolve_source_path(tmp_path, "dataset/ifc/train/example.ifc", expected_sha256=digest) == target
    assert not (tmp_path / "dataset/ifc").exists()


def test_existing_unmapped_source_keeps_its_path(tmp_path):
    target, _, digest = _layout(tmp_path)
    assert resolve_source_path(tmp_path, "dataset/external/example.ifc", expected_sha256=digest) == target


@pytest.mark.parametrize("fault", ["changed_bytes", "wrong_expected_hash", "duplicate", "escape"])
def test_invalid_migration_fails_closed(tmp_path, fault):
    target, manifest, digest = _layout(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if fault == "changed_bytes":
        target.write_bytes(b"different IFC")
    elif fault == "wrong_expected_hash":
        digest = "0" * 64
    elif fault == "duplicate":
        data["records"] *= 2
    else:
        data["records"][0]["new_path"] = "../outside.ifc"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_source_path(tmp_path, "dataset/ifc/train/example.ifc", expected_sha256=digest)


def test_existing_legacy_file_cannot_hide_a_hash_conflict(tmp_path):
    _layout(tmp_path)
    legacy = tmp_path / "dataset/ifc/train/example.ifc"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"unrelated bytes")
    with pytest.raises(ValueError):
        resolve_source_path(tmp_path, "dataset/ifc/train/example.ifc")


@pytest.mark.parametrize("reference", ["../outside.ifc", "dataset/ifc/train/missing.ifc"])
def test_no_basename_search_or_external_fallback(tmp_path, reference):
    _layout(tmp_path)
    with pytest.raises((ValueError, FileNotFoundError)):
        resolve_source_path(tmp_path, reference)
