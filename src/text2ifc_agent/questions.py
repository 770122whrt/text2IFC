"""Map validation gaps to bounded Chinese clarification questions."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from text2ifc_contract.validation import ValidationIssue

from .state import MissingFact, OPEN_MISSING_FACT_STATUS


_PRIORITY_RULES = (
    ("storey", 0),
    ("floor", 0),
    ("楼层", 0),
    ("MISSING_STOREY", 0),
    ("room", 1),
    ("space", 1),
    ("ROOM_SIZE", 1),
    ("SPACE_GEOMETRY", 1),
    ("wall", 2),
    ("WALL_HEIGHT", 2),
    ("door", 3),
    ("DOOR_POSITION", 3),
    ("window", 4),
    ("WINDOW_POSITION", 4),
)


def missing_facts_from_validator_issues(
    issues: list[ValidationIssue],
) -> list[MissingFact]:
    facts: list[MissingFact] = []
    for index, issue in enumerate(issues):
        facts.append(
            MissingFact(
                id=_validator_fact_id(index, issue),
                code=issue.code,
                path=issue.path,
                question_zh=_question_for(issue.code, issue.path, issue.message),
                source="validator",
                rationale=issue.message,
            )
        )
    return facts


def missing_facts_from_draft(draft: dict[str, Any]) -> list[MissingFact]:
    facts: list[MissingFact] = []
    for item in draft.get("missing_facts", []):
        code = str(item.get("code", "MISSING_FACT"))
        path = str(item.get("path", "/"))
        message = str(item.get("message", ""))
        entity_id = str(item.get("entity_id", "unknown"))
        facts.append(
            MissingFact(
                id=f"draft-{_slug(entity_id)}-{_slug(code)}",
                code=code,
                path=path,
                question_zh=_question_for(code, path, message),
                source="draft",
                rationale=message,
            )
        )
    return facts


def rank_missing_facts(facts: list[MissingFact]) -> list[MissingFact]:
    return sorted(
        facts,
        key=lambda fact: (_priority(fact), fact.id, fact.path, fact.code),
    )


def plan_questions(
    state: Any,
    *,
    max_questions: int = 3,
    language: str = "zh-CN",
) -> list[MissingFact]:
    if language != "zh-CN":
        raise ValueError("Phase 5 question planner currently supports zh-CN only")
    limit = max(1, min(3, max_questions))
    open_facts = [
        fact
        for fact in getattr(state, "missing_facts", [])
        if fact.status == OPEN_MISSING_FACT_STATUS
    ]
    return rank_missing_facts(open_facts)[:limit]


def _validator_fact_id(index: int, issue: ValidationIssue) -> str:
    digest = hashlib.sha1(
        f"{issue.code}|{issue.path}|{issue.message}".encode("utf-8")
    ).hexdigest()[:8]
    return f"validator-{index:03d}-{_slug(issue.code)}-{digest}"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]+", "-", value.strip().lower())
    return normalized.strip("-") or "unknown"


def _priority(fact: MissingFact) -> tuple[int, str]:
    haystack = f"{fact.code} {fact.path} {fact.question_zh} {fact.rationale}"
    lowered = haystack.lower()
    for needle, priority in _PRIORITY_RULES:
        if needle.lower() in lowered:
            return (priority, fact.id)
    return (99, fact.id)


def _question_for(code: str, path: str, message: str) -> str:
    haystack = f"{code} {path} {message}".lower()
    if _contains_any(haystack, ("storey", "floor", "楼层", "relative_to")):
        return "这个构件属于哪一个楼层？请提供楼层名称或标高。"
    if _contains_any(haystack, ("ifcdoor", "door", "门")):
        return "这扇门位于哪面墙上？门洞在墙上的水平位置和底部高度是多少？"
    if _contains_any(haystack, ("ifcwindow", "window", "窗")):
        return "这扇窗位于哪面墙上？窗在墙上的水平位置、窗台高度和尺寸是多少？"
    if _contains_any(
        haystack,
        ("ifcspace", "space", "room", "房间", "representation", "space_geometry"),
    ):
        return "房间的长、宽、高分别是多少？"
    if _contains_any(haystack, ("ifcwall", "wall", "墙")):
        return "墙的长度、厚度和高度分别是多少？"
    if _contains_any(haystack, ("objectplacement", "placement", "position")):
        return "这个构件相对于哪个楼层或父构件放置？位置坐标是多少？"
    return "请补充这个构件缺少的尺寸、位置或关系信息。"


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in value for needle in needles)
