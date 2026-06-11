"""BIM JSON 2.0 validation skeleton for RED tests."""

from __future__ import annotations

from .validation import ValidationIssue


def validate_v2_document(document):
    return [
        ValidationIssue(
            code="NOT_IMPLEMENTED",
            path="/",
            message="BIM JSON 2.0 validation is not implemented.",
        )
    ]
