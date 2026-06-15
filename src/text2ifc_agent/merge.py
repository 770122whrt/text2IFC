"""Merge user clarification answers into Agent state."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from .state import (
    ANSWERED_MISSING_FACT_STATUS,
    OPEN_MISSING_FACT_STATUS,
    AcceptedFact,
    AgentState,
    AgentStatus,
    MissingFact,
    UNKNOWN_MISSING_FACT_STATUS,
)


UNKNOWN_ANSWER_MARKERS = (
    "不知道",
    "不清楚",
    "不确定",
    "不知道。",
    "我不知道",
    "暂时不知道",
    "i do not know",
    "i don't know",
    "unknown",
)


@dataclass(frozen=True)
class ParsedAnswer:
    question_id: str
    raw_answer: str
    path: str
    correction_of: str | None = None


def parse_answer_bundle(payload: dict[str, Any]) -> dict[str, ParsedAnswer]:
    answers: dict[str, ParsedAnswer] = {}
    for question_id, value in payload.items():
        if isinstance(value, dict):
            raw_answer = str(value.get("answer", ""))
            path = str(value.get("path", f"/answers/{question_id}"))
            correction_of = value.get("correction_of")
            if correction_of is not None:
                correction_of = str(correction_of)
        else:
            raw_answer = str(value)
            path = f"/answers/{question_id}"
            correction_of = None
        answers[str(question_id)] = ParsedAnswer(
            question_id=str(question_id),
            raw_answer=raw_answer,
            path=path,
            correction_of=correction_of,
        )
    return answers


def merge_answers(state: AgentState, payload: dict[str, Any]) -> AgentState:
    updated = state
    for answer in parse_answer_bundle(payload).values():
        updated = updated.append_user_answer(answer.raw_answer, [answer.question_id])
        if is_unknown_answer(answer.raw_answer):
            updated = _with_missing_fact_status(
                updated,
                answer.question_id,
                UNKNOWN_MISSING_FACT_STATUS,
                status=AgentStatus.DRAFT,
            )
            continue
        updated = updated.append_accepted_fact(
            AcceptedFact(
                id=_next_fact_id(updated, answer.question_id),
                source_question_id=answer.question_id,
                path=answer.path,
                value=answer.raw_answer,
                raw_answer=answer.raw_answer,
                correction_of=answer.correction_of,
            )
        )
        updated = _with_missing_fact_status(
            updated,
            answer.question_id,
            ANSWERED_MISSING_FACT_STATUS,
            status=_status_after_answer(updated),
        )
    return updated


def is_unknown_answer(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in UNKNOWN_ANSWER_MARKERS


def _next_fact_id(state: AgentState, question_id: str) -> str:
    count = (
        sum(1 for fact in state.accepted_facts if fact.source_question_id == question_id)
        + 1
    )
    return f"fact-{question_id}-{count:03d}"


def _with_missing_fact_status(
    state: AgentState,
    fact_id: str,
    fact_status: str,
    *,
    status: AgentStatus,
) -> AgentState:
    facts = [
        _replace_fact_status(fact, fact_status) if fact.id == fact_id else fact
        for fact in state.missing_facts
    ]
    return replace(state, status=status, missing_facts=facts)


def _replace_fact_status(fact: MissingFact, status: str) -> MissingFact:
    return replace(fact, status=status)


def _status_after_answer(state: AgentState) -> AgentStatus:
    if any(fact.status == OPEN_MISSING_FACT_STATUS for fact in state.missing_facts):
        return AgentStatus.NEEDS_CLARIFICATION
    return state.status
