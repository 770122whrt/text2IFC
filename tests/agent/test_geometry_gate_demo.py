from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case_id", ["simple-room-fixed", "two-room-suite"])
def test_geometry_gate_demo_writes_case_audit_artifacts(
    case_id: str,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / case_id

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/agent/run_geometry_gate_demo.py",
            "--case",
            case_id,
            "--output-dir",
            str(output_dir),
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    for name in (
        "input.txt",
        "prompt-used.md",
        "raw-response.txt",
        "candidate.json",
        "diagnostics.json",
        "metrics.json",
        "report.md",
        "expected.json",
        "output.ifc",
    ):
        assert (output_dir / name).exists(), name

    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["parse_valid"] is True
    assert metrics["bim_json_valid"] is True
    assert metrics["geometry_pass"] is True
    assert metrics["attributes_pass"] is True
    assert metrics["relationships_pass"] is True
    assert metrics["ifc_structure_pass"] is True
    assert metrics["compile_reopen_success"] is True
    assert metrics["iteration_count"] == 1
