"""Generate or check the BIM JSON Patch 1.0 reference."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_jsonfix.reference import (  # noqa: E402
    DEFAULT_PATCH_REFERENCE_PATH,
    check_patch_reference,
    write_patch_reference,
)
from text2ifc_jsonfix.validation import load_patch_schema  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or check the BIM JSON Patch 1.0 reference."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check schema/reference drift without writing.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_PATCH_REFERENCE_PATH,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    schema = load_patch_schema()
    if args.check:
        matches, message = check_patch_reference(schema, args.output)
        print(message)
        return 0 if matches else 1
    write_patch_reference(schema, args.output)
    print(f"Wrote BIM JSON patch reference: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
