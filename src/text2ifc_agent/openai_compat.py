"""OpenAI-compatible provider config and evidence helpers for Phase 6.2."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from .providers import (
    LiveProviderResult,
    ProviderOutput,
    ProviderOutputError,
    redact_provider_payload,
    validate_provider_output,
)


PROVIDER_ENV = "TEXT2IFC_PROVIDER"
PROVIDER_MIMO = "mimo"
PROVIDER_DEEPSEEK = "deepseek"
OPENAI_API_KEY_ENV_CHOICES = ("API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY")
DEEPSEEK_API_KEY_ENV_CHOICES = ("DEEPSEEK_API_KEY", "API_KEY", "OPENAI_API_KEY")
OPENAI_BASE_URL_ENV_CHOICES = ("OpenAI_BASE_URL", "OPENAI_BASE_URL")
MIMO_MODEL_ENV = "TEXT2IFC_MIMO_MODEL"
DEEPSEEK_MODEL_ENV = "TEXT2IFC_DEEPSEEK_MODEL"
OPENAI_MAX_COMPLETION_TOKENS_ENV = "TEXT2IFC_MIMO_MAX_COMPLETION_TOKENS"
DEEPSEEK_MAX_TOKENS_ENV = "TEXT2IFC_DEEPSEEK_MAX_TOKENS"
PROVIDER_TIMEOUT_SECONDS_ENV = "TEXT2IFC_PROVIDER_TIMEOUT_SECONDS"
DEFAULT_OPENAI_MAX_COMPLETION_TOKENS = 131072
DEFAULT_DEEPSEEK_MAX_TOKENS = 8192
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 1800.0


@dataclass
class OpenAICompatError(ValueError):
    """Raised when OpenAI-compatible evidence is not semantically usable."""

    message: str
    evidence: dict[str, Any]

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, repr=False)
class OpenAICompatRuntimeConfig:
    provider: str
    provider_label: str
    api_key: str
    api_key_env: str
    base_url: str
    base_url_env: str
    model: str
    model_env: str
    max_completion_tokens: int = DEFAULT_OPENAI_MAX_COMPLETION_TOKENS
    timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS

    def __repr__(self) -> str:
        return (
            "OpenAICompatRuntimeConfig("
            f"provider={self.provider!r}, "
            f"api_key_env={self.api_key_env!r}, "
            f"base_url_env={self.base_url_env!r}, "
            f"model_env={self.model_env!r}, "
            f"model={self.model!r}, "
            f"max_completion_tokens={self.max_completion_tokens!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, "
            "api_key='[REDACTED]', base_url='[REDACTED]')"
        )


def normalize_openai_base_url(raw_url: str, *, provider: str = PROVIDER_MIMO) -> str:
    """Normalize provider-specific OpenAI-compatible base URLs."""

    url = raw_url.rstrip("/")
    if provider == PROVIDER_DEEPSEEK:
        return url
    if url.endswith("/v1"):
        return url
    return f"{url}/v1"


def load_openai_compatible_config(
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a redacted config status for the OpenAI-compatible path."""

    env = {} if environ is None else environ
    provider = _resolve_provider(env)
    provider_label = _provider_label(provider)
    api_key_env = _first_present(env, _api_key_env_choices(provider))
    base_url_env = _first_present(env, OPENAI_BASE_URL_ENV_CHOICES)
    model_env = _model_env(provider, env)
    missing: list[str] = []
    if api_key_env is None:
        missing.append(_api_key_missing_label(provider))
    if base_url_env is None:
        missing.append("OpenAI_BASE_URL or OPENAI_BASE_URL")
    if not model_env:
        missing.append(_model_missing_label(provider))
    return {
        "provider": provider_label,
        "provider_key": provider,
        "configured": not missing,
        "missing": missing,
        "required_env": [
            _api_key_missing_label(provider),
            "OpenAI_BASE_URL or OPENAI_BASE_URL",
            _model_missing_label(provider),
        ],
        "api_key_configured": api_key_env is not None,
        "api_key_env": api_key_env,
        "base_url_configured": base_url_env is not None,
        "base_url_env": base_url_env,
        "model_env": model_env,
        "model": env.get(model_env, "") if model_env else None,
        "max_completion_tokens": _load_max_completion_tokens(env, provider=provider),
        "timeout_seconds": _load_provider_timeout_seconds(env),
    }


