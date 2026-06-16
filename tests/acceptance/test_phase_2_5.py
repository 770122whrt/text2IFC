from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
AUDIT = (
    ROOT
    / "dataset"
    / "processed"
    / "bim-json-2.0"
    / "extraction-audit.json"
)
FAMILIES = (
    ROOT
    / "dataset"
    / "processed"
    / "bim-json-2.0"
    / "scene-families.json"
)
BIM_JSON_REFERENCE = ROOT / "docs" / "reference" / "bim-json-2.0.md"
PROFILE_REFERENCE = (
    ROOT / "docs" / "reference" / "ifc2x3-generation-profile.md"
)
CATEGORIES = {
    "entities",
    "relationships",
    "properties",
    "representations",
    "materials",
    "types",
    "connections",
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest() -> list[dict]:
    return [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_balanced(inventory: dict) -> None:
    assert set(inventory) == CATEGORIES
    for record in inventory.values():
        assert record["source"] == (
            record["represented"] + record["reported"]
        )
        assert min(record.values()) >= 0


def test_bimnet_manifest_covers_authorized_ifc2x3_without_inferred_rights() -> None:
    records = _manifest()

    assert len(records) == 25
    assert len({record["id"] for record in records}) == 25
    assert len({record["sha256"] for record in records}) == 25
    assert all(record["declared_schema"] == "IFC2X3" for record in records)
    assert all(record["source_revision"] is None for record in records)
    assert all(record["training_eligible"] is True for record in records)
    assert all(
        record["authorization"]["confirmed_at"] == "2026-06-11"
        for record in records
    )
    assert all(
        record["authorization"]["redistribution_inferred"] is False
        for record in records
    )
    for record in records:
        local_path = ROOT / record["local_path"]
        assert local_path.is_file()
        assert record["sha256"] == _sha256(local_path)


def test_scene_families_are_recorded_before_split_assignment() -> None:
    payload = _json(FAMILIES)
    records = _manifest()

    assert payload["schema_version"] == "text2ifc/scene-families-v1"
    assert payload["split_assignment"] is None
    assert len(payload["families"]) == 19
    assert sum(
        len(family["file_ids"]) for family in payload["families"]
    ) == 25
    assert {
        (record["id"], record["scene_family"]) for record in records
    } == {
        (file_id, family["scene_family"])
        for family in payload["families"]
        for file_id in family["file_ids"]
    }
    family_sizes = Counter(record["scene_family"] for record in records)
    assert family_sizes["7y3"] == 2
    assert family_sizes["e9z"] == 2
    assert family_sizes["px4"] == 3


def test_all_25_extractions_have_balanced_per_file_and_aggregate_accounts() -> None:
    payload = _json(AUDIT)
    manifest = _manifest()

    assert payload["schema_version"] == "text2ifc/extraction-audit-v1"
    assert payload["file_count"] == 25
    assert len(payload["files"]) == 25
    assert {record["id"] for record in payload["files"]} == {
        record["id"] for record in manifest
    }
    for record in payload["files"]:
        assert record["status"] in {"formal", "draft"}
        _assert_balanced(record["inventory"])
    _assert_balanced(payload["aggregate"]["inventory"])
    assert sum(payload["aggregate"]["status_counts"].values()) == 25


def test_checked_in_audit_regenerates_without_drift() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ifc_pipeline_v2/audit_bimnet.py",
            "--check-accounting",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_generated_contract_and_profile_references_are_current() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/bim_json_v2/generate_reference.py",
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    contract = BIM_JSON_REFERENCE.read_text(encoding="utf-8")
    profile = PROFILE_REFERENCE.read_text(encoding="utf-8")
    assert "`bim-json/2.0`" in contract
    assert "Formal" in contract and "Draft Envelope" in contract
    assert "`Representation.position`" in contract
    assert "25" in profile
    assert "`IfcWallStandardCase`" in profile
    assert "`IfcWallType`" in profile
    assert "`IfcRelDefinesByType`" in profile
    assert "`IfcCartesianPoint`" in profile
    assert "compiler-only" in profile
