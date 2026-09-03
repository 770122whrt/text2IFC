import json
from pathlib import Path

from text2ifc_dataset.ifc_repair_benchmarks import (
    BENCHMARK_SCHEMA_VERSION,
    build_benchmark_record,
    load_and_validate_benchmark_manifest,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "dataset" / "manifests" / "ifc-repair-benchmarks.jsonl"


def test_checked_in_benchmark_manifest_has_the_approved_models() -> None:
    records = load_and_validate_benchmark_manifest(MANIFEST, root=ROOT)

    assert [record["benchmark_id"] for record in records] == [
        "bimnet-vvo-five-window-primary",
        "bimnet-px4-1-medium-compatibility",
        "bim-whale-advanced-project-stress",
        "bim-whale-basic-house-optional-stress",
    ]
    for record in records:
        assert record["schema_version"] == BENCHMARK_SCHEMA_VERSION
        assert record["ifc_schema"] == "IFC2X3"
        assert record["size_bytes"] > 0
        assert record["entity_count"] > 0
        assert record["window_count"] >= 5
        assert record["valid_window_opening_wall_chain_count"] >= 5
        assert record["straight_wall_count"] > 0
        assert len(record["source_sha256"]) == 64

    assert records[0]["project_split"] == "test"
    assert records[0]["execution_role"] == "primary_full_pipeline"
    assert records[1]["project_split"] == "train"


def test_vvo_benchmark_record_rebuilds_exactly() -> None:
    checked_in = json.loads(MANIFEST.read_text(encoding="utf-8").splitlines()[0])

    rebuilt = build_benchmark_record(
        root=ROOT,
        benchmark_id=checked_in["benchmark_id"],
        local_path=checked_in["local_path"],
        execution_role=checked_in["execution_role"],
        suitability=checked_in["suitability"],
    )

    assert rebuilt == checked_in

