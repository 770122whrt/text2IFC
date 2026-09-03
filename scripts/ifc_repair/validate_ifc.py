"""Run standalone or baseline-delta IfcOpenShell validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import ifcopenshell


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from text2ifc_ifc_repair.ifc_validation import (  # noqa: E402
    compare_validation_models,
    validate_model,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one IFC, or compare candidate diagnostics with an "
            "existing damaged/source baseline."
        )
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    try:
        candidate = ifcopenshell.open(str(arguments.candidate))
        if arguments.baseline is None:
            report = validate_model(candidate)
        else:
            baseline = ifcopenshell.open(str(arguments.baseline))
            report = compare_validation_models(baseline, candidate)
    except Exception as error:
        report = {
            "schema_version": "text2ifc/ifc-validation-delta/0.1",
            "status": "not_evaluable",
            "error_type": type(error).__name__,
            "error": str(error)[:1024],
        }

    serialized = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    if arguments.output is None:
        print(serialized)
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(serialized + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "output": str(arguments.output.resolve()),
                },
                ensure_ascii=False,
            )
        )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
