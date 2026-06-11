import json
import sys
from typing import Any


def _write_payload(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    del argv
    _write_payload(
        {
            "success": False,
            "output_path": None,
            "schema": None,
            "input_errors": [
                {
                    "code": "NOT_IMPLEMENTED",
                    "path": "/",
                    "message": "Compiler CLI is not implemented.",
                }
            ],
            "ifc_errors": [],
        }
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

