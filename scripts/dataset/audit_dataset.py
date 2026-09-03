"""Run the read-only dataset audit and optionally verify a saved report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.audit import ROOT, audit_dataset, render_json
from text2ifc_text.splits import atomic_write_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = render_json(audit_dataset(args.root))
    if args.check is not None:
        if not args.check.is_file() or args.check.read_text(encoding="utf-8") != rendered:
            raise SystemExit("DATASET_AUDIT_DRIFT")
    if args.output is not None:
        atomic_write_text(args.output, rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
