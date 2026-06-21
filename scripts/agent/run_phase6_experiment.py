from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from run_geometry_gate_demo import _case  # noqa: E402
from text2ifc_agent.experiments import run_phase6_case, run_phase6_matrix  # noqa: E402


DEFAULT_OUTPUT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6-multiagent"
DEFAULT_MATRIX_OUTPUT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6-experiment-matrix"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    case = _case("simple-room-fixed")
    output_dir = args.output_dir or (
        DEFAULT_MATRIX_OUTPUT if args.matrix else DEFAULT_OUTPUT
    )
    if args.matrix:
        summary = run_phase6_matrix(cases=_matrix_cases(case), output_dir=output_dir)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        expected_routes = {
            "no_repair_needed",
            "draft_required",
            "repair_attempted",
            "blocked_failure",
        }
        expected_classes = {
            "success",
            "draft",
            "invalid_bim_json",
            "invalid_json",
            "audit_mismatch",
        }
        valid = (
            set(summary["failure_routes"]) == expected_routes
            and set(summary["failure_classes"]) == expected_classes
        )
        return 0 if valid or not args.check else 2

    input_text = _complete_request()
    design_brief = _design_brief(input_text)
    record = run_phase6_case(
        case_id="simple-room-fixed",
        input_text=input_text,
        design_brief=design_brief,
        candidate=case["candidate"],
        expectation=case["expected"],
        output_dir=output_dir,
    )
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0 if record["metrics"]["success"] or not args.check else 2


def _complete_request() -> str:
    return (
        "创建一个单层矩形房间，长6米、宽4米、高3米；"
        "四面墙闭合，南墙中央有门，北墙中央有窗。"
    )


def _design_brief(input_text: str, *, include_width: bool = True) -> dict:
    room = {"length_mm": 6000, "height_mm": 3000}
    if include_width:
        room["width_mm"] = 4000
    return {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": input_text,
        "known_facts": {
            "storey_count": 1,
            "room": room,
            "walls": {"count": 4, "enclosure": "closed"},
            "door": {"host": "south_wall", "position": "center"},
            "window": {"host": "north_wall", "position": "center"},
        },
        "missing_facts": []
        if include_width
        else [
            {
                "id": "room-width",
                "code": "ROOM_WIDTH_MISSING",
                "path": "/room/width_mm",
                "message": "缺少房间宽度。",
                "source": "user_request",
            }
        ],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source": "user_request"},
    }


def _draft_candidate() -> dict:
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {"room": {}},
        "missing_facts": [
            {
                "entity_id": "space-1",
                "path": "/room/width_mm",
                "code": "ROOM_WIDTH_MISSING",
                "message": "缺少房间宽度。",
            }
        ],
        "losses": [],
        "clarification_targets": [
            {
                "entity_id": "space-1",
                "path": "/room/width_mm",
                "question": "房间宽度是多少？",
            }
        ],
        "provenance": {"source": "provider"},
    }


def _matrix_cases(case: dict) -> list[dict]:
    complete = _complete_request()
    return [
        {
            "case_id": "success",
            "input_text": complete,
            "design_brief": _design_brief(complete),
            "candidate": case["candidate"],
            "expectation": case["expected"],
        },
        {
            "case_id": "draft",
            "input_text": "创建一个房间，但我不知道宽度。",
            "design_brief": _design_brief(
                "创建一个房间，但我不知道宽度。",
                include_width=False,
            ),
            "candidate": _draft_candidate(),
            "expectation": case["expected"],
        },
        {
            "case_id": "repair",
            "input_text": complete,
            "design_brief": _design_brief(complete),
            "candidate": {"schema_version": "bim-json/2.0"},
            "expectation": case["expected"],
        },
        {
            "case_id": "blocked",
            "input_text": complete,
            "design_brief": _design_brief(complete),
            "raw_response": "{",
            "expectation": case["expected"],
        },
        {
            "case_id": "audit",
            "input_text": complete,
            "design_brief": _design_brief(complete),
            "candidate": case["candidate"],
            "expectation": case["expected"],
            "audit_mismatches": [
                {
                    "code": "USER_INTENT_MISMATCH",
                    "message": "生成结果与用户意图不一致。",
                }
            ],
        },
    ]


if __name__ == "__main__":
    raise SystemExit(main())
