"""Mimo provider smoke skeleton for Phase 5 RED tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.providers import load_mimo_config_from_env  # noqa: E402


def main() -> int:
    if "--check-config" in sys.argv:
        print(json.dumps(load_mimo_config_from_env(), sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
