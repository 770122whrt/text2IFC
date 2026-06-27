import json
from pathlib import Path

from text2ifc_agent.session_store import SessionStore


def test_phase6_2_fix_verifier_rejects_scripted_stdin_acceptance(tmp_path):
    from scripts.agent import verify_phase6_2_fix_artifacts

    root, final_path = _write_minimal_acceptance(
        tmp_path,
        interaction_mode="scripted_regression",
        input_source="scripted_stdin",
        event_types=[
            "repl_session_started",
            "assistant_question_displayed",
            "user_answer_requested",
            "user_answer_received",
        ],
    )

    result = verify_phase6_2_fix_artifacts.verify(root, session_from=final_path)

    assert result["valid"] is False
    assert result["interaction_mode"] == "scripted_regression"
    assert result["input_source"] == "scripted_stdin"
    assert "human_repl_live" in result["issues"]
    assert "terminal_input_required" in result["issues"]


def test_phase6_2_fix_verifier_rejects_missing_question_before_answer_event(tmp_path):
    from scripts.agent import verify_phase6_2_fix_artifacts

    root, final_path = _write_minimal_acceptance(
        tmp_path,
        interaction_mode="human_repl_live",
        input_source="terminal",
        event_types=[
            "repl_session_started",
            "user_answer_requested",
            "user_answer_received",
        ],
    )

    result = verify_phase6_2_fix_artifacts.verify(root, session_from=final_path)

    assert result["valid"] is False
    assert "assistant_question_displayed_before_answer" in result["issues"]


def test_phase6_2_fix_verifier_rejects_missing_semantic_coverage(tmp_path):
    from scripts.agent import verify_phase6_2_fix_artifacts

    root, final_path = _write_minimal_acceptance(
        tmp_path,
        interaction_mode="human_repl_live",
        input_source="terminal",
        event_types=[
            "repl_session_started",
            "assistant_question_displayed",
            "user_answer_requested",
            "user_answer_received",
        ],
    )

    result = verify_phase6_2_fix_artifacts.verify(root, session_from=final_path)

    assert result["valid"] is False
    assert "semantic_coverage_required" in result["issues"]


def _write_minimal_acceptance(
    tmp_path: Path,
    *,
    interaction_mode: str,
    input_source: str,
    event_types: list[str],
) -> tuple[Path, Path]:
    root = tmp_path / "phase6.2-fix-repl"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.create_session(original_input="manual acceptance fixture")
        store.mark_session_status(session.session_id, "compiled")
        for event_type in event_types:
            payload = {}
            if event_type == "repl_session_started":
                payload = {
                    "interaction_mode": interaction_mode,
                    "input_source": input_source,
                }
            store.append_event(session.session_id, event_type=event_type, payload=payload)
        store.record_payload(
            session.session_id,
            table="metrics",
            payload={
                "stage": "acceptance",
                "valid": True,
                "audit_evidence_class": "live",
                "compile_reopen_success": True,
                "geometry_success": True,
            },
        )
        store.record_artifact(
            session.session_id,
            kind="report",
            path=Path("runs") / session.session_hash / "report.md",
        )
        export_path = store.export_session(session.session_id)
    finally:
        store.close()

    run_dir = root / "runs" / session.session_hash
    (run_dir / "report.md").write_text(
        "\n".join(
            [
                "# Phase 6.2-fix REPL Report",
                "## REPL Interaction Evidence",
                "interaction_mode",
                "input_source",
                "## Final Artifacts",
            ]
        ),
        encoding="utf-8",
    )
    final = {
        "schema_version": "text2ifc/phase6.2-fix-final-acceptance-v1",
        "session_id": session.session_id,
        "session_hash": session.session_hash,
        "status": "compiled",
        "artifacts": {
            "report": f"runs/{session.session_hash}/report.md",
            "session_export": f"runs/{session.session_hash}/{export_path.name}",
        },
    }
    final_path = root / "final-acceptance.json"
    final_path.write_text(
        json.dumps(final, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root, final_path
