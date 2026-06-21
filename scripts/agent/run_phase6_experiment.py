from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from run_geometry_gate_demo import _case  # noqa: E402
from text2ifc_agent.experiments import run_phase6_case  # noqa: E402


DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6-multiagent"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    case = _case("simple-room-fixed")
    input_text = "创建一个单层矩形房间，长6米、宽4米、高3米；四面墙闭合，南墙中央有门，北墙中央有窗。"
    design_brief = {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": input_text,
        "known_facts": {
            "storey_count": 1,
            "room": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
            "walls": {"count": 4, "enclosure": "closed"},
            "door": {"host": "south_wall", "position": "center"},
            "window": {"host": "north_wall", "position": "center"},
        },
        "missing_facts": [], "ambiguities": [], "user_corrections": [],
        "clarification_questions": [], "provenance": {"source": "user_request"},
    }
    record = run_phase6_case(
        case_id="simple-room-fixed", input_text=input_text, design_brief=design_brief,
        candidate=case["candidate"], expectation=case["expected"], output_dir=args.output_dir,
    )
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0 if record["metrics"]["success"] or not args.check else 2


if __name__ == "__main__":
    raise SystemExit(main())
