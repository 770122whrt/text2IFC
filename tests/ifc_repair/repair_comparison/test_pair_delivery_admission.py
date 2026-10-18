"""Selected public pairs reuse bound native receipts without reading private inputs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import batch_cases as api


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def delivery(tmp_path):
    import ifcopenshell

    root = tmp_path / "delivery"
    public = root / "public"
    public.mkdir(parents=True)
    rows, provenance, public_hashes, bindings = [], [], {}, {}
    for identifier in ("z-first", "a-second"):
        model, request = public / f"{identifier}.ifc", public / f"{identifier}.txt"
        model.write_bytes(identifier.encode())
        request.write_text("Public request", encoding="utf-8")
        row = {"case_id": identifier, "ifc_path": model.name, "request_path": request.name,
               "level": "S1", "primary_target_count": "1", "task_kind": "geometry"}
        rows.append(row)
        public_hashes.update({model.name: digest(model), request.name: digest(request)})
        case_path = f"sources/source-a/cases/{identifier}"
        case = root / "private/production" / case_path
        native = case / "private/validation.json"
        write_json(native, {"passed": True, "finding_count": 0, "schema": "IFC2X3",
                            "express_rules": True, "ifcopenshell_version": ifcopenshell.version})
        seal = case / "private/seal.json"
        write_json(seal, {"schema_version": "text2ifc/ifc-repair-dataset-seal/1.0",
                          "sha256": {"public/model.ifc": digest(model),
                                     "private/validation.json": digest(native)}})
        bindings.update({str(native): digest(native), str(seal): digest(seal)})
        provenance.append({"case_id": identifier, "source_id": "source-a", "case_path": case_path,
                           "model_sha256": digest(model), "public_request_sha256": digest(request),
                           "public_row": row})
    index = public / "inputs.csv"
    with index.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    public_hashes[index.name] = digest(index)
    export = root / "private/evaluation/export.json"
    write_json(export, {"schema_version": "text2ifc/dataset-pair-export/1.1", "status": "complete",
                        "public_root": str(public), "source_root": str(root / "private/production"),
                        "pairs": 2, "distinct_damages": 2, "source_models": 1,
                        "request_profile": "text2ifc/dataset-request/1.4", "pair_provenance": provenance,
                        "public_file_sha256": public_hashes, "bound_hashes": bindings})
    checks = root / "private/finalization/checks.json"
    write_json(checks, {"schema_version": "text2ifc/dataset-offline-delivery/1.3", "passed": True})
    summary = root / "private/finalization/summary.json"
    write_json(summary, {"schema_version": "text2ifc/dataset-offline-delivery/1.3", "status": "complete",
                         "pairs": 2, "distinct_damages": 2, "source_models": 1,
                         "authority_sha256": {str(export): digest(export), str(checks): digest(checks)}})
    return public, summary


def test_csv_order_is_authoritative_for_batch_ordinals(tmp_path):
    public, _ = delivery(tmp_path)
    assert [c["case_id"] for c in api.load_pair_candidates(public)] == ["z-first", "a-second"]


def test_selection_reads_only_selected_public_bytes_and_reuses_bound_native(tmp_path, monkeypatch):
    public, summary = delivery(tmp_path)
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.name not in {"a-second.ifc", "a-second.txt", "mutation.json", "reference.ifc"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    candidates = api.load_pair_candidates(public, case_ids=["z-first"], delivery_receipt=summary)
    assert len(candidates) == 1
    admitted = candidates[0]["upstream_admission"]
    assert admitted["machine_validated"] is True
    assert admitted["native_validation"]["reused"] is True
    assert admitted["native_validation"]["finding_count"] == 0
    assert admitted["live_stage_admission"] is False
    output = api.materialize_public(candidates, tmp_path / "run")
    assert "private" not in json.dumps(output["cases"])


def test_selection_does_not_walk_unselected_input_files(tmp_path, monkeypatch):
    public, summary = delivery(tmp_path)
    original = Path.lstat

    def guarded(path, *args, **kwargs):
        assert path.name not in {"a-second.ifc", "a-second.txt"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", guarded)
    assert len(api.load_pair_candidates(public, case_ids=["z-first"], delivery_receipt=summary)) == 1


@pytest.mark.parametrize("change", ["public", "index", "native", "seal", "export", "checks"])
def test_changed_delivery_inputs_or_evidence_fail_closed(tmp_path, change):
    public, summary = delivery(tmp_path)
    paths = {"public": public / "z-first.ifc", "index": public / "inputs.csv",
             "native": public.parent / "private/production/sources/source-a/cases/z-first/private/validation.json",
             "seal": public.parent / "private/production/sources/source-a/cases/z-first/private/seal.json",
             "export": public.parent / "private/evaluation/export.json",
             "checks": public.parent / "private/finalization/checks.json"}
    paths[change].write_bytes(paths[change].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="DELIVERY_.*BINDING"):
        api.load_pair_candidates(public, case_ids=["z-first"], delivery_receipt=summary)


def test_receipt_is_explicit_and_selection_rejects_unknown_ids(tmp_path):
    public, _ = delivery(tmp_path)
    candidates = api.load_pair_candidates(public, case_ids=["z-first"])
    assert "machine_validated" not in candidates[0]["upstream_admission"]
    with pytest.raises(ValueError, match="UNKNOWN_CASE_SELECTION"):
        api.load_pair_candidates(public, case_ids=["absent"])


@pytest.mark.parametrize("change", [{"passed": False}, {"finding_count": 1}, {"finding_count": False},
                                    {"express_rules": False}, {"schema": "IFC4"},
                                    {"ifcopenshell_version": "stale"}])
def test_hash_bound_native_receipt_still_requires_current_zero_finding_contract(tmp_path, change):
    public, summary_path = delivery(tmp_path)
    folder = public.parent / "private/production/sources/source-a/cases/z-first/private"
    native_path, seal_path = folder / "validation.json", folder / "seal.json"
    native = json.loads(native_path.read_text(encoding="utf-8"))
    write_json(native_path, {**native, **change})
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["sha256"]["private/validation.json"] = digest(native_path)
    write_json(seal_path, seal)
    export_path = public.parent / "private/evaluation/export.json"
    export = json.loads(export_path.read_text(encoding="utf-8"))
    export["bound_hashes"].update({str(native_path): digest(native_path), str(seal_path): digest(seal_path)})
    write_json(export_path, export)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["authority_sha256"][str(export_path)] = digest(export_path)
    write_json(summary_path, summary)
    with pytest.raises(ValueError, match="DELIVERY_NATIVE_RECEIPT_INVALID"):
        api.load_pair_candidates(public, case_ids=["z-first"], delivery_receipt=summary_path)


def test_selected_receipt_changes_after_loading_prevent_materialization(tmp_path):
    public, summary = delivery(tmp_path)
    candidates = api.load_pair_candidates(public, case_ids=["z-first"], delivery_receipt=summary)
    native = public.parent / "private/production/sources/source-a/cases/z-first/private/validation.json"
    native.write_bytes(native.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="CASE_METADATA_BINDING_FAILED"):
        api.materialize_public(candidates, tmp_path / "run")
    assert not (tmp_path / "run").exists()
