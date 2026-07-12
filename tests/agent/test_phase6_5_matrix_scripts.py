import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_matrix_cli_and_verifier_produce_machine_readable_evidence(tmp_path):
    output_root = tmp_path / "phase6.5-matrix-cli"
    matrix = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent/run_phase6_5_deterministic_matrix.py"),
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
    assert matrix.returncode == 0, matrix.stderr
    summary = json.loads(matrix.stdout)
    assert summary["case_count"] == 8

    verified = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent/verify_phase6_5_artifacts.py"),
            "--root",
            str(output_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert verified.returncode == 0, verified.stderr
    result = json.loads(verified.stdout)
    assert result["schema_version"] == "text2ifc/phase6.5-verification/1.0"
    assert result["valid"] is True
    assert result["secret_finding_count"] == 0
    assert result["accepted_multistorey_count"] == 2
    assert result["false_accept_count"] == 0
    assert (output_root / "final-verification.json").is_file()


def test_verifier_rejects_tampered_preservation_evidence(tmp_path):
    from scripts.agent import run_phase6_5_deterministic_matrix

    output_root = tmp_path / "phase6.5-matrix"
    run_phase6_5_deterministic_matrix.run_matrix(output_root)
    path = output_root / "scoped-repair-accepted" / "case-result.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    row["preservation_rate"] = 0.5
    path.write_text(json.dumps(row), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent/verify_phase6_5_artifacts.py"),
            "--root",
            str(output_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 2
    verification = json.loads(result.stdout)
    assert "PRESERVATION_EVIDENCE_INVALID" in verification["issue_codes"]
