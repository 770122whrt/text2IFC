"""Draft Envelope validation skeleton for RED tests."""

from __future__ import annotations

from .validation import ValidationIssue


def validate_draft(document):
    return [
        ValidationIssue(
            code="NOT_IMPLEMENTED",
            path="/",
            message="Draft Envelope validation is not implemented.",
        )
    ]
