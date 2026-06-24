"""OpenAI-compatible Mimo config and evidence helpers for Phase 6.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .providers import redact_provider_payload


OPENAI_API_KEY_ENV_CHOICES = ("API_KEY", "MIMO_API_KEY", "OPENAI_API_KEY")
OPENAI_BASE_URL_ENV_CHOICES = ("OpenAI_BASE_URL", "OPENAI_BASE_URL")
OPENAI_MODEL_ENV = "TEXT2IFC_MIMO_MODEL"


@dataclass
class OpenAICompatError(ValueError):
    """Raised when OpenAI-compatible evidence is not semantically usable."""

    message: str
    evidence: dict[str, Any]

    def __str__(self) -> str:
        return self.message


def normalize_openai_base_url(raw_url: str) -> str:
    """Normalize an OpenAI-compatible base URL to the `/v1` root."""

    url = raw_url.rstrip("/")
    if url.endswith("/v1"):
        return url
    return f"{url}/v1"


def load_openai_compatible_config(
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a redacted config status for the Mimo OpenAI-compatible path."""

    env = {} if environ is None else environ
    api_key_env = _first_present(env, OPENAI_API_KEY_ENV_CHOICES)
    base_url_env = _first_present(env, OPENAI_BASE_URL_ENV_CHOICES)
    missing: list[str] = []
    if api_key_env is None:
        missing.append("API_KEY or MIMO_API_KEY or OPENAI_API_KEY")
    if base_url_env is None:
        missing.append("OpenAI_BASE_URL or OPENAI_BASE_URL")
    if not env.get(OPENAI_MODEL_ENV):
        missing.append(OPENAI_MODEL_ENV)
    return {
        "provider": "mimo-openai-compatible",
        "configured": not missing,
        "missing": missing,
        "required_env": [
            "API_KEY or MIMO_API_KEY or OPENAI_API_KEY",
            "OpenAI_BASE_URL or OPENAI_BASE_URL",
            OPENAI_MODEL_ENV,
        ],
        "api_key_configured": api_key_env is not None,
        "api_key_env": api_key_env,
        "base_url_configured": base_url_env is not None,
        "base_url_env": base_url_env,
        "model": env.get(OPENAI_MODEL_ENV) or None,
    }


def parse_chat_completion_evidence(
    response: dict[str, Any],
    *,
    request: dict[str, Any],
    evidence_class: str,
) -> dict[str, Any]:
    """Extract acceptance evidence from an OpenAI chat-completion response."""

    choice = _first_choice(response)
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    finish_reason = choice.get("finish_reason")
    evidence = {
        "provider": "mimo-openai-compatible",
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
    implementation_route = (
        "agents_sdk"
        if decision == "adopt_agents_sdk"
        else "native_orchestrator_with_openai_sdk_provider"
    )
    return {
        "phase": "6.2",
        "provider": "mimo-openai-compatible",
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
        return "native_orchestrator"
    if agents_sdk.get("status") == "passed" and not agents_sdk.get("metadata_gaps"):
        return "adopt_agents_sdk"
    if agents_sdk.get("status") in {"passed", "limited"}:
        return "limited_sdk"
    return "native_orchestrator"
