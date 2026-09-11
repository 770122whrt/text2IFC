"""Build the approved Phase 10.3 IFC repair benchmark records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.ifc_repair_benchmarks import (
    ROOT,
    build_benchmark_record,
    render_jsonl,
)
from text2ifc_text.splits import atomic_write_text


BENCHMARKS = (
    {
        "benchmark_id": "bimnet-vvo-five-window-primary",
        "local_path": "dataset/external/bimnet/vvo.ifc",
        "execution_role": "primary_full_pipeline",
        "suitability": (
            "23 valid Window chains on 77 straight walls; project test split; "
            "small enough for repeated five-operation end-to-end validation"
        ),
    },
    {
        "benchmark_id": "bimnet-px4-1-medium-compatibility",
        "local_path": "dataset/external/bimnet/px4_1.ifc",
        "execution_role": "medium_compatibility",
        "suitability": (
            "19 valid Window chains and roughly ten times vvo entity scale"
        ),
    },
    {
        "benchmark_id": "bim-whale-advanced-project-stress",
        "local_path": (
            "dataset/external/bim-whale-ifc-samples/AdvancedProject/IFC/"
            "AdvancedProject.ifc"
        ),
        "execution_role": "high_window_count_stress",
        "suitability": (
            "263 valid Window chains provide target-index and candidate-volume stress"
        ),
    },
    {
        "benchmark_id": "bim-whale-basic-house-optional-stress",
        "local_path": (
            "dataset/external/bim-whale-ifc-samples/BasicHouse/IFC/BasicHouse.ifc"
        ),
        "execution_role": "optional_serialization_stress",
        "suitability": (
            "million-entity IFC2X3 model for optional reopen and serialization stress"
        ),
    },
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    records = [
        build_benchmark_record(root=ROOT, **definition)
        for definition in BENCHMARKS
    ]
    rendered = render_jsonl(records)
    if args.write:
        atomic_write_text(ROOT / "dataset/manifests/ifc-repair-benchmarks.jsonl", rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
