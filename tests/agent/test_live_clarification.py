import inspect

import pytest

from text2ifc_agent.clarification import (
    ClarificationCall,
    ClarificationController,
    ClarificationError,
)


EVIDENCE = [
    {"evidence_id": "schema:bim-json-v2:representation"},
    {"evidence_id": "capability:IFC2X3:IfcSpace"},
    {"evidence_id": "capability:IFC2X3:IfcWall"},
]
REQUEST = "请创建一个长6米、宽4米、高3米的单层矩形房间，四面墙闭合。"


def _brief(*, status="needs_clarification", source_turns=None):
    source_turns = source_turns or ["turn-user-001"]
    blocker = {
        "id": "mf-wall-thickness",
        "code": "WALL_THICKNESS_MISSING",
        "path": "/known_facts/walls/thickness_mm",
        "message": "墙体厚度尚未提供。",
        "reason": "生成用户要求的实体墙体需要明确厚度。",
        "blocking": True,
        "evidence_refs": ["schema:bim-json-v2:representation"],
        "source_turns": ["turn-user-001"],
    }
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": REQUEST,
        "status": status,
        "known_facts": {
            "space": {
                "length_mm": 6000,
                "width_mm": 4000,
                "height_mm": 3000,
            },
            "walls": {"count": 4, "enclosure": "closed"},
        },
        "fact_sources": [
            {
                "path": "/known_facts",
                "source_turns": source_turns,
                "evidence_refs": ["capability:IFC2X3:IfcSpace"],
            }
        ],
        "missing_facts": [blocker] if status != "ready" else [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [],
        "clarification_questions": (
            [
                {
                    "id": "q-wall-thickness",
                    "text": "请问墙体厚度是多少毫米？",
                    "targets": ["mf-wall-thickness"],
                    "reason": "缺少厚度时不能生成所要求的实体墙体。",
                    "evidence_refs": ["schema:bim-json-v2:representation"],
                }
            ]
            if status == "needs_clarification"
            else []
        ),
        "provenance": {
            "source_turns": source_turns,
            "selected_evidence_ids": [
                "schema:bim-json-v2:representation",
                "capability:IFC2X3:IfcSpace",
                "capability:IFC2X3:IfcWall",
            ],
            "few_shot_ids": [],
        },
    }


def _call(index, brief, response_id=None):
    return ClarificationCall(
        call_index=index,
        response_id=response_id or f"msg_live_{index}",
        prompt_template_id="design-brief.v2.1",
        prompt_template_hash="sha256:prompt-v2.1",
        artifact_dir=f"calls/{index:02d}-design-brief",
        brief=brief,
        evidence_catalog=EVIDENCE,
    )


def test_controller_preserves_agent_authored_questions_without_legacy_planner(
    monkeypatch,
):
    def forbidden_planner(*args, **kwargs):
        raise AssertionError("legacy plan_questions must not be called")

    monkeypatch.setattr(
        "text2ifc_agent.questions.plan_questions",
        forbidden_planner,
    )
    controller = ClarificationController.start(
        case_id="clarified-room",
        user_request=REQUEST,
    )

    updated = controller.record_model_call(_call(1, _brief()))

    assert [turn.role for turn in updated.transcript] == ["user", "assistant"]
    assert updated.transcript[1].content == "请问墙体厚度是多少毫米？"
    assert updated.transcript[1].question_ids == ("q-wall-thickness",)
    assert updated.status == "needs_clarification"
    assert "plan_questions" not in inspect.getsource(ClarificationController)


def test_each_raw_user_answer_is_appended_then_triggers_exactly_one_new_call():
    controller = ClarificationController.start(
        case_id="clarified-room",
        user_request=REQUEST,
    ).record_model_call(_call(1, _brief()))
    observed = []

    def invoke(transcript, call_index):
        observed.append((transcript, call_index))
        return _call(
            2,
            _brief(
                status="ready",
                source_turns=["turn-user-001", "turn-user-003"],
            ),
        )

    updated = controller.answer_and_rerun(
        answer="墙体厚度为300毫米。",
        invoke_design_brief=invoke,
    )

    assert len(observed) == 1
    transcript, call_index = observed[0]
    assert call_index == 2
    assert [turn["turn_id"] for turn in transcript] == [
        "turn-user-001",
        "turn-assistant-002",
        "turn-user-003",
    ]
    assert transcript[-1]["content"] == "墙体厚度为300毫米。"
    assert [turn.content for turn in updated.transcript] == [
        REQUEST,
        "请问墙体厚度是多少毫米？",
        "墙体厚度为300毫米。",
    ]
    assert updated.status == "ready"
    assert [call.response_id for call in updated.calls] == [
        "msg_live_1",
        "msg_live_2",
    ]


def test_unknown_answer_remains_raw_and_model_draft_is_preserved():
    controller = ClarificationController.start(
        case_id="unknown-room",
        user_request=REQUEST,
    ).record_model_call(_call(1, _brief()))

    def invoke(transcript, call_index):
        assert transcript[-1]["content"] == "这个厚度我不知道。"
        return _call(
            call_index,
            _brief(
                status="draft_required",
                source_turns=["turn-user-001", "turn-user-003"],
            ),
        )

    updated = controller.answer_and_rerun(
        answer="这个厚度我不知道。",
        invoke_design_brief=invoke,
    )

    assert updated.status == "draft_required"
    assert updated.transcript[-1].content == "这个厚度我不知道。"
    assert updated.calls[-1].brief["known_facts"]["walls"] == {
        "count": 4,
        "enclosure": "closed",
    }


def test_controller_rejects_source_turn_not_present_in_immutable_transcript():
    controller = ClarificationController.start(
        case_id="clarified-room",
        user_request=REQUEST,
    )
    brief = _brief(source_turns=["turn-user-999"])

    with pytest.raises(ClarificationError, match="turn-user-999"):
        controller.record_model_call(_call(1, brief))


def test_controller_rejects_model_question_without_valid_target_or_evidence():
    controller = ClarificationController.start(
        case_id="clarified-room",
        user_request=REQUEST,
    )
    brief = _brief()
    brief["clarification_questions"][0]["targets"] = ["not-a-blocker"]

    with pytest.raises(ClarificationError, match="UNKNOWN_CLARIFICATION_TARGET"):
        controller.record_model_call(_call(1, brief))
