"""Answer merge skeleton for Phase 5 RED tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import AgentState


@dataclass(frozen=True)
class ParsedAnswer:
    question_id: str
    raw_answer: str
    path: str
    correction_of: str | None = None


def parse_answer_bundle(payload: dict[str, Any]) -> dict[str, ParsedAnswer]:
    del payload
    return {}


def merge_answers(state: AgentState, payload: dict[str, Any]) -> AgentState:
    del payload
    return state

