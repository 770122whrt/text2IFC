"""Run the deterministic Phase 6 service acceptance demo."""

from __future__ import annotations

import argparse
import json
import site
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))
USER_SITE = Path(site.getusersitepackages())
sys.path.append(str(USER_SITE))

from text2ifc_service import DEFAULT_OUTPUT_DIR, run_demo_scenario  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=("complete", "draft", "blocked"),
        default="complete",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run_demo_scenario(
        scenario=args.scenario,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "scenario": result["scenario"],
                "expected_outcome": result["expected_outcome"],
                "metrics": result["record"]["metrics"],
                "output_dir": str(args.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if args.check and not result["expected_outcome"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
