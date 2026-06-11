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
SCHEMA_V2_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "bim-json"
    / "2.0"
    / "schema.json"
)
DRAFT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "bim-json"
    / "draft"
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


def _load_schema_path(path: Path) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    _assert_local_references(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def load_schema_v2() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH)


def load_draft_schema() -> dict[str, Any]:
    return _load_schema_path(DRAFT_SCHEMA_PATH)
