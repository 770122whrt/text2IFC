"""Agent state skeleton for Phase 5 RED tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    FORMAL_READY = "formal_ready"
    COMPILED = "compiled"


@dataclass(frozen=True)
class MissingFact:
    id: str
    code: str
    path: str
    question_zh: str
    source: str
    rationale: str = ""
    status: str = "open"


@dataclass(frozen=True)
class AgentTurn:
    role: str
    content: str
    question_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AcceptedFact:
    id: str
    source_question_id: str
    path: str
    value: Any
    raw_answer: str


@dataclass(frozen=True)
class AgentState:
    schema_version: str
    language: str
    status: AgentStatus
    original_request: str
    transcript: list[AgentTurn] = field(default_factory=list)
    missing_facts: list[MissingFact] = field(default_factory=list)
    accepted_facts: list[AcceptedFact] = field(default_factory=list)
    candidate_document: dict[str, Any] | None = None

    @classmethod
    def start(cls, user_text: str) -> "AgentState":
        return cls(
            schema_version="",
            language="",
            status=AgentStatus.DRAFT,
            original_request="",
            transcript=[],
        )

    def with_missing_facts(self, facts: list[MissingFact]) -> "AgentState":
        return self

    def append_question_turn(
        self, content: str, question_ids: list[str]
    ) -> "AgentState":
        return self

    def append_user_answer(self, content: str, question_ids: list[str]) -> "AgentState":
        return self

    def append_accepted_fact(self, fact: AcceptedFact) -> "AgentState":
        return self

    def to_dict(self) -> dict[str, Any]:
        return {}

    def to_json(self) -> str:
        return "{}\n"


def redact_metadata(metadata: Any) -> Any:
    return metadata
