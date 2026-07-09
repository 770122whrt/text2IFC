"""Build Phase 6.4 chain correctness and completeness evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.chain_completeness import build_chain_completeness  # noqa: E402


DEFAULT_LIVE_ROOT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-live-deepseek"
DEFAULT_MATRIX_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-feedback-routing-matrix"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-root", type=Path, default=DEFAULT_LIVE_ROOT)
    parser.add_argument("--matrix-root", type=Path, default=DEFAULT_MATRIX_ROOT)
    args = parser.parse_args(argv)

    result = build_chain_completeness(live_root=args.live_root, matrix_root=args.matrix_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["overall_status"] == "phase6_4_evidence_complete_with_boundaries" else 2


if __name__ == "__main__":
    raise SystemExit(main())
