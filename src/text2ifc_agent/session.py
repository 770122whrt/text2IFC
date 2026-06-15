"""Session orchestration for the clarification Agent."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document

from .merge import merge_answers
from .questions import missing_facts_from_validator_issues, plan_questions
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
        active_config = config or AgentConfig()
        state = AgentState.start(
            user_text,
            language=active_config.language,
            candidate_document=candidate_document,
        )
        if missing_facts:
            state = state.with_missing_facts(missing_facts)
        return cls(state=state, config=active_config)

    def next_questions(self) -> list[MissingFact]:
        return plan_questions(
            self.state,
            max_questions=self.config.max_questions,
            language=self.config.language,
        )

    def apply_answers(self, payload: dict[str, Any]) -> "AgentSession":
        merged = merge_answers(self.state, payload)
        evaluated = self._evaluate_after_merge(merged)
        return replace(self, state=evaluated)

    def current_status(self) -> AgentStatus:
        return self.state.status

    def _evaluate_after_merge(self, state: AgentState) -> AgentState:
        if any(fact.status == "unknown" for fact in state.missing_facts):
            return replace(state, status=AgentStatus.DRAFT)
        open_facts = [fact for fact in state.missing_facts if fact.status == "open"]
        if open_facts:
            return replace(state, status=AgentStatus.NEEDS_CLARIFICATION)
        if state.candidate_document is None:
            return replace(state, status=AgentStatus.DRAFT)
        issues = validate_v2_document(state.candidate_document)
        if not issues:
            return replace(state, status=AgentStatus.FORMAL_READY)
        return replace(
            state,
            status=AgentStatus.NEEDS_CLARIFICATION,
            missing_facts=missing_facts_from_validator_issues(issues),
        )