def load_openai_compatible_runtime_config(
    environ: dict[str, str] | None = None,
) -> OpenAICompatRuntimeConfig:
    """Load the secret-bearing runtime config without exposing it in repr."""

    env = {} if environ is None else environ
    status = load_openai_compatible_config(env)
    if not status["configured"]:
        raise OpenAICompatError(
            "OpenAI-compatible config is incomplete",
            evidence={
                "provider": status["provider"],
                "parse_eligible": False,
                "failure_class": "missing_config",
                "missing": list(status["missing"]),
            },
        )
    api_key_env = status["api_key_env"]
    base_url_env = status["base_url_env"]
    model_env = status["model_env"]
    assert isinstance(api_key_env, str)
    assert isinstance(base_url_env, str)
    assert isinstance(model_env, str)
    provider = str(status["provider_key"])
    return OpenAICompatRuntimeConfig(
        provider=provider,
        provider_label=str(status["provider"]),
        api_key=env[api_key_env],
        api_key_env=api_key_env,
        base_url=normalize_openai_base_url(env[base_url_env], provider=provider),
        base_url_env=base_url_env,
        model=str(env[model_env]),
        model_env=model_env,
        max_completion_tokens=_load_max_completion_tokens(env, provider=provider),
        timeout_seconds=_load_provider_timeout_seconds(env),
    )


