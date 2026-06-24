"""DB-backed Phase 6.2 interactive Agent flows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .clarification import ClarificationCall, ClarificationController, DesignBriefInvoker
from .session_store import SessionStore


@dataclass(frozen=True)
class DesignBriefLoopResult:
    session_id: str
    session_hash: str
    status: str
    call_count: int


def run_design_brief_clarification_loop(
    *,
    store: SessionStore,
    session: str,
    invoke_design_brief: DesignBriefInvoker,
    user_answers: Iterable[str],
) -> DesignBriefLoopResult:
    """Run Design Brief clarification while persisting all turns in the DB."""

    stored_session = store.get_session(session)
    controller = ClarificationController.start(
        case_id=stored_session.session_hash,
        user_request=stored_session.original_input,
    )
    persisted_turn_count = 1

    first_call = invoke_design_brief(controller.transcript_dicts(), 1)
    controller = controller.record_model_call(first_call)
    _record_call(store, stored_session.session_id, first_call)
    persisted_turn_count = _persist_new_turns(
        store=store,
        session_id=stored_session.session_id,
        controller=controller,
        persisted_turn_count=persisted_turn_count,
    )

    answers = iter(user_answers)
    while controller.status == "needs_clarification":
        try:
            answer = next(answers)
        except StopIteration:
            break
        controller = controller.answer_and_rerun(
            answer=answer,
            invoke_design_brief=invoke_design_brief,
        )
        _record_call(store, stored_session.session_id, controller.calls[-1])
        persisted_turn_count = _persist_new_turns(
            store=store,
            session_id=stored_session.session_id,
            controller=controller,
            persisted_turn_count=persisted_turn_count,
        )

    store.mark_session_status(stored_session.session_id, controller.status)
    _write_design_brief_artifact(store, stored_session.session_id, controller.calls[-1])
    return DesignBriefLoopResult(
        session_id=stored_session.session_id,
        session_hash=stored_session.session_hash,
        status=controller.status,
        call_count=len(controller.calls),
    )


def _record_call(store: SessionStore, session_id: str, call: ClarificationCall) -> None:
    store.record_agent_call(
        session_id,
        {
            "role": "design_brief",
            "call_index": call.call_index,
            "response_id": call.response_id,
            "prompt_template_id": call.prompt_template_id,
            "prompt_template_hash": call.prompt_template_hash,
            "artifact_dir": call.artifact_dir,
            "status": call.brief.get("status"),
        },
    )


def _persist_new_turns(
    *,
    store: SessionStore,
    session_id: str,
    controller: ClarificationController,
    persisted_turn_count: int,
) -> int:
    for turn in controller.transcript[persisted_turn_count:]:
        store.append_turn(session_id, role=turn.role, text=turn.content)
    return len(controller.transcript)


def _write_design_brief_artifact(
    store: SessionStore,
    session_id: str,
    call: ClarificationCall,
) -> None:
    session = store.get_session(session_id)
    artifact_path = session.run_dir / "design-brief.json"
    artifact_path.write_text(
        json.dumps(call.brief, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    store.record_artifact(
        session.session_id,
        kind="design_brief",
        path=Path("runs") / session.session_hash / "design-brief.json",
    )
