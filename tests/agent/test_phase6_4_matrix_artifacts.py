import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase6_4_matrix_runner_writes_case_and_root_artifacts(tmp_path):
    from scripts.agent import run_phase6_4_feedback_matrix

    output_root = tmp_path / "phase6.4-matrix"

    summary = run_phase6_4_feedback_matrix.run_matrix(output_root)

    assert summary["schema_version"] == "text2ifc/phase6.4-feedback-matrix/1.0"
    assert summary["case_count"] == 8
    assert summary["false_accept_count"] == 0
    assert summary["accepted_count"] >= 1
    assert summary["blocked_count"] >= 1
    assert summary["draft_count"] >= 1
    assert (output_root / "matrix-result.json").is_file()
    assert (output_root / "matrix-report.md").is_file()

    for case in summary["cases"]:
        case_dir = output_root / case["case_id"]
        assert (case_dir / "case-result.json").is_file()
        assert (case_dir / "issues.json").is_file()
        assert (case_dir / "route-decision.json").is_file()
        assert (case_dir / "feedback-rounds.json").is_file()
        assert (case_dir / "report.md").is_file()
        case_result = json.loads((case_dir / "case-result.json").read_text(encoding="utf-8"))
        assert case_result["input_language"] == "zh-CN"
        assert case_result["workflow_language"] == "en-US-control"
        assert case_result["prompt_language"] == "zh-CN"
        assert isinstance(case_result["schema_passed"], bool)
        assert isinstance(case_result["deterministic_gates_passed"], bool)
        assert isinstance(case_result["audit_passed"], bool)
        assert case_result["route"] == case["route"]
        assert case_result["evidence_paths"]
        if case_result["final_status"] == "accepted":
            assert case_result["deterministic_gates_passed"] is True
            assert case_result["audit_passed"] is True
            assert (case_dir / "output.ifc").is_file()
        else:
            assert case_result["blocking_issue_count"] > 0


def test_phase6_4_matrix_cli_writes_json_summary(tmp_path):
    output_root = tmp_path / "phase6.4-matrix-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_phase6_4_feedback_matrix.py"),
            "--output-root",
            str(output_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["schema_version"] == "text2ifc/phase6.4-feedback-matrix/1.0"
    assert (output_root / "matrix-result.json").is_file()
    assert (output_root / "matrix-report.md").is_file()
