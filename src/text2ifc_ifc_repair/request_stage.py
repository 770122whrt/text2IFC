"""Public-only Provider stage for natural-language IFC repair requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import (
    ProviderOutputError,
    redact_provider_payload,
    validate_provider_output,
)
from text2ifc_text.splits import atomic_write_text

from .registry import OperationRegistry
from .repair_intent import (
    DEFAULT_REPAIR_INTENT_LIMITS,
    RepairIntent,
    RepairIntentCode,
    RepairIntentError,
    fingerprint_text,
    hash_request,
    load_repair_intent_schema,
)


TEMPLATE_ID = "ifc-repair-intent.v0.1"
MAX_REQUEST_BYTES = DEFAULT_REPAIR_INTENT_LIMITS.max_request_bytes
MAX_PROVIDER_RESPONSE_BYTES = (
    DEFAULT_REPAIR_INTENT_LIMITS.max_provider_response_bytes
)
MAX_CORRECTION_ATTEMPTS = DEFAULT_REPAIR_INTENT_LIMITS.max_correction_attempts


def generate_repair_intent(
    *,
    provider: Any,
    request_id: str,
    repair_request: str,
    registry: OperationRegistry,
    output_dir: Path | str,
    max_attempts: int = MAX_CORRECTION_ATTEMPTS,
) -> dict[str, Any]:
    """Generate one Registry-bound RepairIntent from bounded public data."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if len(repair_request.encode("utf-8")) > MAX_REQUEST_BYTES:
        return _failure(RepairIntentCode.REQUEST_TOO_LARGE, attempts=())
    if not 1 <= max_attempts <= MAX_CORRECTION_ATTEMPTS:
        return _failure(RepairIntentCode.ATTEMPT_BUDGET_INVALID, attempts=())

    schema = load_repair_intent_schema()
    source_request_hash = hash_request(repair_request)
    supported_operations = _supported_operations(registry)
    feedback: list[dict[str, str]] = []
    rendered = render_prompt(
        template_id=TEMPLATE_ID,
        inputs={
            "REQUEST_ID": request_id,
            "REPAIR_REQUEST": repair_request,
            "SOURCE_REQUEST_HASH": source_request_hash,
            "PROMPT_FINGERPRINT": _registered_prompt_hash(),
            "SUPPORTED_OPERATIONS": supported_operations,
            "REPAIR_INTENT_SCHEMA": schema,
            "VALIDATION_FEEDBACK": feedback,
        },
    )
    renderer_input = dict(rendered["inputs"])
    atomic_write_text(output / "renderer-input.json", _pretty_json(renderer_input))
    atomic_write_text(output / "rendered-prompt.md", str(rendered["text"]))

    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, max_attempts + 1):
        if attempt_number > 1:
            rendered = render_prompt(
                template_id=TEMPLATE_ID,
                inputs={**renderer_input, "VALIDATION_FEEDBACK": feedback},
            )
        provider_arguments = {
            "session_id": f"ifc-repair-intent-{request_id}",
            "prompt": str(rendered["text"]),
            "schema": schema,
            "state": {
                "request_id": request_id,
                "stage": "ifc_repair_intent",
                "attempt": attempt_number,
            },
        }
        try:
            provider_output, live_evidence = _call_provider(
                provider, provider_arguments
            )
        except ProviderOutputError as error:
            issues = [
                _issue(
                    RepairIntentCode.PROVIDER_REQUEST_FAILED,
                    type(error).__name__,
                )
            ]
            attempt = _attempt_record(
                attempt_number=attempt_number,
                issues=issues,
                provider_metadata={},
                raw_text="",
            )
            attempts.append(attempt)
            atomic_write_text(
                output / f"attempt-{attempt_number:03d}.json",
                _pretty_json(attempt),
            )
            feedback = issues
            continue
        issues: list[dict[str, str]] = []
        intent: RepairIntent | None = None
        raw_text = provider_output.text
        if len(raw_text.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
            issues.append(
                _issue(
                    RepairIntentCode.PROVIDER_RESPONSE_TOO_LARGE,
                    "Provider response exceeds the public Stage 1 byte limit.",
                )
            )
        else:
            parse_status, parsed, parse_issues = provider_output.parse_json()
            if parse_status != "ok" or parsed is None:
                issues.extend(_normalize_issues(parse_issues))
            elif parse_issues:
                issues.extend(_normalize_issues(parse_issues))
            else:
                try:
                    intent = RepairIntent.from_dict(parsed, registry=registry)
                    _validate_bindings(
                        intent,
                        request_id=request_id,
                        source_request_hash=source_request_hash,
                        prompt_fingerprint=str(
                            rendered["metadata"]["template_hash"]
                        ),
                        model=str(provider_output.metadata.get("model", "")),
                    )
                except RepairIntentError as error:
                    issues.append(_issue(error.code, error.detail, path=error.path))

        issues = sorted(
            issues,
            key=lambda item: (item["code"], item["path"], item["message"]),
        )
        attempt = _attempt_record(
            attempt_number=attempt_number,
            issues=issues,
            provider_metadata=provider_output.metadata,
            raw_text=raw_text,
            valid=intent is not None and not issues,
        )
        attempts.append(attempt)
        atomic_write_text(
            output / f"attempt-{attempt_number:03d}.json",
            _pretty_json(attempt),
        )
        _write_live_evidence(output, attempt_number, live_evidence)
        if intent is not None and not issues:
            atomic_write_text(
                output / "repair-intent.json", _pretty_json(intent.to_dict())
            )
            return {
                "valid": True,
                "classification": "repair_intent",
                "intent": intent,
                "prompt": _prompt_identity(rendered),
                "attempts": attempts,
                "error_code": None,
            }
        feedback = issues

    return _failure(
        RepairIntentCode.RETRY_EXHAUSTED,
        attempts=tuple(attempts),
        prompt=_prompt_identity(rendered),
    )


def _call_provider(
    provider: Any, provider_arguments: Mapping[str, Any]
) -> tuple[Any, Mapping[str, Any] | None]:
    generate_live = getattr(provider, "generate_live", None)
    if callable(generate_live):
        live_result = generate_live(**provider_arguments)
        return validate_provider_output(live_result.output), {
            "request": live_result.request,
            "response": live_result.response,
            "events": list(live_result.events),
        }
    return (
        validate_provider_output(provider.generate_candidate(**provider_arguments)),
        None,
    )


def _validate_bindings(
    intent: RepairIntent,
    *,
    request_id: str,
    source_request_hash: str,
    prompt_fingerprint: str,
    model: str,
) -> None:
    checks = (
        (intent.request_id == request_id, RepairIntentCode.REQUEST_ID_MISMATCH),
        (
            intent.source_request_hash == source_request_hash,
            RepairIntentCode.REQUEST_HASH_MISMATCH,
        ),
        (
            intent.prompt_fingerprint == prompt_fingerprint,
            RepairIntentCode.PROMPT_FINGERPRINT_MISMATCH,
        ),
        (
            bool(model) and intent.model_fingerprint == fingerprint_text(model),
            RepairIntentCode.MODEL_FINGERPRINT_MISMATCH,
        ),
    )
    for passed, code in checks:
        if not passed:
            raise RepairIntentError(code, code)


def _supported_operations(registry: OperationRegistry) -> list[dict[str, Any]]:
    return [
        {
            "operation_type": operation_type,
            "target_ifc_classes": list(
                registry.require(operation_type).target_ifc_classes
            ),
            "parameter_schema": dict(
                registry.require(operation_type).parameter_schema
            ),
            "capability_constraints": dict(
                registry.require(operation_type).capability_constraints
            ),
        }
        for operation_type in registry.operation_types
    ]


def _registered_prompt_hash() -> str:
    from text2ifc_agent.prompt_registry import load_prompt_registry

    return str(load_prompt_registry()[TEMPLATE_ID]["sha256"])


def _normalize_issues(values: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        _issue(
            str(item.get("code", "PROVIDER_JSON_INVALID")),
            str(item.get("message", "Provider JSON is invalid.")),
            path=str(item.get("path", "")),
        )
        for item in values
    ]


def _issue(
    code: RepairIntentCode | str, message: str, *, path: str = ""
) -> dict[str, str]:
    stable_code = code.value if isinstance(code, RepairIntentCode) else code
    return {"code": stable_code, "path": path, "message": message[:1000]}


def _failure(
    error_code: RepairIntentCode | str,
    *,
    attempts: tuple[dict[str, Any], ...],
    prompt: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "valid": False,
        "classification": "invalid",
        "intent": None,
        "prompt": dict(prompt or {}),
        "attempts": list(attempts),
        "error_code": (
            error_code.value
            if isinstance(error_code, RepairIntentCode)
            else error_code
        ),
    }


def _prompt_identity(rendered: Mapping[str, Any]) -> dict[str, str]:
    metadata = rendered["metadata"]
    return {
        "template_id": str(metadata["template_id"]),
        "template_hash": str(metadata["template_hash"]),
    }


def _bounded_redacted_excerpt(value: str) -> str:
    redacted = str(_redact_private(value))
    return redacted[: DEFAULT_REPAIR_INTENT_LIMITS.max_attempt_excerpt_chars]


def _redact_private(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for term in DEFAULT_REPAIR_INTENT_LIMITS.private_canary_terms:
            redacted = redacted.replace(term, "[REDACTED_PRIVATE]")
        return redacted
    if isinstance(value, Mapping):
        return {str(key): _redact_private(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_private(item) for item in value]
    return value


def _attempt_record(
    *,
    attempt_number: int,
    issues: list[dict[str, str]],
    provider_metadata: Mapping[str, Any],
    raw_text: str,
    valid: bool = False,
) -> dict[str, Any]:
    return {
        "attempt": attempt_number,
        "status": "valid" if valid else "invalid",
        "issues": issues,
        "provider_metadata": _redact_private(
            redact_provider_payload(provider_metadata)
        ),
        "response_excerpt": _bounded_redacted_excerpt(raw_text),
    }


def _write_live_evidence(
    output: Path,
    attempt_number: int,
    evidence: Mapping[str, Any] | None,
) -> None:
    if evidence is None:
        return
    atomic_write_text(
        output / f"live-attempt-{attempt_number:03d}.json",
        _pretty_json(_redact_private(redact_provider_payload(evidence))),
    )


def _pretty_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"


__all__ = [
    "MAX_CORRECTION_ATTEMPTS",
    "MAX_PROVIDER_RESPONSE_BYTES",
    "MAX_REQUEST_BYTES",
    "TEMPLATE_ID",
    "generate_repair_intent",
]