def run_openai_sdk_chat_smoke(
    config: OpenAICompatRuntimeConfig,
    *,
    client_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run one OpenAI SDK Chat Completions smoke and return evidence."""

    client = _create_openai_client(
        config=config,
        client_factory=client_factory,
    )
    request = {
        "model": config.model,
        "messages": [
            {
                "role": "user",
                "content": 'Return exactly this JSON object: {"ok": true}',
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request.update(_token_limit_request(config))
    response = client.chat.completions.create(**request)
    payload = _object_to_dict(response)
    evidence = parse_chat_completion_evidence(
        payload,
        request=request,
        evidence_class="sdk_smoke",
        provider_label=config.provider_label,
    )
    return {
        "status": "passed",
        **evidence,
    }


class OpenAICompatibleLiveProvider:
    """OpenAI-compatible adapter for live Generator/Audit calls."""

    def __init__(
        self,
        *,
        config: OpenAICompatRuntimeConfig,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config
        self.client = _create_openai_client(
            config=config,
            client_factory=client_factory,
        )

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> LiveProviderResult:
        del schema, state
        request = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request.update(_token_limit_request(self.config))
        try:
            response = self.client.chat.completions.create(**request)
        except Exception as exc:
            raise ProviderOutputError(
                f"OpenAI-compatible live request failed for {session_id}: {type(exc).__name__}",
                details={
                    "provider": self.config.provider_label,
                    "failure_class": "provider_connection_error",
                    "exception_type": type(exc).__name__,
                    "session_id": session_id,
                    "request": redact_provider_payload(request),
                },
            ) from exc
        payload = _object_to_dict(response)
        evidence = parse_chat_completion_evidence(
            payload,
            request=request,
            evidence_class="live",
            provider_label=self.config.provider_label,
        )
        output = validate_provider_output(
            ProviderOutput(
                text=str(evidence["content_text"]),
                metadata={
                    "provider": self.config.provider_label,
                    "evidence_class": "live",
                    "session_id": session_id,
                    "response_id": evidence["response_id"],
                    "model": evidence["model"],
                    "stop_reason": evidence["finish_reason"],
                    "usage": evidence["usage"],
                },
            )
        )
        response_envelope = {
            **payload,
            "stop_reason": evidence["finish_reason"],
            "usage": evidence["usage"],
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="live",
            http_status=200,
            request=request,
            response=response_envelope,
            events=(
                {
                    "sequence": 0,
                    "event": "chat.completion",
                    "data": redact_provider_payload(response_envelope),
                },
            ),
            output=output,
        )


class OpenAICompatibleMimoLiveProvider(OpenAICompatibleLiveProvider):
    """Backward-compatible class name for the original Mimo path."""


def run_phase6_2_compatibility_check(
    environ: dict[str, str],
    *,
    openai_sdk_runner: Callable[[OpenAICompatRuntimeConfig], dict[str, Any]] | None = None,
    agents_sdk_runner: Callable[[OpenAICompatRuntimeConfig], dict[str, Any]] | None = None,
    responses_api_probe: Callable[[OpenAICompatRuntimeConfig], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the Wave 0 compatibility probes and combine the report."""

    try:
        config = load_openai_compatible_runtime_config(environ)
    except OpenAICompatError as exc:
        return {
            "phase": "6.2",
            "provider": exc.evidence.get("provider", "openai-compatible"),
            "decision": "blocked",
            "implementation_route": "blocked",
            "blocker": exc.evidence.get("failure_class"),
            "config": load_openai_compatible_config(environ),
        }
    openai_runner = openai_sdk_runner or _safe_openai_sdk_runner
    agents_runner = agents_sdk_runner or _safe_agents_sdk_runner
    responses_probe = responses_api_probe or _safe_responses_api_probe
    return build_compatibility_report(
        openai_sdk=openai_runner(config),
        agents_sdk=agents_runner(config),
        responses_api=responses_probe(config),
    )


def parse_chat_completion_evidence(
    response: dict[str, Any],
    *,
    request: dict[str, Any],
    evidence_class: str,
    provider_label: str = "mimo-openai-compatible",
) -> dict[str, Any]:
    """Extract acceptance evidence from an OpenAI chat-completion response."""

    choice = _first_choice(response)
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    finish_reason = choice.get("finish_reason")
    evidence = {
        "provider": provider_label,
        "evidence_class": evidence_class,
        "response_id": response.get("id"),
        "object": response.get("object"),
        "model": response.get("model"),
        "finish_reason": finish_reason,
        "content_text": str(message.get("content", "")),
        "usage": dict(response.get("usage", {})) if isinstance(response.get("usage"), dict) else {},
        "request": redact_provider_payload(request),
        "parse_eligible": finish_reason != "length",
    }
    if finish_reason == "length":
        evidence["failure_class"] = "truncated"
        raise OpenAICompatError(
            "OpenAI-compatible chat completion is truncated: finish_reason=length",
            evidence=evidence,
        )
    return evidence


def build_compatibility_report(
    *,
    openai_sdk: dict[str, Any],
    agents_sdk: dict[str, Any],
    responses_api: dict[str, Any],
) -> dict[str, Any]:
    """Build the Wave 0 compatibility report skeleton and route decision."""

    decision = _decide_route(openai_sdk=openai_sdk, agents_sdk=agents_sdk)
    implementation_route = {
        "adopt_agents_sdk": "agents_sdk",
        "blocked": "blocked",
    }.get(decision, "native_orchestrator_with_openai_sdk_provider")
    return {
        "phase": "6.2",
        "provider": str(openai_sdk.get("provider", "mimo-openai-compatible")),
        "decision": decision,
        "implementation_route": implementation_route,
        "openai_sdk": redact_provider_payload(openai_sdk),
        "agents_sdk": redact_provider_payload(agents_sdk),
        "responses_api": redact_provider_payload(responses_api),
    }


def _first_present(env: dict[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        if env.get(name):
            return name
    return None


def _resolve_provider(env: dict[str, str]) -> str:
    configured = env.get(PROVIDER_ENV, "").strip().lower()
    if configured in {PROVIDER_MIMO, PROVIDER_DEEPSEEK}:
        return configured
    if env.get(DEEPSEEK_MODEL_ENV):
        return PROVIDER_DEEPSEEK
    return PROVIDER_MIMO


def _provider_label(provider: str) -> str:
    return f"{provider}-openai-compatible"


def _api_key_env_choices(provider: str) -> tuple[str, ...]:
    return (
        DEEPSEEK_API_KEY_ENV_CHOICES
        if provider == PROVIDER_DEEPSEEK
        else OPENAI_API_KEY_ENV_CHOICES
    )


def _api_key_missing_label(provider: str) -> str:
    if provider == PROVIDER_DEEPSEEK:
        return "DEEPSEEK_API_KEY or API_KEY or OPENAI_API_KEY"
    return "API_KEY or MIMO_API_KEY or OPENAI_API_KEY"


def _model_env(provider: str, env: dict[str, str]) -> str | None:
    if provider == PROVIDER_DEEPSEEK:
        return DEEPSEEK_MODEL_ENV if env.get(DEEPSEEK_MODEL_ENV) else None
    return MIMO_MODEL_ENV if env.get(MIMO_MODEL_ENV) else None


def _model_missing_label(provider: str) -> str:
    return DEEPSEEK_MODEL_ENV if provider == PROVIDER_DEEPSEEK else MIMO_MODEL_ENV


def token_limit_request(config: OpenAICompatRuntimeConfig) -> dict[str, int]:
    if config.provider == PROVIDER_DEEPSEEK:
        return {"max_tokens": config.max_completion_tokens}
    return {"max_completion_tokens": config.max_completion_tokens}


def _load_provider_timeout_seconds(env: dict[str, str]) -> float:
    raw = env.get(PROVIDER_TIMEOUT_SECONDS_ENV, "").strip()
    if not raw:
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_PROVIDER_TIMEOUT_SECONDS


def _token_limit_request(config: OpenAICompatRuntimeConfig) -> dict[str, int]:
    return token_limit_request(config)


def _create_openai_client(
    *,
    config: OpenAICompatRuntimeConfig,
    client_factory: Callable[..., Any] | None,
) -> Any:
    if client_factory is None:
        from openai import OpenAI

        return OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
    return client_factory(api_key=config.api_key, base_url=config.base_url)


def _load_max_completion_tokens(env: dict[str, str], *, provider: str) -> int:
    env_name = (
        DEEPSEEK_MAX_TOKENS_ENV
        if provider == PROVIDER_DEEPSEEK
        else OPENAI_MAX_COMPLETION_TOKENS_ENV
    )
    raw_value = env.get(env_name)
    if raw_value is None or raw_value.strip() == "":
        if provider == PROVIDER_DEEPSEEK:
            return DEFAULT_DEEPSEEK_MAX_TOKENS
        return DEFAULT_OPENAI_MAX_COMPLETION_TOKENS
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise OpenAICompatError(
            "OpenAI-compatible max completion token setting must be an integer",
            evidence={
                "provider": _provider_label(provider),
                "parse_eligible": False,
                "failure_class": "invalid_max_completion_tokens",
                "env": env_name,
            },
        ) from exc
    if value <= 0:
        raise OpenAICompatError(
            "OpenAI-compatible max completion token setting must be positive",
            evidence={
                "provider": _provider_label(provider),
                "parse_eligible": False,
                "failure_class": "invalid_max_completion_tokens",
                "env": env_name,
            },
        )
    return value


def _first_choice(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise OpenAICompatError(
            "OpenAI-compatible chat completion has no first choice",
            evidence={
                "provider": "mimo-openai-compatible",
                "response_id": response.get("id"),
                "parse_eligible": False,
                "failure_class": "missing_choice",
            },
        )
    return choices[0]


def _decide_route(
    *,
    openai_sdk: dict[str, Any],
    agents_sdk: dict[str, Any],
) -> str:
    if openai_sdk.get("status") != "passed":
        return "blocked"
    if agents_sdk.get("status") == "passed" and not agents_sdk.get("metadata_gaps"):
        return "adopt_agents_sdk"
    if agents_sdk.get("status") in {"passed", "limited"}:
        return "limited_sdk"
    return "native_orchestrator"


def _safe_openai_sdk_runner(config: OpenAICompatRuntimeConfig) -> dict[str, Any]:
    try:
        return run_openai_sdk_chat_smoke(config)
    except OpenAICompatError as exc:
        return {
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": exc.evidence.get("failure_class", "openai_sdk_unusable"),
            "evidence": exc.evidence,
        }
    except Exception as exc:  # pragma: no cover - live provider safety path
        return {
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": "openai_sdk_exception",
            "error_type": type(exc).__name__,
        }


def _safe_responses_api_probe(config: OpenAICompatRuntimeConfig) -> dict[str, Any]:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        response = client.responses.create(
            model=config.model,
            input='Return exactly this JSON object: {"ok": true}',
            max_output_tokens=128,
        )
        payload = _object_to_dict(response)
        return {
            "status": "passed",
            "evidence_class": "sdk_smoke",
            "response_id": payload.get("id"),
            "object": payload.get("object"),
            "model": payload.get("model"),
        }
    except Exception as exc:  # pragma: no cover - live provider safety path
        http_status = getattr(exc, "status_code", None)
        return {
            "status": "unavailable",
            "evidence_class": "sdk_smoke",
            "http_status": http_status,
            "error_type": type(exc).__name__,
        }


def _safe_agents_sdk_runner(config: OpenAICompatRuntimeConfig) -> dict[str, Any]:
    try:
        from agents import (
            Agent,
            ModelSettings,
            OpenAIChatCompletionsModel,
            Runner,
            set_tracing_disabled,
        )
        from openai import AsyncOpenAI

        set_tracing_disabled(True)
        openai_client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
        model = OpenAIChatCompletionsModel(
            model=config.model,
            openai_client=openai_client,
        )
        agent = Agent(
            name="Phase 6.2 compatibility smoke",
            instructions="Return exactly the requested JSON object and nothing else.",
            model=model,
            model_settings=ModelSettings(
                temperature=0,
                max_tokens=config.max_completion_tokens,
            ),
        )
        result = Runner.run_sync(
            agent,
            'Return exactly this JSON object: {"ok": true}',
        )
        usage = (
            result.raw_responses[-1].usage
            if result.raw_responses
            else None
        )
        metadata_gaps: list[str] = []
        if result.last_response_id is None:
            metadata_gaps.append("response_id_not_first_class")
        metadata_gaps.append("finish_reason_not_first_class")
        return {
            "status": "limited" if metadata_gaps else "passed",
            "evidence_class": "sdk_smoke",
            "response_id": result.last_response_id,
            "final_output": str(result.final_output),
            "metadata_gaps": metadata_gaps,
            "usage": _object_to_dict(usage) if usage is not None else {},
        }
    except Exception as exc:  # pragma: no cover - live provider safety path
        return {
            "status": "blocked",
            "evidence_class": "sdk_smoke",
            "blocker": "agents_sdk_exception",
            "error_type": type(exc).__name__,
        }
    finally:
        if "openai_client" in locals():
            asyncio.run(openai_client.close())


def _object_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}
