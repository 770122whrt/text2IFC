import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_ROOT = ROOT / "dataset/processed/agent-demo/phase6.2-interactive-cli"


def test_phase6_2_artifact_verifier_accepts_live_cli_ifc_bundle():
    from scripts.agent import verify_phase6_2_artifacts

    final_acceptance = json.loads(
        (ACCEPTANCE_ROOT / "final-acceptance.json").read_text(encoding="utf-8")
    )
    result = verify_phase6_2_artifacts.verify(
        ACCEPTANCE_ROOT,
        session_from=ACCEPTANCE_ROOT / "final-acceptance.json",
    )

    assert result["valid"] is True
    assert result["session_hash"] == final_acceptance["session_hash"]
    assert result["session_in_db"] is True
    assert result["output_ifc_reopenable"] is True
    assert result["geometry_success"] is True
    assert result["compile_reopen_success"] is True
    assert result["secret_finding_count"] == 0
    assert result["report_has_required_sections"] is True
    assert result["export_matches_db_session"] is True


def test_phase6_2_artifact_verifier_rejects_mismatched_session_index(tmp_path):
    from scripts.agent import verify_phase6_2_artifacts

    root = tmp_path / "phase6.2-interactive-cli"
    root.mkdir()
    final_acceptance = {
        "schema_version": "text2ifc/phase6.2-final-acceptance-v1",
        "session_id": "phase6.2-missing",
        "session_hash": "missing",
        "status": "compiled",
        "artifacts": {
            "ifc": "runs/missing/output.ifc",
            "report": "runs/missing/report.md",
            "session_export": "runs/missing/session-export.json",
        },
    }
    session_from = root / "final-acceptance.json"
    session_from.write_text(
        json.dumps(final_acceptance, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = verify_phase6_2_artifacts.verify(root, session_from=session_from)

    assert result["valid"] is False
    assert "sessions.sqlite" in result["missing"]
    assert result["session_in_db"] is False
