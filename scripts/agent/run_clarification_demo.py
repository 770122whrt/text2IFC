"""Scripted clarification demo skeleton for Phase 5 RED tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))


DEFAULT_OUTPUT_DIR = ROOT / "dataset" / "processed" / "agent-demo" / "simple-room"
DEFAULT_REQUEST = "请帮我创建一个单层矩形房间，包含四面墙、一扇门和一扇窗。"


def run_demo(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    check: bool = False,
    force_invalid: bool = False,
) -> dict[str, Any]:
    del check, force_invalid
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "diagnostics.json").write_text(
        json.dumps({"compiled_ifc": {"attempted": False}}, sort_keys=True),
        encoding="utf-8",
    )
    return {"success": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    result = run_demo(output_dir=arguments.output_dir, check=arguments.check)
    print(json.dumps({"success": result["success"]}, sort_keys=True))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
