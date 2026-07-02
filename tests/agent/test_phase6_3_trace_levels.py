import json
import subprocess
import sys
from pathlib import Path

from text2ifc_agent.live_trace import write_live_trace
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.interactive_cli_flow import SessionIfcResult
from text2ifc_agent.repl_chat import ReplChatResult
from text2ifc_agent.run_report import build_live_run_report
from text2ifc_agent.session_store import SessionStore
from text2ifc_agent.trace_levels import (
    DEFAULT_TRACE_LEVEL,
    TraceLevelError,
    normalize_trace_level,
    should_preserve_deep_evidence,
)


ROOT = Path(__file__).resolve().parents[2]


def test_trace_level_contract_defaults_to_compact():
    assert DEFAULT_TRACE_LEVEL == "compact"
    assert normalize_trace_level(None) == "compact"
    assert normalize_trace_level("debug") == "debug"
    assert normalize_trace_level("full") == "full"

    try:
        normalize_trace_level("verbose")
    except TraceLevelError as exc:
        assert "compact|debug|full" in str(exc)
    else:
        raise AssertionError("invalid trace level should fail")


def test_text2ifc_chat_cli_exposes_trace_level_contract():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_text2ifc_chat.py"),
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert "--trace-level" in result.stdout
    assert "compact" in result.stdout
    assert "debug" in result.stdout
    assert "full" in result.stdout


def test_text2ifc_chat_passes_trace_level_to_repl(monkeypatch, tmp_path):
    from scripts.agent import run_text2ifc_chat

    captured: dict[str, str | None] = {}

    def fake_run_repl_chat(**kwargs):
        captured["trace_level"] = kwargs.get("trace_level")
        return ReplChatResult(
            session_id="session-1",
            session_hash="hash-1",
            status="ready",
        )

    monkeypatch.setattr(run_text2ifc_chat, "run_repl_chat", fake_run_repl_chat)

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--trace-level",
            "full",
            "--output-root",
            str(tmp_path / "out"),
            "--db",
            str(tmp_path / "out" / "sessions.sqlite"),
        ]
    )

    assert exit_code == 0
    assert captured["trace_level"] == "full"


def test_repl_passes_trace_level_to_ifc_generation(monkeypatch, tmp_path):
    import text2ifc_agent.repl_chat as repl_chat

    store = SessionStore.open(tmp_path / "sessions.sqlite", artifact_root=tmp_path)
    captured: dict[str, str | None] = {}

    def invoke_design_brief(transcript, call_index):
        return _ready_call(call_index, transcript[0]["content"])

    def fake_run_ready_session_to_ifc(**kwargs):
        captured["trace_level"] = kwargs.get("trace_level")
        session = kwargs["store"].get_session(kwargs["session"])
        return SessionIfcResult(
            session_id=session.session_id,
            session_hash=session.session_hash,
            status="compiled",
            generator_status="formal",
            repair_route="no_repair_needed",
            audit_status="accepted",
            ifc_path=None,
            report_path=None,
        )

    monkeypatch.setattr(
        repl_chat,
        "run_ready_session_to_ifc",
        fake_run_ready_session_to_ifc,
    )

    try:
        result = repl_chat.run_repl_chat(
            store=store,
            invoke_design_brief=invoke_design_brief,
            input_func=lambda prompt: "创建一个简单房间",
            stop_after="ifc",
            provider_factory=lambda: object(),
            trace_level="full",
        )
    finally:
        store.close()

    assert result.status == "compiled"
    assert captured["trace_level"] == "full"


