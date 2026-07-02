import json
import subprocess
import sys
from pathlib import Path

from text2ifc_agent.live_trace import write_live_trace
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
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
