from text2ifc_agent.questions import (
    missing_facts_from_draft,
    missing_facts_from_validator_issues,
    plan_questions,
)
from text2ifc_agent.state import AgentState, MissingFact
from text2ifc_contract.validation import ValidationIssue


FORBIDDEN_TERMS = {
    "IfcCartesianPoint",
    "IfcDirection",
    "IfcOwnerHistory",
    "STEP",
    "schema",
    "attributes",
    "Representation",
    "/entities",
}


def _assert_user_facing_chinese(question: str) -> None:
    assert any("\u4e00" <= char <= "\u9fff" for char in question)
    for term in FORBIDDEN_TERMS:
        assert term not in question
    assert not question.startswith("/")


def test_room_representation_issue_yields_room_size_question():
    issues = [
        ValidationIssue(
            code="REQUIRED_FIELD",
            path="/entities/12/attributes/Representation",
            message="IfcSpace room representation is missing.",
        )
    ]

    facts = missing_facts_from_validator_issues(issues)

    assert len(facts) == 1
    assert facts[0].source == "validator"
    assert facts[0].status == "open"
    assert facts[0].path == "/entities/12/attributes/Representation"
    assert "房间" in facts[0].question_zh
    assert "长" in facts[0].question_zh
    assert "宽" in facts[0].question_zh
    assert "高" in facts[0].question_zh
    _assert_user_facing_chinese(facts[0].question_zh)


def test_missing_storey_context_yields_floor_question():
    issues = [
        ValidationIssue(
            code="UNRESOLVED_PLACEMENT_REFERENCE",
            path="/entities/4/attributes/ObjectPlacement/relative_to",
            message="Wall placement does not reference a known storey.",
        )
    ]

    facts = missing_facts_from_validator_issues(issues)

    assert len(facts) == 1
    assert "楼层" in facts[0].question_zh
    _assert_user_facing_chinese(facts[0].question_zh)


def test_door_and_window_placement_issue_yields_host_or_position_question():
    issues = [
        ValidationIssue(
            code="REQUIRED_FIELD",
            path="/entities/8/attributes/ObjectPlacement",
            message="IfcDoor host wall and opening position are missing.",
        ),
        ValidationIssue(
            code="REQUIRED_FIELD",
            path="/entities/9/attributes/ObjectPlacement",
            message="IfcWindow host wall and sill position are missing.",
        ),
    ]

    facts = missing_facts_from_validator_issues(issues)
    questions = [fact.question_zh for fact in facts]

    assert any("门" in question and ("墙" in question or "位置" in question) for question in questions)
    assert any("窗" in question and ("墙" in question or "位置" in question) for question in questions)
    for question in questions:
        _assert_user_facing_chinese(question)


def test_question_planner_returns_top_three_and_keeps_remaining_open():
    facts = [
        MissingFact(
            id=f"mf-{index}",
            code=code,
            path=f"/entities/{index}/attributes/ObjectPlacement",
            question_zh=question,
            source="validator",
        )
        for index, (code, question) in enumerate(
            [
                ("MISSING_STOREY", "这个构件属于哪一层？"),
                ("MISSING_ROOM_SIZE", "房间的长、宽、高分别是多少？"),
                ("MISSING_WALL_HEIGHT", "墙高是多少？"),
                ("MISSING_DOOR_POSITION", "门在哪面墙上？"),
                ("MISSING_WINDOW_POSITION", "窗在哪面墙上？"),
            ]
        )
    ]
    state = AgentState.start("建一个房间。").with_missing_facts(facts)

    selected = plan_questions(state, max_questions=3)

    assert [fact.id for fact in selected] == ["mf-0", "mf-1", "mf-2"]
    assert len(selected) == 3
    assert [fact.status for fact in state.missing_facts] == ["open"] * 5


def test_draft_missing_facts_become_open_agent_missing_facts_without_loss():
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "target_schema_version": "bim-json/2.0",
        "partial_document": {
            "schema_version": "bim-json/2.0",
            "entities": [{"id": "space-1", "attributes": {}}],
        },
        "missing_facts": [
            {
                "entity_id": "space-1",
                "path": "/entities/0/attributes/Representation",
                "code": "MISSING_SPACE_GEOMETRY",
                "message": "Space boundary and height are not known.",
            }
        ],
        "losses": [],
        "clarification_targets": [],
        "provenance": {"source": "test"},
    }

    facts = missing_facts_from_draft(draft)

    assert len(facts) == 1
    assert facts[0].id == "draft-space-1-missing-space-geometry"
    assert facts[0].code == "MISSING_SPACE_GEOMETRY"
    assert facts[0].path == "/entities/0/attributes/Representation"
    assert facts[0].source == "draft"
    assert facts[0].status == "open"
    assert "房间" in facts[0].question_zh
    _assert_user_facing_chinese(facts[0].question_zh)

