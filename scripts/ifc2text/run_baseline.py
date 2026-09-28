"""Prepare IFC2Text baseline artifacts or compare a reconstructed IFC."""

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

from text2ifc_ifc2text.roundtrip import (  # noqa: E402
    finalize_roundtrip_baseline,
    prepare_roundtrip_baseline,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deterministic IFC2Text phase-1 baseline.")
    parser.add_argument("source", type=Path, help="Source IFC; never modified.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reconstructed", type=Path, help="Optional reconstructed IFC to compare.")
    parser.add_argument("--no-space-inference", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest = prepare_roundtrip_baseline(
        args.source,
        args.output_dir,
        infer_spaces=not args.no_space_inference,
    )
    if args.reconstructed is not None:
        manifest = finalize_roundtrip_baseline(
            args.source,
            args.reconstructed,
            args.output_dir,
            reconstruction_evidence={"mode": "externally_supplied_reconstruction"},
        )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
