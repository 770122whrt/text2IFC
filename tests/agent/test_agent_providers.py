import importlib
import io
import json
import subprocess
import sys
import urllib.error

import pytest

from text2ifc_agent.providers import (
    FakeAgentProvider,
    FileAgentProvider,
    LiveProviderResult,
    MimoAgentProvider,
    MimoConfig,
    ProviderOutput,
    ProviderOutputError,
    load_mimo_config_from_env,
    redact_provider_payload,
    validate_provider_output,
)


def test_fake_provider_returns_deterministic_candidate_by_session_id():
    provider = FakeAgentProvider(
        {
            "session-1": {
                "text": '{"status":"draft"}',
                "metadata": {"provider": "fake"},
            }
        }
    )

    output = provider.generate_candidate(
        session_id="session-1",
        prompt="请生成候选 BIM JSON。",
        schema={},
        state={},
    )

    assert output.text == '{"status":"draft"}'
    assert output.metadata == {"provider": "fake"}


def test_file_provider_replays_jsonl_responses(tmp_path):
    responses = tmp_path / "responses.jsonl"
    responses.write_text(
        json.dumps(
            {
                "session_id": "session-1",
                "text": '{"status":"draft"}',
                "metadata": {"source": "fixture"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    provider = FileAgentProvider.from_path(responses)
    output = provider.generate_candidate(
        session_id="session-1",
        prompt="",
        schema={},
        state={},
    )

    assert output.text == '{"status":"draft"}'
    assert output.metadata == {"source": "fixture"}


def test_provider_output_invalid_json_is_diagnostic_not_payload():
    output = ProviderOutput(text="{", metadata={"provider": "fake"})

    status, payload, diagnostics = output.parse_json()

    assert status == "parse_error"
    assert payload is None
    assert diagnostics[0]["code"] == "JSON_DECODE_ERROR"


@pytest.mark.parametrize(
    "text",
    [
        '```json\n{"ok": true}\n```',
        '```\n{"ok": true}\n```',
    ],
)
def test_provider_output_accepts_one_outer_json_code_fence(text):
    output = ProviderOutput(text=text, metadata={"provider": "mimo"})

    status, payload, diagnostics = output.parse_json()

    assert status == "ok"
    assert payload == {"ok": True}
    assert diagnostics == [
        {
            "code": "OUTER_JSON_FENCE_REMOVED",
            "path": "",
            "message": "Removed one outer Markdown fence before JSON parsing.",
        }
    ]


@pytest.mark.parametrize(
    "text",
    [
        'Here is JSON:\n```json\n{"ok": true}\n```',
        '```json\n{"ok": true}\n```\nextra',
        '{"first": true}\n{"second": true}',
    ],
)
def test_provider_output_does_not_extract_json_from_mixed_content(text):
    status, payload, diagnostics = ProviderOutput(text=text, metadata={}).parse_json()

    assert status == "parse_error"
    assert payload is None
    assert diagnostics[0]["code"] == "JSON_DECODE_ERROR"


def test_mimo_config_check_reports_missing_env_names_without_values(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("TEXT2IFC_MIMO_MODEL", raising=False)

    result = load_mimo_config_from_env()
    rendered = json.dumps(result, sort_keys=True)

    assert result["configured"] is False
    assert "ANTHROPIC_AUTH_TOKEN" in rendered
    assert "ANTHROPIC_BASE_URL" in rendered
    assert "TEXT2IFC_MIMO_MODEL" in rendered
    assert "Bearer" not in rendered
    assert "https://" not in rendered


def test_mimo_config_accepts_official_api_key_env_without_legacy_token():
    result = load_mimo_config_from_env(
        {
            "API_KEY": "secret-token",
            "ANTHROPIC_BASE_URL": "https://api.xiaomimimo.com/anthropic",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    rendered = json.dumps(result, sort_keys=True)

    assert result["configured"] is True
    assert result["token_configured"] is True
    assert result["token_env"] == "API_KEY"
    assert result["missing"] == []
    assert "secret-token" not in rendered
    assert "https://api.xiaomimimo.com" not in rendered


def test_redaction_removes_secret_values_from_provider_payloads():
    payload = {
        "headers": {"authorization": "test-secret-value"},
        "token": "secret-token",
        "base_url": "https://example.invalid/private",
        "env": ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"],
    }

    redacted = redact_provider_payload(payload)
    rendered = json.dumps(redacted, sort_keys=True)

    assert "test-secret-value" not in rendered
    assert "secret-token" not in rendered
    assert "https://example.invalid/private" not in rendered
    assert "ANTHROPIC_AUTH_TOKEN" in rendered
    assert redacted["headers"]["authorization"] == "[REDACTED]"


@pytest.mark.parametrize(
    "text",
    [
        "ISO-10303-21; #1=IFCCARTESIANPOINT((0.,0.,0.)); ENDSEC;",
        '{"entity":"IfcOwnerHistory"}',
    ],
)
def test_raw_ifc_step_or_low_level_helper_output_is_rejected(text):
    with pytest.raises(ProviderOutputError):
        validate_provider_output(ProviderOutput(text=text, metadata={}))


def test_mimo_check_config_cli_is_redacted_and_non_networked(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("TEXT2IFC_MIMO_MODEL", raising=False)
    missing_env_file = tmp_path / "missing.env"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/agent/run_mimo_smoke.py",
            "--check-config",
            "--env-file",
            str(missing_env_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"configured": false' in result.stdout
    assert "ANTHROPIC_AUTH_TOKEN" in result.stdout
    assert "Bearer" not in result.stdout


def test_mimo_provider_uses_configured_generation_limits(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"content":[{"type":"text","text":"{\\"ok\\": true}"}]}'

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        fake_urlopen,
    )

    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://example.invalid/anthropic",
            model="mimo-v2.5-pro",
            max_tokens=2048,
            timeout_seconds=45,
        )
    )

    output = provider.generate_candidate(
        session_id="mimo-budget",
        prompt='Return {"ok": true}',
        schema={},
        state={},
    )

    assert captured["body"]["max_tokens"] == 2048
    assert captured["timeout"] == 45
    assert captured["url"] == "https://example.invalid/anthropic/v1/messages"
    assert captured["headers"]["Api-key"] == "secret-token"
    assert "X-api-key" not in captured["headers"]
    assert output.text == '{"ok": true}'


def test_mimo_provider_does_not_duplicate_full_messages_endpoint(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"content":[{"type":"text","text":"{\\"ok\\": true}"}]}'

    def fake_urlopen(request, timeout):
        del timeout
        captured["url"] = request.full_url
        return Response()

    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        fake_urlopen,
    )

    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://api.xiaomimimo.com/anthropic/v1/messages",
            model="mimo-v2.5-pro",
        )
    )

    provider.generate_candidate(
        session_id="mimo-endpoint",
        prompt='Return {"ok": true}',
        schema={},
        state={},
    )

    assert captured["url"] == "https://api.xiaomimimo.com/anthropic/v1/messages"


def test_mimo_default_config_uses_documented_live_limits():
    config = MimoConfig(
        token="secret-token",
        base_url="https://example.invalid/anthropic",
        model="mimo-v2.5-pro",
    )

    assert config.max_tokens == 131072
    assert config.timeout_seconds == 900


def _streaming_response(stop_reason="end_turn"):
    payloads = [
        {
            "type": "message_start",
            "message": {
                "id": "msg-live-001",
                "type": "message",
                "role": "assistant",
                "model": "mimo-v2.5-pro",
                "content": [],
                "stop_reason": None,
                "usage": {"input_tokens": 11, "cache_read_input_tokens": 3},
            },
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": '{"ok":'},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": " true}"},
        },
        {"type": "content_block_stop", "index": 0},
        {
            "type": "content_block_start",
            "index": 1,
            "content_block": {"type": "thinking", "thinking": ""},
        },
        {
            "type": "content_block_delta",
            "index": 1,
            "delta": {"type": "thinking_delta", "thinking": "checked"},
        },
        {"type": "content_block_stop", "index": 1},
        {
            "type": "message_delta",
            "delta": {"stop_reason": stop_reason, "stop_sequence": None},
            "usage": {"output_tokens": 7},
        },
        {"type": "message_stop"},
    ]

    class StreamingResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def __iter__(self):
            for payload in payloads:
                yield f"event: {payload['type']}\n".encode("utf-8")
                yield (
                    "data: " + json.dumps(payload, ensure_ascii=False) + "\n"
                ).encode("utf-8")
                yield b"\n"

    return StreamingResponse()


def test_mimo_replay_stream_preserves_exact_response_envelope(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _streaming_response()

    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        fake_urlopen,
    )
    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://example.invalid/anthropic",
            model="mimo-v2.5-pro",
        )
    )

    result = provider.generate_live(
        session_id="mimo-live-envelope",
        prompt='Return exactly {"ok": true}',
        schema={},
        state={},
    )

    assert captured["body"]["stream"] is True
    assert captured["body"]["max_tokens"] == 131072
    assert captured["timeout"] == 900
    assert result.evidence_class == "live"
    assert result.http_status == 200
    assert [event["event"] for event in result.events] == [
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_delta",
        "content_block_stop",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
    ]
    assert result.response == {
        "id": "msg-live-001",
        "type": "message",
        "role": "assistant",
        "model": "mimo-v2.5-pro",
        "content": [
            {"type": "text", "text": '{"ok": true}'},
            {"type": "thinking", "thinking": "checked"},
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 11,
            "cache_read_input_tokens": 3,
            "output_tokens": 7,
        },
    }
    assert result.output.text == '{"ok": true}'
    assert result.output.metadata["response_id"] == "msg-live-001"
    assert "secret-token" not in json.dumps(result.request, sort_keys=True)
    assert "example.invalid" not in json.dumps(result.request, sort_keys=True)


