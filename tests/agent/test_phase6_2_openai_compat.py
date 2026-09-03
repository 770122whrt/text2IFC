import json
import sys
import types
import text2ifc_agent.openai_compat as openai_compat
from pathlib import Path

import pytest

from text2ifc_agent.openai_compat import (
    OpenAICompatError,
    OpenAICompatibleMimoLiveProvider,
    build_compatibility_report,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
    normalize_openai_base_url,
    parse_chat_completion_evidence,
    run_openai_sdk_chat_smoke,
    run_phase6_2_compatibility_check,
)
from text2ifc_agent.providers import ProviderOutputError


def test_real_openai_clients_disable_hidden_sdk_retries(monkeypatch):
    calls = []

    class OpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=OpenAI))
    config = openai_compat.OpenAICompatRuntimeConfig(
        provider="deepseek",
        provider_label="DeepSeek",
        api_key="secret",
        api_key_env="API_KEY",
        base_url="https://provider.invalid",
        base_url_env="OpenAI_BASE_URL",
        model="model",
        model_env="TEXT2IFC_DEEPSEEK_MODEL",
        timeout_seconds=123,
    )

    openai_compat._create_openai_client(config=config, client_factory=None)
    from text2ifc_agent.interactive_cli_flow import _openai_client

    _openai_client(config=config, client_factory=None)

    assert calls == [
        {
            "api_key": "secret",
            "base_url": "https://provider.invalid",
            "timeout": 123,
            "max_retries": 0,
        },
        {
            "api_key": "secret",
            "base_url": "https://provider.invalid",
            "timeout": 123,
            "max_retries": 0,
        },
    ]


def test_openai_compatible_config_accepts_api_key_without_leaking_values():
    config = load_openai_compatible_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    rendered = json.dumps(config, sort_keys=True)

    assert config["configured"] is True
    assert config["api_key_env"] == "API_KEY"
    assert config["base_url_configured"] is True
    assert config["model"] == "mimo-v2.5-pro"
    assert config["missing"] == []
    assert "secret-api-key" not in rendered
    assert "api.xiaomimimo.com" not in rendered


def test_deepseek_config_accepts_flash_model_without_leaking_values():
    config = load_openai_compatible_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )
    rendered = json.dumps(config, sort_keys=True)

    assert config["configured"] is True
    assert config["provider"] == "deepseek-openai-compatible"
    assert config["api_key_env"] == "API_KEY"
    assert config["base_url_configured"] is True
    assert config["model"] == "deepseek-v4-flash"
    assert config["missing"] == []
    assert "secret-deepseek-key" not in rendered
    assert "api.deepseek.com" not in rendered


def test_openai_compatible_config_reports_missing_names_only():
    config = load_openai_compatible_config({})
    rendered = json.dumps(config, sort_keys=True)

    assert config["configured"] is False
    assert "API_KEY or MIMO_API_KEY or OPENAI_API_KEY" in rendered
    assert "OpenAI_BASE_URL or OPENAI_BASE_URL" in rendered
    assert "TEXT2IFC_MIMO_MODEL" in rendered
    assert "Bearer" not in rendered
    assert "https://" not in rendered


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://api.xiaomimimo.com", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/v1", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/v1/", "https://api.xiaomimimo.com/v1"),
    ],
)
def test_normalize_openai_base_url_targets_v1(raw, expected):
    assert normalize_openai_base_url(raw) == expected


def test_parse_chat_completion_evidence_preserves_required_metadata():
    response = {
        "id": "chatcmpl-live-001",
        "object": "chat.completion",
        "model": "mimo-v2.5-pro",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": '{"ok": true}'},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
    }

    evidence = parse_chat_completion_evidence(
        response,
        request={
            "model": "mimo-v2.5-pro",
            "messages": [{"role": "user", "content": "hello"}],
            "max_completion_tokens": 1024,
        },
        evidence_class="sdk_smoke",
    )

    assert evidence["provider"] == "mimo-openai-compatible"
    assert evidence["evidence_class"] == "sdk_smoke"
    assert evidence["response_id"] == "chatcmpl-live-001"
    assert evidence["model"] == "mimo-v2.5-pro"
    assert evidence["finish_reason"] == "stop"
    assert evidence["parse_eligible"] is True
    assert evidence["content_text"] == '{"ok": true}'
    assert evidence["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 3,
        "total_tokens": 13,
    }
    assert evidence["request"]["max_completion_tokens"] == 1024
    assert "hello" in json.dumps(evidence["request"], sort_keys=True)


