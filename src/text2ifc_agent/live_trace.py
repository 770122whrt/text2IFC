"""Durable, secret-safe trace artifacts for real provider calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .providers import LiveProviderResult, redact_provider_payload


TRACE_FILES = {
    "request": "request.redacted.json",
    "response": "response.raw.json",
    "metadata": "response-metadata.json",
    "events": "events.jsonl",
    "text": "model-text.txt",
}


def write_live_trace(
    *,
    result: LiveProviderResult,
    output_dir: Path | str,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    provider = str(result.output.metadata.get("provider", "mimo"))

    request_artifact = {
        "provider": provider,
        "evidence_class": result.evidence_class,
        "session_id": result.session_id,
        "request": redact_provider_payload(result.request),
    }
    metadata_artifact = {
        "provider": provider,
        "evidence_class": result.evidence_class,
        "session_id": result.session_id,
        "http_status": result.http_status,
        "response_id": result.response.get("id"),
        "model": result.response.get("model"),
        "stop_reason": result.response.get("stop_reason"),
        "usage": dict(result.response.get("usage", {})),
        "event_count": len(result.events),
    }

    _write_json(output / TRACE_FILES["request"], request_artifact)
    _write_json(output / TRACE_FILES["response"], result.response)
    _write_json(output / TRACE_FILES["metadata"], metadata_artifact)
    _write_jsonl(output / TRACE_FILES["events"], result.events)
    _write_text(output / TRACE_FILES["text"], result.output.text)

    return {
        "provider": provider,
        "evidence_class": result.evidence_class,
        "session_id": result.session_id,
        "response_id": result.response.get("id"),
        "stop_reason": result.response.get("stop_reason"),
        "artifacts": dict(TRACE_FILES),
    }


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, records: tuple[dict[str, Any], ...]) -> None:
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    _write_text(path, "\n".join(lines) + "\n")


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
