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

    def __init__(self, message: str, *, live_result: "LiveProviderResult | None" = None) -> None:
        super().__init__(message)
        self.live_result = live_result


@dataclass(frozen=True)
class ProviderOutput:
    text: str
    metadata: dict[str, Any]

    def parse_json(self) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
        text, normalization_diagnostics = _normalize_json_text(self.text)
        try:
            payload = json.loads(text)
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
        return ("ok", payload, normalization_diagnostics)


def _normalize_json_text(text: str) -> tuple[str, list[dict[str, str]]]:
    stripped = text.strip()
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].strip().lower() in {"```", "```json"}:
        if lines[-1].strip() == "```":
            return (
                "\n".join(lines[1:-1]).strip(),
                [
                    {
                        "code": "OUTER_JSON_FENCE_REMOVED",
                        "path": "",
                        "message": "Removed one outer Markdown fence before JSON parsing.",
                    }
                ],
            )
    return text, []


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
    max_tokens: int = 131072
    timeout_seconds: int = 900


@dataclass(frozen=True)
class LiveProviderResult:
    session_id: str
    evidence_class: str
    http_status: int
    request: dict[str, Any]
    response: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    output: ProviderOutput


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
    """Anthropic-compatible provider adapter with an auditable streaming path."""

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
                "max_tokens": self.config.max_tokens,
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
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
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

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> LiveProviderResult:
        del schema, state
        request_payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }
        body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
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
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                events = tuple(_read_anthropic_sse(response))
                http_status = int(getattr(response, "status", 200))
        except (OSError, urllib.error.URLError, UnicodeDecodeError) as exc:
            raise ProviderOutputError(
                f"Mimo live request failed for {session_id}: {type(exc).__name__}"
            ) from exc

        response_envelope = _reconstruct_anthropic_message(events)
        output = validate_provider_output(
            ProviderOutput(
                text=_extract_anthropic_text(response_envelope),
                metadata={
                    "provider": "mimo",
                    "evidence_class": "live",
                    "session_id": session_id,
                    "response_id": response_envelope.get("id"),
                    "model": response_envelope.get("model"),
                    "stop_reason": response_envelope.get("stop_reason"),
                    "usage": dict(response_envelope.get("usage", {})),
                },
            )
        )
        result = LiveProviderResult(
            session_id=session_id,
            evidence_class="live",
            http_status=http_status,
            request=request_payload,
            response=response_envelope,
            events=events,
            output=output,
        )
        stop_reason = response_envelope.get("stop_reason")
        if stop_reason != "end_turn":
            raise ProviderOutputError(
                f"Mimo live response is not complete: stop_reason={stop_reason}",
                live_result=result,
            )
        return result


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


def _read_anthropic_sse(response: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_name: str | None = None
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event_name, data_lines
        if not data_lines:
            event_name = None
            return
        data_text = "\n".join(data_lines)
        data_lines = []
        if data_text == "[DONE]":
            event_name = None
            return
        try:
            payload = json.loads(data_text)
        except json.JSONDecodeError as exc:
            raise ProviderOutputError(
                f"Mimo SSE event is not valid JSON at event {len(events)}"
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderOutputError(
                f"Mimo SSE event must be an object at event {len(events)}"
            )
        resolved_name = event_name or str(payload.get("type", "message"))
        events.append(
            {
                "sequence": len(events),
                "event": resolved_name,
                "data": payload,
            }
        )
        event_name = None

    for raw_line in response:
        line = raw_line.decode("utf-8").rstrip("\r\n")
        if not line:
            flush()
        elif line.startswith(":"):
            continue
        elif line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].lstrip())
    flush()
    if not events:
        raise ProviderOutputError("Mimo live response contained no SSE events")
    return events


def _reconstruct_anthropic_message(
    events: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> dict[str, Any]:
    message: dict[str, Any] | None = None
    blocks: dict[int, dict[str, Any]] = {}

    for event in events:
        payload = event.get("data", {})
        event_type = payload.get("type", event.get("event"))
        if event_type == "message_start":
            initial = payload.get("message")
            if not isinstance(initial, dict):
                raise ProviderOutputError("Mimo message_start is missing message object")
            message = json.loads(json.dumps(initial, ensure_ascii=False))
            message["content"] = []
            message["usage"] = dict(initial.get("usage", {}))
        elif event_type == "content_block_start":
            index = payload.get("index")
            block = payload.get("content_block")
            if not isinstance(index, int) or not isinstance(block, dict):
                raise ProviderOutputError("Mimo content_block_start is malformed")
            blocks[index] = json.loads(json.dumps(block, ensure_ascii=False))
        elif event_type == "content_block_delta":
            index = payload.get("index")
            delta = payload.get("delta")
            if not isinstance(index, int) or not isinstance(delta, dict) or index not in blocks:
                raise ProviderOutputError("Mimo content_block_delta is malformed")
            _apply_content_delta(blocks[index], delta)
        elif event_type == "message_delta":
            if message is None:
                raise ProviderOutputError("Mimo message_delta arrived before message_start")
            delta = payload.get("delta", {})
            if isinstance(delta, dict):
                for key, value in delta.items():
                    message[key] = value
            usage = payload.get("usage", {})
            if isinstance(usage, dict):
                message.setdefault("usage", {}).update(usage)

    if message is None:
        raise ProviderOutputError("Mimo SSE stream is missing message_start")
    message["content"] = [blocks[index] for index in sorted(blocks)]
    if not message.get("id") or not message.get("model"):
        raise ProviderOutputError("Mimo response envelope is missing id or model")
    return message


def _apply_content_delta(block: dict[str, Any], delta: dict[str, Any]) -> None:
    delta_type = delta.get("type")
    field_by_type = {
        "text_delta": "text",
        "thinking_delta": "thinking",
        "signature_delta": "signature",
        "input_json_delta": "partial_json",
    }
    field = field_by_type.get(str(delta_type))
    if field is None:
        raise ProviderOutputError(f"Unsupported Mimo content delta type: {delta_type}")
    block[field] = str(block.get(field, "")) + str(delta.get(field, ""))
