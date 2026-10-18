"""Dataset adapter boundaries; opaque inputs do not claim IFC validation."""
from __future__ import annotations

import csv
import hashlib
import importlib
import json
from pathlib import Path

import pytest


def api():
    return importlib.import_module("scripts.ifc_repair.repair_comparison.batch_cases")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def dataset(tmp_path, *, pilot=False, entries=None):
    root = tmp_path / "dataset"
    rows = []
    entries = entries or [
        ("source-a", "door", 1, 0),
        ("source-b", "attribute", 0, 1),
        ("source-c", "window", 1, 0),
        ("source-d", "door_window", 2, 0),
    ]
    for i, (source_id, family, deleted, properties) in enumerate(entries, 1):
        local_id = "case-001-a01" if pilot else f"case-{i:03d}"
        folder = root / "sources" / source_id / "cases" / local_id
        public = folder / "public"
        public.mkdir(parents=True)
        (public / "model.ifc").write_bytes(f"OPAQUE PUBLIC INPUT {i}".encode())
        (public / "request-world.txt").write_text(f"请修复公开模型 {i}。", encoding="utf-8")
        if pilot:
            (public / "request.txt").write_bytes((public / "request-world.txt").read_bytes())
        source_hash = hashlib.sha256(source_id.encode()).hexdigest()
        meta = {
            "schema_version": "text2ifc/ifc-repair-dataset-case/1.1" if pilot else "text2ifc/ifc-repair-dataset-case/1.0",
            "status": "passed", "family": family, "severity": "light",
            "source_sha256": source_hash, "damaged_sha256": digest(public / "model.ifc"),
            "deleted_counts": {"door": deleted, "window": 0, "beam": 0, "column": 0},
            "property_changes": properties, "source_unchanged": True,
            "machine_validated": True, "human_reviewed": False,
            "private_identity_leakage": False,
            "prompt_templates": {"world": {"applicable": True, "sha256": digest(public / "request-world.txt")}},
            # Unknown/private metadata is intentionally absent from projections.
            "deleted_ids": ["PRIVATE-DELETED-IDENTITY"], "reference_ifc": "private/reference.ifc",
        }
        if pilot:
            meta.update(primary_prompt="world", information_sufficient=True,
                        wall_check_passed=True, independent_mesh_check_passed=True)
        write_json(folder / "case.json", meta)
        write_json(folder / "private" / "mutation.json", {"private": "DO NOT READ"})
        (folder / "private" / "reference.ifc").write_bytes(b"PRIVATE GOLD")
        paths = ["case.json", "public/model.ifc", "public/request-world.txt"]
        if pilot:
            paths.append("public/request.txt")
        write_json(folder / "private" / "seal.json", {"sha256": {p: digest(folder / p) for p in paths}})
        row = {"case_id": local_id if pilot else f"{source_id}-{i:03d}",
               "path": folder.relative_to(root).as_posix(), "status": "passed",
               "family": family, "severity": "light"}
        if pilot:
            row.update(source_id=source_id, primary_prompt="world")
        rows.append(row)
    with (root / "cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    schema = "text2ifc/dataset-pilot-report/1.0" if pilot else "text2ifc/ifc-repair-dataset-summary/1.0"
    summary = {"schema_version": schema, "status": "complete", "target_cases": len(rows),
               "machine_validated_cases": len(rows), "attempted_cases": len(rows),
               "source_models": len(entries), "provider_calls": 0}
    if pilot:
        summary.update(source_hashes_unchanged=True, unique_damaged_bytes=True, worker_errors=[],
                       sources=[{"source_id": source, "source_unchanged": True, "source_native_passed": True,
                                 "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "status": "complete"}
                                for source, *_ in entries])
    else:
        summary.update(all_sources_unchanged=True,
                       source_results=[{"source_id": source, "source_unchanged": True, "status": "complete"}
                                       for source, *_ in entries])
    write_json(root / "summary.json", summary)
    write_json(root / "build.json", {"schema_version": "text2ifc/dataset-pilot-build/1.0" if pilot else "text2ifc/ifc-repair-dataset-build/1.0",
                                    "configuration": {"seed": 42}})
    return root


def update_case(root, update):
    path = next(root.glob("sources/*/cases/*/case.json"))
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(update)
    write_json(path, value)
    seal = path.parent / "private/seal.json"
    values = json.loads(seal.read_text(encoding="utf-8"))
    values["sha256"]["case.json"] = digest(path)
    write_json(seal, values)


def collected_dataset(tmp_path):
    root = dataset(tmp_path, pilot=True)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    program_hash = "f" * 64
    summary["program_sha256"] = program_hash
    write_json(root / "summary.json", summary)
    selected = []
    for source in summary["sources"]:
        result = root / "sources" / source["source_id"] / "result.json"
        write_json(result, source)
        selected.append({"source_id": source["source_id"], "result_sha256": digest(result)})
    write_json(root / "build.json", {
        "schema_version": "text2ifc/dataset-pilot-collection/1.0",
        "configuration": {"program_sha256": program_hash, "sources": selected, "cases_per_ifc": 1},
    })
    with (root / "cases.csv").open(encoding="utf-8-sig", newline="") as stream:
        paths = [row["path"] for row in csv.DictReader(stream)]
    write_json(root / "integrity.json", {
        "schema_version": "text2ifc/dataset-pilot-integrity/1.0", "passed": True,
        "sealed_cases": 4, "native_zero_findings_cases": 4, "prompt_checked_cases": 4,
        "distinct_source_sha256": 4, "distinct_damaged_sha256": 4,
        "source_hashes_unchanged": True, "program_sha256": program_hash, "checked_paths": paths,
    })
    return root


def test_collected_pilot_uses_bound_completed_manifest(tmp_path):
    root = collected_dataset(tmp_path)
    cases = api().load_candidates(root)
    assert len(cases) == 4
    assert str(root / "integrity.json") in cases[0]["upstream_admission"]["metadata_bindings"]
    result = root / "sources/source-a/result.json"
    result.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="DATASET_COLLECTION_BINDING"):
        api().load_candidates(root)


@pytest.mark.parametrize("change", [{"passed": False}, {"sealed_cases": 3}, {"checked_paths": []}])
def test_collection_integrity_shortfall_or_stale_index_is_rejected(tmp_path, change):
    root = collected_dataset(tmp_path)
    integrity = json.loads((root / "integrity.json").read_text(encoding="utf-8"))
    integrity.update(change)
    write_json(root / "integrity.json", integrity)
    with pytest.raises(ValueError, match="DATASET_COLLECTION_BINDING"):
        api().load_candidates(root)


def test_load_full_batch_uses_existing_ids_world_request_and_admission(tmp_path, monkeypatch):
    root = dataset(tmp_path)
    original_read = Path.open

    def guarded_read(path, *args, **kwargs):
        assert path.name not in {"mutation.json", "reference.ifc"}
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_read)
    cases = api().load_candidates(root)
    assert len(cases) == 4
    assert cases[0]["case_id"] == "source-a-001"
    assert Path(cases[0]["model_path"]).is_absolute()
    assert Path(cases[0]["request_path"]).name == "request-world.txt"
    assert cases[0]["upstream_admission"]["machine_validated"] is True
    assert cases[0]["upstream_admission"]["human_reviewed"] is False
    assert [c["level"] for c in cases] == ["S1", "S1", "S1", "S2"]
    assert [c["category"] for c in cases] == ["geometry", "property", "geometry", "geometry"]
    assert "PRIVATE-DELETED-IDENTITY" not in json.dumps(cases)
    assert "reference.ifc" not in json.dumps(cases)


