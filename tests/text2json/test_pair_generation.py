from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_text.pairs import (
    PairGenerationError,
    build_pair_manifest,
    build_pair_records,
)


ROOT = Path(__file__).resolve().parents[2]
GOLD_MANIFEST = ROOT / "dataset" / "processed" / "text2json" / "gold-set-manifest.json"


REQUIRED_FIELDS = {
    "record_id",
    "target_kind",
    "input_text",
    "target_json_path",
    "split",
    "scene_family",
    "source_file_id",
    "source_sha256",
    "text_style",
    "template_id",
    "review_status",
}
SIDECAR_ONLY_TERMS = {
    "MATERIAL_ASSOCIATION",
    "TYPE_RELATIONSHIP",
    "CONNECTION_RELATIONSHIP",
    "FACETED_BREP_GEOMETRY",
    "MAPPED_GEOMETRY",
    "BOOLEAN_GEOMETRY",
    "UNSUPPORTED_GEOMETRY",
}


def test_pair_generation_refuses_missing_gold_manifest(tmp_path: Path) -> None:
    with pytest.raises(PairGenerationError, match="gold"):
        build_pair_records(tmp_path / "missing-gold-set-manifest.json")


def test_pair_records_are_split_aware_and_provenance_linked() -> None:
    records = build_pair_records(GOLD_MANIFEST)

    assert records
    assert {record["text_style"] for record in records} >= {
        "concise",
        "enumerated",
        "spatial",
        "property_focused",
    }
    assert {record["split"] for record in records} == {"train", "validation", "test"}

    train_families = {
        record["scene_family"] for record in records if record["split"] == "train"
    }
    for record in records:
        assert REQUIRED_FIELDS <= set(record)
        assert record["target_kind"] == "formal"
        assert record["review_status"] == "generated"
        assert record["input_text"].strip()
        assert len(record["source_sha256"]) == 64
        target_path = ROOT / record["target_json_path"]
        assert target_path.is_file()
        assert f"/{record['split']}/" in target_path.as_posix()
        if record["split"] in {"validation", "test"}:
            assert record["scene_family"] not in train_families
        for blocked in SIDECAR_ONLY_TERMS:
            assert blocked not in record["input_text"]


def test_pair_manifest_counts_are_deterministic() -> None:
    records = build_pair_records(GOLD_MANIFEST)
    manifest = build_pair_manifest(records, source_manifest=GOLD_MANIFEST)

    assert manifest["schema_version"] == "text2ifc/text2json-pair-manifest-v1"
    assert manifest["record_count"] == len(records)
    assert manifest["counts_by_style"]["concise"] == 25
    assert manifest["counts_by_style"]["enumerated"] == 25
    assert manifest["counts_by_style"]["spatial"] == 25
    assert manifest["counts_by_style"]["property_focused"] == 25
    assert manifest["counts_by_split"]["train"] == 68
    assert manifest["counts_by_split"]["validation"] == 20
    assert manifest["counts_by_split"]["test"] == 12

    serialized = json.dumps(manifest, sort_keys=True)
    assert "draft_clarification" not in serialized