def test_mimo_replay_stream_rejects_non_end_turn_before_json_parse(monkeypatch):
    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        lambda request, timeout: _streaming_response("max_tokens"),
    )
    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://example.invalid/anthropic",
            model="mimo-v2.5-pro",
        )
    )

    with pytest.raises(ProviderOutputError, match="stop_reason=max_tokens"):
        provider.generate_live(
            session_id="mimo-truncated",
            prompt='Return exactly {"ok": true}',
            schema={},
            state={},
        )


def test_mimo_http_error_preserves_safe_provider_diagnostics(monkeypatch):
    def reject(request, timeout):
        raise urllib.error.HTTPError(
            url="https://example.invalid/private/v1/messages",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(
                json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "type": "invalid_request_error",
                            "message": "max_tokens exceeds provider limit",
                        },
                    }
                ).encode("utf-8")
            ),
        )

    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        reject,
    )
    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://example.invalid/private",
            model="mimo-v2.5-pro",
        )
    )

    with pytest.raises(ProviderOutputError, match="HTTP 400") as captured:
        provider.generate_live(
            session_id="mimo-rejected",
            prompt='Return exactly {"ok": true}',
            schema={},
            state={},
        )

    assert captured.value.details == {
        "http_status": 400,
        "error_type": "invalid_request_error",
        "message": "max_tokens exceeds provider limit",
    }
    rendered = json.dumps(captured.value.details, sort_keys=True)
    assert "secret-token" not in rendered
    assert "example.invalid" not in rendered


