"""Scripted clarification demo skeleton for Phase 5 RED tests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_agent.session import AgentConfig, AgentSession  # noqa: E402
from text2ifc_agent.state import MissingFact  # noqa: E402
from text2ifc_compiler import compile_document  # noqa: E402
from text2ifc_contract.validation_v2 import validate_v2_document  # noqa: E402


DEFAULT_OUTPUT_DIR = ROOT / "dataset" / "processed" / "agent-demo" / "simple-room"
DEFAULT_REQUEST = "请帮我创建一个单层矩形房间，包含四面墙、一扇门和一扇窗。"
SCRIPTED_ANSWERS = {
    "mf-room-size": "房间长 6 米，宽 4 米，高 3 米。",
    "mf-door-position": "门在南侧墙中间，宽 0.9 米，高 2.1 米，底部贴地。",
    "mf-window-position": "窗在北侧墙中间，宽 1.2 米，高 1.5 米，窗台高 0.9 米。",
}


def run_demo(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    check: bool = False,
    force_invalid: bool = False,
) -> dict[str, Any]:
    del check
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate = (
        {"schema_version": "bim-json/2.0"}
        if force_invalid
        else build_simple_room_candidate()
    )
    session = AgentSession.start(
        user_text=DEFAULT_REQUEST,
        config=AgentConfig(language="zh-CN", max_questions=3),
        candidate_document=candidate,
        missing_facts=_initial_missing_facts(),
    )
    questions = session.next_questions()
    question_text = "\n".join(fact.question_zh for fact in questions)
    session = replace(
        session,
        state=session.state.append_question_turn(
            question_text,
            [fact.id for fact in questions],
        ),
    )
    answers = {
        fact.id: SCRIPTED_ANSWERS[fact.id]
        for fact in questions
        if fact.id in SCRIPTED_ANSWERS
    }
    session = session.apply_answers(answers)

    issues = validate_v2_document(candidate)
    validation = {
        "stage": "ok" if not issues else "validation",
        "issues": [_issue_payload(issue) for issue in issues],
    }
    diagnostics: dict[str, Any] = {
        "validation": validation,
        "compiled_ifc": {"attempted": False, "success": False, "reopen_success": False},
    }

    success = False
    if not issues and session.current_status().value == "formal_ready":
        output_ifc = output / "output.ifc"
        compilation = compile_document(candidate, output_ifc)
        success = compilation.success
        diagnostics["compiled_ifc"] = {
            "attempted": True,
            "success": compilation.success,
            "reopen_success": compilation.success,
            "output_path": _artifact_path(output_ifc) if compilation.success else None,
            "issues": _compiler_issues(compilation),
        }

    _write_artifacts(
        output=output,
        session=session,
        candidate=candidate,
        diagnostics=diagnostics,
        success=success,
    )
    return {
        "success": success,
        "state": session.state.to_dict(),
        "diagnostics": diagnostics,
    }


def _initial_missing_facts() -> list[MissingFact]:
    return [
        MissingFact(
            id="mf-room-size",
            code="MISSING_ROOM_SIZE",
            path="/entities/space-1/attributes/Representation",
            question_zh="房间的长、宽、高分别是多少？",
            source="agent",
            rationale="simple-room demo requires explicit room dimensions",
        ),
        MissingFact(
            id="mf-door-position",
            code="MISSING_DOOR_POSITION",
            path="/entities/door-1/attributes/ObjectPlacement",
            question_zh="门位于哪面墙上？门洞的水平位置和底部高度是多少？",
            source="agent",
            rationale="door placement must be explicit",
        ),
        MissingFact(
            id="mf-window-position",
            code="MISSING_WINDOW_POSITION",
            path="/entities/window-1/attributes/ObjectPlacement",
            question_zh="窗位于哪面墙上？窗的水平位置、窗台高度和尺寸是多少？",
            source="agent",
            rationale="window placement must be explicit",
        ),
    ]


def build_simple_room_candidate() -> dict[str, Any]:
    return {
        "schema_version": "bim-json/2.0",
        "ifc_schema": "IFC2X3",
        "units": {"length": "MILLIMETRE"},
        "entities": [
            _entity("project-1", "IfcProject", {"Name": "Text2IFC Demo Project"}),
            _entity(
                "site-1",
                "IfcSite",
                {"Name": "Site", "ObjectPlacement": _placement("project-1")},
            ),
            _entity(
                "building-1",
                "IfcBuilding",
                {"Name": "Building", "ObjectPlacement": _placement("site-1")},
            ),
            _entity(
                "storey-1",
                "IfcBuildingStorey",
                {
                    "Name": "Level 1",
                    "Elevation": 0,
                    "ObjectPlacement": _placement("building-1"),
                },
            ),
            _entity(
                "space-1",
                "IfcSpace",
                {
                    "Name": "Room",
                    "InteriorOrExteriorSpace": "INTERNAL",
                    "ObjectPlacement": _placement("storey-1", [0, 0, 0]),
                    "Representation": _polygon_representation(
                        [[0, 0], [6000, 0], [6000, 4000], [0, 4000], [0, 0]],
                        3000,
                    ),
                },
            ),
            _wall("wall-south", [0, 0, 0], 6000),
            _wall("wall-north", [0, 4000, 0], 6000),
            _wall("wall-west", [0, 0, 0], 4000),
            _wall("wall-east", [6000, 0, 0], 4000),
            _opening("opening-door-1", "wall-south", [2550, 0, 0], 900, 2100),
            _entity(
                "door-1",
                "IfcDoor",
                {
                    "Name": "Door",
                    "OverallWidth": 900,
                    "OverallHeight": 2100,
                    "ObjectPlacement": _placement("opening-door-1"),
                    "Representation": _rectangle_representation(900, 100, 2100),
                },
            ),
            _opening("opening-window-1", "wall-north", [2400, 0, 900], 1200, 1500),
            _entity(
                "window-1",
                "IfcWindow",
                {
                    "Name": "Window",
                    "OverallWidth": 1200,
                    "OverallHeight": 1500,
                    "ObjectPlacement": _placement("opening-window-1"),
                    "Representation": _rectangle_representation(1200, 100, 1500),
                },
            ),
        ],
        "relationships": [
            _relationship(
                "void-door-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-south",
                    "RelatedOpeningElement": "opening-door-1",
                },
            ),
            _relationship(
                "fill-door-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-door-1",
                    "RelatedBuildingElement": "door-1",
                },
            ),
            _relationship(
                "void-window-1",
                "IfcRelVoidsElement",
                {
                    "RelatingBuildingElement": "wall-north",
                    "RelatedOpeningElement": "opening-window-1",
                },
            ),
            _relationship(
                "fill-window-1",
                "IfcRelFillsElement",
                {
                    "RelatingOpeningElement": "opening-window-1",
                    "RelatedBuildingElement": "window-1",
                },
            ),
        ],
        "provenance": {"source": "phase-5-scripted-demo"},
    }


def _entity(entity_id: str, ifc_class: str, attributes: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "phase-5-scripted-demo"},
    }


def _relationship(
    relationship_id: str, ifc_class: str, attributes: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": relationship_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "provenance": {"source": "phase-5-scripted-demo"},
    }


def _placement(relative_to: str, origin: list[float] | None = None) -> dict[str, Any]:
    return {
        "relative_to": relative_to,
        "origin": origin or [0, 0, 0],
        "axis": [0, 0, 1],
        "ref_direction": [1, 0, 0],
    }


def _rectangle_representation(x: float, y: float, depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "rectangle", "x": x, "y": y},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _polygon_representation(points: list[list[float]], depth: float) -> dict[str, Any]:
    return {
        "kind": "extruded_profile",
        "profile": {"kind": "polygon", "points": points},
        "depth": depth,
        "direction": [0, 0, 1],
    }


def _wall(entity_id: str, origin: list[float], length: float) -> dict[str, Any]:
    return _entity(
        entity_id,
        "IfcWall",
        {
            "Name": entity_id,
            "ObjectPlacement": _placement("storey-1", origin),
            "Representation": _rectangle_representation(length, 200, 3000),
        },
    )


def _opening(
    entity_id: str,
    wall_id: str,
    origin: list[float],
    width: float,
    height: float,
) -> dict[str, Any]:
    return _entity(
        entity_id,
        "IfcOpeningElement",
        {
            "Name": entity_id,
            "ObjectPlacement": _placement(wall_id, origin),
            "Representation": _rectangle_representation(width, 200, height),
        },
    )


def _issue_payload(issue: Any) -> dict[str, Any]:
    return {"code": issue.code, "path": issue.path, "message": issue.message}


def _compiler_issues(compilation: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for issue in getattr(compilation, "input_issues", ()):
        issues.append(_issue_payload(issue))
    for issue in getattr(compilation, "ifc_issues", ()):
        issues.append(
            {
                "code": issue.code,
                "path": f"{issue.entity}/{issue.attribute}",
                "message": issue.message,
            }
        )
    return issues


def _write_artifacts(
    *,
    output: Path,
    session: AgentSession,
    candidate: dict[str, Any],
    diagnostics: dict[str, Any],
    success: bool,
) -> None:
    state = session.state.to_dict()
    transcript = {
        "schema_version": "text2ifc/agent-transcript-v1",
        "turns": state["transcript"],
    }
    metrics = {
        "schema_version": "text2ifc/agent-demo-metrics-v1",
        "turn_count": len(state["transcript"]),
        "asked_question_count": sum(
            len(turn["question_ids"])
            for turn in state["transcript"]
            if turn["role"] == "agent"
        ),
        "final_status": state["status"],
        "validation_status": diagnostics["validation"]["stage"],
        "compile_success": diagnostics["compiled_ifc"]["success"],
    }
    _write_json(output / "transcript.json", transcript)
    _write_json(output / "state.json", state)
    _write_json(output / "candidate.json", candidate)
    _write_json(output / "diagnostics.json", diagnostics)
    _write_json(output / "metrics.json", metrics)
    _write_report(output / "report.md", success, diagnostics, metrics)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_report(
    path: Path,
    success: bool,
    diagnostics: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    lines = [
        "# Phase 5 Clarification Demo Report",
        "",
        f"- Success: {success}",
        f"- Final status: {metrics['final_status']}",
        f"- Turns: {metrics['turn_count']}",
        f"- Asked questions: {metrics['asked_question_count']}",
        f"- Validation: {diagnostics['validation']['stage']}",
        f"- Compile attempted: {diagnostics['compiled_ifc']['attempted']}",
        f"- Compile success: {diagnostics['compiled_ifc']['success']}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _artifact_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


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
