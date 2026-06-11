"""Migrate one valid BIM JSON 1.0 file to a loss-explicit Draft Envelope."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_contract import loads_strict_json  # noqa: E402
from text2ifc_contract.migration_v2 import migrate_v1_document  # noqa: E402
from text2ifc_contract.validation import validate_document  # noqa: E402


MAX_INPUT_BYTES = 10 * 1024 * 1024


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps({"success": False, "code": "USAGE_ERROR"}))
        return 2
    source_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    if source_path == output_path:
        print(json.dumps({"success": False, "code": "PATH_CONFLICT"}))
        return 2
    try:
        if source_path.stat().st_size > MAX_INPUT_BYTES:
            raise OverflowError("input exceeds 10 MiB")
        document = loads_strict_json(source_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, OverflowError) as exc:
        print(json.dumps({"success": False, "code": "INVALID_INPUT", "message": str(exc)}))
        return 2
    issues = validate_document(document)
    if issues:
        print(json.dumps({"success": False, "code": "INVALID_V1_DOCUMENT"}))
        return 1
    draft = migrate_v1_document(document, str(source_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(draft, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(
        json.dumps(
            {"success": True, "output_path": str(output_path)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
