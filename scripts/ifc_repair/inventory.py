"""Inspect the frozen IFC repair sample and target chain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from text2ifc_ifc_repair.sample import (
    inspect_sample,
    inspect_sample_capabilities,
    inspect_target_chain,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--wall-id", required=True)
    parser.add_argument("--opening-id", required=True)
    parser.add_argument("--window-id", required=True)
    arguments = parser.parse_args()
    payload = {
        "sample": inspect_sample(arguments.source),
        "capabilities": inspect_sample_capabilities(arguments.source),
        "target": inspect_target_chain(
            arguments.source,
            wall_global_id=arguments.wall_id,
            opening_global_id=arguments.opening_id,
            window_global_id=arguments.window_id,
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