def test_parse_chat_completion_blocks_length_finish_reason():
    response = {
        "id": "chatcmpl-length-001",
        "object": "chat.completion",
        "model": "mimo-v2.5-pro",
        "choices": [
            {
                "index": 0,
                "finish_reason": "length",
                "message": {"role": "assistant", "content": '{"ok":'},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
    }

    with pytest.raises(OpenAICompatError, match="finish_reason=length") as captured:
        parse_chat_completion_evidence(
            response,
            request={"model": "mimo-v2.5-pro", "messages": []},
            evidence_class="sdk_smoke",
        )

    assert captured.value.evidence["parse_eligible"] is False
    assert captured.value.evidence["failure_class"] == "truncated"
    assert captured.value.evidence["response_id"] == "chatcmpl-length-001"


def test_compatibility_report_shape_records_decision_and_evidence_classes():
    report = build_compatibility_report(
        openai_sdk={
            "status": "passed",
            "evidence_class": "sdk_smoke",
            "response_id": "chatcmpl-live-001",
        },
        agents_sdk={
            "status": "limited",
            "evidence_class": "sdk_smoke",
            "metadata_gaps": ["finish_reason_not_first_class"],
        },
        responses_api={
            "status": "unavailable",
            "http_status": 404,
            "evidence_class": "sdk_smoke",
        },
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["phase"] == "6.2"
    assert report["decision"] == "limited_sdk"
    assert report["implementation_route"] == "native_orchestrator_with_openai_sdk_provider"
    assert report["openai_sdk"]["evidence_class"] == "sdk_smoke"
    assert report["agents_sdk"]["metadata_gaps"] == ["finish_reason_not_first_class"]
    assert report["responses_api"]["http_status"] == 404
    assert "secret" not in rendered.lower()


def test_compatibility_report_blocks_when_openai_sdk_smoke_fails():
    report = build_compatibility_report(
        openai_sdk={
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": "openai_sdk_exception",
        },
        agents_sdk={"status": "not_checked", "evidence_class": "sdk_smoke"},
        responses_api={"status": "not_checked", "evidence_class": "sdk_smoke"},
    )

    assert report["decision"] == "blocked"
    assert report["implementation_route"] == "blocked"


def test_runtime_config_keeps_secrets_out_of_public_repr():
    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )

    assert config.api_key == "secret-api-key"
    assert config.base_url == "https://api.xiaomimimo.com/v1"
    assert config.model == "mimo-v2.5-pro"
    assert "secret-api-key" not in repr(config)
    assert "api.xiaomimimo.com" not in repr(config)


def test_deepseek_runtime_config_keeps_base_url_without_v1_suffix():
    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )

    assert config.provider == "deepseek"
    assert config.provider_label == "deepseek-openai-compatible"
    assert config.api_key == "secret-deepseek-key"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-v4-flash"
    assert "secret-deepseek-key" not in repr(config)
    assert "api.deepseek.com" not in repr(config)


def test_deepseek_runtime_config_defaults_to_64k_input_and_output_budgets():
    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )

    assert config.max_completion_tokens == 65536
    assert config.max_input_tokens == 65536


def test_deepseek_runtime_config_accepts_explicit_output_budget():
    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
            "TEXT2IFC_DEEPSEEK_MAX_TOKENS": "16384",
        }
    )

    assert config.max_completion_tokens == 16384


def test_deepseek_runtime_config_accepts_explicit_input_budget():
    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
            "TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS": "32768",
        }
    )

    assert config.max_input_tokens == 32768


def test_runtime_config_accepts_explicit_provider_timeout():
    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
            "TEXT2IFC_PROVIDER_TIMEOUT_SECONDS": "1800",
        }
    )

    assert config.timeout_seconds == 1800.0
    assert "1800" in repr(config)


def test_runtime_config_defaults_to_large_design_brief_token_budget():
    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )

    assert config.max_completion_tokens == 131072


def test_runtime_config_accepts_explicit_max_completion_tokens():
    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
            "TEXT2IFC_MIMO_MAX_COMPLETION_TOKENS": "4096",
        }
    )

    assert config.max_completion_tokens == 4096


