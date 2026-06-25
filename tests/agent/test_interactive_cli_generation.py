import json
from pathlib import Path

from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.session_store import SessionStore


ROOT = Path(__file__).resolve().parents[2]
PHASE6_1_COMPLETE = (
    ROOT / "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room"
)


class _SequenceLiveProvider:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.session_ids: list[str] = []

    def generate_live(self, *, session_id, prompt, schema, state):
        del prompt, schema, state
        index = len(self.session_ids)
        self.session_ids.append(session_id)
        payload = self.payloads[index]
        text = json.dumps(payload, ensure_ascii=False)
        response = {
            "id": f"msg_phase62_{index + 1}",
            "type": "message",
            "role": "assistant",
            "model": "mimo-v2.5-pro",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "mimo-v2.5-pro",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": "<redacted-test-prompt>"}],
            },
            response=response,
            events=(
                {
                    "sequence": 0,
                    "event": "message_start",
                    "data": {"type": "message_start", "message": response},
                },
                {
                    "sequence": 1,
                    "event": "message_stop",
                    "data": {"type": "message_stop"},
                },
            ),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "mimo", "session_id": session_id},
            ),
        )


def test_ready_phase6_2_session_generates_ifc_report_and_db_artifacts(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(
        original_input=(
            "创建一个长6米、宽4米、高3米的房间，南墙中间有一扇900mm宽、"
            "2100mm高的门，北墙中间有一扇1200mm宽、1500mm高、窗台900mm高的窗。"
            "墙体厚度为300mm。"
        )
    )
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")

    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _SequenceLiveProvider([candidate, audit])

    result = run_ready_session_to_ifc(
        store=store,
        session=session.session_hash,
        provider_factory=lambda: provider,
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "compiled"
    assert result.session_hash == session.session_hash
    assert provider.session_ids == [
        f"phase6.2-{session.session_hash}-generator-01",
        f"phase6.2-{session.session_hash}-audit-01",
    ]
    assert (session.run_dir / "candidate.json").is_file()
    assert (session.run_dir / "output.ifc").is_file()
    assert (session.run_dir / "report.md").is_file()
    assert (session.run_dir / "session-export.json").is_file()
    final_acceptance = json.loads((root / "final-acceptance.json").read_text(encoding="utf-8"))
    assert final_acceptance["session_hash"] == session.session_hash
    assert final_acceptance["artifacts"]["ifc"] == f"runs/{session.session_hash}/output.ifc"
    assert final_acceptance["artifacts"]["report"] == f"runs/{session.session_hash}/report.md"
    assert final_acceptance["artifacts"]["session_export"] == (
        f"runs/{session.session_hash}/session-export.json"
    )
    artifact_paths = {artifact["path"] for artifact in export["artifacts"]}
    assert f"runs/{session.session_hash}/candidate.json" in artifact_paths
    assert f"runs/{session.session_hash}/output.ifc" in artifact_paths
    assert f"runs/{session.session_hash}/report.md" in artifact_paths
    assert store.get_session(session.session_hash).status == "compiled"


def test_phase6_2_cli_resumes_ready_session_to_ifc(tmp_path, capsys):
    from scripts.agent import run_phase6_2_cli

    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个完整的测试房间。")
    _write_ready_design_brief_call(session.run_dir)
    store.mark_session_status(session.session_id, "ready")
    store.close()

    candidate = json.loads(
        (PHASE6_1_COMPLETE / "generator" / "candidate.json").read_text(
            encoding="utf-8"
        )
    )
    audit = {
        "schema_version": "text2ifc/audit/2.0",
        "recommendation": "accept",
        "blocking": False,
        "deterministic_gate_status": "passed",
        "findings": [],
        "evidence_paths": [
            "design-brief/design-brief.json",
            "generator/candidate.json",
            "repair/route.json",
        ],
    }
    provider = _SequenceLiveProvider([candidate, audit])

    exit_code = run_phase6_2_cli.main(
        [
            "--live",
            "--stop-after",
            "ifc",
            "--resume",
            session.session_hash,
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        live_provider_factory=lambda: provider,
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["status"] == "compiled"
    assert summary["session_hash"] == session.session_hash
    assert (session.run_dir / "output.ifc").is_file()
    assert (session.run_dir / "report.md").is_file()


def _write_ready_design_brief_call(run_dir: Path) -> None:
    call_dir = run_dir / "calls" / "01-design-brief"
    call_dir.mkdir(parents=True)
    for source in (PHASE6_1_COMPLETE / "design-brief").iterdir():
        if source.is_file():
            (call_dir / source.name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    for name in ("conversation.json", "context-selection.json", "design-brief.json"):
        (call_dir / name).write_text(
            (PHASE6_1_COMPLETE / "design-brief" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (run_dir / "design-brief.json").write_text(
        (call_dir / "design-brief.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
