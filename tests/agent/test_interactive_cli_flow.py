import json

from text2ifc_agent.clarification import ClarificationCall
from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
from text2ifc_agent.session_store import SessionStore


EVIDENCE = [
    {"evidence_id": "schema:bim-json-v2:representation"},
    {"evidence_id": "capability:IFC2X3:IfcSpace"},
    {"evidence_id": "capability:IFC2X3:IfcWall"},
]


def _brief(*, original_request: str, status: str, source_turns=None):
    source_turns = source_turns or ["turn-user-001"]
    blocker = {
        "id": "mf-wall-thickness",
        "code": "WALL_THICKNESS_MISSING",
        "path": "/known_facts/walls/thickness_mm",
        "message": "墙体厚度尚未提供。",
        "reason": "生成实体墙体需要明确厚度。",
        "blocking": True,
        "evidence_refs": ["schema:bim-json-v2:representation"],
        "source_turns": ["turn-user-001"],
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
                    "text": "墙体厚度是多少毫米？",
                    "targets": ["mf-wall-thickness"],
                    "reason": "缺少厚度时不能生成墙体。",
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
        response_id=f"msg_phase62_{index}",
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


def test_design_brief_loop_persists_agent_question_and_recall(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个6米乘4米的房间，高3米。")
    observed = []

    def invoke(transcript, call_index):
        observed.append((transcript, call_index))
        if call_index == 1:
            return _call(
                call_index,
                original_request=session.original_input,
                status="needs_clarification",
            )
        return _call(
            call_index,
            original_request=session.original_input,
            status="ready",
            source_turns=["turn-user-001", "turn-user-003"],
        )

    result = run_design_brief_clarification_loop(
        store=store,
        session=session.session_hash,
        invoke_design_brief=invoke,
        user_answers=["墙体厚度为300mm。"],
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "ready"
    assert [call_index for _, call_index in observed] == [1, 2]
    assert [turn["role"] for turn in export["turns"]] == ["user", "assistant", "user"]
    assert export["turns"][1]["text"] == "墙体厚度是多少毫米？"
    assert export["turns"][2]["text"] == "墙体厚度为300mm。"
    assert export["agent_calls"][0]["payload"]["response_id"] == "msg_phase62_1"
    assert export["agent_calls"][1]["payload"]["response_id"] == "msg_phase62_2"
    assert (root / "runs" / session.session_hash / "design-brief.json").is_file()


def test_unknown_answer_routes_to_draft_without_ifc_artifact(tmp_path):
    root = tmp_path / "phase6.2-interactive-cli"
    store = SessionStore.open(root / "sessions.sqlite", artifact_root=root)
    session = store.create_session(original_input="创建一个房间。")

    def invoke(transcript, call_index):
        status = "needs_clarification" if call_index == 1 else "draft_required"
        return _call(
            call_index,
            original_request=session.original_input,
            status=status,
            source_turns=["turn-user-001"] if call_index == 1 else ["turn-user-001", "turn-user-003"],
        )

    result = run_design_brief_clarification_loop(
        store=store,
        session=session.session_hash,
        invoke_design_brief=invoke,
        user_answers=["这个厚度我不知道。"],
    )
    export = store.session_export_payload(session.session_hash)

    assert result.status == "draft_required"
    assert store.get_session(session.session_hash).status == "draft_required"
    assert not (root / "runs" / session.session_hash / "output.ifc").exists()
    assert "这个厚度我不知道。" in json.dumps(export["turns"], ensure_ascii=False)
