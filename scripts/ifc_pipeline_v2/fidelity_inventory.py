from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_fidelity import build_fidelity_inventory  # noqa: E402


DEFAULT_MANIFEST = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
DEFAULT_SPLITS = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"
DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "phase4" / "fidelity-inventory.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    if not arguments.all:
        parser.error("Only --all is supported for Phase 4 inventory.")

    inventory = build_fidelity_inventory(arguments.manifest, arguments.splits)
    issues = _check_inventory(inventory) if arguments.check else []
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    _write_json(arguments.output, inventory)
    print(
        json.dumps(
            {
                "success": not issues,
                "output": str(arguments.output),
                "record_count": len(inventory["records"]),
                "issues": issues,
            },
            sort_keys=True,
        )
    )
    return 0 if not issues else 1


def _check_inventory(inventory: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if inventory["counts"]["files"]["total"] != 25:
        issues.append(
            {
                "code": "UNEXPECTED_FILE_COUNT",
                "path": "/counts/files/total",
                "message": "Expected 25 authorized BIMNet IFC2X3 files.",
            }
        )
    for index, record in enumerate(inventory["records"]):
        if not record.get("sha256_verified"):
            issues.append(
                {
                    "code": "SHA256_NOT_VERIFIED",
                    "path": f"/records/{index}/sha256",
                    "message": f"SHA-256 was not verified for {record['id']}.",
                }
            )
    return issues


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
