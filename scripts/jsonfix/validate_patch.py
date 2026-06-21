"""Validate a BIM JSON Patch 1.0 document."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_contract import loads_strict_json  # noqa: E402
from text2ifc_contract.validation import ValidationIssue  # noqa: E402
from text2ifc_jsonfix.validation import validate_patch_document  # noqa: E402


MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_ERRORS = 1000


def _write(issues: list[ValidationIssue]) -> None:
    print(
        json.dumps(
            {
                "document_kind": "bim-json-patch/1.0",
                "valid": not issues,
                "errors": [
                    {
                        "code": issue.code,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in issues[:MAX_ERRORS]
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        _write(
            [
                ValidationIssue(
                    "USAGE_ERROR",
                    "/",
                    "Expected one BIM JSON patch file path.",
                )
            ]
        )
        return 2

    path = Path(arguments[0])
    try:
        size = path.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise OverflowError(
                f"{size} bytes exceeds {MAX_INPUT_BYTES} bytes."
            )
        document = loads_strict_json(path.read_text(encoding="utf-8"))
    except OverflowError as exc:
        _write([ValidationIssue("FILE_TOO_LARGE", "/", str(exc))])
        return 2
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _write([ValidationIssue("INVALID_JSON", "/", str(exc))])
        return 2

    issues = validate_patch_document(document)
    _write(issues)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
