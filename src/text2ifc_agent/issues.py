"""Structured issue contracts for feedback routing."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


ISSUES_SCHEMA_VERSION = "text2ifc/issues/1.0"

ISSUE_SOURCES = {
    "schema_validation",
    "semantic_validation",
    "compiler",
    "reopen_check",
    "geometry_gate",
    "deterministic_gate",
    "audit",
    "provider",
    "runtime",
}

ISSUE_SEVERITIES = {"info", "warning", "blocking", "fatal"}

ISSUE_OWNERS = {
    "user",
    "design_brief",
    "generator",
    "repair",
    "schema",
    "compiler",
    "gate",
    "audit",
    "provider",
    "runtime",
}

ISSUE_TYPES = {
    "missing_required_fact",
    "ambiguous_user_requirement",
    "changed_original_request",
    "invalid_json",
    "schema_mismatch",
    "draft_unresolved_path",
    "unsupported_schema_capability",
    "compiler_unsupported_feature",
    "compile_error",
    "reopen_error",
    "missing_entity",
    "missing_relationship",
    "missing_host",
    "missing_storey_assignment",
    "missing_space_boundary",
    "missing_vertical_connection",
    "geometry_invalid",
    "semantic_mismatch",
    "provider_truncation",
    "provider_format_error",
    "gate_false_positive",
    "runtime_error",
}

SUGGESTED_ROUTES = {
    "accepted",
    "ask_user",
    "revise_design_brief",
    "regenerate_json",
    "repair_json",
    "blocked_as_unsupported",
    "gate_issue",
    "provider_retry",
    "runtime_blocked",
}

CONTROL_VALUE_KEYS = {
    "source",
    "severity",
    "owner",
    "issue_type",
    "suggested_route",
    "route",
    "final_status",
    "target_stage",
}

_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class IssueValidationError(ValueError):
    """Raised when a Phase 6.4 issue artifact violates its contract."""


@dataclass(frozen=True)
class Issue:
    """One normalized workflow issue used by Phase 6.4 routing."""

    issue_id: str
    source: str
    severity: str
    owner: str
    issue_type: str
    evidence: str
    suggested_route: str
    retryable: bool
    expected_fact_ref: str | None = None
    actual_ref: str | None = None
    message_zh: str | None = None

    def __post_init__(self) -> None:
        validate_issue_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "issue_id": self.issue_id,
            "source": self.source,
            "severity": self.severity,
            "owner": self.owner,
            "issue_type": self.issue_type,
            "expected_fact_ref": self.expected_fact_ref,
            "actual_ref": self.actual_ref,
            "evidence": self.evidence,
            "suggested_route": self.suggested_route,
            "retryable": self.retryable,
        }
        if self.message_zh is not None:
            payload["message_zh"] = self.message_zh
        return payload


def validate_issue_dict(payload: Mapping[str, Any]) -> None:
    """Validate one serialized Issue object."""

    required = {
        "issue_id",
        "source",
        "severity",
        "owner",
        "issue_type",
        "evidence",
        "suggested_route",
        "retryable",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise IssueValidationError(f"issue missing required fields: {missing}")
    if not isinstance(payload.get("issue_id"), str) or not payload["issue_id"]:
        raise IssueValidationError("issue_id must be a non-empty string")
    _validate_enum(payload, "source", ISSUE_SOURCES)
    _validate_enum(payload, "severity", ISSUE_SEVERITIES)
    _validate_enum(payload, "owner", ISSUE_OWNERS)
    _validate_enum(payload, "issue_type", ISSUE_TYPES)
    _validate_enum(payload, "suggested_route", SUGGESTED_ROUTES)
    if not isinstance(payload.get("evidence"), str) or not payload["evidence"]:
        raise IssueValidationError("evidence must be a non-empty string")
    if not isinstance(payload.get("retryable"), bool):
        raise IssueValidationError("retryable must be a boolean")
    assert_machine_control_language(dict(payload))


def issue_to_dict(issue: Issue | Mapping[str, Any]) -> dict[str, Any]:
    """Return a validated issue dictionary from an Issue or mapping."""

    payload = issue.to_dict() if isinstance(issue, Issue) else dict(issue)
    validate_issue_dict(payload)
    return payload


def write_issues(path: Path | str, issues: Sequence[Issue | Mapping[str, Any]]) -> Path:
    """Write a Phase 6.4 `issues.json` artifact."""

    target = Path(path)
    payload = {
        "schema_version": ISSUES_SCHEMA_VERSION,
        "issues": [issue_to_dict(issue) for issue in issues],
    }
    assert_machine_control_language(payload)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def assert_machine_control_language(payload: Any) -> None:
    """Reject Chinese control keys and values in machine-readable artifacts."""

    _walk_language_policy(payload, path="")


def _validate_enum(
    payload: Mapping[str, Any],
    field: str,
    allowed: set[str],
) -> None:
    value = payload.get(field)
    if value not in allowed:
        raise IssueValidationError(
            f"{field} must be one of {sorted(allowed)}, got {value!r}"
        )


def _walk_language_policy(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise IssueValidationError(f"control key at {path or '/'} must be a string")
            if _CJK_RE.search(key):
                raise IssueValidationError(f"Chinese control key is not allowed at {path}/{key}")
            next_path = f"{path}/{key}"
            if key in CONTROL_VALUE_KEYS and isinstance(item, str) and _CJK_RE.search(item):
                raise IssueValidationError(
                    f"Chinese control value is not allowed at {next_path}"
                )
            _walk_language_policy(item, path=next_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_language_policy(item, path=f"{path}/{index}")
