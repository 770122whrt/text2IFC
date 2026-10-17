"""Materialization cost and snapshot invariants; entirely synthetic input bytes."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import batch_cases as api


def candidates(tmp_path, count=6, receipt_bytes=64 * 1024):
    root = tmp_path / "source"
    root.mkdir(parents=True)
    receipt = root / "receipt.json"
    receipt.write_bytes(b" " * receipt_bytes)
    receipt_hash = api.sha256(receipt)
    rows = []
    for number in range(count):
        identifier = f"case-{number:03d}"
        model, request = root / (identifier + ".ifc"), root / (identifier + ".txt")
        model.write_bytes(b"OPAQUE TEST IFC\n" * 64)
        request.write_text("Synthetic public request", encoding="utf-8")
        hashes = {"model.ifc": api.sha256(model), "request.txt": api.sha256(request)}
        rows.append({"case_id": identifier, "dataset_case_id": identifier,
                     "dataset_root": str(root), "input_kind": "public_pair",
                     "model_path": str(model), "request_path": str(request),
                     "level": "S1", "source_id": identifier, "source_sha256": hashes["model.ifc"],
                     "input_digests": hashes, "upstream_admission": {"metadata_bindings": {
                         str(receipt): receipt_hash, str(model): hashes["model.ifc"],
                         str(request): hashes["request.txt"]}}})
    return rows, receipt


def test_shared_metadata_is_hashed_only_at_whole_snapshot_boundaries(tmp_path, monkeypatch):
    rows, receipt = candidates(tmp_path)
    original, calls = api.sha256, Counter()

    def counted(path):
        calls[Path(path)] += 1
        return original(path)

    monkeypatch.setattr(api, "sha256", counted)
    result = api.materialize_public(rows, tmp_path / "output")
    assert len(result["cases"]) == len(rows)
    # Whole-snapshot preflight and final recheck are sufficient for shared
    # immutable evidence. Cost must not grow with the number of references.
    assert calls[receipt] <= 2
    # Source inputs also occur in metadata_bindings. Do not hash that alias
    # twice within the same phase; retain before/copy/final source checks.
    assert all(calls[Path(row["model_path"])] <= 3 for row in rows)


def test_shared_metadata_change_during_copy_still_rejects_snapshot(tmp_path, monkeypatch):
    rows, receipt = candidates(tmp_path, count=3)
    original = api.shutil.copyfile

    def change_during_copy(source, target):
        copied = original(source, target)
        if Path(source) == Path(rows[1]["request_path"]):
            receipt.write_bytes(b"CHANGED SHARED EVIDENCE")
        return copied

    monkeypatch.setattr(api.shutil, "copyfile", change_during_copy)
    with pytest.raises(ValueError, match="METADATA_BINDING_FAILED"):
        api.materialize_public(rows, tmp_path / "output")
    assert receipt.read_bytes() == b"CHANGED SHARED EVIDENCE"


def test_conflicting_expected_shared_hashes_fail_before_any_copy(tmp_path):
    rows, receipt = candidates(tmp_path, count=3)
    rows[1]["upstream_admission"]["metadata_bindings"][str(receipt)] = "f" * 64
    with pytest.raises(ValueError, match="METADATA_BINDING_FAILED"):
        api.materialize_public(rows, tmp_path / "output")
    assert not (tmp_path / "output").exists()
