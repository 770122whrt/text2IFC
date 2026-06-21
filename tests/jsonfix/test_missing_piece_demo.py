from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_jsonfix.ifc_artifact import check_ifc2x3_artifact


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "jsonfix" / "run_missing_piece_demo.py"


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.demo")
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing-piece demo is not implemented: {exc}")
    return module.run_missing_piece_demo


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_missing_piece_demo_writes_complete_acceptance_artifacts(
    tmp_path: Path,
) -> None:
    run_missing_piece_demo = _api()

    result = run_missing_piece_demo(
        output_dir=tmp_path,
        inventory_roots=[],
    )

    assert result["success"]
    required = {
        "input.txt",
        "base.json",
        "patch.json",
        "composed.json",
        "diagnostics.json",
        "metrics.json",
        "report.md",
        "output.ifc",
        "provenance.json",
        "external-inventory.json",
    }
    assert required.issubset(
        {path.name for path in tmp_path.iterdir() if path.is_file()}
    )


def test_demo_composed_json_and_ifc_pass_independent_gates(
    tmp_path: Path,
) -> None:
    run_missing_piece_demo = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])
    composed = _json(tmp_path / "composed.json")

    assert validate_v2_document(composed) == []
    artifact = check_ifc2x3_artifact(tmp_path / "output.ifc")
    assert artifact.success
    assert artifact.declared_file_schema == "IFC2X3"
    assert artifact.reopened_schema == "IFC2X3"
    assert artifact.ifc_validation_error_count == 0


def test_demo_metrics_record_all_hard_acceptance_facts(
    tmp_path: Path,
) -> None:
    run_missing_piece_demo = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])
    metrics = _json(tmp_path / "metrics.json")

    assert metrics["patch_valid"] is True
    assert metrics["composition_valid"] is True
    assert metrics["formal_bim_json_valid"] is True
    assert metrics["compile_success"] is True
    assert metrics["declared_file_schema"] == "IFC2X3"
    assert metrics["reopened_schema"] == "IFC2X3"
    assert metrics["ifc_validation_error_count"] == 0
    assert metrics["generated_ifc_quality_passed"] is True
    assert metrics["success"] is True


def test_demo_quality_and_provenance_report_are_explicit(
    tmp_path: Path,
) -> None:
    run_missing_piece_demo = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])
    diagnostics = _json(tmp_path / "diagnostics.json")
    provenance = _json(tmp_path / "provenance.json")
    report = (tmp_path / "report.md").read_text(encoding="utf-8")

    assert diagnostics["patch_validation"] == []
    assert diagnostics["formal_validation"] == []
    assert diagnostics["artifact"]["success"] is True
    assert diagnostics["quality"]["success"] is True
    assert provenance["summary"]["patch_fact_count"] == 1
    for heading in (
        "## Source Facts",
        "## Patch Facts",
        "## Validation Facts",
        "## Compiler Facts",
        "## External Evidence",
    ):
        assert heading in report
    assert "wall-west" in report
    assert "IFC2X3" in report


def test_demo_cli_check_uses_the_same_acceptance_path(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--output-dir",
            str(tmp_path),
            "--skip-external-inventory",
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["success"]
    assert Path(payload["output_dir"]) == tmp_path
