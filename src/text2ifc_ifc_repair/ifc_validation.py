"""IfcOpenShell schema validation with baseline-aware regression reporting."""

from __future__ import annotations

from collections import Counter
import hashlib
from typing import Any

from ifcopenshell import validate


VALIDATION_SCHEMA_VERSION = "text2ifc/ifc-validation-delta/0.1"
NORMALIZED_VALIDATION_SCHEMA_VERSION = "text2ifc/ifc-validation-normalized/0.1"
VALIDATION_POLICY_VERSION = "ifcopenshell-schema-no-express/0.1"
DIAGNOSTIC_NORMALIZATION_VERSION = "ifc-diagnostic-signature/0.1"
_MAX_PUBLIC_DIAGNOSTICS = 64
_MAX_PUBLIC_MESSAGE_LENGTH = 1024


def validate_model(model: Any) -> dict[str, Any]:
    """Return one bounded, JSON-safe IfcOpenShell validation result."""

    diagnostics = _collect_diagnostics(model)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "status": "passed" if not diagnostics else "failed",
        "diagnostic_count": len(diagnostics),
        "diagnostics": [
            _public_diagnostic(item)
            for item in diagnostics[:_MAX_PUBLIC_DIAGNOSTICS]
        ],
        "diagnostics_truncated": len(diagnostics) > _MAX_PUBLIC_DIAGNOSTICS,
    }


def normalized_validation_result(model: Any) -> dict[str, Any]:
    """Return immutable normalized evidence suitable for content caching."""

    diagnostics = _collect_diagnostics(model)
    counts = Counter(item["_signature"] for item in diagnostics)
    return {
        "schema_version": NORMALIZED_VALIDATION_SCHEMA_VERSION,
        "status": "passed" if not diagnostics else "failed",
        "diagnostic_count": len(diagnostics),
        "signature_counts": dict(sorted(counts.items())),
        "diagnostics": [
            _public_diagnostic(item)
            for item in diagnostics[:_MAX_PUBLIC_DIAGNOSTICS]
        ],
        "diagnostics_truncated": len(diagnostics) > _MAX_PUBLIC_DIAGNOSTICS,
    }


def compare_validation_models(
    baseline_model: Any,
    candidate_model: Any,
    *,
    baseline_result: dict[str, Any] | None = None,
    candidate_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail only when the candidate introduces validation diagnostics."""

    if baseline_result is None:
        baseline = _collect_diagnostics(baseline_model)
        baseline_result = _normalized_from_diagnostics(baseline)
    else:
        baseline = _diagnostic_examples(baseline_result)
    if candidate_result is None:
        candidate = _collect_diagnostics(candidate_model)
        candidate_result = _normalized_from_diagnostics(candidate)
    else:
        candidate = _diagnostic_examples(candidate_result)
    baseline_counter = Counter(baseline_result["signature_counts"])
    candidate_counter = Counter(candidate_result["signature_counts"])
    new_counter = candidate_counter - baseline_counter
    resolved_counter = baseline_counter - candidate_counter
    new_diagnostics = _counter_examples(candidate, new_counter)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "status": "passed" if not new_counter else "failed",
        "baseline_status": "passed" if not baseline_counter else "invalid_existing",
        "baseline_diagnostic_count": baseline_result["diagnostic_count"],
        "candidate_diagnostic_count": candidate_result["diagnostic_count"],
        "new_diagnostic_count": sum(new_counter.values()),
        "resolved_diagnostic_count": sum(resolved_counter.values()),
        "new_diagnostics": [
            _public_diagnostic(item)
            for item in new_diagnostics[:_MAX_PUBLIC_DIAGNOSTICS]
        ],
        "new_diagnostics_truncated": (
            len(new_diagnostics) > _MAX_PUBLIC_DIAGNOSTICS
        ),
    }


def _normalized_from_diagnostics(
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    counts = Counter(item["_signature"] for item in diagnostics)
    return {
        "schema_version": NORMALIZED_VALIDATION_SCHEMA_VERSION,
        "status": "passed" if not diagnostics else "failed",
        "diagnostic_count": len(diagnostics),
        "signature_counts": dict(sorted(counts.items())),
        "diagnostics": [
            _public_diagnostic(item)
            for item in diagnostics[:_MAX_PUBLIC_DIAGNOSTICS]
        ],
        "diagnostics_truncated": len(diagnostics) > _MAX_PUBLIC_DIAGNOSTICS,
    }


def _diagnostic_examples(result: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "_signature": str(item["signature"]),
            "level": str(item.get("level", "")),
            "attribute": str(item.get("attribute", "")),
            "instance_class": str(item.get("instance_class", "")),
            "instance_identity": str(item.get("instance_identity", "")),
            "message": str(item.get("message", "")),
        }
        for item in result.get("diagnostics", ())
    ]


def _collect_diagnostics(model: Any) -> list[dict[str, str]]:
    logger = validate.json_logger()
    validate.validate(model, logger, express_rules=False)
    return [_normalize_statement(statement) for statement in logger.statements]


def _normalize_statement(statement: dict[str, Any]) -> dict[str, str]:
    instance = statement.get("instance")
    instance_class = ""
    instance_identity = ""
    if instance is not None and hasattr(instance, "is_a"):
        instance_class = str(instance.is_a())
        global_id = getattr(instance, "GlobalId", None)
        instance_identity = (
            f"guid:{global_id}"
            if global_id
            else f"step:{int(instance.id())}"
        )
    message = str(statement.get("message") or "")
    normalized = {
        "level": str(statement.get("level") or ""),
        "attribute": str(statement.get("attribute") or ""),
        "instance_class": instance_class,
        "instance_identity": instance_identity,
        "message": message,
    }
    signature_payload = "\x1f".join(normalized.values()).encode("utf-8")
    normalized["_signature"] = hashlib.sha256(signature_payload).hexdigest()
    return normalized


def _counter_examples(
    diagnostics: list[dict[str, str]],
    counter: Counter[str],
) -> list[dict[str, str]]:
    remaining = counter.copy()
    examples: list[dict[str, str]] = []
    for diagnostic in diagnostics:
        signature = diagnostic["_signature"]
        if remaining[signature] <= 0:
            continue
        examples.append(diagnostic)
        remaining[signature] -= 1
    return examples


def _public_diagnostic(diagnostic: dict[str, str]) -> dict[str, str]:
    return {
        "signature": diagnostic["_signature"],
        "level": diagnostic["level"],
        "attribute": diagnostic["attribute"],
        "instance_class": diagnostic["instance_class"],
        "instance_identity": diagnostic["instance_identity"],
        "message": diagnostic["message"][:_MAX_PUBLIC_MESSAGE_LENGTH],
    }


__all__ = [
    "VALIDATION_SCHEMA_VERSION",
    "VALIDATION_POLICY_VERSION",
    "DIAGNOSTIC_NORMALIZATION_VERSION",
    "NORMALIZED_VALIDATION_SCHEMA_VERSION",
    "compare_validation_models",
    "validate_model",
    "normalized_validation_result",
]
