"""Create an immutable damaged IFC Window-repair case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from text2ifc_ifc_repair.mutation import remove_window_and_opening


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--wall-id", required=True)
    parser.add_argument("--opening-id", required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--expected-source-sha256")
    arguments = parser.parse_args()
    result = remove_window_and_opening(
        source_path=arguments.source,
        output_dir=arguments.output,
        wall_global_id=arguments.wall_id,
        opening_global_id=arguments.opening_id,
        window_global_id=arguments.window_id,
        expected_source_sha256=arguments.expected_source_sha256,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
