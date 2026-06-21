"""Build deterministic jsonfix repair case artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_jsonfix.repair_cases import build_repair_case  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic semantic repair case."
    )
    parser.add_argument("--case", default="missing-piece-repair")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build_repair_case(args.case, args.output_dir)
    except (OSError, ValueError) as exc:
        result = {
            "success": False,
            "case_id": args.case,
            "error": str(exc),
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["success"] or not args.check else 2


if __name__ == "__main__":
    raise SystemExit(main())
