import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_contract.reference import (
    DEFAULT_REFERENCE_PATH,
    check_reference,
    write_reference,
)
from text2ifc_contract.schema import load_schema


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or check the BIM JSON 1.0 contract reference."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for schema/reference drift without writing.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REFERENCE_PATH,
        help="Reference output path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    schema = load_schema()

    if args.check:
        matches, message = check_reference(schema, args.output)
        print(message)
        return 0 if matches else 1

    write_reference(schema, args.output)
    print(f"Wrote BIM JSON reference: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