def test_compact_live_trace_writes_fewer_provider_artifacts_than_debug(tmp_path):
    result = _live_result()
    debug_dir = tmp_path / "debug"
    compact_dir = tmp_path / "compact"

    debug_manifest = write_live_trace(
        result=result,
        output_dir=debug_dir,
        trace_level="debug",
    )
    compact_manifest = write_live_trace(
        result=result,
        output_dir=compact_dir,
        trace_level="compact",
    )

    debug_files = {path.name for path in debug_dir.iterdir() if path.is_file()}
    compact_files = {path.name for path in compact_dir.iterdir() if path.is_file()}

    assert debug_manifest["trace_level"] == "debug"
    assert compact_manifest["trace_level"] == "compact"
    assert len(compact_files) < len(debug_files)
    assert "request.redacted.json" in debug_files
    assert "response.raw.json" in debug_files
    assert "model-text.txt" in debug_files
    assert "request.redacted.json" not in compact_files
    assert "response.raw.json" not in compact_files
    assert "model-text.txt" not in compact_files
    assert compact_manifest["deferred_artifacts"]["response_sha256"].startswith("sha256:")
    assert compact_manifest["deferred_artifacts"]["model_text_sha256"].startswith("sha256:")


def test_compact_live_trace_can_preserve_deep_evidence_under_trace_directory(tmp_path):
    result = _live_result()

    manifest = write_live_trace(
        result=result,
        output_dir=tmp_path,
        trace_level="compact",
        preserve_deep_evidence=True,
    )

    top_level_files = {path.name for path in tmp_path.iterdir() if path.is_file()}
    trace_files = {
        path.name
        for path in (tmp_path / "trace").iterdir()
        if path.is_file()
    }

    assert "response-metadata.json" in top_level_files
    assert "response.raw.json" not in top_level_files
    assert "request.redacted.json" not in top_level_files
    assert "response.raw.json" in trace_files
    assert "request.redacted.json" in trace_files
    assert "model-text.txt" in trace_files
    assert manifest["deep_evidence"]["response"] == "trace/response.raw.json"
    assert manifest["deferred_artifacts"]["response_sha256"].startswith("sha256:")


def test_run_report_writes_trace_manifest_with_compact_evidence_hashes(tmp_path):
    case_dir = _write_compact_report_case(tmp_path / "case")

    report_path = build_live_run_report(case_dir=case_dir)

    manifest_path = case_dir / "trace-manifest.json"
    assert report_path == case_dir / "report.md"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest["artifact_hashes"]
    assert manifest["schema_version"] == "text2ifc/run-trace-manifest/1.0"
    assert artifacts["report.md"].startswith("sha256:")
    assert artifacts["generator/candidate.json"].startswith("sha256:")
    assert artifacts["expected-facts.json"].startswith("sha256:")
    assert artifacts["gate-summary.json"].startswith("sha256:")
    assert artifacts["route-decision.json"].startswith("sha256:")
    assert artifacts["generator/trace/response.raw.json"].startswith("sha256:")
    assert "generator/response.raw.json" not in artifacts


def test_non_accept_routes_force_deep_evidence_preservation():
    assert should_preserve_deep_evidence(route="accept", validation_valid=True) is False
    assert (
        should_preserve_deep_evidence(
            route="generator_regeneration_required",
            validation_valid=True,
        )
        is True
    )
    assert should_preserve_deep_evidence(route="accept", validation_valid=False) is True
    assert should_preserve_deep_evidence(route="blocked_gate_dispute", validation_valid=True) is True


def _live_result() -> LiveProviderResult:
    response = {
        "id": "msg_trace_level",
        "type": "message",
        "role": "assistant",
        "model": "unit-test",
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": "{\"ok\": true}"}],
        "usage": {"input_tokens": 1, "output_tokens": 2},
    }
    return LiveProviderResult(
        session_id="trace-level-test",
        evidence_class="unit_test_fixture",
        http_status=200,
        request={
            "model": "unit-test",
            "messages": [{"role": "user", "content": "<prompt>"}],
        },
        response=response,
        events=(
            {"sequence": 0, "event": "message_start", "data": response},
            {"sequence": 1, "event": "message_stop", "data": {}},
        ),
        output=ProviderOutput(
            text=json.dumps({"ok": True}),
            metadata={"provider": "unit-test"},
        ),
    )


