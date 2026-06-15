"""Deterministic state primitives for the clarification Agent."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


AGENT_STATE_SCHEMA_VERSION = "text2ifc/agent-state-v1"
DEFAULT_LANGUAGE = "zh-CN"
OPEN_MISSING_FACT_STATUS = "open"
UNKNOWN_MISSING_FACT_STATUS = "unknown"
ANSWERED_MISSING_FACT_STATUS = "answered"
DEFERRED_MISSING_FACT_STATUS = "deferred"
REDACTED = "[REDACTED]"
_SECRET_KEY_PARTS = (
    "authorization",
    "api-key",
    "api_key",
    "apikey",
    "auth_token",
    "token",
    "secret",
    "password",
    "credential",
    "base_url",
    "url",
)
_ENV_VAR_NAMES = {"ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"}


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
    status: str = OPEN_MISSING_FACT_STATUS

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "path": self.path,
            "question_zh": self.question_zh,
            "status": self.status,
            "source": self.source,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class AgentTurn:
    role: str
    content: str
    question_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "question_ids": list(self.question_ids),
        }


@dataclass(frozen=True)
class AcceptedFact:
    id: str
    source_question_id: str
    path: str
    value: Any
    raw_answer: str
    correction_of: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "source_question_id": self.source_question_id,
            "path": self.path,
            "value": copy.deepcopy(self.value),
            "raw_answer": self.raw_answer,
        }
        if self.correction_of is not None:
            payload["correction_of"] = self.correction_of
        return payload


@dataclass(frozen=True)
class AgentState:
    original_request: str
    schema_version: str = AGENT_STATE_SCHEMA_VERSION
    language: str = DEFAULT_LANGUAGE
    status: AgentStatus = AgentStatus.DRAFT
    transcript: list[AgentTurn] = field(default_factory=list)
    missing_facts: list[MissingFact] = field(default_factory=list)
    accepted_facts: list[AcceptedFact] = field(default_factory=list)
    candidate_document: dict[str, Any] | None = None

    @classmethod
    def start(
        cls,
        user_text: str,
        *,
        language: str = DEFAULT_LANGUAGE,
        candidate_document: dict[str, Any] | None = None,
    ) -> "AgentState":
        return cls(
            schema_version=AGENT_STATE_SCHEMA_VERSION,
            language=language,
            status=AgentStatus.DRAFT,
            original_request=user_text,
            transcript=[AgentTurn(role="user", content=user_text)],
            candidate_document=copy.deepcopy(candidate_document),
        )

    def with_missing_facts(self, facts: list[MissingFact]) -> "AgentState":
        status = (
            AgentStatus.NEEDS_CLARIFICATION
            if any(fact.status == OPEN_MISSING_FACT_STATUS for fact in facts)
            else self.status
        )
        return replace(self, status=status, missing_facts=list(facts))

    def append_question_turn(
        self, content: str, question_ids: list[str]
    ) -> "AgentState":
        return replace(
            self,
            status=AgentStatus.NEEDS_CLARIFICATION,
            transcript=[
                *self.transcript,
                AgentTurn(
                    role="agent",
                    content=content,
                    question_ids=list(question_ids),
                ),
            ],
        )

    def append_user_answer(self, content: str, question_ids: list[str]) -> "AgentState":
        return replace(
            self,
            transcript=[
                *self.transcript,
                AgentTurn(role="user", content=content, question_ids=list(question_ids)),
            ],
        )

    def append_accepted_fact(self, fact: AcceptedFact) -> "AgentState":
        return replace(self, accepted_facts=[*self.accepted_facts, fact])

    def mark_unknown(self, fact_id: str) -> "AgentState":
        facts = [
            replace(fact, status=UNKNOWN_MISSING_FACT_STATUS)
            if fact.id == fact_id
            else fact
            for fact in self.missing_facts
        ]
        return replace(self, status=AgentStatus.DRAFT, missing_facts=facts)

    def with_candidate_document(
        self,
        candidate_document: dict[str, Any] | None,
        *,
        status: AgentStatus | None = None,
    ) -> "AgentState":
        return replace(
            self,
            status=self.status if status is None else status,
            candidate_document=copy.deepcopy(candidate_document),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "language": self.language,
            "status": self.status.value,
            "original_request": self.original_request,
            "transcript": [turn.to_dict() for turn in self.transcript],
            "missing_facts": [fact.to_dict() for fact in self.missing_facts],
            "accepted_facts": [fact.to_dict() for fact in self.accepted_facts],
            "candidate_document": copy.deepcopy(self.candidate_document),
        }
        return payload

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            + "\n"
        )


def redact_metadata(metadata: Any) -> Any:
    return _redact(metadata, parent_key="")


def _redact(value: Any, *, parent_key: str) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if _is_secret_key(key_text):
                redacted[key] = REDACTED
            else:
                redacted[key] = _redact(child, parent_key=key_text)
        return redacted
    if isinstance(value, list):
        return [_redact(item, parent_key=parent_key) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact(item, parent_key=parent_key) for item in value)
    if isinstance(value, str):
        if value in _ENV_VAR_NAMES:
            return value
        if _is_secret_key(parent_key) or _looks_like_secret_value(value):
            return REDACTED
    return value


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("_", "-")
    return any(part in normalized for part in _SECRET_KEY_PARTS)


def _looks_like_secret_value(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("bearer ", "basic ")):
        return True
    if lowered.startswith(("http://", "https://")):
        return True
    return False
