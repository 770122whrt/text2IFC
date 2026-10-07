"""Behavioral checks for the shared schema and atomic-write refactor."""

import json
import os
from pathlib import Path

import pytest

from text2ifc_contract import schema
from text2ifc_text import gold, splits


@pytest.mark.parametrize("reference", ["https://example.invalid/schema", "other.json", 3, None])
def test_schema_rejects_nested_nonlocal_references(tmp_path, monkeypatch, reference):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({"allOf": [{"$ref": reference}]}), encoding="utf-8")
    monkeypatch.setattr(schema, "SCHEMA_PATH", path)
    with pytest.raises(ValueError, match="Remote schema references are forbidden"):
        schema.load_schema()


def test_schema_loads_are_independent():
    first = schema.load_schema_v26()
    first["properties"].clear()
    assert schema.load_schema_v26()["properties"]


@pytest.mark.parametrize("writer", [gold.atomic_write_text, splits.atomic_write_text])
def test_atomic_writer_preserves_destination_on_replace_failure(tmp_path, monkeypatch, writer):
    target = tmp_path / "data.json"
    target.write_text("原始数据\n", encoding="utf-8")

    def fail_replace(source, destination):
        assert Path(source).parent == target.parent
        assert Path(source).read_text(encoding="utf-8") == "更新数据\n"
        raise OSError("injected replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        writer(target, "更新数据\n")
    assert target.read_text(encoding="utf-8") == "原始数据\n"
    assert sorted(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("writer", [gold.atomic_write_text, splits.atomic_write_text])
def test_atomic_writer_creates_parents_and_preserves_utf8(tmp_path, writer):
    target = tmp_path / "nested" / "文本.json"
    writer(target, "{\"说明\":\"门窗\"}\n")
    assert target.read_bytes() == '{"说明":"门窗"}\n'.encode("utf-8")
    assert list(target.parent.iterdir()) == [target]
