from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from text2ifc_text.splits import (
    SplitManifestError,
    build_scene_family_splits,
    check_scene_family_splits,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
FAMILIES_PATH = (
    ROOT / "dataset" / "processed" / "bim-json-2.0" / "scene-families.json"
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    return path


def _families(payload: dict[str, Any]) -> set[str]:
    return {
        family_record["scene_family"]
        for split_records in payload["splits"].values()
        for family_record in split_records
    }


def _file_ids(payload: dict[str, Any]) -> list[str]:
    return [
        file_id
        for split_records in payload["splits"].values()
        for family_record in split_records
        for file_id in family_record["file_ids"]
    ]


def test_build_scene_family_splits_covers_all_families_and_files() -> None:
    payload = build_scene_family_splits(MANIFEST_PATH, FAMILIES_PATH)

    assert payload["schema_version"] == "text2ifc/bimnet-scene-splits-v1"
    assert payload["seed"] == 20260614
    assert payload["policy"] == "scene-family-shuffle-70-15-15-v1"
    assert payload["source_manifest"] == "dataset/manifests/bimnet-ifc2x3.jsonl"
    assert (
        payload["source_scene_families"]
        == "dataset/processed/bim-json-2.0/scene-families.json"
    )
    assert payload["created_at"] == "2026-06-14"
    assert set(payload["splits"]) == {"train", "validation", "test"}

    assert len(_families(payload)) == 19
    assert len(_file_ids(payload)) == 25
    assert len(set(_file_ids(payload))) == 25

    check_scene_family_splits(payload)


def test_no_scene_family_appears_in_more_than_one_split() -> None:
    payload = build_scene_family_splits(MANIFEST_PATH, FAMILIES_PATH)

    family_to_split: dict[str, str] = {}
    for split_name, split_records in payload["splits"].items():
        for family_record in split_records:
            scene_family = family_record["scene_family"]
            assert scene_family not in family_to_split
            family_to_split[scene_family] = split_name

    assert set(family_to_split) == _families(payload)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda record: record["approved_uses"].remove("dataset-construction"),
            "dataset-construction",
        ),
        (
            lambda record: record["approved_uses"].remove("local-model-training"),
            "local-model-training",
        ),
        (lambda record: record.__setitem__("training_eligible", False), "eligible"),
        (lambda record: record.__delitem__("sha256"), "sha256"),
        (lambda record: record.__setitem__("declared_schema", "IFC4"), "IFC2X3"),
    ],
)
def test_authorization_and_provenance_mutations_are_rejected(
    tmp_path: Path,
    mutation: Any,
    message: str,
) -> None:
    records = _read_jsonl(MANIFEST_PATH)
    mutated = copy.deepcopy(records)
    mutation(mutated[0])
    manifest_path = _write_jsonl(tmp_path / "mutated-bimnet.jsonl", mutated)

    with pytest.raises(SplitManifestError, match=message):
        build_scene_family_splits(manifest_path, FAMILIES_PATH)


def test_split_checker_rejects_family_leakage() -> None:
    leaked_payload = {
        "schema_version": "text2ifc/bimnet-scene-splits-v1",
        "source_manifest": "dataset/manifests/bimnet-ifc2x3.jsonl",
        "source_scene_families": "dataset/processed/bim-json-2.0/scene-families.json",
        "seed": 20260614,
        "policy": "scene-family-shuffle-70-15-15-v1",
        "created_at": "2026-06-14",
        "counts": {
            "families": {"train": 1, "validation": 1, "test": 0, "total": 2},
            "files": {"train": 1, "validation": 1, "test": 0, "total": 2},
        },
        "splits": {
            "train": [{"scene_family": "1px", "file_ids": ["bimnet-ifc2x3-1px"]}],
            "validation": [
                {"scene_family": "1px", "file_ids": ["bimnet-ifc2x3-1px"]}
            ],
            "test": [],
        },
    }

    with pytest.raises(SplitManifestError, match="scene_family"):
        check_scene_family_splits(leaked_payload)
