"""Focused safety and final-layout checks for the user-requested audit move."""
from pathlib import Path
import ast
import importlib.util
import json
import re

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "incoming_audit_migration", ROOT / "scripts/dataset/migrate_incoming_ifc_audit_to_external.py"
)
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


def test_preview_does_not_move_or_write(tmp_path):
    source = tmp_path / MIGRATION.OLD
    source.mkdir(parents=True)
    (source / "evidence.json").write_bytes(b'{"valid": false}\n')
    result = MIGRATION.migrate(tmp_path)
    assert result["file_count"] == 1
    assert not result["applied"]
    assert source.is_dir()
    assert not (tmp_path / MIGRATION.NEW).exists()


def test_move_preserves_exact_bytes_and_records_mapping(tmp_path):
    source = tmp_path / MIGRATION.OLD
    source.mkdir(parents=True)
    original = {"evidence.json": b'{"valid": false}\r\n', "README.md": "中文记录\n".encode()}
    for name, data in original.items():
        (source / name).write_bytes(data)
    result = MIGRATION.migrate(tmp_path, apply=True)
    target = tmp_path / MIGRATION.NEW
    assert not source.exists()
    assert result["byte_equality_verified"]
    assert not result["model_files_touched"]
    for name, data in original.items():
        assert (target / name).read_bytes() == data
    assert json.loads((target / "migration.json").read_text(encoding="utf-8"))["file_count"] == 2


def test_existing_destination_is_not_overwritten(tmp_path):
    source, target = tmp_path / MIGRATION.OLD, tmp_path / MIGRATION.NEW
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "keep.json").write_bytes(b"{}")
    (target / "existing.json").write_bytes(b"[]")
    with pytest.raises(RuntimeError, match="DESTINATION_ALREADY_EXISTS"):
        MIGRATION.migrate(tmp_path, apply=True)
    assert (source / "keep.json").read_bytes() == b"{}"
    assert (target / "existing.json").read_bytes() == b"[]"


def test_repository_moved_evidence_and_current_references():
    target = ROOT / MIGRATION.NEW
    assert target.is_dir()
    assert not (ROOT / MIGRATION.OLD).exists()
    move = json.loads((target / "migration.json").read_text(encoding="utf-8"))
    assert move["file_count"] == 88
    assert move["byte_equality_verified"]
    for entry in move["moved_files"]:
        path = target / entry["path"]
        assert path.is_file()
        if entry["path"] != "README.md":
            assert path.stat().st_size == entry["size_bytes_at_move"]
    for path in target.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "dataset/manifests/external-corpora.json").read_text(encoding="utf-8"))
    bench = next(r for r in manifest["corpora"] if r["corpus_id"] == "ifc-bench")
    assert bench["missing_upstream_status"] == "intentionally_excluded_by_user_oversize"
    assert bench["exclusion_reason_source"] == "user_confirmation_2026-09-10"
    assert bench["exclusion_size_threshold_bytes"] is None
    assert bench["ifc_inventory"]["file_count"] == 48
    assert (ROOT / bench["inventory_evidence"]).is_file()
    for name in ("check_incoming_ifc_archives.py", "reconcile_incoming_ifc_evidence.py", "summarize_incoming_ifc_checks.py"):
        path = ROOT / "scripts/dataset" / name
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        assert MIGRATION.NEW.as_posix() in text
        assert MIGRATION.OLD.as_posix() not in text
    docs = [target / "README.md", target / "HANDOFF-SUMMARY.md", target / "REPAIR-AGENT-PROMPT.md",
            ROOT / "dataset/external/README.md", ROOT / "dataset/manifests/README.md"]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in link and not link.startswith("#"):
                assert (doc.parent / link.split("#")[0]).exists(), (str(doc), link)
