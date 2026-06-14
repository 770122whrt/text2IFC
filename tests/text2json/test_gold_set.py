from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from text2ifc_text.gold import (
    GoldSetError,
    build_formal_target_from_draft,
    build_gold_set,
    triage_extraction_audit,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "dataset" / "processed" / "bim-json-2.0" / "extraction-audit.json"
SPLIT_PATH = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"
COMPLETE_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    return path


def _source_record(**overrides: Any) -> dict[str, Any]:
    record = {
        "approved_uses": [
            "local-extraction",
            "dataset-construction",
            "baseline-evaluation",
            "local-model-training",
        ],
        "authorization": {
            "basis": "test",
            "confirmed_at": "2026-06-14",
            "redistribution_inferred": False,
            "scope": [
                "local-extraction",
                "dataset-construction",
                "baseline-evaluation",
                "local-model-training",
            ],
        },
        "declared_schema": "IFC2X3",
        "id": "bimnet-ifc2x3-1px",
        "license": "user-authorized-local-use",
        "local_path": "valid.ifc",
        "retrieved_at": None,
        "scene_family": "1px",
        "sha256": "a" * 64,
        "source_path": "ifc/train/valid.ifc",
        "source_repository": "LydJason/BIMNet",
        "source_revision": None,
        "training_eligible": True,
        "validation": "test",
    }
    record.update(overrides)
    return record


def _split_manifest() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/bimnet-scene-splits-v1",
        "source_manifest": "test-manifest.jsonl",
        "source_scene_families": "test-scene-families.json",
        "seed": 20260614,
        "policy": "scene-family-shuffle-70-15-15-v1",
        "created_at": "2026-06-14",
        "counts": {
            "families": {"train": 1, "validation": 1, "test": 1, "total": 3},
            "files": {"train": 1, "validation": 1, "test": 1, "total": 3},
        },
        "splits": {
            "train": [
                {
                    "scene_family": "1px",
                    "file_ids": ["bimnet-ifc2x3-1px"],
                }
            ],
            "validation": [
                {
                    "scene_family": "759",
                    "file_ids": ["bimnet-ifc2x3-759"],
                }
            ],
            "test": [
                {
                    "scene_family": "b6b",
                    "file_ids": ["bimnet-ifc2x3-b6b"],
                }
            ],
        },
    }


def _loss(kind: str) -> dict[str, str]:
    return {
        "source_ref": "sha256:test#IfcRel:1",
        "path": "/relationships",
        "kind": kind,
        "message": f"{kind} is sidecar-only in Phase 3.",
    }


def _draft(partial_document: dict[str, Any], losses: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": partial_document,
        "missing_facts": [],
        "losses": losses,
        "clarification_targets": [],
        "provenance": partial_document["provenance"],
    }


def test_triage_extraction_audit_preserves_counts_and_split_join() -> None:
    triage = triage_extraction_audit(AUDIT_PATH, SPLIT_PATH)

    assert triage["schema_version"] == "text2ifc/text2json-draft-triage-v1"
    assert triage["file_count"] == 25
    assert triage["aggregate"]["status_counts"] == {"draft": 25}
    assert triage["aggregate"]["loss_count"] == 8280
    assert len(triage["records"]) == 25
    assert {record["split"] for record in triage["records"]} == {
        "train",
        "validation",
        "test",
    }

    for record in triage["records"]:
        assert record["source_file_id"].startswith("bimnet-ifc2x3-")
        assert record["source_path"].endswith(".ifc")
        assert len(record["source_sha256"]) == 64
        assert record["scene_family"]
        assert record["draft_status"] == "draft"
        assert record["target_kind"] == "draft_pending_validation"
        assert record["target_scope"] == "supported_generation_profile"
        assert record["loss_count"] == sum(record["loss_counts"].values())