def test_openai_sdk_chat_smoke_uses_injected_client_and_preserves_evidence():
    captured = {}

    class Response:
        def model_dump(self):
            return {
                "id": "chatcmpl-live-001",
                "object": "chat.completion",
                "model": "mimo-v2.5-pro",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": '{"ok": true}'},
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "total_tokens": 13,
                },
            }

    class ChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return Response()

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    def client_factory(*, api_key, base_url):
        assert api_key == "secret-api-key"
        assert base_url == "https://api.xiaomimimo.com/v1"
        return Client()

    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    evidence = run_openai_sdk_chat_smoke(config, client_factory=client_factory)

    assert captured["model"] == "mimo-v2.5-pro"
    assert captured["max_completion_tokens"] == 131072
    assert captured["response_format"] == {"type": "json_object"}
    assert evidence["status"] == "passed"
    assert evidence["response_id"] == "chatcmpl-live-001"
    assert evidence["finish_reason"] == "stop"
    assert evidence["usage"]["total_tokens"] == 13


def test_openai_compatible_live_provider_returns_live_provider_result():
    captured = {}

    class Response:
        def model_dump(self):
            return {
                "id": "chatcmpl-generator-001",
                "object": "chat.completion",
                "model": "mimo-v2.5-pro",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": '{"schema_version":"bim-json/2.0"}',
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            }

    class ChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return Response()

    class Client:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    provider = OpenAICompatibleMimoLiveProvider(
        config=config,
        client_factory=Client,
    )

    result = provider.generate_live(
        session_id="phase6.2-session-generator-01",
        prompt="Return JSON",
        schema={"schema_version": "bim-json/2.0"},
        state={"stage": "generate"},
    )

    assert result.evidence_class == "live"
    assert result.http_status == 200
    assert result.response["id"] == "chatcmpl-generator-001"
    assert result.response["stop_reason"] == "stop"
    assert result.output.text == '{"schema_version":"bim-json/2.0"}'
    assert result.output.metadata["provider"] == "mimo-openai-compatible"
    assert captured["model"] == "mimo-v2.5-pro"
    assert captured["max_completion_tokens"] == 131072
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["client_kwargs"]["api_key"] == "secret-api-key"


def test_deepseek_live_provider_records_enabled_thinking_request_and_evidence():
    captured = {}

    class Response:
        def model_dump(self):
            return {
                "id": "deepseek-chat-001",
                "object": "chat.completion",
                "model": "deepseek-v4-flash",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": '{"ok":true}',
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            }

    class ChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return Response()

    class Client:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )
    provider_cls = getattr(openai_compat, "OpenAICompatibleLiveProvider")
    provider = provider_cls(
        config=config,
        client_factory=Client,
    )

    result = provider.generate_live(
        session_id="phase6.2-session-generator-01",
        prompt="Return JSON",
        schema={"schema_version": "bim-json/2.0"},
        state={"stage": "generate"},
    )

    assert result.evidence_class == "live"
    assert result.response["id"] == "deepseek-chat-001"
    assert result.output.text == '{"ok":true}'
    assert result.output.metadata["provider"] == "deepseek-openai-compatible"
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["max_tokens"] == 65536
    assert "max_completion_tokens" not in captured
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["extra_body"] == {"thinking": {"type": "enabled"}}
    assert result.request["extra_body"] == {"thinking": {"type": "enabled"}}
    assert result.output.metadata["request_configuration"] == {
        "thinking": {"type": "enabled"},
        "temperature": {"value": 0, "effective": False},
    }
    assert captured["client_kwargs"] == {
        "api_key": "secret-deepseek-key",
        "base_url": "https://api.deepseek.com",
    }


def test_deepseek_live_provider_rejects_prompt_over_input_budget_before_call():
    called = False

    class Client:
        def __init__(self, **kwargs):
            del kwargs
            self.chat = self
            self.completions = self

        def create(self, **kwargs):
            nonlocal called
            called = True
            del kwargs
            raise AssertionError("provider call must not occur")

    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
            "TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS": "1",
        }
    )
    provider = openai_compat.OpenAICompatibleLiveProvider(
        config=config, client_factory=Client
    )

    with pytest.raises(ProviderOutputError, match="input token budget") as captured:
        provider.generate_live(
            session_id="over-budget",
            prompt="12345",
            schema={},
            state={},
        )

    assert called is False
    assert captured.value.details["max_input_tokens"] == 1
    assert captured.value.details["estimated_input_tokens"] == 2


