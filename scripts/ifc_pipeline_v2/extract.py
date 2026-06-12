"""Extract IFC2X3 into formal BIM JSON 2.0 or a Draft Envelope."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_extractor import extract_ifc2x3  # noqa: E402


def _print(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _error(code: str, message: str) -> int:
    _print({"error": {"code": code, "message": message}})
    return 2


def main() -> int:
    if len(sys.argv) != 3:
        return _error("USAGE_ERROR", "Expected INPUT.ifc OUTPUT.json.")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2]).resolve()
    try:
        result = extract_ifc2x3(source)
    except (OSError, RuntimeError, ValueError) as exc:
        code = (
            "UNSUPPORTED_SCHEMA"
            if "expected IFC2X3" in str(exc)
            else "EXTRACTION_ERROR"
        )
        return _error(code, f"{type(exc).__name__}: {exc}")

    payload = result.draft if result.draft is not None else result.document
    document_kind = "draft" if result.draft is not None else "formal"
    temporary_path: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(
                payload,
                temporary,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    except (OSError, TypeError, ValueError) as exc:
        return _error("OUTPUT_ERROR", f"{type(exc).__name__}: {exc}")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    _print(
        {
            "document_kind": document_kind,
            "inventory": result.inventory,
            "output_path": str(output),
            "source_sha256": result.source_sha256,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
