"""Build the Phase 6.4 supplemental live chain coverage report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.live_chain_coverage import build_live_chain_coverage  # noqa: E402


DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-live-deepseek"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--accepted-session-hash", required=True)
    parser.add_argument("--nonaccept-session-hash", required=True)
    args = parser.parse_args(argv)

    result = build_live_chain_coverage(
        output_root=args.output_root,
        accepted_session_hash=args.accepted_session_hash,
        nonaccept_session_hash=args.nonaccept_session_hash,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["all_required_links_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