def test_deepseek_live_provider_wraps_connection_failure_without_secrets():
    class ChatCompletions:
        def create(self, **kwargs):
            del kwargs
            raise RuntimeError(
                "peer closed connection; token=secret-deepseek-key; url=https://api.deepseek.com"
            )

    class Client:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )
    provider = openai_compat.OpenAICompatibleLiveProvider(
        config=config,
        client_factory=Client,
    )

    with pytest.raises(ProviderOutputError, match="OpenAI-compatible live request failed") as captured:
        provider.generate_live(
            session_id="phase6.2-session-generator-01",
            prompt="Return JSON",
            schema={"schema_version": "bim-json/2.0"},
            state={"stage": "generate"},
        )

    details = captured.value.details
    rendered = json.dumps(details, sort_keys=True)
    assert details["provider"] == "deepseek-openai-compatible"
    assert details["failure_class"] == "provider_connection_error"
    assert details["exception_type"] == "RuntimeError"
    assert details["request"]["max_tokens"] == 65536
    assert "secret-deepseek-key" not in rendered
    assert "api.deepseek.com" not in rendered


def test_deepseek_live_provider_retries_transient_connection_then_succeeds():
    calls = 0
    delays = []

    class APIConnectionError(Exception):
        pass

    class Response:
        def model_dump(self):
            return {
                "id": "deepseek-retry-001",
                "object": "chat.completion",
                "model": "deepseek-v4-flash",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": '{"ok":true}'},
                    }
                ],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 3,
                    "total_tokens": 8,
                },
            }

    class ChatCompletions:
        def create(self, **kwargs):
            nonlocal calls
            del kwargs
            calls += 1
            if calls == 1:
                raise APIConnectionError("transient secret-bearing detail")
            return Response()

    class Client:
        def __init__(self, **kwargs):
            del kwargs
            self.chat = type("Chat", (), {"completions": ChatCompletions()})()

    config = load_openai_compatible_runtime_config(
        {
            "TEXT2IFC_PROVIDER": "deepseek",
            "API_KEY": "secret-deepseek-key",
            "OpenAI_BASE_URL": "https://api.deepseek.com",
            "TEXT2IFC_DEEPSEEK_MODEL": "deepseek-v4-flash",
        }
    )
    provider = openai_compat.OpenAICompatibleLiveProvider(
        config=config,
        client_factory=Client,
        connection_retry_delay_seconds=0.25,
        sleep=delays.append,
    )

    result = provider.generate_live(
        session_id="phase6.2-retry",
        prompt="Return JSON",
        schema={},
        state={},
    )

    assert calls == 2
    assert delays == [0.25]
    assert result.output.metadata["transport_attempts"] == 2


def test_phase6_2_compatibility_check_combines_live_probe_results():
    report = run_phase6_2_compatibility_check(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        },
        openai_sdk_runner=lambda config: {
            "status": "passed",
            "evidence_class": "sdk_smoke",
            "response_id": "chatcmpl-live-001",
        },
        agents_sdk_runner=lambda config: {
            "status": "limited",
            "evidence_class": "sdk_smoke",
            "metadata_gaps": ["finish_reason_not_first_class"],
        },
        responses_api_probe=lambda config: {
            "status": "unavailable",
            "http_status": 404,
            "evidence_class": "sdk_smoke",
        },
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["decision"] == "limited_sdk"
    assert report["openai_sdk"]["response_id"] == "chatcmpl-live-001"
    assert report["agents_sdk"]["metadata_gaps"] == ["finish_reason_not_first_class"]
    assert report["responses_api"]["status"] == "unavailable"
    assert "secret-api-key" not in rendered
    assert "api.xiaomimimo.com" not in rendered


def test_agents_sdk_smoke_closes_async_openai_client(monkeypatch):
    import sys
    import text2ifc_agent.openai_compat as openai_compat

    clients = []

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.closed = False
            clients.append(self)

        async def close(self):
            self.closed = True

    class FakeModelSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeUsage:
        def model_dump(self):
            return {"total_tokens": 3}

    class FakeRawResponse:
        usage = FakeUsage()

    class FakeResult:
        final_output = '{"ok": true}'
        last_response_id = None
        raw_responses = [FakeRawResponse()]

    class FakeRunner:
        @staticmethod
        def run_sync(agent, prompt):
            assert prompt
            return FakeResult()

    fake_agents = types.SimpleNamespace(
        Agent=FakeAgent,
        ModelSettings=FakeModelSettings,
        OpenAIChatCompletionsModel=FakeModel,
        Runner=FakeRunner,
        set_tracing_disabled=lambda disabled: None,
    )
    fake_openai = types.SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI)
    monkeypatch.setitem(sys.modules, "agents", fake_agents)
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    config = load_openai_compatible_runtime_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )

    evidence = openai_compat._safe_agents_sdk_runner(config)

    assert evidence["status"] == "limited"
    assert clients and clients[0].closed is True


