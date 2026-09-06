"""Presentation checks must fail closed without changing original evidence."""
import importlib.util
import json
from pathlib import Path

import ifcopenshell
import pytest

ROOT = Path(__file__).resolve().parents[2]


def tool(name):
    path = ROOT / "scripts" / "proof" / f"{name}.py"
    assert path.is_file(), f"missing human-view tool: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path, *, outcome="repaired", workflow="repair"):
    root = tmp_path / "repo"
    authority = root / "dataset/processed/proof/frozen/case"
    authority.mkdir(parents=True)
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))
    model.write(str(authority / "source.ifc"))
    (authority / "request.txt").write_text("公共请求", encoding="utf-8")
    view = root / "dataset/processed/proof/repair/phase11/test"
    case = view / "case"
    (case / "evidence").mkdir(parents=True)
    for path in [view / "README.md", view / "REPORT.md", case / "REPORT.md", case / "evidence/README.md"]:
        path.write_text("报告", encoding="utf-8")
    (case / "request.txt").write_bytes((authority / "request.txt").read_bytes())
    (case / "02-damaged.ifc").write_bytes((authority / "source.ifc").read_bytes())
    record = {"case_id": "c1", "path": "case", "status": "pending_human_review", "outcome": outcome,
              "authority": authority.relative_to(root).as_posix(), "original_role": None,
              "artifacts": {"request.txt": (authority / "request.txt").relative_to(root).as_posix(),
                            "02-damaged.ifc": (authority / "source.ifc").relative_to(root).as_posix()}}
    if outcome == "repaired":
        (case / "03-repaired.ifc").write_bytes((authority / "source.ifc").read_bytes())
        record["artifacts"]["03-repaired.ifc"] = (authority / "source.ifc").relative_to(root).as_posix()
    else:
        (case / "NO-REPAIR.md").write_text("正确无输出", encoding="utf-8")
    manifest = {"schema_version": "text2ifc/workflow-human-proof/0.1", "workflow": workflow,
                "collection_id": "test", "status": "pending_human_review", "cases": [record]}
    (view / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root, view, case, manifest


def validate(root, view):
    return tool("validate_human_views").validate_collection(view, root)


def test_external_authority_inside_allowed_repository_tree_is_valid(tmp_path):
    root, view, case, manifest = fixture(tmp_path)
    result = validate(root, view)
    assert result["errors"] == []
    assert result["reopened_ifc_count"] == 2
    assert json.loads((view / "manifest.json").read_text(encoding="utf-8"))["status"] == "pending_human_review"


@pytest.mark.parametrize("extra", ["03-repaired.ifc", "repaired.ifc", "candidate.ifc"])
def test_no_output_rejects_any_extra_ifc(tmp_path, extra):
    root, view, case, _ = fixture(tmp_path, outcome="no_output")
    (case / extra).write_bytes((case / "02-damaged.ifc").read_bytes())
    assert any("no-output" in e for e in validate(root, view)["errors"])


@pytest.mark.parametrize("bad", ["../outside", "src", "dataset/processed/proof/../../../../outside"])
def test_authority_cannot_escape_explicit_evidence_roots(tmp_path, bad):
    root, view, case, manifest = fixture(tmp_path)
    manifest["cases"][0]["authority"] = bad
    (view / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert any("authority" in e for e in validate(root, view)["errors"])


def test_copy_mismatch_is_not_a_valid_view(tmp_path):
    root, view, case, _ = fixture(tmp_path)
    (case / "request.txt").write_text("改写的请求", encoding="utf-8")
    assert any("copy mismatch" in e for e in validate(root, view)["errors"])


def test_original_requires_predeclared_role(tmp_path):
    root, view, case, _ = fixture(tmp_path)
    (case / "01-original.ifc").write_bytes((case / "02-damaged.ifc").read_bytes())
    assert any("original role" in e for e in validate(root, view)["errors"])


def test_builder_never_overwrites_independent_artifacts(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"authority")
    target.write_bytes(b"independent user work")
    with pytest.raises(FileExistsError):
        tool("build_human_views").copy_exact(source, target)
    assert target.read_bytes() == b"independent user work"
    assert source.read_bytes() == b"authority"


def test_existing_identical_copy_is_reusable(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_bytes(b"authority")
    target.write_bytes(source.read_bytes())
    tool("build_human_views").copy_exact(source, target)
    assert target.read_bytes() == b"authority"


def test_json_request_projection_is_exact_and_bound(tmp_path):
    root, view, case, manifest = fixture(tmp_path)
    authority = root / manifest["cases"][0]["authority"]
    (authority / "request.json").write_text(json.dumps({"text": "公共请求"}), encoding="utf-8")
    manifest["cases"][0]["artifacts"]["request.txt"] = {"path": (authority / "request.json").relative_to(root).as_posix(), "field": "text"}
    (view / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert validate(root, view)["errors"] == []
    (case / "request.txt").write_text("公共请求\n", encoding="utf-8")
    assert any("copy mismatch" in e for e in validate(root, view)["errors"])
