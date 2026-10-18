"""Small, content-free observations carried through the existing run authority."""
from __future__ import annotations

import json
import re
from typing import Any


SCENE_DIAGNOSTICS_VERSION = "text2ifc/scene-diagnostics/0.1"
MAX_SCENE_DIAGNOSTICS_BYTES = 12 * 1024


def checked_scene_diagnostics(value: Any) -> dict | None:
    if value is None:
        return None
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
        _require(len(encoded.encode("utf8")) <= MAX_SCENE_DIAGNOSTICS_BYTES)
        _require(isinstance(value, dict) and set(value) == {"schema_version", "rounds", "terminal_reason"})
        _require(value["schema_version"] == SCENE_DIAGNOSTICS_VERSION)
        _require(_token(value["terminal_reason"], 128))
        rows = value["rounds"]
        _require(isinstance(rows, list) and len(rows) <= 8)
        required = {"round", "action", "stage", "outcome", "issue_codes", "issue_paths", "context_bytes"}
        optional = {"query_id", "returned_count", "total_matches"}
        for index, row in enumerate(rows, 1):
            _require(isinstance(row, dict) and required <= set(row) <= required | optional)
            _require(type(row["round"]) is int and row["round"] == index)
            _require(row["action"] in {"query", "intent", "clarification", "unknown"})
            _require(row["stage"] in {"provider", "parse", "schema", "query", "geometry", "intent", "clarification", "context"})
            _require(row["outcome"] in {"valid", "invalid", "terminal"})
            _require(type(row["context_bytes"]) is int and row["context_bytes"] >= 0)
            for key in ("issue_codes", "issue_paths"):
                _require(isinstance(row[key], list) and len(row[key]) <= 5)
                _require(all(isinstance(item, str) and len(item) <= 160 for item in row[key]))
            _require(all(_token(item, 160) for item in row["issue_codes"]))
            _require(all(not item or re.fullmatch(r"/[A-Za-z0-9_~/.-]*", item) for item in row["issue_paths"]))
            if "query_id" in row:
                _require(re.fullmatch(r"q[1-9][0-9]*", row["query_id"]))
            for key in ("returned_count", "total_matches"):
                if key in row:
                    _require(type(row[key]) is int and row[key] >= 0)
        return json.loads(encoded)
    except (TypeError, ValueError, KeyError) as error:
        raise ValueError("SCENE_DIAGNOSTICS_INVALID") from error


def _token(value: Any, limit: int) -> bool:
    return isinstance(value, str) and 0 < len(value) <= limit and bool(re.fullmatch(r"[A-Za-z0-9_.:-]+", value))


def _require(condition: Any) -> None:
    if not condition:
        raise ValueError("SCENE_DIAGNOSTICS_INVALID")
