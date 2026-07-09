"""Bounded feedback-round planning for Phase 6.4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .issues import Issue, issue_to_dict
from .route_decision import decide_route_from_issues


FEEDBACK_ROUNDS_SCHEMA_VERSION = "text2ifc/feedback-rounds/1.0"
DEFAULT_MAX_FEEDBACK_ROUNDS = 2


def plan_feedback_round(
    *,
    source_stage: str,
    issues: Sequence[Issue | Mapping[str, Any]],
    previous_issue_count: int | None,
    current_feedback_round: int,
    max_feedback_rounds: int = DEFAULT_MAX_FEEDBACK_ROUNDS,
) -> dict[str, Any]:
    """Plan one bounded feedback round from normalized issues."""

    issue_payloads = [issue_to_dict(issue) for issue in issues]
    output_issue_count = len(
        [
            issue
            for issue in issue_payloads
            if issue["severity"] in {"warning", "blocking", "fatal"}
        ]
    )
    input_issue_count = (
        output_issue_count if previous_issue_count is None else previous_issue_count
    )
    issue_delta = None if previous_issue_count is None else input_issue_count - output_issue_count
    route_decision = decide_route_from_issues(
        issue_payloads,
        current_feedback_round=current_feedback_round,
        max_feedback_rounds=max_feedback_rounds,
    )
    retry_allowed = bool(route_decision["retry_allowed"])
    attempted_action = _attempted_action(str(route_decision["route"]))
    terminal_status = _terminal_status(
        route=str(route_decision["route"]),
        final_status=str(route_decision["final_status"]),
        retry_allowed=retry_allowed,
    )

    if str(route_decision["route"]) == "ask_user":
        retry_allowed = False
        attempted_action = "stop_for_user_input"
        terminal_status = "draft"
    elif current_feedback_round >= max_feedback_rounds and route_decision["route"] != "accepted":
        retry_allowed = False
        attempted_action = "stop_attempt_limit"
        terminal_status = "blocked_attempt_limit"
    elif previous_issue_count is not None and output_issue_count >= previous_issue_count and route_decision["route"] != "accepted":
        retry_allowed = False
        attempted_action = "stop_non_improving"
        terminal_status = "blocked_non_improving"

    return {
        "schema_version": "text2ifc/feedback-round/1.0",
        "round_index": current_feedback_round,
        "source_stage": source_stage,
        "input_issue_count": input_issue_count,
        "output_issue_count": output_issue_count,
        "issue_delta": issue_delta,
        "route": route_decision["route"],
        "target_stage": route_decision["target_stage"],
        "retry_allowed": retry_allowed,
        "attempted_action": attempted_action,
        "terminal_status": terminal_status,
        "max_feedback_rounds": max_feedback_rounds,
        "issues": issue_payloads,
        "route_decision": {**route_decision, "retry_allowed": retry_allowed},
    }


def write_feedback_rounds(
    run_dir: Path | str,
    rounds: Sequence[Mapping[str, Any]],
) -> Path:
    """Write `feedback-rounds.json` in a run directory."""

    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "feedback-rounds.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": FEEDBACK_ROUNDS_SCHEMA_VERSION,
                "rounds": [dict(round_record) for round_record in rounds],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def write_feedback_artifacts(
    run_dir: Path | str,
    *,
    source_stage: str,
    issues: Sequence[Issue | Mapping[str, Any]],
    previous_issue_count: int | None = None,
    current_feedback_round: int = 0,
    max_feedback_rounds: int = DEFAULT_MAX_FEEDBACK_ROUNDS,
) -> dict[str, Any]:
    """Write route-decision v2 and feedback-rounds artifacts for a terminal run."""

    root = Path(run_dir)
    round_record = plan_feedback_round(
        source_stage=source_stage,
        issues=issues,
        previous_issue_count=previous_issue_count,
        current_feedback_round=current_feedback_round,
        max_feedback_rounds=max_feedback_rounds,
    )
    route_decision_path = root / "route-decision.json"
    route_decision_path.write_text(
        json.dumps(
            round_record["route_decision"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_feedback_rounds(root, [round_record])
    return round_record


def _attempted_action(route: str) -> str:
    return {
        "accepted": "none",
        "ask_user": "stop_for_user_input",
        "revise_design_brief": "prepare_design_brief_feedback",
        "regenerate_json": "prepare_generator_feedback",
        "repair_json": "prepare_repair_feedback",
        "blocked_as_unsupported": "stop_unsupported",
        "gate_issue": "stop_gate_review",
        "provider_retry": "prepare_provider_retry",
        "runtime_blocked": "stop_runtime_blocked",
    }.get(route, "stop_runtime_blocked")


def _terminal_status(
    *,
    route: str,
    final_status: str,
    retry_allowed: bool,
) -> str:
    if route == "accepted":
        return "accepted"
    if route == "ask_user":
        return "draft"
    if retry_allowed:
        return "retry_prepared"
    if final_status == "failed":
        return "failed"
    return "blocked"
