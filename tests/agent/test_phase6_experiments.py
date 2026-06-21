import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
GEOMETRY_CASE = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "geometry-gate"
    / "simple-room-fixed"
)
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


def _brief(*, include_width=True):
    room = {"length_mm": 6000, "height_mm": 3000}
    if include_width:
        room["width_mm"] = 4000
    return {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": "创建一个长6米、宽4米、高3米的单层房间。",
        "known_facts": {
            "storey_count": 1,
            "room": room,
            "walls": {"count": 4, "enclosure": "closed"},
        },
        "missing_facts": []
        if include_width
        else [
            {
                "id": "room-width",
                "code": "ROOM_WIDTH_MISSING",
                "path": "/room/width_mm",
                "message": "缺少房间宽度。",
                "source": "user_request",
            }
        ],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source": "user_request"},
    }


def _geometry_candidate():
    return json.loads((GEOMETRY_CASE / "candidate.json").read_text(encoding="utf-8"))


def _geometry_expectation():
    return json.loads((GEOMETRY_CASE / "expected.json").read_text(encoding="utf-8"))


def _draft():
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {"room": {}},
        "missing_facts": [
            {
                "entity_id": "space-1",
                "path": "/room/width_mm",
                "code": "ROOM_WIDTH_MISSING",
                "message": "缺少房间宽度。",
            }
        ],
        "losses": [],
        "clarification_targets": [
            {
                "entity_id": "space-1",
                "path": "/room/width_mm",
                "question": "房间宽度是多少？",
            }
        ],
        "provenance": {"source": "provider"},
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


def test_experiment_matrix_covers_success_draft_repair_block_and_audit(tmp_path):
    experiments = _experiments()
    cases = [
        {
            "case_id": "success",
            "input_text": _brief()["original_request"],
            "design_brief": _brief(),
            "candidate": _geometry_candidate(),
            "expectation": _geometry_expectation(),
        },
        {
            "case_id": "draft",
            "input_text": "创建一个房间，但我不知道宽度。",
            "design_brief": _brief(include_width=False),
            "candidate": _draft(),
            "expectation": _geometry_expectation(),
        },
        {
            "case_id": "repair",
            "input_text": _brief()["original_request"],
            "design_brief": _brief(),
            "candidate": {"schema_version": "bim-json/2.0"},
            "expectation": _geometry_expectation(),
        },
        {
            "case_id": "blocked",
            "input_text": _brief()["original_request"],
            "design_brief": _brief(),
            "raw_response": "{",
            "expectation": _geometry_expectation(),
        },
        {
            "case_id": "audit",
            "input_text": _brief()["original_request"],
            "design_brief": _brief(),
            "candidate": _geometry_candidate(),
            "expectation": _geometry_expectation(),
            "audit_mismatches": [
                {
                    "code": "USER_INTENT_MISMATCH",
                    "message": "生成结果与用户意图不一致。",
                }
            ],
        },
    ]

    summary = experiments.run_phase6_matrix(cases=cases, output_dir=tmp_path)

    assert set(summary["failure_routes"]) == {
        "no_repair_needed",
        "draft_required",
        "repair_attempted",
        "blocked_failure",
    }
    assert set(summary["failure_classes"]) == {
        "success",
        "draft",
        "invalid_bim_json",
        "invalid_json",
        "audit_mismatch",
    }
    assert (tmp_path / "experiment-matrix.json").exists()


def test_failed_rerun_removes_stale_ifc_and_candidate(tmp_path):
    experiments = _experiments()
    output = tmp_path / "same-case"
    common = {
        "case_id": "same-case",
        "input_text": _brief()["original_request"],
        "design_brief": _brief(),
        "expectation": _geometry_expectation(),
        "output_dir": output,
    }
    experiments.run_phase6_case(candidate=_geometry_candidate(), **common)
    assert (output / "output.ifc").exists()

    experiments.run_phase6_case(raw_response="{", **common)

    assert not (output / "output.ifc").exists()
    assert not (output / "candidate.json").exists()
    assert (output / "parsed-response.json").exists()


def test_phase6_matrix_cli_writes_durable_controlled_cases(tmp_path):
    output = tmp_path / "matrix"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/agent/run_phase6_experiment.py",
            "--output-dir",
            str(output),
            "--matrix",
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads((output / "experiment-matrix.json").read_text(encoding="utf-8"))
    assert summary["case_count"] == 5
    assert set(summary["failure_routes"]) == {
        "no_repair_needed",
        "draft_required",
        "repair_attempted",
        "blocked_failure",
    }
    assert set(summary["failure_classes"]) == {
        "success",
        "draft",
        "invalid_bim_json",
        "invalid_json",
        "audit_mismatch",
    }
    for case_id in ("success", "draft", "repair", "blocked", "audit"):
        assert (output / case_id / "report.md").exists()
