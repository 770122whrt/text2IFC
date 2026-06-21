"""Deterministic routing for generation failures and bounded repair."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ROUTES = {
    "no_repair_needed",
    "repair_attempted",
    "draft_required",
    "blocked_failure",
}


def route_generation_failure(
    *,
    previous_candidate: dict[str, Any] | None,
    validation_feedback: Sequence[Mapping[str, Any]],
    geometry_feedback: Sequence[Mapping[str, Any]],
    known_facts: Mapping[str, Any],
    repaired_candidate: dict[str, Any] | None = None,
    repaired_feedback: Sequence[Mapping[str, Any]] | None = None,
    blocking_reason: str | None = None,
) -> dict[str, Any]:
    """Choose one evidence-backed route without inventing missing facts."""
    input_issues = [*validation_feedback, *geometry_feedback]
    if blocking_reason:
        return _route("blocked_failure", blocking_reason=blocking_reason)
    if not input_issues:
        return _route("no_repair_needed")
    if previous_candidate is None:
        return _route(
            "blocked_failure",
            blocking_reason="failure feedback has no previous candidate",
        )

    known_paths = _value_paths(known_facts)
    required_paths = sorted(
        {
            str(path)
            for issue in input_issues
            for path in issue.get("required_fact_paths", [])
        }
    )
    missing_paths = [path for path in required_paths if path not in known_paths]
    if missing_paths:
        questions = [
            str(issue["question"])
            for issue in input_issues
            if issue.get("question")
            and any(
                path in missing_paths
                for path in issue.get("required_fact_paths", [])
            )
        ][:3]
        return _route(
            "draft_required",
            missing_fact_paths=missing_paths,
            questions=questions,
        )

    output_issues = list(repaired_feedback or [])
    input_codes = sorted({str(issue.get("code", "UNKNOWN")) for issue in input_issues})
    output_codes = sorted({str(issue.get("code", "UNKNOWN")) for issue in output_issues})
    attempt = {
        "attempt_number": 1,
        "input_issue_count": len(input_issues),
        "output_issue_count": len(output_issues),
        "fixed_issue_codes": sorted(set(input_codes) - set(output_codes)),
        "remaining_issue_codes": output_codes,
    }
    if repaired_candidate is not None and _is_draft(repaired_candidate):
        attempt["result_status"] = "draft"
        return _route("repair_attempted", repair_attempts=[attempt])
    if repaired_candidate is not None and len(output_issues) < len(input_issues):
        attempt["result_status"] = "improved"
        return _route("repair_attempted", repair_attempts=[attempt])
    if repaired_candidate is None:
        attempt["output_issue_count"] = None
        attempt["result_status"] = "pending"
        return _route("repair_attempted", repair_attempts=[attempt])
    attempt["result_status"] = "not_improved"
    return _route(
        "blocked_failure",
        repair_attempts=[attempt],
        blocking_reason="repair did not reduce issues or return Draft",
    )


def _route(route: str, **details: Any) -> dict[str, Any]:
    if route not in ROUTES:
        raise ValueError(f"unknown generation route: {route}")
    return {
        "route": route,
        "repair_attempts": details.pop("repair_attempts", []),
        **details,
    }


def _value_paths(value: Any, base: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{base}/{key}"
            paths.add(path)
            paths.update(_value_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{base}/{index}"
            paths.add(path)
            paths.update(_value_paths(child, path))
    return paths


def _is_draft(candidate: Mapping[str, Any]) -> bool:
    return candidate.get("draft_version") == "bim-json-draft/1.0"
