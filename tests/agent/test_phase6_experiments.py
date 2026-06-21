import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_HEADINGS = (
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


def _experiments():
    name = "text2ifc_agent.experiments"
    assert importlib.util.find_spec(name) is not None, "experiment harness is missing"
    return importlib.import_module(name)


def _record():
    return {
        "case_id": "simple-room-fixed",
        "split": "fixture",
        "prompt_template_id": "bim-json-generator.v1",
        "prompt_hash": "sha256:" + "a" * 64,
        "provider_mode": "fake",
        "repair_attempts": [],
        "metrics": {"success": True},
        "failure_class": None,
        "artifact_paths": {"report": "report.md"},
    }


def test_experiment_record_requires_prompt_identity():
    experiments = _experiments()
    record = _record()
    del record["prompt_hash"]

    with pytest.raises(experiments.ExperimentError, match="prompt_hash"):
        experiments.validate_experiment_record(record)


def test_run_report_requires_full_intermediate_io_manifest(tmp_path):
    experiments = _experiments()
    manifest = {
        heading: "input.txt" for heading in experiments.REQUIRED_REPORT_SECTIONS
    }
    del manifest["## Geometry Feedback"]
    (tmp_path / "input.txt").write_text("fixture", encoding="utf-8")

    with pytest.raises(experiments.ExperimentError, match="Geometry Feedback"):
        experiments.write_experiment_report(tmp_path, manifest)


def test_experiment_secret_status_requires_real_scan(tmp_path):
    experiments = _experiments()
    (tmp_path / "raw-response.txt").write_text(
        "authorization: Bearer should-not-appear",
        encoding="utf-8",
    )

    with pytest.raises(experiments.ExperimentError, match="secret scan"):
        experiments.assert_artifacts_secret_safe(tmp_path)


def test_phase6_experiment_writes_real_trace_report_and_ifc(tmp_path):
    output = tmp_path / "phase6-multiagent"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/agent/run_phase6_experiment.py",
            "--output-dir",
            str(output),
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
        "design-brief.json",
        "prompt-render-input.json",
        "prompt-metadata.json",
        "prompt-rendered.md",
        "raw-response.txt",
        "candidate.json",
        "validation-feedback.json",
        "geometry-feedback.json",
        "repair-attempts.json",
        "audit-report.json",
        "metrics.json",
        "artifact-manifest.json",
        "experiment-record.json",
        "report.md",
        "output.ifc",
    ):
        assert (output / name).exists(), name

    report = (output / "report.md").read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in report
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["success"] is True
    assert metrics["failure_route"] == "no_repair_needed"
    assert metrics["repair_attempt_count"] == 0