def _ready_call(call_index: int, original_request: str) -> ClarificationCall:
    return ClarificationCall(
        call_index=call_index,
        response_id=f"msg_trace_ready_{call_index}",
        prompt_template_id="design-brief.v2.1",
        prompt_template_hash="sha256:test",
        artifact_dir=f"calls/{call_index:02d}-design-brief",
        brief={
            "schema_version": "text2ifc/design-brief/2.0",
            "language": "zh-CN",
            "original_request": original_request,
            "status": "ready",
            "known_facts": {},
            "fact_sources": [],
            "missing_facts": [],
            "ambiguities": [],
            "unsupported_requests": [],
            "user_corrections": [],
            "clarification_questions": [],
            "provenance": {
                "source_turns": ["turn-user-001"],
                "selected_evidence_ids": [],
                "few_shot_ids": [],
            },
        },
        evidence_catalog=[],
    )


def _write_compact_report_case(case_dir: Path) -> Path:
    design = case_dir / "design-brief"
    generator = case_dir / "generator"
    repair = case_dir / "repair"
    audit = case_dir / "audit"
    _write_text(design / "input.txt", "创建一个简单房间\n")
    _write_json(design / "conversation.json", [{"role": "user", "content": "创建一个简单房间"}])
    _write_text(design / "prompt-rendered.md", "Design Brief prompt")
    _write_json(design / "trace" / "response.raw.json", {"id": "msg_design", "stop_reason": "end_turn"})
    _write_text(design / "trace" / "model-text.txt", '{"status":"ready"}')
    _write_json(design / "trace" / "request.redacted.json", {"request": {"model": "unit-test"}})
    _write_json(design / "design-brief.json", {"status": "ready"})
    _write_json(design / "validation.json", {"valid": True, "issues": []})
    _write_json(design / "metrics.json", {"response_id": "msg_design", "evidence_class": "unit"})

    _write_text(generator / "prompt-rendered.md", "Generator prompt")
    _write_json(generator / "trace" / "response.raw.json", {"id": "msg_generator", "stop_reason": "end_turn"})
    _write_text(generator / "trace" / "model-text.txt", '{"schema_version":"bim-json/2.0"}')
    _write_json(generator / "trace" / "request.redacted.json", {"request": {"model": "unit-test"}})
    _write_json(generator / "candidate.json", {"schema_version": "bim-json/2.0"})
    _write_json(generator / "validation.json", {"valid": True, "issues": []})
    _write_json(generator / "metrics.json", {"response_id": "msg_generator", "evidence_class": "unit"})

    _write_json(repair / "route.json", {"route": "no_repair_needed", "provider_call_count": 0})
    _write_json(repair / "repair-attempts.json", [])
    _write_json(repair / "metrics.json", {"route": "no_repair_needed", "evidence_class": "unit"})

    _write_text(audit / "prompt-rendered.md", "Audit prompt")
    _write_json(audit / "trace" / "response.raw.json", {"id": "msg_audit", "stop_reason": "end_turn"})
    _write_text(audit / "trace" / "model-text.txt", '{"recommendation":"accept"}')
    _write_json(audit / "trace" / "request.redacted.json", {"request": {"model": "unit-test"}})
    _write_json(audit / "audit-report.json", {"recommendation": "accept", "blocking": False})
    _write_json(audit / "validation.json", {"valid": True, "issues": []})
    _write_json(audit / "metrics.json", {"response_id": "msg_audit", "evidence_class": "unit"})

    _write_json(case_dir / "expected-facts.json", {"schema_version": "text2ifc/expected-facts/1.0"})
    _write_json(
        case_dir / "gate-summary.json",
        {
            "schema_version": "text2ifc/gate-summary/1.0",
            "candidate_hash": "sha256:test",
            "expected_facts_hash": "sha256:test",
            "gates": [],
            "overall_status": "passed",
        },
    )
    _write_json(
        case_dir / "route-decision.json",
        {
            "schema_version": "text2ifc/route-decision/1.0",
            "route": "accept",
        },
    )
    return case_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
