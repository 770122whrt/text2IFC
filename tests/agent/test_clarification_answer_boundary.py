"""Offline failure family: no design decision without a nonblank user turn."""

import copy
import json

import pytest

from text2ifc_agent.clarification import ClarificationController, ClarificationError
from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
from text2ifc_agent.session_store import SessionStore
from tests.agent.test_live_clarification import EVIDENCE, REQUEST, _brief, _call


def _pending(*, conflict=False):
    brief = _brief()
    if conflict:
        brief["missing_facts"] = []
        brief["ambiguities"] = [{
            "id": "stair-layout-conflict",
            "path": "/known_facts/stairs",
            "message": "二层楼梯的位置与通行要求冲突。",
            "reason": "需要用户选择调整位置或保留原要求。",
            "blocking": True,
            "evidence_refs": ["schema:bim-json-v2:representation"],
            "source_turns": ["turn-user-001"],
            "options": ["调整位置", "保留原要求"],
        }]
        brief["clarification_questions"][0].update(
            text="二层楼梯的位置需要调整还是保留？",
            targets=["stair-layout-conflict"],
        )
    return brief


@pytest.mark.parametrize("answer", ["", " ", "\t\r\n", "\u3000"])
@pytest.mark.parametrize("conflict", [False, True], ids=["missing-dimension", "layout-conflict"])
def test_blank_answer_does_not_invoke_or_change_pending_state(answer, conflict):
    controller = ClarificationController.start(case_id="answer-boundary", user_request=REQUEST)
    controller = controller.record_model_call(_call(1, _pending(conflict=conflict)))
    before = copy.deepcopy(controller.to_dict())
    calls = []

    def invoke(transcript, index):
        calls.append(index)
        return _call(index, _brief(status="ready"))

    with pytest.raises(ClarificationError, match="non-empty"):
        controller.answer_and_rerun(answer=answer, invoke_design_brief=invoke)
    assert calls == []
    assert controller.to_dict() == before


@pytest.mark.parametrize("status", ["needs_clarification", "ready", "draft_required", "blocked"])
def test_new_brief_cannot_replace_waiting_or_terminal_state_without_user_turn(status):
    controller = ClarificationController.start(case_id="transition-boundary", user_request=REQUEST)
    controller = controller.record_model_call(_call(1, _brief(status=status)))
    before = copy.deepcopy(controller.to_dict())
    with pytest.raises(ClarificationError, match="awaiting_model"):
        controller.record_model_call(_call(2, _brief(status="ready")))
    assert controller.to_dict() == before


@pytest.mark.parametrize("answer,status", [
    ("  墙厚为200毫米。\n", "ready"),
    ("  我不知道。\n", "draft_required"),
    ("先确认墙厚，其他问题还需要讨论。", "needs_clarification"),
])
def test_nonblank_answer_is_preserved_and_result_is_not_forced_ready(answer, status):
    controller = ClarificationController.start(case_id="valid-answer", user_request=REQUEST)
    controller = controller.record_model_call(_call(1, _pending()))
    calls = []

    def invoke(transcript, index):
        calls.append(index)
        assert transcript[-1]["content"] == answer
        assert transcript[-1]["question_ids"] == list(controller.pending_question_ids)
        return _call(index, _brief(status=status))

    updated = controller.answer_and_rerun(answer=answer, invoke_design_brief=invoke)
    assert calls == [2]
    assert updated.status == status
    assert updated.transcript[2].content == answer
    assert controller.status == "needs_clarification"


@pytest.mark.parametrize("resume", [False, True], ids=["initial-loop", "reopened-session"])
def test_public_loop_rejects_blank_before_followup_and_keeps_question_recoverable(tmp_path, resume):
    db = tmp_path / "sessions.sqlite"
    store = SessionStore.open(db, artifact_root=tmp_path)
    session = store.create_session(original_input=REQUEST)
    calls = []

    def invoke(transcript, index):
        calls.append(index)
        brief = _pending(conflict=True) if index == 1 else _brief(status="ready")
        directory = session.run_dir / "calls" / f"{index:02d}-design-brief"
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "design-brief.json").write_text(json.dumps(brief), encoding="utf-8")
        (directory / "context-selection.json").write_text(
            json.dumps({"evidence": EVIDENCE}), encoding="utf-8"
        )
        return _call(index, brief)

    try:
        if resume:
            run_design_brief_clarification_loop(
                store=store, session=session.session_hash,
                invoke_design_brief=invoke, user_answers=[],
            )
            store.close()
            store = SessionStore.open(db, artifact_root=tmp_path)

        with pytest.raises(ClarificationError, match="non-empty"):
            run_design_brief_clarification_loop(
                store=store, session=session.session_hash,
                invoke_design_brief=invoke, user_answers=[" \t\u3000"],
            )
        assert calls == [1]
        assert [turn.role for turn in store.list_turns(session.session_hash)] == ["user", "assistant"]
        assert not list(session.run_dir.rglob("*.ifc"))
        original = (session.run_dir / "calls/01-design-brief/design-brief.json").read_bytes()
        recovered = run_design_brief_clarification_loop(
            store=store, session=session.session_hash,
            invoke_design_brief=invoke, user_answers=["调整位置，我会补充明确尺寸。"],
        )
        assert recovered.status == "ready"  # Fake model output, not design reasoning evidence.
        assert calls == [1, 2]
        assert (session.run_dir / "calls/01-design-brief/design-brief.json").read_bytes() == original
    finally:
        store.close()
