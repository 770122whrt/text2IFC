"""Positive public allowlist and private-canary boundary checks."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


PUBLIC_EVALUATION_SCHEMA_VERSION = "text2ifc/ifc-repair-evaluation-public/0.2"
_ROOT_FIELDS = (
    "policy_version",
    "status",
    "reason",
    "complete_repair_success",
    "successful_artifact_publishable",
    "diagnostic_artifact_retained",
)


class PrivateCanaryLeakError(ValueError):
    """A private token crossed into a Provider/public artifact."""


def project_public_evaluation(private_report: Mapping[str, Any]) -> dict[str, Any]:
    """Construct public evidence exclusively from explicitly safe fields."""

    public: dict[str, Any] = {"schema_version": PUBLIC_EVALUATION_SCHEMA_VERSION}
    for field in _ROOT_FIELDS:
        public[field] = private_report[field]
    public["application"] = _project_gate(private_report["application"])
    public["preservation"] = _project_gate(private_report["preservation"])
    public["operations"] = [
        _project_operation(operation) for operation in private_report["operations"]
    ]
    return public


def assert_public_bundle_has_no_canaries(
    bundle: Any,
    canaries: Iterable[str],
) -> None:
    """Fail closed when any complete Provider/public bundle value leaks Gold."""

    tokens = tuple(token.encode("utf-8") for token in canaries if token)
    if not tokens:
        raise ValueError("PRIVATE_CANARY_SET_EMPTY")
    payload = _bundle_bytes(bundle)
    if any(token in payload for token in tokens):
        raise PrivateCanaryLeakError("PRIVATE_CANARY_DETECTED_IN_PUBLIC_BOUNDARY")


def _bundle_bytes(value: Any) -> bytes:
    if isinstance(value, Path):
        try:
            return value.read_bytes()
        except OSError as error:
            raise PrivateCanaryLeakError("PUBLIC_BOUNDARY_FILE_UNREADABLE") from error
    if isinstance(value, Mapping):
        return json.dumps(
            {str(key): _json_value(child) for key, child in value.items()},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return {"path": value.as_posix(), "content": value.read_bytes().decode("latin1")}
    if isinstance(value, Mapping):
        return {str(key): _json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(child) for child in value]
    return value


def _project_gate(gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check_id": gate["check_id"],
        "status": gate["status"],
        "reason": gate["reason"],
    }


def _project_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operation_id": operation["operation_id"],
        "operation_type": operation["operation_type"],
        "policy_id": operation["policy_id"],
        "policy_version": operation["policy_version"],
        "status": operation["status"],
        "reason": operation["reason"],
        "levels": [_project_level(level) for level in operation["levels"]],
    }


def _project_level(level: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "level": level["level"],
        "status": level["status"],
        "reason": level["reason"],
        "checks": [_project_check(check) for check in level["checks"]],
    }


def _project_check(check: Mapping[str, Any]) -> dict[str, Any]:
    source_kinds = sorted(
        {
            str(evidence["source_kind"])
            for evidence in check.get("evidence", ())
            if evidence.get("source_kind")
        }
    )
    status = str(check["status"])
    return {
        "check_id": check["check_id"],
        "policy_id": check["policy_id"],
        "applicability": check["applicability"],
        "mandatory": check["mandatory"],
        "status": status,
        "reason": check["reason"],
        "difference_category": _difference_category(str(check["check_id"])),
        "remediation_required": bool(check["mandatory"])
        and status in {"failed", "partial", "not_evaluable"},
        "provenance_source_kinds": source_kinds,
    }


def _difference_category(check_id: str) -> str:
    normalized = check_id.lower()
    for token, category in (
        ("is-external", "is_external"),
        ("material", "material"),
        ("classification", "classification"),
        ("quantity", "quantity"),
        ("pset", "pset"),
        ("type", "type"),
        ("host", "host"),
        ("storey", "storey"),
        ("width", "dimension"),
        ("height", "dimension"),
    ):
        if token in normalized:
            return category
    return "physical" if normalized.startswith("l1.") else "other"


__all__ = [
    "PUBLIC_EVALUATION_SCHEMA_VERSION",
    "PrivateCanaryLeakError",
    "assert_public_bundle_has_no_canaries",
    "project_public_evaluation",
]
