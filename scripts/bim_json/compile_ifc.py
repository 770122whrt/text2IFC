import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_compiler import compile_document
from text2ifc_contract import loads_strict_json
from text2ifc_contract.validation import ValidationIssue


MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_ERRORS = 1000


def _write_payload(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")


def _input_issue(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, path="/", message=message)


def _input_error_payload(issue: ValidationIssue) -> dict[str, str]:
    return {
        "code": issue.code,
        "path": issue.path,
        "message": issue.message,
    }


def _ifc_error_payload(issue: Any) -> dict[str, str]:
    return {
        "code": issue.code,
        "entity": issue.entity,
        "attribute": issue.attribute,
        "message": issue.message,
    }


def _result_payload(
    *,
    success: bool,
    output_path: Path | None = None,
    schema: str | None = None,
    input_issues: tuple[ValidationIssue, ...] = (),
    ifc_issues: tuple[Any, ...] = (),
) -> dict[str, Any]:
    return {
        "success": success,
        "output_path": str(output_path) if output_path is not None else None,
        "schema": schema,
        "input_errors": [
            _input_error_payload(issue)
            for issue in input_issues[:MAX_ERRORS]
        ],
        "ifc_errors": [
            _ifc_error_payload(issue) for issue in ifc_issues[:MAX_ERRORS]
        ],
    }


def _load_document(path: Path) -> Any:
    size = path.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ValueError(
            f"FILE_TOO_LARGE:{size} bytes exceeds the "
            f"{MAX_INPUT_BYTES} byte limit."
        )
    return loads_strict_json(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        _write_payload(
            _result_payload(
                success=False,
                input_issues=(
                    _input_issue(
                        "USAGE_ERROR",
                        "Expected input JSON and output IFC paths.",
                    ),
                ),
            )
        )
        return 2

    source = Path(args[0])
    output = Path(args[1])
    if source.resolve() == output.resolve():
        _write_payload(
            _result_payload(
                success=False,
                input_issues=(
                    _input_issue(
                        "PATH_CONFLICT",
                        "Input and output paths must differ.",
                    ),
                ),
            )
        )
        return 2

    try:
        document = _load_document(source)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("FILE_TOO_LARGE:"):
            code = "FILE_TOO_LARGE"
            message = message.removeprefix("FILE_TOO_LARGE:")
        else:
            code = "INVALID_JSON"
        _write_payload(
            _result_payload(
                success=False,
                input_issues=(_input_issue(code, message),),
            )
        )
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _write_payload(
            _result_payload(
                success=False,
                input_issues=(
                    _input_issue("INVALID_JSON", str(exc)),
                ),
            )
        )
        return 2

    result = compile_document(document, output)
    payload = _result_payload(
        success=result.success,
        output_path=result.output_path,
        schema=document.get("target_schema") if result.success else None,
        input_issues=result.input_issues,
        ifc_issues=result.ifc_issues,
    )
    _write_payload(payload)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
