import json

from text2ifc_agent.state import (
    AcceptedFact,
    AgentState,
    AgentStatus,
    MissingFact,
    redact_metadata,
)


def test_start_preserves_original_chinese_request_and_first_transcript_turn():
    request = "我想要一个单层矩形房间，需要一扇门和一扇窗。"

    state = AgentState.start(request)

    assert state.schema_version == "text2ifc/agent-state-v1"
    assert state.language == "zh-CN"
    assert state.status == AgentStatus.DRAFT
    assert state.original_request == request
    assert len(state.transcript) == 1
    assert state.transcript[0].role == "user"
    assert state.transcript[0].content == request
    assert state.transcript[0].question_ids == []


def test_missing_facts_are_stable_addressable_and_make_state_need_clarification():
    fact = MissingFact(
        id="mf-room-size",
        code="MISSING_ROOM_SIZE",
        path="/entities/room-1/attributes/Representation",
        question_zh="房间的长、宽、高分别是多少？",
        source="validator",
        rationale="生成房间和墙体需要明确尺寸。",
    )

    state = AgentState.start("建一个矩形房间。").with_missing_facts([fact])
    payload = state.to_dict()

    assert state.status == AgentStatus.NEEDS_CLARIFICATION
    assert payload["missing_facts"] == [
        {
            "id": "mf-room-size",
            "code": "MISSING_ROOM_SIZE",
            "path": "/entities/room-1/attributes/Representation",
            "question_zh": "房间的长、宽、高分别是多少？",
            "status": "open",
            "source": "validator",
            "rationale": "生成房间和墙体需要明确尺寸。",
        }
    ]


def test_status_values_cover_draft_clarification_formal_ready_and_compiled():
    assert {status.value for status in AgentStatus} == {
        "draft",
        "needs_clarification",
        "formal_ready",
        "compiled",
    }


def test_question_and_answer_turns_preserve_prior_transcript_order():
    state = (
        AgentState.start("做一个小房间。")
        .append_question_turn("房间的长、宽、高分别是多少？", ["mf-room-size"])
        .append_user_answer("长 6 米，宽 4 米，高 3 米。", ["mf-room-size"])
    )

    assert [turn.role for turn in state.transcript] == ["user", "agent", "user"]
    assert [turn.content for turn in state.transcript] == [
        "做一个小房间。",
        "房间的长、宽、高分别是多少？",
        "长 6 米，宽 4 米，高 3 米。",
    ]
    assert state.transcript[1].question_ids == ["mf-room-size"]
    assert state.transcript[2].question_ids == ["mf-room-size"]


def test_accepted_facts_append_without_overwriting_original_request():
    state = AgentState.start("我需要一个会议室。")
    state = state.append_accepted_fact(
        AcceptedFact(
            id="fact-room-size",
            source_question_id="mf-room-size",
            path="/rooms/0/size",
            value={"length": 6000, "width": 4000, "height": 3000},
            raw_answer="长 6 米，宽 4 米，高 3 米。",
        )
    )

    assert state.original_request == "我需要一个会议室。"
    assert len(state.accepted_facts) == 1
    assert state.accepted_facts[0].value == {
        "length": 6000,
        "width": 4000,
        "height": 3000,
    }


def test_serialization_is_deterministic_json():
    state = AgentState.start("建一个矩形房间。").append_question_turn(
        "房间的长、宽、高分别是多少？", ["mf-room-size"]
    )

    first = state.to_json()
    second = state.to_json()

    assert first == second
    assert json.loads(first)["schema_version"] == "text2ifc/agent-state-v1"
    assert first.endswith("\n")


def test_redaction_removes_secret_values_but_preserves_environment_variable_names():
    metadata = {
        "provider": "mimo",
        "env": ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"],
        "headers": {
            "authorization": "test-secret-value",
            "x-api-key": "another-secret-value",
        },
        "base_url": "https://example.invalid/private-endpoint",
        "nested": {"token": "sensitive-token-value"},
    }

    redacted = redact_metadata(metadata)
    rendered = json.dumps(redacted, ensure_ascii=False, sort_keys=True)

    assert "ANTHROPIC_AUTH_TOKEN" in rendered
    assert "ANTHROPIC_BASE_URL" in rendered
    assert "test-secret-value" not in rendered
    assert "another-secret-value" not in rendered
    assert "sensitive-token-value" not in rendered
    assert "https://example.invalid/private-endpoint" not in rendered
    assert redacted["headers"]["authorization"] == "[REDACTED]"
    assert redacted["headers"]["x-api-key"] == "[REDACTED]"


def test_redaction_preserves_numeric_token_counters_but_not_credentials():
    metadata = {
        "max_tokens": 131072,
        "input_tokens": 70,
        "output_tokens": 28,
        "cache_read_input_tokens": 192,
        "token": "sensitive-token-value",
        "auth_token": "another-sensitive-value",
    }

    redacted = redact_metadata(metadata)

    assert redacted["max_tokens"] == 131072
    assert redacted["input_tokens"] == 70
    assert redacted["output_tokens"] == 28
    assert redacted["cache_read_input_tokens"] == 192
    assert redacted["token"] == "[REDACTED]"
    assert redacted["auth_token"] == "[REDACTED]"