def test_pilot_repeated_local_ids_keep_original_identity_and_primary_request(tmp_path):
    root = dataset(tmp_path, pilot=True)
    cases = api().load_candidates(root)
    assert len({c["case_id"] for c in cases}) == 4
    assert {c["dataset_case_id"] for c in cases} == {"case-001-a01"}
    assert cases[0]["case_id"] == "source-a-case-001-a01"
    assert Path(cases[0]["request_path"]).name == "request.txt"


@pytest.mark.parametrize("change", [
    {"status": "incomplete"}, {"machine_validated_cases": 3}, {"all_sources_unchanged": False},
])
def test_incomplete_or_inconsistent_completion_is_rejected(tmp_path, change):
    root = dataset(tmp_path)
    summary = root / "summary.json"
    data = json.loads(summary.read_text(encoding="utf-8"))
    data.update(change)
    write_json(summary, data)
    with pytest.raises(ValueError, match="DATASET_"):
        api().load_candidates(root)


@pytest.mark.parametrize("change", [
    {"machine_validated": False}, {"source_unchanged": False}, {"private_identity_leakage": True},
])
def test_case_admission_cannot_be_bypassed_by_csv_passed_label(tmp_path, change):
    root = dataset(tmp_path)
    update_case(root, change)
    with pytest.raises(ValueError, match="CASE_ADMISSION"):
        api().load_candidates(root)


