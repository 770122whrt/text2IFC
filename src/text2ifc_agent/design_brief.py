"""Schema-backed Design Brief validation for the Phase 6 intent boundary."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import (
    ValidationIssue,
    _normalize_error,
    _sort_issues,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_BRIEF_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "design-brief" / "1.0" / "schema.json"
)


@lru_cache(maxsize=1)
def load_design_brief_schema() -> dict[str, Any]:
    """Load and meta-validate the canonical Design Brief schema."""
    schema = json.loads(DESIGN_BRIEF_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_design_brief(document: Any) -> list[ValidationIssue]:
    """Return stable field-level issues without mutating the brief."""
    validator = Draft202012Validator(load_design_brief_schema())
    issues = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    return _sort_issues(issues)