def test_valid_draft_partial_document_promotes_to_formal_target_with_sidecar() -> None:
    partial_document = _load_json(COMPLETE_FIXTURE)
    losses = [
        _loss("MATERIAL_ASSOCIATION"),
        _loss("TYPE_RELATIONSHIP"),
        _loss("CONNECTION_RELATIONSHIP"),
        _loss("FACETED_BREP_GEOMETRY"),
        _loss("UNSUPPORTED_PROPERTY_VALUE"),
    ]
    result = build_formal_target_from_draft(
        _draft(partial_document, losses),
        source_record=_source_record(),
        split="train",
    )

    assert result["target_kind"] == "formal"
    assert result["target"] == partial_document
    assert result["sidecar"]["losses"] == losses
    assert result["sidecar"]["loss_count"] == len(losses)
    assert result["sidecar"]["source_file_id"] == "bimnet-ifc2x3-1px"
    assert result["sidecar"]["split"] == "train"
    serialized_target = json.dumps(result["target"], sort_keys=True)
    for sidecar_only_kind in (
        "MATERIAL_ASSOCIATION",
        "TYPE_RELATIONSHIP",
        "CONNECTION_RELATIONSHIP",
        "FACETED_BREP_GEOMETRY",
        "UNSUPPORTED_PROPERTY_VALUE",
    ):
        assert sidecar_only_kind not in serialized_target


def test_invalid_partial_document_stays_draft_clarification() -> None:
    invalid_partial = copy.deepcopy(_load_json(COMPLETE_FIXTURE))
    invalid_partial.pop("units")

    result = build_formal_target_from_draft(
        _draft(invalid_partial, [_loss("MATERIAL_ASSOCIATION")]),
        source_record=_source_record(),
        split="train",
    )

    assert result["target_kind"] == "draft_clarification"
    assert result["target"] is None
    assert result["sidecar"]["validation_issues"]
    assert result["sidecar"]["losses"][0]["kind"] == "MATERIAL_ASSOCIATION"


def test_gold_set_writes_formal_targets_only_for_valid_partials(tmp_path: Path) -> None:
    complete = _load_json(COMPLETE_FIXTURE)
    invalid = copy.deepcopy(complete)
    invalid.pop("ifc_schema")
    losses = [_loss("MATERIAL_ASSOCIATION"), _loss("TYPE_RELATIONSHIP")]
    drafts = {
        "valid.ifc": _draft(complete, losses),
        "invalid.ifc": _draft(invalid, losses),
        "also-invalid.ifc": _draft(invalid, losses),
    }

    def fake_extract(path: str | Path) -> SimpleNamespace:
        draft = drafts[Path(path).as_posix()]
        return SimpleNamespace(
            source_sha256="a" * 64,
            document=None,
            draft=draft,
            inventory={"entities": {"source": 1, "represented": 1, "reported": 0}},
        )

    manifest_path = _write_jsonl(
        tmp_path / "manifest.jsonl",
        [
            _source_record(
                id="bimnet-ifc2x3-1px",
                scene_family="1px",
                local_path="valid.ifc",
                sha256="a" * 64,
            ),
            _source_record(
                id="bimnet-ifc2x3-759",
                scene_family="759",
                local_path="invalid.ifc",
                sha256="b" * 64,
            ),
            _source_record(
                id="bimnet-ifc2x3-b6b",
                scene_family="b6b",
                local_path="also-invalid.ifc",
                sha256="c" * 64,
            ),
        ],
    )
    split_path = _write_json(tmp_path / "splits.json", _split_manifest())

    manifest = build_gold_set(
        manifest_path,
        split_path,
        output_dir=tmp_path / "text2json",
        extractor=fake_extract,
    )

    assert manifest["counts"]["formal"] == 1
    assert manifest["counts"]["draft_clarification"] == 2
    assert (tmp_path / "text2json" / "formal-gold" / "train" / "bimnet-ifc2x3-1px.json").is_file()
    assert not (
        tmp_path
        / "text2json"
        / "formal-gold"
        / "validation"
        / "bimnet-ifc2x3-759.json"
    ).exists()
    sidecar = _load_json(
        tmp_path
        / "text2json"
        / "sidecars"
        / "train"
        / "bimnet-ifc2x3-1px.sidecar.json"
    )
    assert sidecar["losses"] == losses
    assert manifest["records"][0]["target_kind"] == "formal"
    assert manifest["records"][1]["target_kind"] == "draft_clarification"


def test_formal_target_builder_rejects_non_draft_without_fabricating() -> None:
    with pytest.raises(GoldSetError, match="Draft"):
        build_formal_target_from_draft(
            {"schema_version": "bim-json/2.0"},
            source_record=_source_record(),
            split="train",
        )
