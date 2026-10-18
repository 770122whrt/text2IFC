"""Load local JSON schemas without allowing external reference resolution."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def assert_local_references(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError(f"Remote schema references are forbidden: {child!r}")
            assert_local_references(child)
    elif isinstance(value, list):
        for child in value:
            assert_local_references(child)


def load_local_schema(path: Path) -> dict[str, Any]:
    """Return a fresh, meta-validated schema; callers own any caching policy."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema
