"""Additive part-appearance contract, retaining all 2.1 semantic/geometry gates."""
from jsonschema import Draft202012Validator

from .schema import load_schema_v22
from .validation import _normalize_error, _sort_issues
from .validation_v2 import _semantic_issues
from .part_appearance import validate_part_appearance_document


def validate_v22_document(document):
    structural = [issue for error in Draft202012Validator(load_schema_v22()).iter_errors(document) for issue in _normalize_error(error)]
    # Malformed structures are handled by the schema before traversing records.
    if structural:
        for issue in structural:
            if '/part_appearance' in issue.path:
                from .validation import ValidationIssue
                return _sort_issues([*structural, ValidationIssue('INVALID_PART_APPEARANCE', issue.path, issue.message)])
        return _sort_issues(structural)
    return _sort_issues([*_semantic_issues(document, extended=True), *validate_part_appearance_document(document)])
