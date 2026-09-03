"""Build the approved Phase 10.3 IFC repair benchmark records."""

from __future__ import annotations

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


BENCHMARKS = (
    {
        "benchmark_id": "bimnet-vvo-five-window-primary",
        "local_path": "dataset/ifc/train/vvo.ifc",
        "execution_role": "primary_full_pipeline",
        "suitability": (
            "23 valid Window chains on 77 straight walls; project test split; "
            "small enough for repeated five-operation end-to-end validation"
        ),
    },
    {
        "benchmark_id": "bimnet-px4-1-medium-compatibility",
        "local_path": "dataset/ifc/train/px4_1.ifc",
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
    records = [
        build_benchmark_record(root=ROOT, **definition)
        for definition in BENCHMARKS
    ]
    print(render_jsonl(records), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
