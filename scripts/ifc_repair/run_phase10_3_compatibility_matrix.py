"""Measure deterministic index and capability compatibility on admitted IFCs."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.ifc_repair_benchmarks import (
    load_and_validate_benchmark_manifest,
)
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.sample import inspect_sample_capabilities
from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "dataset" / "manifests" / "ifc-repair-benchmarks.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "dataset"
            / "processed"
            / "ifc-repair"
            / "phase10.3-compatibility-matrix.json"
        ),
    )
    args = parser.parse_args()
    records = load_and_validate_benchmark_manifest(args.manifest, root=ROOT)
    results = []
    with tempfile.TemporaryDirectory(prefix="text2ifc-phase10-3-") as temporary:
        temporary_root = Path(temporary)
        for record in records:
            source = ROOT / record["local_path"]
            started = time.perf_counter()
            try:
                capabilities = inspect_sample_capabilities(source)
                capability_seconds = time.perf_counter() - started
                index_path = temporary_root / f"{record['benchmark_id']}.sqlite"
                index_started = time.perf_counter()
                metadata = build_ifc_index(source, index_path)
                index_seconds = time.perf_counter() - index_started
                with SQLiteIndexRepository.open(
                    index_path,
                    expected_source_ifc_sha256=metadata.source_ifc_sha256,
                ) as repository:
                    element_count = sum(1 for _ in repository.iter_records())
                    type_count = sum(1 for _ in repository.iter_type_records())
                    diagnostic_count = len(repository.diagnostics())
                results.append(
                    {
                        "benchmark_id": record["benchmark_id"],
                        "local_path": record["local_path"],
                        "status": "passed",
                        "size_bytes": record["size_bytes"],
                        "entity_count": record["entity_count"],
                        "window_count": record["window_count"],
                        "valid_window_opening_wall_chain_count": capabilities[
                            "valid_window_opening_wall_chain_count"
                        ],
                        "straight_wall_count": capabilities["straight_wall_count"],
                        "unsupported_wall_count": capabilities[
                            "unsupported_wall_count"
                        ],
                        "capability_scan_seconds": round(capability_seconds, 3),
                        "index_build_seconds": round(index_seconds, 3),
                        "indexed_element_count": element_count,
                        "indexed_type_count": type_count,
                        "index_diagnostic_count": diagnostic_count,
                        "source_mutated": False,
                        "full_batch_pipeline": (
                            record["execution_role"] == "primary_full_pipeline"
                        ),
                    }
                )
            except Exception as error:
                results.append(
                    {
                        "benchmark_id": record["benchmark_id"],
                        "local_path": record["local_path"],
                        "status": "failed",
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "source_mutated": False,
                    }
                )
    report = {
        "schema_version": "text2ifc/phase10.3-compatibility-matrix/0.1",
        "source_manifest": args.manifest.relative_to(ROOT).as_posix(),
        "records": results,
        "all_passed": all(item["status"] == "passed" for item in results),
        "notes": [
            "Every source is opened read-only; SQLite indexes are temporary and rebuildable.",
            "Only vvo is admitted for the full five-Window pipeline in Phase 10.3.",
            "Larger files measure compatibility and indexing cost, not Provider success.",
        ],
    }
    atomic_write_text(
        args.output,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
