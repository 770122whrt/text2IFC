import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_contract import loads_strict_json
from text2ifc_contract.validation import ValidationIssue, validate_document


MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_ERRORS = 1000


def _issue(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path="/", message=message)


def _write_payload(valid: bool, issues: list[ValidationIssue]) -> None:
    payload: dict[str, Any] = {
        "valid": valid,
        "errors": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in issues[:MAX_ERRORS]
        ],
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")


def _load_document(path: Path) -> Any:
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ValueError(
            f"FILE_TOO_LARGE:{size} bytes exceeds the {MAX_INPUT_BYTES} byte limit."
        )
    return loads_strict_json(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        _write_payload(False, [_issue("USAGE_ERROR", "Expected one JSON file path.")])
        return 2

    path = Path(args[0])
    try:
        document = _load_document(path)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("FILE_TOO_LARGE:"):
            code = "FILE_TOO_LARGE"
            message = message.removeprefix("FILE_TOO_LARGE:")
        else:
            code = "INVALID_JSON"
        _write_payload(False, [_issue(code, message)])
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _write_payload(False, [_issue("INVALID_JSON", str(exc))])
        return 2

    issues = validate_document(document)
    _write_payload(not issues, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
