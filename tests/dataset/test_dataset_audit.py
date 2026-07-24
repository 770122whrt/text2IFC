import json
from pathlib import Path

import pytest

from text2ifc_dataset.audit import (
    DatasetAuditError,
    audit_dataset,
    audit_file_manifest,
    render_json,
)


ROOT = Path(__file__).resolve().parents[2]


def test_repository_dataset_audit_is_valid_and_read_only() -> None:
    processed = ROOT / "dataset" / "processed"
    before = {
        path.relative_to(processed).as_posix(): path.stat().st_size
        for path in processed.rglob("*")
        if path.is_file()
    }

    result = audit_dataset(ROOT)

    after = {
        path.relative_to(processed).as_posix(): path.stat().st_size
        for path in processed.rglob("*")
        if path.is_file()
    }
    assert result["schema_version"] == "text2ifc/dataset-audit/1.0"
    assert result["valid"] is True
    assert result["manifests"]["bimnet-ifc2x3"]["record_count"] == 25
    assert result["manifests"]["raw-files"]["record_count"] >= 11
    assert result["processed_inventory"]["mutation_policy"] == "read_only"
    assert {
        item["classification"]
        for item in result["processed_inventory"]["roots"]
    } <= {"retain", "regenerable", "review_before_delete"}
    assert after == before
    assert render_json(result) == render_json(audit_dataset(ROOT))


def test_file_manifest_reports_hash_drift_without_rewriting(
    tmp_path: Path,
) -> None:
    source = tmp_path / "model.ifc"
    source.write_text(
        "ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC2X3'));\nENDSEC;\n"
        "DATA;\nENDSEC;\nEND-ISO-10303-21;\n",
        encoding="ascii",
    )
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "sample",
                "local_path": "model.ifc",
                "sha256": "0" * 64,
                "declared_schema": "IFC2X3",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = source.read_bytes()

    with pytest.raises(DatasetAuditError, match="HASH_MISMATCH"):
        audit_file_manifest(manifest, root=tmp_path)

    assert source.read_bytes() == before
    assert json.loads(manifest.read_text(encoding="utf-8"))["sha256"] == "0" * 64

