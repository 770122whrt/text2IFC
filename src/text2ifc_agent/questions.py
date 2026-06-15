"""Question planner skeleton for Phase 5 RED tests."""

from __future__ import annotations

from typing import Any

from text2ifc_contract.validation import ValidationIssue

from .state import MissingFact


def missing_facts_from_validator_issues(
    issues: list[ValidationIssue],
) -> list[MissingFact]:
    del issues
    return []


def missing_facts_from_draft(draft: dict[str, Any]) -> list[MissingFact]:
    del draft
    return []


def rank_missing_facts(facts: list[MissingFact]) -> list[MissingFact]:
    return list(facts)


def plan_questions(
    state: Any,
    *,
    max_questions: int = 3,
    language: str = "zh-CN",
) -> list[MissingFact]:
    del language
    return list(getattr(state, "missing_facts", []))[:max_questions]