def test_live_trace_replay_writes_reviewable_secret_safe_bundle(monkeypatch, tmp_path):
    try:
        trace_module = importlib.import_module("text2ifc_agent.live_trace")
    except ModuleNotFoundError:
        pytest.fail("live trace module is not implemented")
    monkeypatch.setattr(
        "text2ifc_agent.providers.urllib.request.urlopen",
        lambda request, timeout: _streaming_response(),
    )
    provider = MimoAgentProvider(
        config=MimoConfig(
            token="secret-token",
            base_url="https://example.invalid/anthropic",
            model="mimo-v2.5-pro",
        )
    )
    result = provider.generate_live(
        session_id="mimo-trace",
        prompt='Return exactly {"ok": true}',
        schema={},
        state={},
    )

    manifest = trace_module.write_live_trace(result=result, output_dir=tmp_path)

    assert manifest["evidence_class"] == "live"
    expected = {
        "events.jsonl",
        "model-text.txt",
        "request.redacted.json",
        "response-metadata.json",
        "response.raw.json",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    request = json.loads(
        (tmp_path / "request.redacted.json").read_text(encoding="utf-8")
    )
    assert request["request"]["max_tokens"] == 131072
    response = json.loads((tmp_path / "response.raw.json").read_text(encoding="utf-8"))
    assert response["id"] == "msg-live-001"
    events = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[0]["event"] == "message_start"
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in tmp_path.iterdir()
        if path.suffix in {".json", ".jsonl", ".txt"}
    )
    assert "secret-token" not in all_text
    assert "example.invalid" not in all_text


def test_mimo_live_cli_writes_trace_bundle_without_secret_output(
    monkeypatch, tmp_path, capsys
):
    smoke = importlib.import_module("scripts.agent.run_mimo_smoke")
    for name in (
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "TEXT2IFC_MIMO_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ANTHROPIC_AUTH_TOKEN=secret-token\n"
        "ANTHROPIC_BASE_URL=https://example.invalid/private\n"
        "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro\n",
        encoding="utf-8",
    )
    output = ProviderOutput(
        text='{"ok": true}',
        metadata={
            "provider": "mimo",
            "evidence_class": "live",
            "response_id": "msg-cli-001",
        },
    )
    live_result = LiveProviderResult(
        session_id="mimo-smoke",
        evidence_class="live",
        http_status=200,
        request={
            "model": "mimo-v2.5-pro",
            "max_tokens": 131072,
            "stream": True,
            "messages": [{"role": "user", "content": "test"}],
        },
        response={
            "id": "msg-cli-001",
            "type": "message",
            "role": "assistant",
            "model": "mimo-v2.5-pro",
            "content": [{"type": "text", "text": '{"ok": true}'}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
        events=(
            {
                "sequence": 0,
                "event": "message_start",
                "data": {"type": "message_start", "message": {"id": "msg-cli-001"}},
            },
        ),
        output=output,
    )

    class Provider:
        def generate_live(self, **kwargs):
            assert kwargs["session_id"] == "mimo-smoke"
            return live_result

    trace_dir = tmp_path / "trace"
    exit_code = smoke.main(
        [
            "--live",
            "--env-file",
            str(env_file),
            "--trace-dir",
            str(trace_dir),
        ],
        provider_factory=Provider,
    )

    stdout = capsys.readouterr().out
    summary = json.loads(stdout)
    assert exit_code == 0
    assert summary["provider"] == "mimo"
    assert summary["evidence_class"] == "live"
    assert summary["response_id"] == "msg-cli-001"
    assert summary["stop_reason"] == "end_turn"
    assert summary["usage"] == {"input_tokens": 1, "output_tokens": 1}
    assert (trace_dir / "response.raw.json").exists()
    assert "secret-token" not in stdout
    assert "example.invalid" not in stdout
