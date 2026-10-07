from pathlib import Path
from typing import Any

from .schema_io import assert_local_references as _assert_local_references
from .schema_io import load_local_schema as _load_schema_path


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


def load_schema() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_PATH)


def load_schema_v2() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH)


def load_schema_v21() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.1" / "schema.json")


def load_schema_v22() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.2" / "schema.json")


def load_schema_v23() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.3" / "schema.json")


def load_schema_v24() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.4" / "schema.json")


def load_schema_v25() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.5" / "schema.json")


def load_draft_schema() -> dict[str, Any]:
    return _load_schema_path(DRAFT_SCHEMA_PATH)


def load_schema_v26() -> dict[str, Any]:
    return _load_schema_path(SCHEMA_V2_PATH.parent.parent / "2.6" / "schema.json")
