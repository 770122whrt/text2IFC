"""Execute the Phase 10.3 deterministic five-Window benchmark proof."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=(
            ROOT
            / "dataset"
            / "processed"
            / "ifc-repair"
            / "phase10.3-vvo-five-window-offline"
        ),
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"OUTPUT_ALREADY_EXISTS:{output}")
    output.mkdir(parents=True)

    specification = runpy.run_path(
        str(ROOT / "tests" / "ifc_repair" / "test_phase10_3_vvo_batch_e2e.py")
    )
    specification[
        "test_vvo_one_text_one_changeset_repairs_five_windows_atomically"
    ](output)

    state_paths = sorted((output / "runs" / "runs").glob("*/state.json"))
    if len(state_paths) != 1:
        raise SystemExit("OFFLINE_RUN_STATE_NOT_UNIQUE")
    state = json.loads(state_paths[0].read_text(encoding="utf-8"))
    summary = {
        "schema_version": "text2ifc/phase10.3-offline-benchmark-result/0.1",
        "case_id": "vvo-five-window-001",
        "status": state["stage"],
        "operation_count": 5,
        "source_ifc": "dataset/external/bimnet/vvo.ifc",
        "source_sha256": (
            "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc"
        ),
        "damaged_ifc": "fixture/damaged.ifc",
        "request": "request.txt",
        "public_spec": "public-spec.json",
        "private_ground_truth_evaluation": (
            "private-ground-truth-evaluation.json"
        ),
        "pipeline_run": state_paths[0].parent.relative_to(output).as_posix(),
        "artifacts": state["result_artifacts"],
        "offline_deterministic_provider": True,
    }
    atomic_write_text(
        output / "benchmark-result.json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if state["stage"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
