import io

from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.session_store import SessionStore


EVIDENCE = [
    {"evidence_id": "schema:bim-json-v2:representation"},
    {"evidence_id": "capability:IFC2X3:IfcSpace"},
    {"evidence_id": "capability:IFC2X3:IfcWall"},
]

ORIGINAL_REQUEST = "\u521b\u5efa\u4e00\u4e2a6\u7c73\u4e584\u7c73\u3001\u9ad83\u7c73\u7684\u623f\u95f4\u3002"
QUESTION_TEXT = "\u5899\u4f53\u539a\u5ea6\u662f\u591a\u5c11\u6beb\u7c73\uff1f"
ANSWER_TEXT = "\u5899\u4f53\u539a\u5ea6\u4e3a300mm\u3002"


def test_live_repl_prints_mimo_question_before_reading_user_answer(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    prompts_seen: list[str] = []
    session_hash_holder: dict[str, str] = {}

    def invoke(transcript, call_index):
        original_request = transcript[0]["content"]
        if call_index == 1:
            return _call(
                call_index,
                original_request=original_request,
                status="needs_clarification",
            )
        return _call(
            call_index,
            original_request=original_request,
            status="ready",
            source_turns=["turn-user-001", "turn-user-003"],
        )

    def input_func(prompt):
        prompts_seen.append(prompt)
        if len(prompts_seen) == 1:
            return ORIGINAL_REQUEST
        visible = output.getvalue()
        assert QUESTION_TEXT in visible
        store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
        try:
            sessions = store.list_sessions()
            assert len(sessions) == 1
            session_hash_holder["value"] = sessions[0].session_hash
            events = store.list_events(sessions[0].session_hash)
        finally:
            store.close()
        event_types = [event.event_type for event in events]
        assert "assistant_question_displayed" in event_types
        assert "user_answer_requested" in event_types
        assert event_types.index("assistant_question_displayed") < event_types.index(
            "user_answer_requested"
        )
        return ANSWER_TEXT

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=invoke,
        input_func=input_func,
        stdout=output,
    )

    assert exit_code == 0
    rendered = output.getvalue()
    assert "\u8bf7\u8f93\u5165\u5efa\u7b51\u9700\u6c42" in rendered
    assert "\u9700\u8981\u8865\u5145\u4fe1\u606f" in rendered
    assert "\u9700\u6c42\u5df2\u660e\u786e" in rendered
    assert "session_hash" in rendered

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.get_session(session_hash_holder["value"])
        export = store.session_export_payload(session.session_hash)
    finally:
        store.close()

    assert session.status == "ready"
    assert [turn["role"] for turn in export["turns"]] == ["user", "assistant", "user"]
    assert export["turns"][1]["text"] == QUESTION_TEXT
    assert export["turns"][2]["text"] == ANSWER_TEXT
    started = [
        event
        for event in export["events"]
        if event["event_type"] == "repl_session_started"
    ][0]
    assert started["payload"]["interaction_mode"] == "human_repl_live"
    assert started["payload"]["input_source"] == "terminal"


def test_live_repl_quit_records_incomplete_without_ifc(tmp_path):
    from scripts.agent import run_text2ifc_chat

    root = tmp_path / "phase6.2-fix-repl"
    output = io.StringIO()
    answers = iter([ORIGINAL_REQUEST, "quit"])

    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--stop-after",
            "design-brief",
            "--output-root",
            str(root),
            "--db",
            str(root / "sessions.sqlite"),
        ],
        design_brief_invoker=lambda transcript, call_index: _call(
            call_index,
            original_request=transcript[0]["content"],
            status="needs_clarification",
        ),
        input_func=lambda prompt: next(answers),
        stdout=output,
    )

    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    try:
        session = store.list_sessions()[0]
    finally:
        store.close()

    assert exit_code == 0
    assert session.status == "incomplete"
    assert not (root / "runs" / session.session_hash / "output.ifc").exists()
    assert "\u5df2\u9000\u51fa" in output.getvalue()


def _brief(*, original_request: str, status: str, source_turns=None):
    source_turns = source_turns or ["turn-user-001"]
    blocker = {
        "id": "mf-wall-thickness",
        "code": "WALL_THICKNESS_MISSING",
        "path": "/known_facts/walls/thickness_mm",
        "message": "\u5899\u4f53\u539a\u5ea6\u5c1a\u672a\u63d0\u4f9b\u3002",
        "reason": "\u751f\u6210\u5b9e\u4f53\u5899\u9700\u8981\u660e\u786e\u539a\u5ea6\u3002",
        "blocking": True,
        "evidence_refs": ["schema:bim-json-v2:representation"],
        "source_turns": source_turns,
    }
    return {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": original_request,
        "status": status,
        "known_facts": {
            "space": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
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
                    "text": QUESTION_TEXT,
                    "targets": ["mf-wall-thickness"],
                    "reason": "\u7f3a\u5c11\u539a\u5ea6\u65f6\u4e0d\u80fd\u751f\u6210\u5899\u4f53\u3002",
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


def _call(index, *, original_request, status, source_turns=None):
    return ClarificationCall(
        call_index=index,
        response_id=f"msg_phase62_fix_{index}",
        prompt_template_id="design-brief.v2.1",
        prompt_template_hash="sha256:prompt-v2.1",
        artifact_dir=f"calls/{index:02d}-design-brief",
        brief=_brief(
            original_request=original_request,
            status=status,
            source_turns=source_turns,
        ),
        evidence_catalog=EVIDENCE,
    )
