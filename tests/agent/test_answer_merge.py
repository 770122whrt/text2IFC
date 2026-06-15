import json
from pathlib import Path

from text2ifc_agent.merge import merge_answers, parse_answer_bundle
from text2ifc_agent.session import AgentConfig, AgentSession
from text2ifc_agent.state import (
    AcceptedFact,
    AgentState,
    AgentStatus,
    MissingFact,
)


FIXTURE = Path("tests/contract_v2/fixtures/complete.json")


def _missing_fact() -> MissingFact:
    return MissingFact(
        id="mf-room-size",
        code="MISSING_ROOM_SIZE",
        path="/entities/13/attributes/Representation",
        question_zh="房间的长、宽、高分别是多少？",
        source="validator",
        rationale="房间尺寸缺失。",
    )


def test_parse_answer_bundle_accepts_scripted_answers():
    answers = parse_answer_bundle(
        {
            "mf-room-size": "长 6 米，宽 4 米，高 3 米。",
            "mf-door-position": {
                "answer": "门在南侧墙中间。",
                "path": "/openings/0/position",
            },
        }
    )

    assert answers["mf-room-size"].raw_answer == "长 6 米，宽 4 米，高 3 米。"
    assert answers["mf-room-size"].path == "/answers/mf-room-size"
    assert answers["mf-door-position"].path == "/openings/0/position"


def test_merge_answer_appends_fact_and_preserves_transcript():
    state = (
        AgentState.start("做一个矩形房间。")
        .with_missing_facts([_missing_fact()])
        .append_question_turn("房间的长、宽、高分别是多少？", ["mf-room-size"])
    )

    updated = merge_answers(state, {"mf-room-size": "长 6 米，宽 4 米，高 3 米。"})

    assert updated.original_request == "做一个矩形房间。"
    assert [turn.role for turn in updated.transcript] == ["user", "agent", "user"]
    assert updated.transcript[-1].question_ids == ["mf-room-size"]
    assert updated.accepted_facts == [
        AcceptedFact(
            id="fact-mf-room-size-001",
            source_question_id="mf-room-size",
            path="/answers/mf-room-size",
            value="长 6 米，宽 4 米，高 3 米。",
            raw_answer="长 6 米，宽 4 米，高 3 米。",
        )
    ]
    assert updated.missing_facts[0].status == "answered"


def test_unknown_answer_keeps_draft_and_adds_no_accepted_fact():
    state = (
        AgentState.start("做一个矩形房间。")
        .with_missing_facts([_missing_fact()])
        .append_question_turn("房间的长、宽、高分别是多少？", ["mf-room-size"])
    )

    updated = merge_answers(state, {"mf-room-size": "不知道"})

    assert updated.status == AgentStatus.DRAFT
    assert updated.accepted_facts == []
    assert updated.missing_facts[0].status == "unknown"
    assert updated.candidate_document is None


def test_explicit_correction_records_new_fact_without_mutating_old_fact():
    state = AgentState.start("做一个矩形房间。").append_accepted_fact(
        AcceptedFact(
            id="fact-mf-room-size-001",
            source_question_id="mf-room-size",
            path="/answers/mf-room-size",
            value="长 6 米，宽 4 米，高 3 米。",
            raw_answer="长 6 米，宽 4 米，高 3 米。",
        )
    )

    updated = merge_answers(
        state,
        {
            "mf-room-size": {
                "answer": "更正：长 7 米，宽 4 米，高 3 米。",
                "correction_of": "fact-mf-room-size-001",
            }
        },
    )

    assert updated.accepted_facts[0].value == "长 6 米，宽 4 米，高 3 米。"
    assert updated.accepted_facts[1].correction_of == "fact-mf-room-size-001"
    assert updated.accepted_facts[1].value == "更正：长 7 米，宽 4 米，高 3 米。"


def test_session_reaches_formal_ready_only_after_answer_and_validation_pass():
    valid_candidate = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = AgentSession.start(
        user_text="做一个矩形房间。",
        config=AgentConfig(language="zh-CN", max_questions=3),
        candidate_document=valid_candidate,
        missing_facts=[_missing_fact()],
    )

    questions = session.next_questions()
    session = session.apply_answers({questions[0].id: "长 6 米，宽 4 米，高 3 米。"})

    assert session.current_status() == AgentStatus.FORMAL_READY
    assert session.state.candidate_document == valid_candidate


def test_session_keeps_validation_issues_as_missing_facts_without_defaults():
    invalid_candidate = {"schema_version": "bim-json/2.0"}
    session = AgentSession.start(
        user_text="做一个矩形房间。",
        config=AgentConfig(language="zh-CN", max_questions=3),
        candidate_document=invalid_candidate,
        missing_facts=[_missing_fact()],
    )

    questions = session.next_questions()
    session = session.apply_answers({questions[0].id: "长 6 米，宽 4 米，高 3 米。"})

    assert session.current_status() == AgentStatus.NEEDS_CLARIFICATION
    assert session.state.candidate_document == invalid_candidate
    assert session.state.missing_facts
    assert all(fact.status == "open" for fact in session.state.missing_facts)

