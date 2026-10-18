from __future__ import annotations

import hashlib
import json

import pytest

from scripts.ifc_repair.dataset_batch.workflow import prepare_source, process_source


def test_source_workflow_produces_verified_cases_and_reuses_only_bound_results(scene_factory, tmp_path):
    scene_factory(tmp_path / "source.ifc")
    spec = {"source_id": "formal-test", "kind": "formal", "input_path": "source.ifc", "source_sha256": hashlib.sha256((tmp_path / "source.ifc").read_bytes()).hexdigest(), "size_bytes": (tmp_path / "source.ifc").stat().st_size, "license": "synthetic fixture", "review": {"human_viewed": False}}
    root = tmp_path / "dataset"
    admission = prepare_source(spec, str(tmp_path), str(root / "private/admissions"), 3, 42)
    assert admission["passed"]
    result = process_source(spec, str(tmp_path), str(root), 3, 42)
    assert result["passed_cases"] == result["target_cases"] == 3
    assert result["provider_calls"] == 0
    assert result["source_unchanged"]
    assert process_source(spec, str(tmp_path), str(root), 3, 42)["passed_cases"] == 3
    case = json.loads((root / "sources/formal-test/cases/case-001/case.json").read_text(encoding="utf-8"))
    assert not case["human_reviewed"]


def test_resume_rejects_tampered_public_prompt(scene_factory, tmp_path):
    scene_factory(tmp_path / "source.ifc")
    spec = {"source_id": "formal-test", "kind": "formal", "input_path": "source.ifc", "source_sha256": hashlib.sha256((tmp_path / "source.ifc").read_bytes()).hexdigest(), "size_bytes": (tmp_path / "source.ifc").stat().st_size}
    root = tmp_path / "dataset"
    process_source(spec, str(tmp_path), str(root), 1, 42)
    request = root / "sources/formal-test/cases/case-001/public/request-world.txt"
    request.write_text("changed public specification", encoding="utf-8")
    with pytest.raises(ValueError, match="EXISTING_CASE_BINDING_FAILED"):
        process_source(spec, str(tmp_path), str(root), 1, 42)


def test_admission_rejects_tampered_validation_receipt(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    spec = {"source_id": "formal-test", "input_path": "source.ifc", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    root = tmp_path / "admissions"
    admission = prepare_source(spec, str(tmp_path), str(root), 1, 42)
    path = root / spec["source_sha256"] / "admission.json"
    changed = json.loads(path.read_text(encoding="utf-8"))
    changed["available_recipes"] = 0
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="ADMISSION_CACHE_INTEGRITY_FAILED"):
        prepare_source(spec, str(tmp_path), str(root), 1, 42)
