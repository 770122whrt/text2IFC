import json
from pathlib import Path

from text2ifc_agent.context_selection import select_design_brief_context
from text2ifc_agent.live_pipeline import (
    complete_room_case,
    run_design_brief_stage,
)
from text2ifc_agent.providers import LiveProviderResult, ProviderOutput


class _RecordingLiveProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.prompt = ""

    def generate_live(self, *, session_id, prompt, schema, state):
        self.prompt = prompt
        text = json.dumps(self.payload, ensure_ascii=False)
        response = {
            "id": "msg_unit_design_brief_v2",
            "type": "message",
            "role": "assistant",
            "model": "mimo-v2.5-pro",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 100, "output_tokens": 200},
        }
        return LiveProviderResult(
            session_id=session_id,
            evidence_class="unit_test_fixture",
            http_status=200,
            request={
                "model": "mimo-v2.5-pro",
                "max_tokens": 131072,
                "stream": True,
                "messages": [{"role": "user", "content": prompt}],
            },
            response=response,
            events=(
                {
                    "sequence": 0,
                    "event": "message_start",
                    "data": {"type": "message_start", "message": response},
                },
                {
                    "sequence": 1,
                    "event": "message_stop",
                    "data": {"type": "message_stop"},
                },
            ),
            output=ProviderOutput(
                text=text,
                metadata={"provider": "mimo", "session_id": session_id},
            ),
        )


def _valid_ready_brief(case: dict) -> dict:
    selection = select_design_brief_context(
        user_request=case["user_request"],
        conversation=case["conversation"],
    )
    evidence_ids = [item["evidence_id"] for item in selection["evidence"]]
    few_shot_ids = [item["few_shot_id"] for item in selection["few_shots"]]
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": case["user_request"],
        "status": "ready",
        "known_facts": {
            "space": {
                "shape": "rectangular",
                "length_mm": 6000,
                "width_mm": 4000,
                "height_mm": 3000,
            },
            "walls": {"count": 4, "enclosure": "closed", "thickness_mm": 300},
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
        "fact_sources": [
            {
                "path": "/known_facts/space",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcSpace"],
            },
            {
                "path": "/known_facts/walls",
                "source_turns": ["turn-user-001", "turn-user-003"],
                "evidence_refs": ["capability:IFC2X3:IfcWall"],
            },
            {
                "path": "/known_facts/door",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcDoor"],
            },
            {
                "path": "/known_facts/window",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["capability:IFC2X3:IfcWindow"],
            },
        ],
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [
            {
                "path": "/known_facts/walls/thickness_mm",
                "value": 300,
                "source_turn": "turn-user-003",
                "evidence_refs": ["schema:bim-json-v2:representation"],
            }
        ],
        "clarification_questions": [],
        "provenance": {
            "source_turns": [
                "turn-user-001",
                "turn-assistant-002",
                "turn-user-003",
            ],
            "selected_evidence_ids": evidence_ids,
            "few_shot_ids": few_shot_ids,
        },
    }


def test_complete_room_case_preserves_real_conversation_without_supervisor_decisions():
    case = complete_room_case()

    assert case["user_request"].startswith("请创建一个单层矩形房间")
    assert case["conversation"][-1] == {
        "turn_id": "turn-user-003",
        "role": "user",
        "content": "厚度为300毫米。",
    }
    serialized = json.dumps(case, ensure_ascii=False)
    assert "supervisor_feedback" not in serialized
    assert "门开启方向" not in serialized
    assert "窗户类型" not in serialized


def test_design_brief_stage_writes_reproducible_unedited_trace(tmp_path: Path):
    case = complete_room_case()
    payload = _valid_ready_brief(case)
    provider = _RecordingLiveProvider(payload)

    result = run_design_brief_stage(
        provider=provider,
        output_dir=tmp_path,
        case=case,
    )

    expected_files = {
        "input.txt",
        "conversation.json",
        "context-selection.json",
        "prompt-render-input.json",
        "prompt-rendered.md",
        "request.redacted.json",
        "response.raw.json",
        "response-metadata.json",
        "events.jsonl",
        "model-text.txt",
        "design-brief.json",
        "validation.json",
        "metrics.json",
        "trace-manifest.json",
    }
    assert expected_files <= {path.name for path in tmp_path.iterdir()}
    assert json.loads((tmp_path / "design-brief.json").read_text(encoding="utf-8")) == payload
    assert (tmp_path / "model-text.txt").read_text(encoding="utf-8") == json.dumps(
        payload, ensure_ascii=False
    )
    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert validation == {"issue_count": 0, "issues": [], "valid": True}
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["parse_valid"] is True
    assert metrics["schema_semantic_valid"] is True
    assert metrics["response_id"] == "msg_unit_design_brief_v2"
    assert metrics["stop_reason"] == "end_turn"
    assert result["status"] == "ready"
    assert "supervisor_feedback" not in provider.prompt
    assert "text2ifc/design-brief/2.0" in provider.prompt


def test_design_brief_stage_records_invalid_model_output_without_editing_it(tmp_path: Path):
    case = complete_room_case()
    payload = _valid_ready_brief(case)
    payload["schema_version"] = "text2ifc/design-brief/9.9"
    provider = _RecordingLiveProvider(payload)

    result = run_design_brief_stage(
        provider=provider,
        output_dir=tmp_path,
        case=case,
    )

    assert result["status"] == "blocked_prompt_defect"
    assert not (tmp_path / "design-brief.json").exists()
    assert json.loads((tmp_path / "parsed-output.json").read_text(encoding="utf-8")) == payload
    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert validation["valid"] is False
    assert validation["issues"][0]["code"] == "UNSUPPORTED_DESIGN_BRIEF_VERSION"