def test_pilot_admission_requires_each_registered_check_field(tmp_path):
    root = dataset(tmp_path, pilot=True)
    path = next(root.glob("sources/*/cases/*/case.json"))
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta.pop("information_sufficient")
    write_json(path, meta)
    update_case(root, {})
    with pytest.raises(ValueError, match="CASE_ADMISSION"):
        api().load_candidates(root)


def test_pilot_primary_request_must_match_index(tmp_path):
    root = dataset(tmp_path, pilot=True)
    index = root / "cases.csv"
    with index.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["primary_prompt"] = "host_wall"
    with index.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="INDEX_METADATA_MISMATCH"):
        api().load_candidates(root)


def test_full_batch_source_manifest_is_bound_when_report_declares_it(tmp_path):
    root = dataset(tmp_path)
    manifest = root / "sources.json"
    write_json(manifest, {"sources": []})
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["sources_manifest_sha256"] = digest(manifest)
    write_json(root / "summary.json", summary)
    write_json(manifest, {"changed": True})
    with pytest.raises(ValueError, match="DATASET_SOURCE_MANIFEST_BINDING"):
        api().load_candidates(root)


def test_stopped_batch_and_escaping_index_path_fail_closed(tmp_path):
    root = dataset(tmp_path)
    (root / "STOPPED-BY-USER.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="DATASET_STOPPED"):
        api().load_candidates(root)
    # Rebuild in a separate owned fixture instead of erasing the stop record.
    other = dataset(tmp_path / "other")
    text = (other / "cases.csv").read_text(encoding="utf-8-sig")
    (other / "cases.csv").write_text(text.replace("sources/source-a/cases/case-001", "../escape"), encoding="utf-8-sig")
    with pytest.raises(ValueError, match="RELATIVE_PATH|CASE_PATH"):
        api().load_candidates(other)


def test_multiple_properties_on_one_product_use_declared_distinct_target_count(tmp_path):
    root = dataset(tmp_path, entries=[("source-a", "attribute", 0, 3)])
    with pytest.raises(ValueError, match="PRIMARY_TARGET_COUNT_REQUIRED"):
        api().load_candidates(root)
    update_case(root, {"primary_target_count": 1, "level": "S1"})
    case = api().load_candidates(root)[0]
    assert case["level"] == "S1"
    assert case["primary_target_count"] == 1
    update_case(root, {"level": "S2"})
    with pytest.raises(ValueError, match="LEVEL_MISMATCH"):
        api().load_candidates(root)


def test_selection_is_order_independent_has_two_simple_categories_and_disjoint_rounds(tmp_path):
    cases = api().load_candidates(dataset(tmp_path))
    before = json.dumps(cases, sort_keys=True)
    selection = api().select_rounds(cases, seed=42)
    assert selection == api().select_rounds(list(reversed(cases)), seed=42)
    assert [c["category"] for c in selection["round1"]] == ["geometry", "property"]
    assert all(c["level"] == "S1" for c in selection["round1"])
    assert len({c["source_id"] for c in selection["round1"]}) == 2
    assert len(selection["round2"]) == 2
    assert not {c["case_id"] for c in selection["round1"]} & {c["case_id"] for c in selection["round2"]}
    assert selection["missing_coverage"] == []
    assert json.dumps(cases, sort_keys=True) == before


def test_missing_categories_and_small_pool_are_reported_without_fake_cases(tmp_path):
    cases = api().load_candidates(dataset(tmp_path, entries=[("source-a", "door", 1, 0)]))
    selection = api().select_rounds(cases, second_count=1)
    assert len(selection["round1"]) == 1
    assert selection["round2"] == []
    assert "property_S1" in selection["missing_coverage"]
    assert selection["coverage"]["round1"]["shortfall"] == 1
    assert selection["coverage"]["round2"]["shortfall"] == 1
    with pytest.raises(ValueError, match="SECOND_ROUND_COUNT"):
        api().select_rounds(cases, second_count=3)


def test_materialize_copies_only_two_public_files_and_binds_unchanged_inputs(tmp_path):
    root = dataset(tmp_path)
    cases = api().load_candidates(root)
    cases[0]["approved_answer_card_path"] = "HOST ONLY PRIVATE ANSWER"
    before = {p: digest(p) for p in root.rglob("*") if p.is_file()}
    destination = tmp_path / "run-inputs"
    result = api().materialize_public(cases[:2], destination)
    files = {p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()}
    assert files == {f"{c['case_id']}/public/{name}" for c in cases[:2] for name in ("model.ifc", "request.txt")}
    assert {p: digest(p) for p in before} == before
    assert "approved_answer_card_path" not in json.dumps(result["cases"])
    assert "reference.ifc" not in json.dumps(result)
    assert result["bindings"][cases[0]["case_id"]]["source_sha256"] == cases[0]["source_sha256"]
    assert result["bindings"][cases[0]["case_id"]]["input_digests"] == cases[0]["input_digests"]
    assert "request_convention" not in result
    assert "source_input_digests" not in result["bindings"][cases[0]["case_id"]]
    with pytest.raises(FileExistsError):
        api().materialize_public(cases[:1], destination)


CONVENTION = "existing-ifc-property-units/1.0"
CONVENTION_TEXT = (
    "属性更改中的数值沿用该属性在 IFC 中的有效单位（属性未单独指定时沿用项目对应单位），"
    "保留原属性类型和单位；上述几何尺寸的毫米约定不适用于属性值。单位缺失或冲突时请提出澄清。"
)


def test_request_convention_parts_is_reusable_and_preserves_optional_default():
    assert api().request_convention_parts() == (None, b"")
    metadata, appendix = api().request_convention_parts(CONVENTION)
    assert appendix == ("\n\n" + CONVENTION_TEXT + "\n").encode("utf-8")
    assert metadata == {
        "version": CONVENTION, "text": CONVENTION_TEXT,
        "sha256": hashlib.sha256(CONVENTION_TEXT.encode("utf-8")).hexdigest(),
        "appendix_sha256": hashlib.sha256(appendix).hexdigest(),
    }
    metadata["text"] = "caller-local mutation"
    assert api().request_convention_parts(CONVENTION)[0]["text"] == CONVENTION_TEXT
    with pytest.raises(ValueError, match="INVALID_REQUEST_CONVENTION"):
        api().request_convention_parts("unknown")


@pytest.mark.parametrize("public_pair", [False, True])
def test_property_unit_convention_changes_only_new_public_request_and_binds_both_inputs(tmp_path, public_pair):
    root = pair_root(tmp_path) if public_pair else dataset(tmp_path)
    cases = api().load_pair_candidates(root, default_level="S2") if public_pair else api().load_candidates(root)[:2]
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    frozen_candidates = json.dumps(cases, sort_keys=True)
    result = api().materialize_public(cases, tmp_path / "out", request_convention=CONVENTION)
    appendix = ("\n\n" + CONVENTION_TEXT + "\n").encode("utf-8")
    expected_convention = {
        "version": CONVENTION, "text": CONVENTION_TEXT,
        "sha256": hashlib.sha256(CONVENTION_TEXT.encode("utf-8")).hexdigest(),
        "appendix_sha256": hashlib.sha256(appendix).hexdigest(),
    }
    assert result["request_convention"] == expected_convention
    for source, public in zip(cases, result["cases"], strict=True):
        model, request = Path(public["model_path"]), Path(public["request_path"])
        assert request.read_bytes() == before[Path(source["request_path"])] + appendix
        assert model.read_bytes() == before[Path(source["model_path"])]
        assert {p.name for p in request.parent.iterdir()} == {"model.ifc", "request.txt"}
        effective = {"model.ifc": digest(model), "request.txt": digest(request)}
        binding = result["bindings"][source["case_id"]]
        assert public["input_digests"] == binding["input_digests"] == effective
        assert binding["source_input_digests"] == source["input_digests"]
        assert effective["request.txt"] != source["input_digests"]["request.txt"]
        assert binding["metadata_bindings"] == source["upstream_admission"]["metadata_bindings"]
        assert binding["source_sha256"] == source["source_sha256"]
        assert binding["source_inputs_unchanged"] is True
        assert binding["request_convention"] == expected_convention
    assert {path: path.read_bytes() for path in before} == before
    assert json.dumps(cases, sort_keys=True) == frozen_candidates


@pytest.mark.parametrize("convention", ["", "existing-ifc-property-units/2.0", False, {}, []])
def test_invalid_request_convention_is_rejected_before_input_access(tmp_path, convention):
    with pytest.raises(ValueError, match="INVALID_REQUEST_CONVENTION"):
        api().materialize_public([{"model_path": "nonexistent"}], tmp_path / "out", request_convention=convention)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("changed", ["model_path", "request_path", "metadata"])
def test_convention_cannot_bypass_original_source_or_receipt_binding(tmp_path, changed):
    root = dataset(tmp_path)
    case = api().load_candidates(root)[0]
    target = root / "summary.json" if changed == "metadata" else Path(case[changed])
    target.write_bytes(b"CHANGED AFTER SELECTION")
    with pytest.raises(ValueError, match="INPUT_BINDING|METADATA_BINDING"):
        api().materialize_public([case], tmp_path / "out", request_convention=CONVENTION)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("changed", ["source", "receipt", "copied_request", "earlier_public_request"])
def test_convention_preserves_copy_race_guards(tmp_path, monkeypatch, changed):
    root = dataset(tmp_path)
    cases = api().load_candidates(root)[:2]
    original_copy = api().shutil.copyfile

    def concurrent_change(source, destination):
        copied = original_copy(source, destination)
        if Path(source) == Path(cases[1]["request_path"]):
            target = {
                "source": Path(cases[0]["request_path"]),
                "receipt": root / "summary.json",
                "copied_request": Path(destination),
                "earlier_public_request": Path(destination).parents[2] / cases[0]["case_id"] / "public/request.txt",
            }[changed]
            target.write_bytes(b"CONCURRENT CHANGE")
        return copied

    monkeypatch.setattr(api().shutil, "copyfile", concurrent_change)
    with pytest.raises(ValueError, match="INPUT_BINDING|METADATA_BINDING"):
        api().materialize_public(cases, tmp_path / "out", request_convention=CONVENTION)


def test_convention_never_copies_a_full_mutation_in_place_of_public_request(tmp_path):
    root = dataset(tmp_path)
    case = api().load_candidates(root)[0]
    mutation = Path(case["request_path"]).parent.parent / "private/mutation.json"
    case["request_path"] = str(mutation)
    case["input_digests"]["request.txt"] = digest(mutation)
    with pytest.raises(ValueError, match="INVALID_PUBLIC_INPUT_PATH"):
        api().materialize_public([case], tmp_path / "out", request_convention=CONVENTION)
    assert not (tmp_path / "out").exists()


def test_input_or_completion_change_after_selection_prevents_materialization(tmp_path):
    root = dataset(tmp_path)
    cases = api().load_candidates(root)
    Path(cases[0]["model_path"]).write_bytes(b"CHANGED AFTER SELECTION")
    with pytest.raises(ValueError, match="INPUT_BINDING"):
        api().materialize_public(cases[:1], tmp_path / "run")
    assert not (tmp_path / "run").exists()
    other = dataset(tmp_path / "other")
    cases = api().load_candidates(other)
    (other / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="METADATA_BINDING"):
        api().materialize_public(cases[:1], tmp_path / "run2")


def test_materialization_refuses_source_tree_and_case_id_escape(tmp_path):
    root = dataset(tmp_path)
    cases = api().load_candidates(root)
    with pytest.raises(ValueError, match="SOURCE_OUTPUT_OVERLAP"):
        api().materialize_public(cases[:1], root / "new-inputs")
    cases[0]["case_id"] = "../outside"
    with pytest.raises(ValueError, match="CASE_ID"):
        api().materialize_public(cases[:1], tmp_path / "run")


def test_source_changed_during_another_copy_is_detected_before_return(tmp_path, monkeypatch):
    root = dataset(tmp_path)
    cases = api().load_candidates(root)
    original_copy = api().shutil.copyfile

    def concurrent_change(source, destination):
        copied = original_copy(source, destination)
        if Path(source) == Path(cases[1]["request_path"]):
            Path(cases[0]["model_path"]).write_bytes(b"CONCURRENT SOURCE CHANGE")
        return copied

    monkeypatch.setattr(api().shutil, "copyfile", concurrent_change)
    with pytest.raises(ValueError, match="INPUT_BINDING"):
        api().materialize_public(cases[:2], tmp_path / "run")


def pair_root(tmp_path):
    root = tmp_path / "pairs"
    root.mkdir()
    (root / "scene.IFC").write_bytes(b"OPAQUE PUBLIC INPUT")
    (root / "SCENE.txt").write_text("Public repair request", encoding="utf-8")
    return root


def pair_index(root, rows, *, encoding="utf-8-sig"):
    path = root / "inputs.csv"
    with path.open("w", encoding=encoding, newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_pair_scan_requires_level_and_materializes_only_public_pair(tmp_path):
    root = pair_root(tmp_path)
    (root / "nested").mkdir()
    (root / "nested/original.ifc").write_bytes(b"PRIVATE")
    with pytest.raises(ValueError, match="DEFAULT_LEVEL_REQUIRED"):
        api().load_pair_candidates(root)
    cases = api().load_pair_candidates(root, default_level="S2")
    case = cases[0]
    assert case["case_id"] == "scene"
    assert case["category"] == "unknown"
    assert case["primary_target_count"] is None
    assert case["upstream_admission"]["live_stage_admission"] is False
    result = api().materialize_public(cases, tmp_path / "output")
    assert Path(result["cases"][0]["model_path"]).read_bytes() == b"OPAQUE PUBLIC INPUT"
    assert {p.name for p in (tmp_path / "output/scene/public").iterdir()} == {"model.ifc", "request.txt"}


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_pair_index_uses_authored_level_kind_and_binds_index(tmp_path, encoding):
    root = pair_root(tmp_path)
    folder = root / "public"
    folder.mkdir()
    (folder / "model.ifc").write_bytes(b"SECOND PUBLIC MODEL")
    (folder / "request.txt").write_text("Public request", encoding="utf-8")
    index = pair_index(root, [{"case_id": "case-a", "ifc_path": "public/model.ifc",
                              "request_path": "public/request.txt", "level": "S3",
                              "primary_target_count": "4", "task_kind": "mixed"}], encoding=encoding)
    case = api().load_pair_candidates(root)[0]
    assert (case["level"], case["category"], case["primary_target_count"]) == ("S3", "mixed", 4)
    assert case["upstream_admission"]["metadata_bindings"][str(index)] == digest(index)
    index.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="METADATA_BINDING"):
        api().materialize_public([case], tmp_path / "output")


@pytest.mark.parametrize("change", [
    {"level": "S4"}, {"level": "S2", "primary_target_count": "1"},
    {"primary_target_count": "0"}, {"primary_target_count": "1.0"},
    {"task_kind": "private"}, {"ifc_path": "../scene.IFC"},
    {"ifc_path": "/scene.IFC"}, {"request_path": "private/request.txt"},
    {"ifc_path": "original.ifc"}, {"case_id": "../bad"},
])
def test_pair_index_rejects_invalid_author_metadata_or_paths(tmp_path, change):
    root = pair_root(tmp_path)
    row = {"case_id": "scene", "ifc_path": "scene.IFC", "request_path": "SCENE.txt",
           "level": "S1", "primary_target_count": "1", "task_kind": "geometry"}
    row.update(change)
    pair_index(root, [row])
    with pytest.raises(ValueError):
        api().load_pair_candidates(root)


@pytest.mark.parametrize("name", ["original.ifc", "gold.ifc", "reference.ifc", "mutation.txt"])
def test_pair_scan_rejects_private_looking_top_level_inputs(tmp_path, name):
    root = pair_root(tmp_path)
    (root / name).write_bytes(b"PRIVATE")
    with pytest.raises(ValueError, match="PRIVATE_INPUT"):
        api().load_pair_candidates(root, default_level="S1")


def test_pair_scan_rejects_missing_empty_and_empty_root(tmp_path):
    root = pair_root(tmp_path)
    (root / "unmatched.ifc").write_bytes(b"OPAQUE")
    with pytest.raises(ValueError, match="MISSING_PAIR"):
        api().load_pair_candidates(root, default_level="S1")
    other = tmp_path / "empty"
    other.mkdir()
    with pytest.raises(ValueError, match="NO_PUBLIC_CASES"):
        api().load_pair_candidates(other, default_level="S1")
    (other / "case.ifc").write_bytes(b"")
    (other / "case.txt").write_text(" ", encoding="utf-8")
    with pytest.raises(ValueError, match="EMPTY_INPUT"):
        api().load_pair_candidates(other, default_level="S1")


def test_pair_index_rejects_duplicate_case_and_shared_inputs(tmp_path):
    root = pair_root(tmp_path)
    row = {"case_id": "scene", "ifc_path": "scene.IFC", "request_path": "SCENE.txt", "level": "S1"}
    pair_index(root, [row, {**row, "case_id": "SCENE"}])
    with pytest.raises(ValueError, match="DUPLICATE_CASE_ID"):
        api().load_pair_candidates(root)
    pair_index(root, [row, {**row, "case_id": "other"}])
    with pytest.raises(ValueError, match="DUPLICATE_INPUT_PATH"):
        api().load_pair_candidates(root)


def test_pair_input_change_blocks_materialization(tmp_path):
    root = pair_root(tmp_path)
    cases = api().load_pair_candidates(root, default_level="S1")
    (root / "SCENE.txt").write_text("Changed", encoding="utf-8")
    with pytest.raises(ValueError, match="INPUT_BINDING"):
        api().materialize_public(cases, tmp_path / "output")


def test_pair_index_path_stays_in_root_and_required_columns_fail_closed(tmp_path):
    root = pair_root(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("case_id,ifc_path,request_path,level\n", encoding="utf-8")
    with pytest.raises(ValueError, match="INVALID_INDEX_PATH"):
        api().load_pair_candidates(root, index_path=outside)
    pair_index(root, [{"case_id": "scene", "ifc_path": "scene.IFC", "request_path": "SCENE.txt"}])
    with pytest.raises(ValueError, match="INVALID_INPUT_INDEX_COLUMNS"):
        api().load_pair_candidates(root, default_level="S1")


@pytest.mark.parametrize("count,level", [("1", "S1"), ("2", "S2"), ("3", "S3"), ("10", "S3")])
def test_pair_index_primary_target_boundaries(tmp_path, count, level):
    root = pair_root(tmp_path)
    pair_index(root, [{"case_id": "scene", "ifc_path": "scene.IFC", "request_path": "SCENE.txt",
                       "primary_target_count": count, "level": level}])
    assert api().load_pair_candidates(root)[0]["level"] == level


def test_pair_case_id_maximum_matches_carrier(tmp_path):
    root = pair_root(tmp_path)
    row = {"case_id": "a" * 101, "ifc_path": "scene.IFC", "request_path": "SCENE.txt", "level": "S1"}
    pair_index(root, [row])
    assert len(api().load_pair_candidates(root)[0]["case_id"]) == 101
    pair_index(root, [{**row, "case_id": "a" * 102}])
    with pytest.raises(ValueError, match="INVALID_PAIR_CASE_ID"):
        api().load_pair_candidates(root)


def test_pair_request_whitespace_is_not_a_public_request(tmp_path):
    root = pair_root(tmp_path)
    (root / "SCENE.txt").write_text("\ufeff \n\t", encoding="utf-8")
    with pytest.raises(ValueError, match="EMPTY_INPUT"):
        api().load_pair_candidates(root, default_level="S1")


def test_pair_reparse_point_is_rejected_before_bytes_are_read(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import stat

    root = pair_root(tmp_path)
    original = Path.lstat

    def reparse(path):
        if path == root / "scene.IFC":
            return SimpleNamespace(st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return original(path)

    monkeypatch.setattr(Path, "lstat", reparse)
    with pytest.raises(ValueError, match="LINK_PATH_NOT_ALLOWED"):
        api().load_pair_candidates(root, default_level="S1")


def test_pair_symlink_input_is_rejected(tmp_path):
    root = pair_root(tmp_path)
    target = tmp_path / "external.ifc"
    target.write_bytes(b"EXTERNAL")
    try:
        (root / "linked.ifc").symlink_to(target)
    except OSError as error:
        pytest.skip(f"Host cannot create symlink: {error}")
    with pytest.raises(ValueError, match="LINK_PATH_NOT_ALLOWED"):
        api().load_pair_candidates(root, default_level="S1")


def test_explicit_index_rejects_traversal_even_when_it_resolves_within_root(tmp_path):
    root = pair_root(tmp_path)
    (root / "subfolder").mkdir()
    pair_index(root, [{"case_id": "scene", "ifc_path": "scene.IFC", "request_path": "SCENE.txt", "level": "S1"}])
    with pytest.raises(ValueError, match="INVALID_INDEX_PATH"):
        api().load_pair_candidates(root, index_path=root / "subfolder/../inputs.csv")
