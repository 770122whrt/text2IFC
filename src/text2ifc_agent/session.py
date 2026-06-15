"""Agent session skeleton for Phase 5 RED tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import AgentState, AgentStatus, MissingFact


@dataclass(frozen=True)
class AgentConfig:
    language: str = "zh-CN"
    max_questions: int = 3


@dataclass(frozen=True)
class AgentSession:
    state: AgentState
    config: AgentConfig

    @classmethod
    def start(
        cls,
        *,
        user_text: str,
        config: AgentConfig | None = None,
        candidate_document: dict[str, Any] | None = None,
        missing_facts: list[MissingFact] | None = None,
    ) -> "AgentSession":
        del candidate_document, missing_facts
        return cls(state=AgentState.start(user_text), config=config or AgentConfig())

    def next_questions(self) -> list[MissingFact]:
        return []

    def apply_answers(self, payload: dict[str, Any]) -> "AgentSession":
        del payload
        return self

    def current_status(self) -> AgentStatus:
        return self.state.status