def test_phase6_2_check_openai_compat_cli_writes_report(tmp_path, capsys):
    from scripts.agent import run_phase6_2_cli

    def fake_runner(config):
        assert config["configured"] is True
        return build_compatibility_report(
            openai_sdk={
                "status": "passed",
                "evidence_class": "sdk_smoke",
                "response_id": "chatcmpl-live-001",
            },
            agents_sdk={
                "status": "limited",
                "evidence_class": "sdk_smoke",
                "metadata_gaps": ["finish_reason_not_first_class"],
            },
            responses_api={
                "status": "unavailable",
                "http_status": 404,
                "evidence_class": "sdk_smoke",
            },
        )

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "API_KEY=secret-api-key",
                "OpenAI_BASE_URL=https://api.xiaomimimo.com",
                "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = run_phase6_2_cli.main(
        [
            "--check-openai-compat",
            "--env-file",
            str(env_file),
            "--output-dir",
            str(tmp_path),
        ],
        compatibility_runner=fake_runner,
    )

    stdout = capsys.readouterr().out
    report_path = tmp_path / "compatibility-report.json"
    markdown_path = tmp_path / "report.md"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["decision"] == "limited_sdk"
    assert report["implementation_route"] == "native_orchestrator_with_openai_sdk_provider"
    assert markdown_path.exists()
    assert "limited_sdk" in markdown_path.read_text(encoding="utf-8")
    assert "secret-api-key" not in stdout
    assert "api.xiaomimimo.com" not in stdout
    assert "secret-api-key" not in report_path.read_text(encoding="utf-8")
    assert "secret-api-key" not in markdown_path.read_text(encoding="utf-8")


def test_phase6_2_check_openai_compat_cli_missing_config_is_safe(
    monkeypatch, tmp_path, capsys
):
    from scripts.agent import run_phase6_2_cli

    for name in (
        "API_KEY",
        "DEEPSEEK_API_KEY",
        "MIMO_API_KEY",
        "OPENAI_API_KEY",
        "OpenAI_BASE_URL",
        "OPENAI_BASE_URL",
        "TEXT2IFC_PROVIDER",
        "TEXT2IFC_DEEPSEEK_MODEL",
        "TEXT2IFC_DEEPSEEK_MAX_TOKENS",
        "TEXT2IFC_MIMO_MODEL",
        "TEXT2IFC_MIMO_MAX_COMPLETION_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)

    exit_code = run_phase6_2_cli.main(
        [
            "--check-openai-compat",
            "--env-file",
            str(Path(tmp_path) / "missing.env"),
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    report = json.loads((tmp_path / "compatibility-report.json").read_text(encoding="utf-8"))
    assert exit_code == 2
    assert report["decision"] == "blocked"
    assert report["blocker"] == "missing_openai_compatible_config"
    assert "API_KEY or MIMO_API_KEY or OPENAI_API_KEY" in stdout
    assert "https://" not in stdout


def test_phase6_2_env_file_overrides_stale_process_provider_env(
    monkeypatch, tmp_path, capsys
):
    from scripts.agent import run_phase6_2_cli

    monkeypatch.setenv("TEXT2IFC_PROVIDER", "mimo")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://stale.example.invalid")
    monkeypatch.setenv("TEXT2IFC_MIMO_MODEL", "mimo-v2.5-pro")
    monkeypatch.setenv("API_KEY", "stale-secret")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "TEXT2IFC_PROVIDER=deepseek",
                "OpenAI_BASE_URL=https://api.deepseek.com",
                "API_KEY=secret-deepseek-key",
                "TEXT2IFC_DEEPSEEK_MODEL=deepseek-v4-flash",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = run_phase6_2_cli.main(
        [
            "--check-config",
            "--env-file",
            str(env_file),
        ]
    )

    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert exit_code == 0
    assert payload["provider"] == "deepseek-openai-compatible"
    assert payload["model"] == "deepseek-v4-flash"
    runtime_config = load_openai_compatible_runtime_config(dict(run_phase6_2_cli.os.environ))
    assert runtime_config.base_url == "https://api.deepseek.com"
    assert "secret-deepseek-key" not in stdout
    assert "api.deepseek.com" not in stdout
