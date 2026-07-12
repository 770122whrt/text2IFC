"""Immutable revision and authorized ChangeSet scope contracts."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import ValidationIssue


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REVISION_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "bim-json-revision-1.0.schema.json"
SCOPE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "agent" / "change-scope-1.0.schema.json"


def hash_json_value(value: Any) -> str:
    """Return a canonical semantic SHA-256 for one JSON value."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def validate_revision_record(
    record: Any,
    *,
    candidate: Mapping[str, Any] | None = None,
    expected_facts: Mapping[str, Any] | None = None,
) -> list[ValidationIssue]:
    """Validate one revision and optionally bind it to current artifacts."""

    issues = _schema_issues(record, _revision_schema(), "REVISION_CONTRACT_ERROR")
    if issues or not isinstance(record, Mapping):
        return _sort_issues(issues)

    sequence = record["sequence"]
    parent = record["parent_revision_id"]
    if (sequence == 0 and parent is not None) or (sequence > 0 and parent is None):
        issues.append(
            ValidationIssue(
                code="REVISION_PARENT_CONFLICT",
                path="/parent_revision_id",
                message="Initial revisions have no parent; later revisions require one.",
            )
        )

    if candidate is not None:
        if record["candidate_hash"] != hash_json_value(candidate):
            issues.append(
                ValidationIssue(
                    code="REVISION_CANDIDATE_HASH_MISMATCH",
                    path="/candidate_hash",
                    message="Revision candidate hash does not match the supplied candidate.",
                )
            )
        current_components = _candidate_components(candidate)
        for component_id, expected_hash in record["component_hashes"].items():
            component = current_components.get(component_id)
            if component is None or hash_json_value(component) != expected_hash:
                issues.append(
                    ValidationIssue(
                        code="REVISION_COMPONENT_HASH_MISMATCH",
                        path=f"/component_hashes/{_escape(component_id)}",
                        message=f"Component hash does not match {component_id!r}.",
                    )
                )

    if (
        expected_facts is not None
        and record["expected_facts_hash"] != hash_json_value(expected_facts)
    ):
        issues.append(
            ValidationIssue(
                code="REVISION_EXPECTED_FACTS_HASH_MISMATCH",
                path="/expected_facts_hash",
                message="Revision expected-facts hash does not match the supplied artifact.",
            )
        )
    return _sort_issues(issues)


def validate_change_scope(scope: Any) -> list[ValidationIssue]:
    """Validate one explicit allowed ChangeSet scope."""

    issues = _schema_issues(scope, _scope_schema(), "CHANGE_SCOPE_CONTRACT_ERROR")
    if issues or not isinstance(scope, Mapping):
        return _sort_issues(issues)

    allowed = set(scope["entity_ids"]) | set(scope["relationship_ids"])
    forbidden = set(scope["forbidden_ids"])
    overlap = sorted(allowed & forbidden)
    for component_id in overlap:
        issues.append(
            ValidationIssue(
                code="CHANGE_SCOPE_FORBIDDEN_OVERLAP",
                path="/forbidden_ids",
                message=f"Allowed component {component_id!r} is also forbidden.",
            )
        )

    for component_id in scope["allowed_paths"]:
        if component_id not in allowed:
            issues.append(
                ValidationIssue(
                    code="CHANGE_SCOPE_UNKNOWN_PATH_TARGET",
                    path=f"/allowed_paths/{_escape(component_id)}",
                    message=f"Allowed paths reference undeclared component {component_id!r}.",
                )
            )

    for index, dependency in enumerate(scope["dependencies"]):
        if (
            dependency["target_id"] not in allowed
            or dependency["dependency_id"] not in allowed
        ):
            issues.append(
                ValidationIssue(
                    code="CHANGE_SCOPE_UNKNOWN_DEPENDENCY",
                    path=f"/dependencies/{index}",
                    message="Dependency endpoints must both be in the allowed scope.",
                )
            )
    return _sort_issues(issues)


def write_revision_record(path: Path | str, record: Mapping[str, Any]) -> Path:
    issues = validate_revision_record(record)
    if issues:
        raise ValueError(f"invalid revision: {issues[0].code} at {issues[0].path}")
    return _write_json(path, record)


def write_change_scope(path: Path | str, scope: Mapping[str, Any]) -> Path:
    issues = validate_change_scope(scope)
    if issues:
        raise ValueError(f"invalid change scope: {issues[0].code} at {issues[0].path}")
    return _write_json(path, scope)


@lru_cache(maxsize=1)
def _revision_schema() -> dict[str, Any]:
    return _load_schema(REVISION_SCHEMA_PATH)


@lru_cache(maxsize=1)
def _scope_schema() -> dict[str, Any]:
    return _load_schema(SCOPE_SCHEMA_PATH)


def _load_schema(path: Path) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def _schema_issues(
    value: Any,
    schema: Mapping[str, Any],
    code: str,
) -> list[ValidationIssue]:
    return [
        ValidationIssue(code=code, path=_pointer(error.absolute_path), message=error.message)
        for error in Draft202012Validator(schema).iter_errors(value)
    ]


def _candidate_components(candidate: Mapping[str, Any]) -> dict[str, Any]:
    components: dict[str, Any] = {}
    for collection_name in ("entities", "relationships"):
        collection = candidate.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for component in collection:
            if isinstance(component, Mapping) and isinstance(component.get("id"), str):
                components[component["id"]] = component
    return components


def _write_json(path: Path | str, value: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def _pointer(parts: Iterable[Any]) -> str:
    tokens = [_escape(part) for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"


def _escape(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _sort_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))
