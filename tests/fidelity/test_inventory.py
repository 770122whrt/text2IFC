from __future__ import annotations

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
    assert record["local_path"].endswith("dataset/ifc/train/hxp.ifc")
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
