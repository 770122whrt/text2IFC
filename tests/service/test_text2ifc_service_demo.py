from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "service" / "run_text2ifc_service_demo.py"
REQUIRED_REPORT_HEADINGS = (
    "## Original Input",
    "## Design Brief",
    "## Rendered Prompt",
    "## Model Raw Output",
    "## Parsed BIM JSON or Draft",
    "## Validation Feedback",
    "## Geometry Feedback",
    "## Failure Route",
    "## Audit Result",
    "## Metrics",
    "## Final Artifacts",
)


def _run(tmp_path: Path, scenario: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    output = tmp_path / scenario
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--scenario",
            scenario,
            "--output-dir",
            str(output),
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed, output


def test_complete_request_writes_ifc_trace_bundle_and_report(tmp_path):
    completed, output = _run(tmp_path, "complete")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    for name in (
        "input.txt",
        "design-brief.json",
        "prompt-render-input.json",
        "prompt-metadata.json",
        "prompt-rendered.md",
        "raw-response.txt",
        "parsed-response.json",
        "candidate.json",
        "validation-feedback.json",
        "geometry-feedback.json",
        "repair-attempts.json",
        "audit-report.json",
        "metrics.json",
        "artifact-manifest.json",
        "experiment-record.json",
        "secret-scan.json",
        "report.md",
        "output.ifc",
    ):
        assert (output / name).is_file(), name
    assert (output / "output.ifc").stat().st_size > 1000
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["success"] is True
    assert metrics["failure_route"] == "no_repair_needed"
    assert metrics["repair_attempt_count"] == 0


def test_incomplete_request_stays_draft_without_ifc(tmp_path):
    completed, output = _run(tmp_path, "draft")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert (output / "draft.json").is_file()
    assert not (output / "output.ifc").exists()
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["bim_json_status"] == "draft"
    assert metrics["failure_route"] == "draft_required"
    draft = json.loads((output / "draft.json").read_text(encoding="utf-8"))
    assert draft["missing_facts"]
    assert draft["clarification_targets"]


def test_failed_deterministic_gate_marks_run_blocking(tmp_path):
    completed, output = _run(tmp_path, "blocked")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert not (output / "output.ifc").exists()
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    audit = json.loads((output / "audit-report.json").read_text(encoding="utf-8"))
    assert metrics["success"] is False
    assert metrics["failure_route"] == "blocked_failure"
    assert audit["blocking"] is True
    assert audit["recommendation"] == "reject"


def test_run_report_contains_intermediate_inputs_and_outputs(tmp_path):
    completed, output = _run(tmp_path, "complete")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = (output / "report.md").read_text(encoding="utf-8")
    for heading in REQUIRED_REPORT_HEADINGS:
        assert heading in report
    assert "请创建一个单层矩形房间" in report
    assert "text2ifc/design-brief/1.0" in report
    assert '"schema_version": "bim-json/2.0"' in report
    assert "output.ifc" in report
    assert "secret_redaction_status" in report
