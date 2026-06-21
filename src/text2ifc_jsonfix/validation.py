"""Structural and semantic validation for BIM JSON Patch 1.0."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import (
    ValidationIssue,
    _non_finite_number_issues,
    _normalize_error,
    _sort_issues,
)


PATCH_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "bim-json-patch"
    / "1.0"
    / "schema.json"
)

DESTRUCTIVE_OPERATIONS = frozenset(
    {
        "delete",
        "delete_entity",
        "delete_relationship",
        "remove",
        "remove_entity",
        "remove_relationship",
        "unset_attribute",
        "unset_property",
    }
)
LOW_LEVEL_TERMS = frozenset(
    {
        "ifccartesianpoint",
        "ifcdirection",
        "ifclocalplacement",
        "ifcownerhistory",
        "facevertexindices",
        "usd::usdgeom::mesh",
        "usd::xformop",
    }
)
RAW_STEP = re.compile(
    r"(ISO-10303-21|ENDSEC\s*;|FILE_SCHEMA\s*\(|#\d+\s*=\s*IFC)",
    re.IGNORECASE,
)
STEP_ID = re.compile(r"#\d+")


def _assert_local_references(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key == "$ref" and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError(
                    f"Remote schema references are forbidden: {child!r}"
                )
            _assert_local_references(child)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for child in value:
            _assert_local_references(child)


def load_patch_schema() -> dict[str, Any]:
    schema = json.loads(PATCH_SCHEMA_PATH.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def _escape_pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _pointer(parts: Iterable[Any]) -> str:
    tokens = [_escape_pointer_token(part) for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"


def _issue(
    code: str, path: tuple[Any, ...], message: str
) -> ValidationIssue:
    return ValidationIssue(code=code, path=_pointer(path), message=message)


def _content_guardrail_issues(
    value: Any, path: tuple[Any, ...] = ()
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_path = (*path, key)
            if str(key).casefold() in LOW_LEVEL_TERMS:
                issues.append(
                    _issue(
                        "LOW_LEVEL_IFC_OBJECT_FORBIDDEN",
                        key_path,
                        f"Low-level model output {key!r} is forbidden.",
                    )
                )
            issues.extend(_content_guardrail_issues(child, key_path))
        return issues
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value):
            issues.extend(_content_guardrail_issues(child, (*path, index)))
        return issues
    if not isinstance(value, str):
        return issues

    folded = value.casefold()
    if RAW_STEP.search(value):
        issues.append(
            _issue(
                "RAW_IFC_STEP_FORBIDDEN",
                path,
                "Raw IFC STEP serialization is forbidden in patch output.",
            )
        )
    if STEP_ID.fullmatch(value.strip()):
        issues.append(
            _issue(
                "STEP_ID_FORBIDDEN",
                path,
                "STEP line identifiers are not stable patch targets.",
            )
        )
    if any(term in folded for term in LOW_LEVEL_TERMS):
        issues.append(
            _issue(
                "LOW_LEVEL_IFC_OBJECT_FORBIDDEN",
                path,
                f"Low-level model output {value!r} is forbidden.",
            )
        )
    return issues


def _operation_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    supported_operations = frozenset(
        load_patch_schema()["x-supported-operations"]
    )
    for layer_index, layer in enumerate(document["layers"]):
        for operation_index, operation in enumerate(layer["operations"]):
            path = ("layers", layer_index, "operations", operation_index, "op")
            operation_name = operation["op"]
            if operation_name in DESTRUCTIVE_OPERATIONS:
                issues.append(
                    _issue(
                        "DESTRUCTIVE_OPERATION_REQUIRES_REVIEW",
                        path,
                        "Destructive changes require a review tombstone.",
                    )
                )
            elif operation_name not in supported_operations:
                issues.append(
                    _issue(
                        "UNSUPPORTED_PATCH_OPERATION",
                        path,
                        f"Patch operation {operation_name!r} is not supported.",
                    )
                )
            elif operation_name == "request_tombstone" and not operation.get(
                "review_required"
            ):
                issues.append(
                    _issue(
                        "TOMBSTONE_REVIEW_REQUIRED",
                        (
                            "layers",
                            layer_index,
                            "operations",
                            operation_index,
                            "review_required",
                        ),
                        "Tombstone requests must explicitly require review.",
                    )
                )
    return issues


def validate_patch_document(document: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(load_patch_schema())
    structural = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    structural = _sort_issues(structural)
    if structural:
        return structural

    issues = _non_finite_number_issues(document)
    issues.extend(_operation_issues(document))
    issues.extend(_content_guardrail_issues(document))
    return _sort_issues(issues)
