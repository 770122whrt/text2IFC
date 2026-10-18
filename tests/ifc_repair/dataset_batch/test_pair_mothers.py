"""Frozen pair-mother intake uses tiny STEP fixtures, not external discovery."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ifc_repair import prepare_pair_mothers as mothers
from scripts.ifc_repair.dataset_batch import sources as intake


def _step(tag: str, schema: str = "IFC2X3") -> bytes:
    return ("ISO-10303-21;\nHEADER;\n"
            f"FILE_DESCRIPTION(('{tag}'),'2;1');\n"
            "FILE_NAME('fixture.ifc','',(),(),'','','');\n"
            f"FILE_SCHEMA(('{schema}'));\nENDSEC;\n"
            "DATA;\nENDSEC;\nEND-ISO-10303-21;\n").encode("ascii")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_path(root: Path, number: int = 1) -> Path:
    return root / mothers.FORMAL_ROOT / f"formal-{number:03d}" / "private/task.json"


def _selected(root: Path) -> tuple[Path, dict]:
    path = root / mothers.EXTERNAL_COLLECTION / "sources.json"
    return path, _read(path)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    for n in range(1, 21):
        case_id = f"formal-{n:03d}"
        private = tmp_path / mothers.FORMAL_ROOT / case_id / "private"
        private.mkdir(parents=True)
        reference = private / "reference.ifc"
        reference.write_bytes(_step(case_id))
        (private / "SOURCE-LICENSE.md").write_text("许可：MIT；保留来源通知。", encoding="utf-8")
        review = {"status": "accepted_by_delegation", "human_viewed": n == 1, "kind": "delegated_technical"}
        source = {"source_path": f"dataset/external/original-{n}.ifc", "source_sha256": _sha(reference),
                  "source_id": "legacy-publisher", "license": "MIT", "scene_family": f"family-{n}",
                  "source_url": "https://example.test/formal"}
        _json(private / "task.json", {"case_id": case_id, "source_sha256": _sha(reference), "source": source, "review": review})
        _json(private / "human-review.json", review)
        _json(private / "technical-review.json", {"valid": True, "human_accepted": n == 1})

    # Deliberately unsorted IDs: no reserve reselection or source sorting allowed.
    legacy_ids = ["reserve-029", "external-008", "external-003"] + [f"external-{n:03d}" for n in range(30, 47)]
    selected, results = [], []
    collection = tmp_path / mothers.EXTERNAL_COLLECTION
    for n, source_id in enumerate(legacy_ids, 21):
        folder = collection / "sources" / source_id
        private = folder / "private"
        private.mkdir(parents=True)
        reference = private / "reference.ifc"
        reference.write_bytes(_step(f"extra-{n}"))
        license_file = folder / "LICENSES/notice.md"
        license_file.parent.mkdir()
        license_file.write_text(f"CC BY 4.0 fixture {n}", encoding="utf-8")
        sealed_evidence = {"path": license_file.relative_to(collection).as_posix(), "sha256": _sha(license_file)}
        chosen = {"source_id": source_id, "input_path": f"dataset/external/frozen-{n}.ifc",
                  "source_sha256": _sha(reference), "size_bytes": reference.stat().st_size,
                  "license": "CC-BY-4.0", "scene_family": f"external-family-{n}", "publisher": "fixture-publisher",
                  "model_license_evidence": [sealed_evidence], "machine_source_passed": True,
                  "derived_human_review": "pending_human_review"}
        source = {**deepcopy(chosen), "kind": "external", "schema": "IFC2X3", "review": {},
                  "human_viewed": False, "derived_review": {"status": "pending_human_review", "human_viewed": False},
                  "source_url": "https://example.test/frozen", "license_evidence": {"urls": ["https://example.test/license"]},
                  "pilot_cases": [{"family": "do-not-reuse-two-case-plan"}], "pilot_families": ["door_only"]}
        _json(private / "source.json", source)
        _json(private / "source-validation.json", {"passed": True, "source_sha256": _sha(reference)})
        (folder / "SOURCE.md").write_text("Existing machine review; pending human review", encoding="utf-8")
        selected.append(chosen)
        results.append({"source_id": source_id, "source": source, "source_sha256": _sha(reference),
                        "status": "complete", "source_unchanged": True, "source_native_passed": True})
    _json(collection / "sources.json", {"sources": selected, "source_count": 20, "cases_per_ifc": 2})
    _json(collection / "summary.json", {"status": "complete", "source_models": 20, "sources": sorted(results, key=lambda r: r["source_id"]),
                                        "machine_validated_cases": 40, "human_reviewed_cases": 0})
    return tmp_path


def test_fixed_forty_mothers_keep_selected_order_and_private_paths(repository: Path, monkeypatch):
    def forbidden_discovery(*args, **kwargs):
        raise AssertionError("external corpus discovery is forbidden")
    monkeypatch.setattr(intake, "discover_sources", forbidden_discovery)
    before = {p.relative_to(repository).as_posix(): _sha(p) for p in repository.rglob("*") if p.is_file()}
    selected = _selected(repository)[1]["sources"]
    specs = mothers.build_mother_specs(repository)
    assert len(specs) == len({s["source_sha256"] for s in specs}) == 40
    assert [s["source_id"] for s in specs] == [f"formal-{n:03d}" for n in range(1, 41)]
    assert [s["legacy_source_id"] for s in specs[20:]] == [s["source_id"] for s in selected]
    assert specs[20]["kind"] == "external" and specs[20]["legacy_kind"] == "external"
    for item in specs:
        assert item["schema"] == "IFC2X3" and item["size_bytes"] < 20_000_000
        assert not Path(item["input_path"]).is_absolute()
        assert item["input_path"].endswith("/private/reference.ifc")
        assert _sha(repository / item["input_path"]) == item["source_sha256"]
        assert "pilot_cases" not in item and "pilot_families" not in item
        assert "pilot_cases" not in item["source"] and "pilot_families" not in item["source"]
    after = {p.relative_to(repository).as_posix(): _sha(p) for p in repository.rglob("*") if p.is_file()}
    assert after == before
    assert not (repository / mothers.DEFAULT_OUTPUT.parent).exists()


def test_preserves_license_review_source_and_historical_evidence(repository: Path):
    specs = mothers.build_mother_specs(repository)
    task = _read(_task_path(repository))
    formal = specs[0]
    assert formal["source"] == task["source"]
    assert formal["review"] == task["review"]
    assert formal["human_viewed"] is True
    assert formal["review_records"]["human_review"]["human_viewed"] is True
    evidence = formal["provenance"]["evidence_files"]
    assert {p["path"].split("/")[-1] for p in evidence} >= {"task.json", "SOURCE-LICENSE.md", "human-review.json", "technical-review.json"}
    assert all(_sha(repository / p["path"]) == p["sha256"] for p in evidence)
    extra = specs[20]
    assert extra["human_viewed"] is False and extra["review"] == {}
    assert extra["derived_human_review"] == "pending_human_review"
    assert extra["derived_review"]["human_viewed"] is False
    assert extra["machine_source_passed"] is True
    assert extra["scene_family"] == "external-family-21"
    assert any(p["path"].endswith("/LICENSES/notice.md") for p in extra["provenance"]["evidence_files"])


def test_missing_review_fields_are_not_invented(repository: Path):
    path = _task_path(repository)
    task = _read(path)
    task.pop("review")
    _json(path, task)
    (path.parent / "human-review.json").unlink()
    (path.parent / "technical-review.json").unlink()
    formal = mothers.build_mother_specs(repository)[0]
    assert "review" not in formal and "human_viewed" not in formal
    assert "task_review" not in formal["review_records"] and "human_review" not in formal["review_records"]


def test_scene_family_uses_existing_record_without_fabricating_independence(repository: Path):
    path = _task_path(repository, 11)
    task = _read(path)
    task["source"].pop("scene_family")
    _json(path, task)
    _json(path.parent / "source-record.json", {"sha256": task["source_sha256"], "building_group": "shared-original-group", "license": "MIT"})
    formal = mothers.build_mother_specs(repository)[10]
    assert formal["scene_family"] == "shared-original-group"
    assert formal["source_record"]["building_group"] == "shared-original-group"
    assert formal["provenance"]["scene_family_basis"] == "source_record.building_group"


@pytest.mark.parametrize("location", ["task", "formal_source", "source_record", "selected", "frozen_source", "summary_source"])
def test_mismatch_in_any_explicit_mother_hash_rejected(repository: Path, location: str):
    if location in {"task", "formal_source", "source_record"}:
        path = _task_path(repository)
        data = _read(path)
        if location == "task":
            data["source_sha256"] = "0" * 64
        elif location == "formal_source":
            data["source"]["source_sha256"] = "0" * 64
        else:
            path = path.parent / "source-record.json"
            data = {"sha256": "0" * 64}
    elif location == "selected":
        path, data = _selected(repository)
        data["sources"][0]["source_sha256"] = "0" * 64
    elif location == "frozen_source":
        source_id = _selected(repository)[1]["sources"][0]["source_id"]
        path = repository / mothers.EXTERNAL_COLLECTION / "sources" / source_id / "private/source.json"
        data = _read(path)
        data["source_sha256"] = "0" * 64
    else:
        path = repository / mothers.EXTERNAL_COLLECTION / "summary.json"
        data = _read(path)
        data["sources"][0]["source_sha256"] = "0" * 64
    _json(path, data)
    with pytest.raises(ValueError, match="hash_mismatch"):
        mothers.build_mother_specs(repository)


def test_exact_source_bytes_are_unique_across_legacy_and_selected(repository: Path):
    path, data = _selected(repository)
    original = repository / mothers.FORMAL_ROOT / "formal-001/private/reference.ifc"
    source_id = data["sources"][0]["source_id"]
    target = repository / mothers.EXTERNAL_COLLECTION / "sources" / source_id / "private/reference.ifc"
    target.write_bytes(original.read_bytes())
    data["sources"][0].update(source_sha256=_sha(target), size_bytes=target.stat().st_size)
    _json(path, data)
    for file in (target.parent / "source.json",):
        source = _read(file)
        source.update(source_sha256=_sha(target), size_bytes=target.stat().st_size)
        _json(file, source)
    summary_path = repository / mothers.EXTERNAL_COLLECTION / "summary.json"
    summary = _read(summary_path)
    row = next(r for r in summary["sources"] if r["source_id"] == source_id)
    row["source_sha256"] = _sha(target)
    row["source"].update(source_sha256=_sha(target), size_bytes=target.stat().st_size)
    _json(summary_path, summary)
    with pytest.raises(ValueError, match="duplicate_content"):
        mothers.build_mother_specs(repository)


@pytest.mark.parametrize("payload", [_step("not-IFC2X3", "IFC4"), _step("IFC2X3-in-description", "IFC4"), b"ISO-10303-21;HEADER;ENDSEC;DATA;FILE_SCHEMA(('IFC2X3'));ENDSEC;"])
def test_ifc2x3_must_be_declared_in_actual_header(repository: Path, payload: bytes):
    path = _task_path(repository)
    reference = path.parent / "reference.ifc"
    reference.write_bytes(payload)
    task = _read(path)
    task["source_sha256"] = task["source"]["source_sha256"] = _sha(reference)
    _json(path, task)
    with pytest.raises(ValueError, match="not_ifc2x3|invalid_step_header"):
        mothers.build_mother_specs(repository)


def test_twenty_mb_boundary_rejected_without_native_or_geometry(repository: Path):
    path = _task_path(repository).parent / "reference.ifc"
    with path.open("r+b") as stream:
        stream.truncate(20_000_000)
    with pytest.raises(ValueError, match="size_limit"):
        mothers.build_mother_specs(repository)


@pytest.mark.parametrize("change", ["short_selection", "duplicate_source_id", "unsealed_summary", "summary_missing_selected_source"])
def test_selection_must_be_exact_frozen_twenty(repository: Path, change: str):
    path, selected = _selected(repository)
    summary_path = repository / mothers.EXTERNAL_COLLECTION / "summary.json"
    summary = _read(summary_path)
    if change == "short_selection":
        selected["sources"].pop()
    elif change == "duplicate_source_id":
        selected["sources"][1] = deepcopy(selected["sources"][0])
    elif change == "unsealed_summary":
        summary["status"] = "running"
    else:
        summary["sources"].pop()
    _json(path, selected)
    _json(summary_path, summary)
    with pytest.raises(ValueError, match="selected_count|duplicate_selected_source|collection_not_complete|selected_summary_source_mismatch"):
        mothers.build_mother_specs(repository)


def test_sealed_license_evidence_hash_mismatch_rejected(repository: Path):
    selected = _selected(repository)[1]["sources"][0]
    path = repository / mothers.EXTERNAL_COLLECTION / selected["model_license_evidence"][0]["path"]
    path.write_text("changed license evidence", encoding="utf-8")
    with pytest.raises(ValueError, match="license_evidence_hash_mismatch"):
        mothers.build_mother_specs(repository)


def test_selected_path_escape_rejected(repository: Path):
    path, data = _selected(repository)
    data["sources"][0]["source_id"] = "../outside"
    _json(path, data)
    with pytest.raises(ValueError, match="unsafe_selected_source_id"):
        mothers.build_mother_specs(repository)


def test_cli_writes_private_sources_and_refuses_overwrite(repository: Path, capsys):
    output = repository / "new-private-manifest/mother-sources.json"
    assert mothers.main(["--repository-root", str(repository), "--output", str(output)]) == 0
    manifest = _read(output)
    assert manifest["private_manifest"] is True and len(manifest["sources"]) == manifest["source_count"] == 40
    assert "never Provider input" in manifest["scope"]
    compact = json.loads(capsys.readouterr().out)
    assert compact["source_count"] == compact["unique_source_hashes"] == 40
    assert compact["schemas"] == ["IFC2X3"]
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        mothers.main(["--repository-root", str(repository), "--output", str(output)])
    assert output.read_bytes() == before


def test_invalid_intake_does_not_create_output_directory(repository: Path):
    path = _task_path(repository)
    task = _read(path)
    task["source_sha256"] = "0" * 64
    _json(path, task)
    output = repository / "uncreated/mother-sources.json"
    with pytest.raises(ValueError, match="hash_mismatch"):
        mothers.main(["--repository-root", str(repository), "--output", str(output)])
    assert not output.parent.exists()


def test_default_output_is_runner_private_production_directory():
    assert mothers.DEFAULT_OUTPUT == Path("dataset/processed/ifc-repair/formal-40-pairs-25-20261010/private/production/mother-sources.json")


def test_referenced_source_evidence_is_hashed_and_missing_history_is_explicit(repository: Path):
    path = _task_path(repository)
    task = _read(path)
    known = repository / "dataset/external/prior-native-evidence.json"
    _json(known, {"passed": True, "role": "historical only"})
    task["source"]["schema_validation"] = {"evidence": known.relative_to(repository).as_posix()}
    task["source"]["prior_review_evidence"] = "dataset/external/absent-historical-review.json"
    _json(path, task)
    formal = mothers.build_mother_specs(repository)[0]
    observed = next(p for p in formal["provenance"]["evidence_files"] if p["path"] == known.relative_to(repository).as_posix())
    assert observed["sha256"] == _sha(known)
    assert formal["provenance"]["unavailable_referenced_evidence"] == [{"path": "dataset/external/absent-historical-review.json", "declared_by": "source.prior_review_evidence"}]
    assert formal["source"]["schema_validation"] == task["source"]["schema_validation"]
