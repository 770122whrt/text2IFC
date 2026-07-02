"""Durable, secret-safe trace artifacts for real provider calls."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .providers import LiveProviderResult, redact_provider_payload
from .trace_levels import normalize_trace_level


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
    trace_level: str | None = "debug",
    preserve_deep_evidence: bool = False,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    provider = str(result.output.metadata.get("provider", "mimo"))
    active_trace_level = normalize_trace_level(trace_level)

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

    _write_json(output / TRACE_FILES["metadata"], metadata_artifact)
    deferred_artifacts = {
        "request_sha256": _payload_sha256(request_artifact),
        "response_sha256": _payload_sha256(result.response),
        "events_sha256": _payload_sha256(list(result.events)),
        "model_text_sha256": _text_sha256(result.output.text),
    }
    written_files = {"metadata": TRACE_FILES["metadata"]}
    deep_evidence: dict[str, str] = {}
    if active_trace_level in {"debug", "full"}:
        _write_json(output / TRACE_FILES["request"], request_artifact)
        _write_json(output / TRACE_FILES["response"], result.response)
        _write_jsonl(output / TRACE_FILES["events"], result.events)
        _write_text(output / TRACE_FILES["text"], result.output.text)
        written_files = dict(TRACE_FILES)
    elif preserve_deep_evidence:
        trace_dir = output / "trace"
        trace_dir.mkdir(parents=True, exist_ok=True)
        _write_json(trace_dir / TRACE_FILES["request"], request_artifact)
        _write_json(trace_dir / TRACE_FILES["response"], result.response)
        _write_jsonl(trace_dir / TRACE_FILES["events"], result.events)
        _write_text(trace_dir / TRACE_FILES["text"], result.output.text)
        deep_evidence = {
            key: f"trace/{name}" for key, name in TRACE_FILES.items() if key != "metadata"
        }

    return {
        "provider": provider,
        "trace_level": active_trace_level,
        "evidence_class": result.evidence_class,
        "session_id": result.session_id,
        "response_id": result.response.get("id"),
        "stop_reason": result.response.get("stop_reason"),
        "artifacts": written_files,
        "deferred_artifacts": deferred_artifacts
        if active_trace_level == "compact"
        else {},
        "deep_evidence": deep_evidence,
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


def _payload_sha256(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _text_sha256(text)


def _text_sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
