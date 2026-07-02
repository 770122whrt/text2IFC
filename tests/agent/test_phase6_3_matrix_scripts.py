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


def test_matrix_runner_can_use_same_fixture_and_output_root_without_deleting_sources(
    monkeypatch,
    tmp_path,
):
    from scripts.agent import run_phase6_3_matrix

    source_root = tmp_path / "phase6.3-gate-audit"
    complex_dir = source_root / "complex-two-storey"
    three_dir = source_root / "non-two-storey-three-level"
    complex_dir.mkdir(parents=True)
    three_dir.mkdir(parents=True)
    (complex_dir / "input.txt").write_text(
        "two storey fixture with IfcBuildingStorey\n",
        encoding="utf-8",
    )
    _write_json(
        complex_dir / "expected-manual-review.json",
        {
            "schema_version": "text2ifc/phase6.3-complex-manual-review/1.0",
            "usage": "manual_review_truth_for_phase6_3_wave0_only",
            "expectations": {
                "production_rule": False,
                "storey_count": 2,
                "storey_elevations_mm": {"storey-1": 0, "storey-2": 3150},
                "space_ids_by_storey": {"storey-1": ["space-1"], "storey-2": ["space-2"]},
                "space_counts": {"storey-1": 1, "storey-2": 1},
                "door_counts": {"total": 2, "storey-1": 1, "storey-2": 1},
                "window_counts": {"total": 2, "storey-1": 1, "storey-2": 1},
            },
        },
    )
    _write_json(
        three_dir / "design-brief.json",
        {
            "schema_version": "text2ifc/design-brief/2.0",
            "status": "ready",
            "language": "zh-CN",
            "original_request": "three-storey fixture",
            "known_facts": {
                "storeys": [
                    {"id": "storey-1"},
                    {"id": "storey-2"},
                    {"id": "storey-3"},
                ],
                "spaces": [{"id": "level-3-room", "storey": "storey-3"}],
                "doors": [{"id": "level-3-door", "storey": "storey-3"}],
                "windows": [{"id": "level-3-window", "storey": "storey-3"}],
            },
            "fact_sources": [],
            "missing_facts": [],
            "ambiguities": [],
            "unsupported_requests": [],
        },
    )
    monkeypatch.setattr(run_phase6_3_matrix, "SOURCE_FIXTURE_ROOT", source_root)

    summary = run_phase6_3_matrix.run_matrix(source_root)

    assert summary["case_count"] >= 4
    assert (source_root / "complex-two-storey" / "input.txt").is_file()
    assert (source_root / "non-two-storey-three-level" / "design-brief.json").is_file()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
