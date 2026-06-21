from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.external_inventory")
    except ModuleNotFoundError as exc:
        pytest.fail(f"external IFC inventory is not implemented: {exc}")
    return module


def _step(schema: str) -> str:
    return (
        "ISO-10303-21;\nHEADER;\n"
        f"FILE_SCHEMA(('{schema}'));\n"
        "ENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"
    )


def _hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def test_inventory_is_read_only_and_filters_exact_ifc2x3(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _api()
    corpus = tmp_path / "sample-corpus"
    corpus.mkdir()
    (corpus / "LICENSE").write_text("Fixture license\n", encoding="utf-8")
    (corpus / "README.md").write_text(
        "Source: https://example.invalid/sample\n",
        encoding="utf-8",
    )
    for name, schema in (
        ("a-ifc2x3.ifc", "IFC2X3"),
        ("b-ifc4.ifc", "IFC4"),
        ("c-ifc4x3.ifc", "IFC4X3"),
    ):
        (corpus / name).write_text(_step(schema), encoding="ascii")
    (corpus / "d-broken.ifc").write_text(
        _step("IFC2X3"),
        encoding="ascii",
    )
    before = _hashes(corpus)

    class Model:
        def __init__(self, schema: str) -> None:
            self.schema = schema

    def fake_open(path: str):
        name = Path(path).name
        if name == "d-broken.ifc":
            raise RuntimeError("broken fixture")
        if "ifc4x3" in name:
            return Model("IFC4X3")
        if "ifc4" in name:
            return Model("IFC4")
        return Model("IFC2X3")

    monkeypatch.setattr(module.ifcopenshell, "open", fake_open)

    report = module.inventory_external_ifc(
        [corpus],
        repository_root=tmp_path,
        max_selected_ifc2x3=3,
    )

    assert before == _hashes(corpus)
    assert report["schema_version"] == "text2ifc/external-ifc-inventory-v1"
    assert report["summary"] == {
        "corpus_count": 1,
        "file_count": 4,
        "eligible_ifc2x3_count": 1,
        "selected_ifc2x3_count": 1,
    }
    assert report["selected_ifc2x3"] == [
        "sample-corpus/a-ifc2x3.ifc"
    ]
    records = {Path(item["path"]).name: item for item in report["files"]}
    assert records["a-ifc2x3.ifc"]["eligible_ifc2x3"]
    assert not records["b-ifc4.ifc"]["eligible_ifc2x3"]
    assert not records["c-ifc4x3.ifc"]["eligible_ifc2x3"]
    assert records["d-broken.ifc"]["reopen_status"] == "error"
    assert report["corpora"][0]["license_files"][0]["path"] == (
        "sample-corpus/LICENSE"
    )


def test_absent_corpus_is_reported_without_fabrication(tmp_path: Path) -> None:
    module = _api()
    missing = tmp_path / "missing-corpus"

    report = module.inventory_external_ifc(
        [missing],
        repository_root=tmp_path,
    )

    assert report["summary"]["corpus_count"] == 1
    assert report["summary"]["file_count"] == 0
    assert report["corpora"][0]["available"] is False
    assert report["corpora"][0]["license_files"] == []
    assert report["selected_ifc2x3"] == []
