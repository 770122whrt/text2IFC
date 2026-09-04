"""Audit generated Source IFC manifests without mutating dataset files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.source_manifests import validate_records


FILES_PATH = ROOT / "dataset" / "manifests" / "ifc-files.jsonl"


def main() -> int:
    if not FILES_PATH.is_file():
        raise SystemExit("MISSING_IFC_FILES_MANIFEST")
    records = [json.loads(line) for line in FILES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    validate_records(records, ROOT)
    print(json.dumps({"valid": True, "record_count": len(records)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
