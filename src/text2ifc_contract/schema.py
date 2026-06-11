import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "bim-json"
    / "1.0"
    / "schema.json"
)


def _assert_local_references(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError(f"Remote schema references are forbidden: {child!r}")
            _assert_local_references(child)
    elif isinstance(value, list):
        for child in value:
            _assert_local_references(child)


def load_schema() -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema
