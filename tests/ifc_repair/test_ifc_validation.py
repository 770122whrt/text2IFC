from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import ifcopenshell

from text2ifc_ifc_repair.ifc_validation import compare_validation_models


ROOT = Path(__file__).resolve().parents[2]


def _model_with_missing_coordinates(*, extra_direction_error: bool = False):
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint")
    if extra_direction_error:
        model.create_entity("IfcDirection")
    return model


def test_validation_delta_allows_baseline_errors_but_rejects_new_errors() -> None:
    baseline = _model_with_missing_coordinates()
    unchanged = _model_with_missing_coordinates()
    regressed = _model_with_missing_coordinates(extra_direction_error=True)

    no_regression = compare_validation_models(baseline, unchanged)
    regression = compare_validation_models(baseline, regressed)

    assert no_regression["status"] == "passed"
    assert no_regression["baseline_diagnostic_count"] == 1
    assert no_regression["candidate_diagnostic_count"] == 1
    assert no_regression["new_diagnostic_count"] == 0
    assert regression["status"] == "failed"
    assert regression["new_diagnostic_count"] == 1
    assert regression["new_diagnostics"][0]["attribute"] == (
        "IfcDirection.DirectionRatios"
    )


def test_validate_cli_reports_baseline_delta_and_nonzero_exit(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.ifc"
    candidate = tmp_path / "candidate.ifc"
    _model_with_missing_coordinates().write(str(baseline))
    _model_with_missing_coordinates(extra_direction_error=True).write(
        str(candidate)
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ifc_repair" / "validate_ifc.py"),
            str(candidate),
            "--baseline",
            str(baseline),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "failed"
    assert payload["new_diagnostic_count"] == 1
