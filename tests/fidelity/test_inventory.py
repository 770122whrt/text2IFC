from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from text2ifc_fidelity.inventory import build_fidelity_inventory


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
SPLITS = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"


def test_fidelity_inventory_represents_all_authorized_bimnet_files() -> None:
    inventory = build_fidelity_inventory(MANIFEST, SPLITS)

    assert inventory["schema_version"] == "text2ifc/phase4-fidelity-inventory-v1"
    assert inventory["counts"]["files"]["total"] == 25
    assert inventory["counts"]["files"]["train"] == 17
    assert inventory["counts"]["files"]["validation"] == 5
    assert inventory["counts"]["files"]["test"] == 3
    assert len(inventory["records"]) == 25
    assert {record["split"] for record in inventory["records"]} == {
        "train",
        "validation",
        "test",
    }


def test_fidelity_inventory_counts_phase4_source_fact_classes() -> None:
    inventory = build_fidelity_inventory(MANIFEST, SPLITS)
    record = next(
        item for item in inventory["records"] if item["id"] == "bimnet-ifc2x3-hxp"
    )

    assert record["scene_family"] == "hxp"
    assert record["split"] == "train"
    assert record["sha256"]
    assert record["local_path"].endswith("dataset/external/bimnet/hxp.ifc")
    metrics = record["metrics"]
    for key in (
        "material_associations",
        "material_layers",
        "type_relationships",
        "connection_topology",
        "representation_kinds",
        "mapped_geometry",
        "brep",
        "tessellation",
        "openings",
        "spaces",
        "product_classes",
    ):
        assert key in metrics
    assert isinstance(metrics["product_classes"], dict)
    assert sum(metrics["product_classes"].values()) > 0
    assert set(record["fact_classification"]) == {
        "already_supported",
        "phase4_candidate",
        "explicit_loss",
        "deferred",
    }


def test_fidelity_inventory_cli_writes_checked_inventory(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "fidelity-inventory.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ifc_pipeline_v2/fidelity_inventory.py",
            "--all",
            "--check",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["counts"]["files"]["total"] == 25
    assert len(payload["records"]) == 25
    assert json.loads(completed.stdout)["success"] is True
