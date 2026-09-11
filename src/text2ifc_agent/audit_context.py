"""Opt-in, lossless projection of repeated Audit evidence into one message.

This changes representation, not evidence collection or acceptance. Full prompts
remain the default until model-side quality and whole-loop costs are evaluated.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .openai_compat import estimate_openai_compatible_input_tokens
from .prompt_registry import render_prompt


CONTEXT_VERSION = "text2ifc/audit-evidence-context/1.0"
ROOTS = ("DETERMINISTIC_GATES", "REVISION_EVIDENCE")
REF_KEY = "audit_ref"
MIN_SHARED_BYTES = 512


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _measure(rendered: Mapping[str, Any]) -> dict[str, Any]:
    text = rendered["text"]
    return {
        "template_id": rendered["metadata"]["template_id"],
        "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "utf8_bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "estimated_input_tokens": estimate_openai_compatible_input_tokens(text),
    }


def _pack(roots: dict[str, Any]) -> dict[str, Any] | None:
    counts: Counter[str] = Counter()
    collision = False

    def scan(value: Any) -> None:
        nonlocal collision
        if isinstance(value, dict):
            if not all(isinstance(key, str) for key in value):
                raise ValueError("AUDIT_CONTEXT_NON_JSON_KEY")
            collision |= REF_KEY in value
            for child in value.values():
                scan(child)
        elif isinstance(value, list):
            for child in value:
                scan(child)
        elif value is not None and type(value) not in (str, int, float, bool):
            raise ValueError("AUDIT_CONTEXT_NON_JSON_VALUE")
        if isinstance(value, (dict, list)):
            key = _canonical(value)
            if len(key.encode("utf-8")) >= MIN_SHARED_BYTES:
                counts[key] += 1

    scan(roots)
    if collision:
        return None
    identities: dict[str, str] = {}
    values: dict[str, Any] = {}

    def children(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: encode(value[key]) for key in sorted(value)}
        if isinstance(value, list):
            return [encode(child) for child in value]
        return value

    def encode(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            key = _canonical(value)
            if counts[key] > 1:
                if key not in identities:
                    identity = f"E{len(identities) + 1:04d}"
                    identities[key] = identity
                    values[identity] = children(value)
                return {REF_KEY: identities[key]}
        return children(value)

    encoded_roots = {key: encode(roots[key]) for key in ROOTS}
    return {"schema_version": CONTEXT_VERSION, "roots": encoded_roots, "values": values}


def restore_audit_evidence(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve only same-bundle references; reject incomplete/ambiguous evidence."""
    if (not isinstance(bundle, dict)
            or set(bundle) != {"schema_version", "roots", "values"}
            or bundle["schema_version"] != CONTEXT_VERSION
            or not isinstance(bundle["roots"], dict)
            or set(bundle["roots"]) != set(ROOTS)
            or not isinstance(bundle["values"], dict)):
        raise ValueError("AUDIT_CONTEXT_INVALID_ENVELOPE")
    table = bundle["values"]
    visiting: set[str] = set()
    restored: dict[str, Any] = {}

    def decode(value: Any) -> Any:
        if isinstance(value, dict):
            if REF_KEY in value:
                identity = value[REF_KEY]
                if set(value) != {REF_KEY} or not isinstance(identity, str):
                    raise ValueError("AUDIT_CONTEXT_AMBIGUOUS_REFERENCE")
                if identity not in table or identity in visiting:
                    raise ValueError("AUDIT_CONTEXT_MISSING_OR_CYCLIC_REFERENCE")
                if identity not in restored:
                    visiting.add(identity)
                    restored[identity] = decode(table[identity])
                    visiting.remove(identity)
                return deepcopy(restored[identity])
            if not all(isinstance(key, str) for key in value):
                raise ValueError("AUDIT_CONTEXT_NON_JSON_KEY")
            return {key: decode(child) for key, child in value.items()}
        if isinstance(value, list):
            return [decode(child) for child in value]
        if value is not None and type(value) not in (str, int, float, bool):
            raise ValueError("AUDIT_CONTEXT_NON_JSON_VALUE")
        return value

    roots = decode(bundle["roots"])
    if set(restored) != set(table):
        raise ValueError("AUDIT_CONTEXT_UNREFERENCED_EVIDENCE")
    _canonical(roots)  # Reject non-finite numbers as well as invalid containers.
    return roots


def render_audit_context(
    *, inputs: Mapping[str, Any], review_enabled: bool = False, mode: str = "full",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Render the old or explicitly selected experimental Audit input format.

The baseline's required_inputs determines what was actually sent. Local-only
sidecar fields never enter either measurement or the compact evidence bundle.
"""
    if mode not in ("full", "deduplicated"):
        raise ValueError("AUDIT_CONTEXT_UNKNOWN_MODE")
    baseline = render_prompt(template_id="audit.v3" if review_enabled else "audit.v2", inputs=inputs)
    selected = baseline
    record = {
        "schema_version": "text2ifc/audit-context-record/1.0",
        "requested_mode": mode, "effective_mode": "full", "fallback_reason": None,
        "roundtrip_verified": None, "shared_value_count": 0,
        "baseline": _measure(baseline), "actual_provider_tokens": None,
        "token_measurement": "ascii_cjk_heuristic_not_provider_usage_or_guaranteed_upper_bound",
    }
    if mode == "deduplicated":
        roots = {key: baseline["inputs"][key] for key in ROOTS}
        record["source_roots_sha256"] = hashlib.sha256(_canonical(roots).encode("utf-8")).hexdigest()
        bundle = _pack(roots)
        if bundle is None:
            record["fallback_reason"] = "source_reference_marker_collision"
        else:
            if _canonical(restore_audit_evidence(bundle)) != _canonical(roots):
                raise ValueError("AUDIT_CONTEXT_ROUNDTRIP_MISMATCH")
            record["roundtrip_verified"] = True
            compact_inputs = {key: value for key, value in baseline["inputs"].items() if key not in ROOTS}
            compact_inputs["AUDIT_EVIDENCE_CONTEXT"] = bundle
            compact = render_prompt(template_id="audit.v5" if review_enabled else "audit.v4", inputs=compact_inputs)
            candidate_measure = _measure(compact)
            record["candidate"] = candidate_measure
            record["shared_value_count"] = len(bundle["values"])
            if (candidate_measure["utf8_bytes"] < record["baseline"]["utf8_bytes"]
                    and candidate_measure["estimated_input_tokens"] < record["baseline"]["estimated_input_tokens"]):
                selected = compact
                record["effective_mode"] = "deduplicated"
            else:
                record["fallback_reason"] = "complete_prompt_not_smaller"
    record["selected"] = _measure(selected)
    return selected, record
