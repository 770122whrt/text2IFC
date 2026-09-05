"""Write a generic, repair-agnostic difference report for two IFC files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for entry in (str(ROOT), str(SRC)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from text2ifc_ifc_repair.compare import (  # noqa: E402
    DEFAULT_COMPARISON_TIMEOUT_SECONDS,
    build_ifc_difference_report,
)
from text2ifc_text.splits import atomic_write_text  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare any two IFC files by GlobalId and enrich the changed "
            "products with Type, placement, geometry fingerprint, and direct "
            "property data."
        )
    )
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_COMPARISON_TIMEOUT_SECONDS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_ifc_difference_report(
        args.before,
        args.after,
        timeout_seconds=args.timeout_seconds,
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        output,
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )
    print(
        json.dumps(
            {
                "status": report["comparison_status"],
                "output": str(output),
                **report["summary"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
