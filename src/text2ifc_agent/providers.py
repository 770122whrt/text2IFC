"""Provider adapters and guardrails for the clarification Agent."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .state import redact_metadata


MIMO_TOKEN_ENV = "ANTHROPIC_AUTH_TOKEN"
MIMO_BASE_URL_ENV = "ANTHROPIC_BASE_URL"
MIMO_MODEL_ENV = "TEXT2IFC_MIMO_MODEL"
LOW_LEVEL_FORBIDDEN_TERMS = (
    "ISO-10303-21",
    "HEADER;",
    "DATA;",
    "ENDSEC;",
    "IFCCARTESIANPOINT",
    "IFCDIRECTION",
    "IFCOWNERHISTORY",
)


class ProviderOutputError(ValueError):
    """Raised when provider output violates the Agent boundary."""


@dataclass(frozen=True)
class ProviderOutput:
    text: str
    metadata: dict[str, Any]

    def parse_json(self) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
        try:
            payload = json.loads(self.text)
        except json.JSONDecodeError as exc:
            return (
                "parse_error",
                None,
                [
                    {
                        "code": "JSON_DECODE_ERROR",
                        "path": "",
                        "message": f"{exc.msg} at line {exc.lineno} column {exc.colno}",
                    }
                ],
            )
        if not isinstance(payload, dict):
            return (
                "schema_error",
                None,
                [
                    {
                        "code": "INVALID_JSON_ROOT",
                        "path": "",
                        "message": "Provider output must be a JSON object.",
                    }
                ],
            )
        return ("ok", payload, [])


class FakeAgentProvider:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> ProviderOutput:
        del prompt, schema, state
        if session_id not in self.responses:
            raise ProviderOutputError(f"fake provider has no response for {session_id}")
        response = self.responses[session_id]
        return validate_provider_output(
            ProviderOutput(
                text=str(response.get("text", "")),
                metadata=redact_provider_payload(response.get("metadata", {})),
            )
        )


class FileAgentProvider:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses

    @classmethod
    def from_path(cls, path: Path | str) -> "FileAgentProvider":
        root = Path(path)
        responses: dict[str, dict[str, Any]] = {}
        if root.is_file():
            for line in root.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                session_id = record.get("session_id", record.get("record_id"))
                if not session_id:
                    raise ProviderOutputError("file provider record missing session_id")
                responses[str(session_id)] = {
                    "text": str(record.get("text", "")),
                    "metadata": dict(record.get("metadata", {})),
                }
            return cls(responses)
        for item in sorted(root.glob("*.json")):
            responses[item.stem] = {
                "text": item.read_text(encoding="utf-8"),
                "metadata": {"source_path": str(item)},
            }
        for item in sorted(root.glob("*.txt")):
            responses[item.stem] = {
                "text": item.read_text(encoding="utf-8"),
                "metadata": {"source_path": str(item)},
            }
        return cls(responses)

    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> ProviderOutput:
        del prompt, schema, state
        if session_id not in self.responses:
            raise ProviderOutputError(f"file provider has no response for {session_id}")
        response = self.responses[session_id]
        return validate_provider_output(
            ProviderOutput(
                text=str(response.get("text", "")),
                metadata=redact_provider_payload(response.get("metadata", {})),
            )
        )


@dataclass(frozen=True)
class MimoConfig:
    token: str
    base_url: str
    model: str


def load_mimo_config_from_env(
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    required = (MIMO_TOKEN_ENV, MIMO_BASE_URL_ENV, MIMO_MODEL_ENV)
    missing = [name for name in required if not env.get(name)]
    return {
        "provider": "mimo",
        "configured": not missing,
        "missing": missing,
        "required_env": list(required),
        "token_configured": bool(env.get(MIMO_TOKEN_ENV)),
        "base_url_configured": bool(env.get(MIMO_BASE_URL_ENV)),
        "model": env.get(MIMO_MODEL_ENV, "") if env.get(MIMO_MODEL_ENV) else None,
    }


def _mimo_config_or_error(environ: dict[str, str] | None = None) -> MimoConfig:
    env = os.environ if environ is None else environ
    status = load_mimo_config_from_env(dict(env))
    if not status["configured"]:
        raise ProviderOutputError(
            "Mimo config is incomplete; missing "
            + ", ".join(status["missing"])
        )
    return MimoConfig(
        token=env[MIMO_TOKEN_ENV],
        base_url=env[MIMO_BASE_URL_ENV].rstrip("/"),
        model=env[MIMO_MODEL_ENV],
    )


class MimoAgentProvider:
    """Anthropic-compatible provider adapter used only for optional live smoke."""

    def __init__(self, config: MimoConfig | None = None) -> None:
        self.config = config or _mimo_config_or_error()

    def generate_candidate(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> ProviderOutput:
        del schema, state
        body = json.dumps(
            {
                "model": self.config.model,
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": self.config.token,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ProviderOutputError(
                f"Mimo live smoke failed for {session_id}: {type(exc).__name__}"
            ) from exc
        text = _extract_anthropic_text(payload)
        return validate_provider_output(
            ProviderOutput(
                text=text,
                metadata={
                    "provider": "mimo",
                    "session_id": session_id,
                    "model": self.config.model,
                },
            )
        )


def redact_provider_payload(payload: Any) -> Any:
    return redact_metadata(payload)


def validate_provider_output(output: ProviderOutput) -> ProviderOutput:
    upper = output.text.upper()
    for term in LOW_LEVEL_FORBIDDEN_TERMS:
        if term in upper:
            raise ProviderOutputError(
                "Provider output contains raw IFC/STEP or low-level IFC helper content."
            )
    return output


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    chunks = []
    for item in payload.get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            chunks.append(str(item.get("text", "")))
    if chunks:
        return "\n".join(chunks)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
