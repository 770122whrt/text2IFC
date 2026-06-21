"""Inventory local external IFC corpora without modifying source files."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_jsonfix.external_inventory import inventory_external_ifc  # noqa: E402


DEFAULT_ROOTS = (
    ROOT / "dataset" / "external" / "bim-whale-ifc-samples",
    ROOT / "dataset" / "external" / "ifc-bench",
)


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(
                value,
                temporary,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-selected-ifc2x3", type=int, default=3)
    args = parser.parse_args(argv)
    report = inventory_external_ifc(
        args.root or DEFAULT_ROOTS,
        repository_root=ROOT,
        max_selected_ifc2x3=args.max_selected_ifc2x3,
    )
    if args.output:
        _write_json_atomic(args.output, report)
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
