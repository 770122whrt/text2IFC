"""Scan Agent demo artifacts for persisted secret-like values."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.artifact_scan import scan_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    arguments = parser.parse_args()
    result = scan_path(arguments.path)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
