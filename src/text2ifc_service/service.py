"""Repeatable service orchestration for the Phase 6 supported path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from text2ifc_agent.experiments import run_phase6_case


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6-multiagent"
)
GEOMETRY_FIXTURE = (
    ROOT
    / "dataset"
    / "processed"
    / "agent-demo"
    / "geometry-gate"
    / "simple-room-fixed"
)
COMPLETE_REQUEST = (
    "请创建一个单层矩形房间，长6米、宽4米、高3米；"
    "四面墙闭合，南墙中央设置一扇宽0.9米、高2.1米的门，"
    "北墙中央设置一扇宽1.2米、高1.5米、窗台高0.9米的窗。"
)
DRAFT_REQUEST = "请创建一个单层矩形房间，长6米、高3米，但我不知道房间宽度。"


class Text2IfcServiceError(ValueError):
    """Raised when the service boundary receives an unsupported request."""


def run_text2ifc_request(
    *,
    request_id: str,
    input_text: str,
    design_brief: dict[str, Any],
    expectation: Mapping[str, Any],
    output_dir: Path | str,
    candidate: dict[str, Any] | None = None,
    raw_response: str | None = None,
) -> dict[str, Any]:
    """Run one request through the shared Phase 6 trace and gate chain."""
    return run_phase6_case(
        case_id=request_id,
        input_text=input_text,
        design_brief=design_brief,
        candidate=candidate,
        raw_response=raw_response,
        expectation=expectation,
        output_dir=output_dir,
        split="service-demo",
    )


def run_demo_scenario(
    *,
    scenario: str = "complete",
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Run a deterministic deployment scenario with an explicit expected result."""
    candidate = _read_json(GEOMETRY_FIXTURE / "candidate.json")
    expectation = _read_json(GEOMETRY_FIXTURE / "expected.json")
    if scenario == "complete":
        record = run_text2ifc_request(
            request_id="phase6-service-complete",
            input_text=COMPLETE_REQUEST,
            design_brief=_complete_brief(),
            candidate=candidate,
            expectation=expectation,
            output_dir=output_dir,
        )
        expected = (
            record["metrics"]["success"] is True
            and record["metrics"]["failure_route"] == "no_repair_needed"
        )
    elif scenario == "draft":
        record = run_text2ifc_request(
            request_id="phase6-service-draft",
            input_text=DRAFT_REQUEST,
            design_brief=_draft_brief(),
            candidate=_draft_candidate(),
            expectation=expectation,
            output_dir=output_dir,
        )
        expected = (
            record["metrics"]["bim_json_status"] == "draft"
            and record["metrics"]["failure_route"] == "draft_required"
        )
    elif scenario == "blocked":
        record = run_text2ifc_request(
            request_id="phase6-service-blocked",
            input_text=COMPLETE_REQUEST,
            design_brief=_complete_brief(),
            raw_response="{",
            expectation=expectation,
            output_dir=output_dir,
        )
        expected = (
            record["metrics"]["failure_class"] == "invalid_json"
            and record["metrics"]["failure_route"] == "blocked_failure"
        )
    else:
        raise Text2IfcServiceError(f"unsupported demo scenario: {scenario}")
    return {"scenario": scenario, "expected_outcome": expected, "record": record}


def _complete_brief() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": COMPLETE_REQUEST,
        "known_facts": {
            "storey_count": 1,
            "room": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
            "walls": {"count": 4, "enclosure": "closed"},
            "door": {
                "host": "south_wall",
                "position": "center",
                "width_mm": 900,
                "height_mm": 2100,
            },
            "window": {
                "host": "north_wall",
                "position": "center",
                "width_mm": 1200,
                "height_mm": 1500,
                "sill_height_mm": 900,
            },
        },
        "missing_facts": [],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source": "user_request"},
    }


def _draft_brief() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": DRAFT_REQUEST,
        "known_facts": {
            "storey_count": 1,
            "room": {"length_mm": 6000, "height_mm": 3000},
        },
        "missing_facts": [
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
        "clarification_questions": ["房间宽度是多少？"],
        "provenance": {"source": "user_request"},
    }


def _draft_candidate() -> dict[str, Any]:
    return {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {"room": {"length_mm": 6000, "height_mm": 3000}},
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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Text2IfcServiceError(f"expected JSON object: {path}")
    return value
