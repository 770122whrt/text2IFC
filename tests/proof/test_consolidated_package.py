"""Evidence relocation must preserve bytes and fail closed on path mistakes."""
from pathlib import Path
import importlib
import pytest


def api():
    try:
        return importlib.import_module("scripts.proof.package")
    except ModuleNotFoundError:
        pytest.fail("consolidated proof package implementation is missing")


def fixture(tmp_path):
    source = tmp_path / "old"
    collection = tmp_path / "proof"
    source.mkdir(); collection.mkdir()
    (source / "source.ifc").write_bytes(b"same IFC bytes")
    (source / "FILES.json").write_bytes(b'{"frozen":true}\r\n')
    (collection / "02-damaged.ifc").write_bytes(b"same IFC bytes")
    return source, collection


def test_relocation_reuses_direct_ifc_and_reconstructs_frozen_bytes(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    bundle = m.capture_bundle(source, collection, "legacy", {"source.ifc": "02-damaged.ifc"})
    assert len(list(collection.rglob("*.ifc"))) == 1
    assert (source / "FILES.json").read_bytes() == b'{"frozen":true}\r\n'
    for p in source.iterdir():
        p.unlink()
    source.rmdir()
    result = m.verify_bundle(collection, bundle)
    assert result["files"] == 2
    target = tmp_path / "projection"
    m.materialize_bundle(collection, bundle, target)
    assert (target / "FILES.json").read_bytes() == b'{"frozen":true}\r\n'
    assert (target / "source.ifc").read_bytes() == b"same IFC bytes"


def test_existing_independent_content_is_never_overwritten(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    (collection / "02-damaged.ifc").write_bytes(b"independent data")
    with pytest.raises(FileExistsError):
        m.capture_bundle(source, collection, "legacy", {"source.ifc": "02-damaged.ifc"})
    assert (collection / "02-damaged.ifc").read_bytes() == b"independent data"


@pytest.mark.parametrize("bad", ["../escape", "/absolute", "C:/outside", "x/../../escape"])
def test_mapping_cannot_escape_collection(tmp_path, bad):
    m = api(); source, collection = fixture(tmp_path)
    with pytest.raises(ValueError):
        m.capture_bundle(source, collection, "legacy", {"source.ifc": bad})


def test_same_size_corruption_is_detected_before_materialization(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    bundle = m.capture_bundle(source, collection, "legacy", {"source.ifc": "02-damaged.ifc"})
    (collection / "02-damaged.ifc").write_bytes(b"evil IFC bytes")
    with pytest.raises(ValueError, match="digest"):
        m.materialize_bundle(collection, bundle, tmp_path / "projection")
    assert not (tmp_path / "projection").exists()


def test_projection_never_overwrites_an_existing_directory(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    bundle = m.capture_bundle(source, collection, "legacy")
    target = tmp_path / "projection"; target.mkdir()
    (target / "user.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        m.materialize_bundle(collection, bundle, target)
    assert (target / "user.txt").read_text() == "keep"


def test_duplicate_legacy_names_are_rejected(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    bundle = m.capture_bundle(source, collection, "legacy")
    bundle["entries"].append(dict(bundle["entries"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        m.verify_bundle(collection, bundle)


def test_package_rejects_no_output_case_with_repaired_ifc(tmp_path):
    m = api()
    collection = tmp_path / "proof"; case = collection / "guard"
    (case / "evidence").mkdir(parents=True)
    for name in ["REPORT.md", "request.txt", "02-damaged.ifc", "03-repaired.ifc", "NO-REPAIR.md"]:
        (case / name).write_text("artifact")
    document = {"schema_version": m.SCHEMA, "workflow": "repair", "status": "pending_human_review", "cases": [{"case_id": "guard", "path": "guard", "status": "pending_human_review", "outcome": "no_output", "artifacts": {}}], "legacy_bundles": []}
    result = m.validate_package(collection, document, reopen=False)
    assert result["status"] == "failed"
    assert any("no-output" in error for error in result["errors"])


def test_package_rejects_generation_repair_triplet(tmp_path):
    m = api(); root = tmp_path / "case"; root.mkdir()
    (root / "01-original.ifc").write_bytes(b"fake")
    result = m.validate_package(tmp_path, {"schema_version": m.SCHEMA, "workflow": "generation", "cases": [{"case_id": "case", "path": "case"}]}, reopen=False)
    assert any("generation" in e for e in result["errors"])


def test_projection_cannot_target_package_ancestor(tmp_path):
    m = api(); source, collection = fixture(tmp_path)
    bundle = m.capture_bundle(source, collection, "legacy")
    # Existing targets are always refused, including ancestors.
    with pytest.raises(FileExistsError):
        m.materialize_bundle(collection, bundle, tmp_path)


def test_validator_projection_uses_only_frozen_bundle(tmp_path):
    import json
    m = api(); source, collection = fixture(tmp_path)
    frozen = m.capture_bundle(source, collection, "frozen")
    (collection / "manifest.json").write_text(json.dumps({"schema_version":m.SCHEMA,"legacy_bundles":[frozen]}))
    projection = m.projection_for_validation(collection, tmp_path / "scratch")
    assert (projection / "source.ifc").read_bytes() == b"same IFC bytes"
    assert m.projection_for_validation(source, tmp_path / "scratch") == source


def test_legacy_file_resolves_without_recreating_the_old_tree(tmp_path):
    import json
    m = api(); source, collection = fixture(tmp_path)
    frozen=m.capture_bundle(source, collection, "frozen", {"source.ifc":"02-damaged.ifc"})
    (collection / "manifest.json").write_text(json.dumps({"schema_version":m.SCHEMA,"legacy_bundles":[frozen]}))
    assert m.legacy_file(collection, "source.ifc") == collection / "02-damaged.ifc"
    with pytest.raises(ValueError):m.legacy_file(collection, "missing.ifc")


def test_only_explicit_review_allows_pending_to_accepted():
    m = api()
    old={"collection_id":"plan07-v2","status":"pending_human_review","cases":[{"case_id":"one","status":"pending_human_review","run_id":"unchanged"}]}
    import copy
    current=copy.deepcopy(old);current["status"]="accepted";current["cases"][0]["status"]="accepted"
    assert not m.review_transition_is_valid(old,current)
    current["human_review"]={"decision":"accepted","reviewer":"user","date":"2026-09-07","source":"current conversation","statement":"plan07我审批完了 是通过的","case_ids":["one"]}
    assert m.review_transition_is_valid(old,current)
    current["human_review"]["case_ids"]=[]
    assert not m.review_transition_is_valid(old,current)


def test_approval_does_not_authorize_changed_run_or_outcome():
    m=api()
    old={"collection_id":"p","status":"pending_human_review","cases":[{"case_id":"one","status":"pending_human_review","outcome":"no_output","run_id":"old"}]}
    import copy
    current=copy.deepcopy(old);current["status"]="accepted";current["cases"][0].update(status="accepted",run_id="new")
    current["human_review"]={"decision":"accepted","reviewer":"user","date":"2026-09-07","source":"current conversation","statement":"approved","case_ids":["one"]}
    assert not m.review_transition_is_valid(old,current)
