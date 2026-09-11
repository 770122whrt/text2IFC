"""Focused regression tests for the non-destructive incoming ZIP audit."""
from pathlib import Path
import importlib.util
import io
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("incoming_audit", ROOT / "scripts/dataset/check_incoming_ifc_archives.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_ifc2x3_empty_model_checks_finish(tmp_path, monkeypatch):
    import ifcopenshell
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    folder = tmp_path / "dataset/external"
    folder.mkdir(parents=True)
    with zipfile.ZipFile(folder / AUDIT.ARCHIVES[0], "w") as archive:
        archive.writestr("empty.ifc", ifcopenshell.file(schema="IFC2X3").to_string())
    result = AUDIT.inspect_ifc(AUDIT.ARCHIVES[0], 0)
    assert result["parse_status"] == "ok"
    assert "check_error" not in result
    assert result["body_elements"] == 0
    assert not result["basic_candidate"]


def test_strict_size_boundary():
    assert AUDIT.below_target(10 * 1024 * 1024 - 1)
    assert not AUDIT.below_target(10 * 1024 * 1024)


def test_duplicate_names_keep_distinct_member_indices():
    data = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("same.ifc", b"one")
            archive.writestr("same.ifc", b"two")
    data.seek(0)
    with zipfile.ZipFile(data) as archive:
        rows = AUDIT.inventory_members(archive)
    assert [row["index"] for row in rows] == [0, 1]
    assert rows[0]["sha256"] != rows[1]["sha256"]


def test_exact_duplicates_require_content_not_name():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("one.ifc", b"same bytes")
        archive.writestr("two.ifc", b"same bytes")
    data.seek(0)
    with zipfile.ZipFile(data) as archive:
        rows = AUDIT.inventory_members(archive)
    assert rows[0]["sha256"] == rows[1]["sha256"]


def test_path_safety_flags_without_extraction():
    assert not AUDIT.safe_member_name("../escape.ifc")
    assert not AUDIT.safe_member_name("C:/escape.ifc")
    assert not AUDIT.safe_member_name("/absolute.ifc")
    assert AUDIT.safe_member_name("models/house.ifc")


def test_failed_check_is_not_empty_model():
    result = AUDIT.classify({"size_bytes": 1, "parse_status": "missing_dependency"})
    assert "missing_check_dependency" in result
    assert "no_body_representation" not in result


def test_overlapping_flags_are_preserved():
    result = AUDIT.classify({"size_bytes": 20 * 1024 * 1024, "parse_status": "ok", "schema": "IFC2X3", "body_elements": 0, "grid_count": 1})
    assert "size_limit" in result
    assert "no_body_representation" in result
    assert "grid_present" in result
