import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase6_3_matrix_runner_and_verifier_write_acceptance_artifacts(tmp_path):
    output_root = tmp_path / "phase6.3-matrix"

    matrix = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_phase6_3_matrix.py"),
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
    matrix_summary = json.loads(matrix.stdout)
    assert matrix_summary["schema_version"] == "text2ifc/phase6.3-matrix/1.0"
    assert matrix_summary["case_count"] >= 4
    assert matrix_summary["complex_two_storey_status"] in {"blocked", "accepted"}
    assert matrix_summary["false_accept_count"] == 0
    assert matrix_summary["non_two_storey_gate_route_covered"] is True
    assert (output_root / "matrix-report.md").is_file()

    verifier = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "verify_phase6_3_artifacts.py"),
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

    assert verifier.returncode == 0, verifier.stderr
    verification = json.loads(verifier.stdout)
    assert verification["schema_version"] == "text2ifc/phase6.3-final-verification/1.0"
    assert verification["valid"] is True
    assert verification["secret_finding_count"] == 0
    assert verification["hash_binding_valid"] is True
    assert verification["non_two_storey_gate_route_covered"] is True
    assert (output_root / "final-verification.json").is_file()


def test_phase6_3_verifier_rejects_false_accepted_blocking_gate(tmp_path):
    output_root = tmp_path / "phase6.3-matrix"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_phase6_3_matrix.py"),
            "--output-root",
            str(output_root),
        ],
        cwd=ROOT,
        check=True,
    )
    route_path = output_root / "complex-two-storey" / "route-decision.json"
    route = json.loads(route_path.read_text(encoding="utf-8"))
    route["route"] = "accept"
    route["owner_stage"] = "none"
    route_path.write_text(
        json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    verifier = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "verify_phase6_3_artifacts.py"),
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

    assert verifier.returncode == 2
    verification = json.loads(verifier.stdout)
    assert verification["valid"] is False
    assert "FALSE_ACCEPT_BLOCKING_GATES" in verification["issue_codes"]
