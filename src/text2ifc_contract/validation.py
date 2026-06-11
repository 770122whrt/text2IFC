from dataclasses import dataclass
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .schema import load_schema


_CODE_BY_VALIDATOR = {
    "required": "REQUIRED_FIELD",
    "type": "INVALID_TYPE",
    "enum": "INVALID_ENUM",
    "const": "INVALID_ENUM",
    "minimum": "VALUE_OUT_OF_RANGE",
    "exclusiveMinimum": "VALUE_OUT_OF_RANGE",
    "additionalProperties": "UNSUPPORTED_FIELD",
}


@dataclass(frozen=True, order=True)
class ValidationIssue:
    code: str
    path: str
    message: str


def _escape_pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _pointer(parts: Iterable[Any]) -> str:
    tokens = [_escape_pointer_token(part) for part in parts]
    return "/" + "/".join(tokens) if tokens else "/"


def _required_issues(error: ValidationError) -> list[ValidationIssue]:
    missing = [
        key for key in error.validator_value if key not in error.instance
    ]
    return [
        ValidationIssue(
            code="REQUIRED_FIELD",
            path=_pointer([*error.absolute_path, key]),
            message=f"Required field {key!r} is missing.",
        )
        for key in missing
    ]


def _additional_property_issues(error: ValidationError) -> list[ValidationIssue]:
    allowed = set(error.schema.get("properties", {}))
    unexpected = sorted(set(error.instance) - allowed)
    return [
        ValidationIssue(
            code="UNSUPPORTED_FIELD",
            path=_pointer([*error.absolute_path, key]),
            message=f"Field {key!r} is not supported.",
        )
        for key in unexpected
    ]


def _normalize_error(error: ValidationError) -> list[ValidationIssue]:
    if error.validator == "required" and isinstance(error.instance, dict):
        return _required_issues(error)
    if error.validator == "additionalProperties" and isinstance(
        error.instance, dict
    ):
        return _additional_property_issues(error)
    return [
        ValidationIssue(
            code=_CODE_BY_VALIDATOR.get(
                error.validator, "INVALID_STRUCTURE"
            ),
            path=_pointer(error.absolute_path),
            message=error.message,
        )
    ]


def validate_document(document: Any) -> list[ValidationIssue]:
    validator = Draft202012Validator(load_schema())
    issues = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    return sorted(set(issues), key=lambda issue: (issue.path, issue.code, issue.message))
