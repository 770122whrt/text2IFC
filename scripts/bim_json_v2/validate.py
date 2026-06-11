"""Validate formal BIM JSON 2.0 or a BIM JSON Draft Envelope."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_contract import loads_strict_json  # noqa: E402
from text2ifc_contract.draft import validate_draft  # noqa: E402
from text2ifc_contract.validation import ValidationIssue  # noqa: E402
from text2ifc_contract.validation_v2 import validate_v2_document  # noqa: E402


MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_ERRORS = 1000


def _write(kind: str, issues: list[ValidationIssue]) -> None:
    payload = {
        "document_kind": kind,
        "valid": not issues,
        "errors": [
            {"code": item.code, "path": item.path, "message": item.message}
            for item in issues[:MAX_ERRORS]
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"formal", "draft"}:
        _write("unknown", [ValidationIssue("USAGE_ERROR", "/", "Expected KIND FILE.")])
        return 2
    kind, raw_path = sys.argv[1:]
    path = Path(raw_path)
    try:
        size = path.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise OverflowError(f"{size} bytes exceeds {MAX_INPUT_BYTES} bytes.")
        document = loads_strict_json(path.read_text(encoding="utf-8"))
    except OverflowError as exc:
        _write(kind, [ValidationIssue("FILE_TOO_LARGE", "/", str(exc))])
        return 2
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _write(kind, [ValidationIssue("INVALID_JSON", "/", str(exc))])
        return 2
    issues = (
        validate_v2_document(document) if kind == "formal" else validate_draft(document)
    )
    _write(kind, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
