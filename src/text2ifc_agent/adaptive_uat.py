"""Adaptive live-UAT helpers for Phase 6.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class LiveUATEvidenceError(ValueError):
    """Raised when evidence is not acceptable as final live UAT."""


@dataclass(frozen=True)
class PlannedAnswer:
    intent: str
    answer: str


@dataclass(frozen=True)
class AdaptiveAnswerPolicy:
    """Map actual clarification questions to answer intents."""

    answers_by_intent: Mapping[str, str]

    def answer_question(self, question: str) -> PlannedAnswer:
        intent = classify_question_intent(question)
        answer = self.answers_by_intent.get(intent) or self.answers_by_intent.get(
            "unknown",
            "unknown",
        )
        return PlannedAnswer(intent=intent, answer=answer)


def classify_question_intent(question: str) -> str:
    text = question.lower()
    if _contains_any(text, ("墙厚", "墙体厚", "wall thick", "walls be")):
        return "wall_thickness"
    if _contains_any(text, ("地板厚", "楼板", "slab", "floor thickness", "地坪板")):
        return "slab_thickness"
    if _contains_any(text, ("窗台", "window", "窗的", "窗户", "窗宽")):
        return "window_dimensions"
    if _contains_any(text, ("门洞", "门宽", "宽和高", "door size", "door dimension")):
        return "door_dimensions"
    if _contains_any(text, ("哪一侧", "哪面", "host wall", "开在哪", "入口开在")):
        return "door_host"
    if _contains_any(text, ("高度", "净高", "竖向", "height", "顶部")):
        return "height"
    return "unknown"


def validate_live_uat_evidence(payload: Mapping[str, Any]) -> None:
    """Reject evidence that cannot count as final live DeepSeek acceptance."""

    if "scripted" in str(payload.get("interaction_mode", "")).lower() or "scripted" in str(
        payload.get("input_source", "")
    ).lower():
        raise LiveUATEvidenceError("scripted stdin cannot satisfy final live acceptance")
    if payload.get("used_answers_json") is True:
        raise LiveUATEvidenceError("prewritten answers.json cannot satisfy final live acceptance")
    if payload.get("used_fake_or_replay_provider") is True:
        raise LiveUATEvidenceError("fake or replay provider evidence cannot satisfy final live acceptance")
    if payload.get("provider") != "deepseek-openai-compatible":
        raise LiveUATEvidenceError("final live acceptance requires DeepSeek provider evidence")
    if payload.get("evidence_class") != "live_deepseek":
        raise LiveUATEvidenceError("final live acceptance requires live_deepseek evidence class")
    response_ids = payload.get("response_ids")
    if not isinstance(response_ids, list) or not response_ids:
        raise LiveUATEvidenceError("live evidence must include response IDs")
    finish_reasons = payload.get("finish_reasons")
    if not isinstance(finish_reasons, list) or not finish_reasons:
        raise LiveUATEvidenceError("live evidence must include finish reasons")
    if any(reason == "length" for reason in finish_reasons):
        raise LiveUATEvidenceError("truncated provider responses cannot be accepted")


def build_live_uat_result(
    *,
    provider: str,
    model: str | None,
    response_ids: Sequence[str],
    finish_reasons: Sequence[str],
    usage: Sequence[Mapping[str, Any]],
    interaction_mode: str,
    input_source: str,
    used_answers_json: bool,
    used_fake_or_replay_provider: bool,
    artifacts: Mapping[str, str],
) -> dict[str, Any]:
    """Build a redacted Phase 6.4 live-UAT result payload."""

    payload = {
        "schema_version": "text2ifc/phase6.4-live-uat/1.0",
        "mode": "live_uat",
        "provider": provider,
        "evidence_class": "live_deepseek",
        "model": model,
        "response_ids": list(response_ids),
        "finish_reasons": list(finish_reasons),
        "usage": [dict(item) for item in usage],
        "interaction_mode": interaction_mode,
        "input_source": input_source,
        "used_answers_json": used_answers_json,
        "used_fake_or_replay_provider": used_fake_or_replay_provider,
        "artifacts": dict(artifacts),
        "config": {
            "api_key": "[REDACTED]",
            "base_url": "[REDACTED]",
        },
    }
    validate_live_uat_evidence(payload)
    return payload


def build_config_check_result(config_status: Mapping[str, Any]) -> dict[str, Any]:
    """Build a redacted config-check payload for the live harness."""

    return {
        "schema_version": "text2ifc/phase6.4-live-uat/1.0",
        "mode": "check_config",
        "provider": config_status.get("provider"),
        "configured": bool(config_status.get("configured")),
        "missing": list(config_status.get("missing", [])),
        "model": config_status.get("model"),
        "model_env": config_status.get("model_env"),
        "api_key_env": config_status.get("api_key_env"),
        "base_url_env": config_status.get("base_url_env"),
        "max_completion_tokens": config_status.get("max_completion_tokens"),
        "config": {
            "api_key": "[REDACTED]",
            "base_url": "[REDACTED]",
        },
    }


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)
