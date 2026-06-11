"""Validation for incomplete BIM JSON Draft Envelopes."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from .schema import load_draft_schema
from .validation import ValidationIssue, _normalize_error, _sort_issues


def _path_parent_exists(document: Any, pointer: str) -> bool:
    tokens = pointer.lstrip("/").split("/")
    current = document
    for raw in tokens[:-1]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError):
                return False
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            return False
    return True


def validate_draft(document: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(load_draft_schema())
    issues = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    if issues or not isinstance(document, dict):
        return _sort_issues(issues)
    if not document["missing_facts"] and not document["losses"]:
        issues.append(
            ValidationIssue(
                "UNDECLARED_OMISSION",
                "/missing_facts",
                "A Draft must declare at least one missing fact or loss.",
            )
        )
    partial = document["partial_document"]
    for index, fact in enumerate(document["missing_facts"]):
        if not _path_parent_exists(partial, fact["path"]):
            issues.append(
                ValidationIssue(
                    "UNRESOLVED_DRAFT_PATH",
                    f"/missing_facts/{index}/path",
                    f"Draft path {fact['path']!r} is not addressable.",
                )
            )
    return _sort_issues(issues)
