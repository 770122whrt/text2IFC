"""Run the deterministic jsonfix missing-piece IFC2X3 demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_jsonfix.demo import run_missing_piece_demo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--skip-external-inventory", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    roots = [] if args.skip_external_inventory else None
    result = run_missing_piece_demo(
        output_dir=args.output_dir,
        inventory_roots=roots,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["success"] or not args.check else 2


if __name__ == "__main__":
    raise SystemExit(main())
