import json
import subprocess
import sys

import pytest

from text2ifc_agent.providers import (
    FakeAgentProvider,
    FileAgentProvider,
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


def test_mimo_config_check_reports_missing_env_names_without_values(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
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
