import json
from pathlib import Path

from text2ifc_dataset.source_manifests import (
    build_file_records,
    build_source_payload,
    render_json,
    render_jsonl,
    validate_records,
)

ROOT = Path(__file__).resolve().parents[2]


def test_source_payload_contains_bimnet_policy() -> None:
    payload = build_source_payload(ROOT)
    by_id = {item["source_id"]: item for item in payload["sources"]}
    bimnet = by_id["bimnet"]
    assert bimnet["classification"] == "authorized_local"
    assert bimnet["training_use"] == "authorized_local_only"
    assert bimnet["redistribution"] == "not_inferred"
    assert bimnet["file_count"] == 25


def test_file_records_are_deterministic_and_deduplicated_by_sha() -> None:
    first = build_file_records(ROOT, probe=False)
    second = build_file_records(ROOT, probe=False)
    assert render_jsonl(first) == render_jsonl(second)
    hashes = [record["sha256"] for record in first]
    assert len(hashes) == len(set(hashes))
    validate_records(first, ROOT)


def test_bimnet_records_preserve_scene_family_and_current_layout() -> None:
    records = build_file_records(ROOT, probe=False)
    bimnet = [record for record in records if record["source_id"] == "bimnet"]
    assert len(bimnet) == 25
    assert {record["source_family"] for record in bimnet} >= {"7y3", "px4", "vvo"}
    assert all(record["declared_schema"] == "IFC2X3" for record in bimnet)
    assert all(
        record["local_path"].startswith("dataset/external/bimnet/")
        for record in bimnet
    )


def test_render_json_is_stable() -> None:
    payload = {"b": 2, "a": 1}
    assert render_json(payload) == '{\n  "a": 1,\n  "b": 2\n}\n'
    assert json.loads(render_json(payload)) == payload
