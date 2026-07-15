"""Route decisions derived from Gate/Audit evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .gate_audit_bundle import (
    gate_summary_hash,
    hash_json_file,
    validate_gate_summary_binding,
)
from .issues import Issue, issue_to_dict


ROUTE_DECISION_SCHEMA_VERSION = "text2ifc/route-decision/1.0"
ROUTE_DECISION_V2_SCHEMA_VERSION = "text2ifc/route-decision/2.0"

CANONICAL_ROUTES = {
    "accept",
    "design_revision_required",
    "generator_regeneration_required",
    "local_repair_required",
    "draft_required",
    "blocked_gate_dispute",
    "blocked_failure",
}

_DESIGN_CODES = {
    "DESIGN_BRIEF_FACT_OMITTED",
    "DESIGN_BRIEF_EXPECTED_FACT_MISSING",
    "EXPECTED_FACTS_INCOMPLETE",
}
_GENERATOR_CODES = {
    "EXPECTED_ENTITY_MISSING",
    "STOREY_CONTAINMENT_MISMATCH",
    "CONTAINMENT_INCOMPLETE",
}
_REPAIR_CODES = {
    "HOST_WALL_MISMATCH",
    "OPENING_FILL_RELATIONSHIP_MISSING",
    "VOID_RELATIONSHIP_MISSING",
    "PLACEMENT_RELATIONSHIP_MISMATCH",
}
_DRAFT_CODES = {
    "UNSUPPORTED_FACT",
    "UNKNOWN_CAPABILITY_FACT",
    "REQUIRED_USER_FACT_MISSING",
}
_DISPUTE_CODES = {
    "GATE_APPLICABILITY_INCONCLUSIVE",
    "GATE_DISPUTE_CANDIDATE",
}


def write_route_decision(
    *,
    case_dir: Path | str,
    audit: Mapping[str, Any] | None = None,
    attempt_index: int = 0,
    previous_issue_count: int | None = None,
    max_attempts: int = 1,
) -> dict[str, Any]:
    """Write a bounded route decision for the current gate summary."""
    root = Path(case_dir)
    gate_summary_path = root / "gate-summary.json"
    if not gate_summary_path.is_file():
        raise ValueError("route decision requires gate-summary.json")
    gate_summary = _read_json(gate_summary_path)

    binding_issues = validate_gate_summary_binding(
        case_dir=root,
        summary=gate_summary,
    )
    gate_issues = _gate_issues(gate_summary)
    audit_issues = _audit_issues(audit or {})
    source_issues = [*binding_issues, *gate_issues, *audit_issues]
    issue_codes = sorted({str(issue.get("code", "UNKNOWN")) for issue in source_issues})
    current_issue_count = len(source_issues)

    route = _choose_route(
        gate_summary=gate_summary,
        audit=audit or {},
        issue_codes=issue_codes,
        binding_issues=binding_issues,
    )
    if attempt_index >= max_attempts and route not in {"accept", "draft_required"}:
        route = "blocked_failure"
        issue_codes = sorted({*issue_codes, "ATTEMPT_LIMIT_EXHAUSTED"})
        source_issues.append(
            {
                "code": "ATTEMPT_LIMIT_EXHAUSTED",
                "path": "/attempt_index",
                "message": "Route attempt limit was reached.",
            }
        )
        current_issue_count = len(source_issues)

    issue_delta = None
    if previous_issue_count is not None:
        issue_delta = previous_issue_count - current_issue_count
        if route not in {"accept", "draft_required"} and current_issue_count >= previous_issue_count:
            route = "blocked_failure"
            issue_codes = sorted({*issue_codes, "NON_IMPROVING_ROUTE_ATTEMPT"})
            source_issues.append(
                {
                    "code": "NON_IMPROVING_ROUTE_ATTEMPT",
                    "path": "/issue_delta",
                    "message": "Issue count did not decrease after a bounded attempt.",
                }
            )
            current_issue_count = len(source_issues)
            issue_delta = previous_issue_count - current_issue_count

    decision = {
        "schema_version": ROUTE_DECISION_SCHEMA_VERSION,
        "route": route,
        "owner_stage": _owner_stage(route),
        "allowed_next_action": _allowed_next_action(route),
        "attempt_index": attempt_index,
        "max_attempts": max_attempts,
        "input_issue_count": previous_issue_count
        if previous_issue_count is not None
        else current_issue_count,
        "output_issue_count": current_issue_count,
        "issue_delta": issue_delta,
        "candidate_hash": gate_summary.get("candidate_hash"),
        "expected_facts_hash": gate_summary.get("expected_facts_hash"),
        "gate_summary_hash": gate_summary_hash(gate_summary_path),
        "source_issue_codes": issue_codes,
        "source_issues": source_issues,
        "source_gates": [
            {
                "name": gate.get("name"),
                "status": gate.get("status"),
                "issue_codes": gate.get("issue_codes", []),
            }
            for gate in gate_summary.get("gates", [])
            if isinstance(gate, Mapping)
        ],
        "route_basis": {
            "gate_summary_overall_status": gate_summary.get("overall_status"),
            "audit_recommendation": audit.get("recommendation") if audit else None,
            "audit_blocking": audit.get("blocking") if audit else None,
            "non_two_storey_evidence": _has_non_two_storey_evidence(source_issues),
        },
    }
    _write_json(root / "route-decision.json", decision)
    return decision


def validate_route_decision_binding(
    *,
    case_dir: Path | str,
    decision: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return evidence binding issues for a persisted route decision."""
    root = Path(case_dir)
    issues: list[dict[str, Any]] = []
    candidate_path = root / "generator" / "candidate.json"
    if candidate_path.is_file() and decision.get("candidate_hash") != hash_json_file(candidate_path):
        issues.append(
            {
                "code": "ROUTE_CANDIDATE_HASH_MISMATCH",
                "path": "/candidate_hash",
                "expected": hash_json_file(candidate_path),
                "actual": decision.get("candidate_hash"),
            }
        )
    expected_path = root / "expected-facts.json"
    if expected_path.is_file() and decision.get("expected_facts_hash") != hash_json_file(expected_path):
        issues.append(
            {
                "code": "ROUTE_EXPECTED_FACTS_HASH_MISMATCH",
                "path": "/expected_facts_hash",
                "expected": hash_json_file(expected_path),
                "actual": decision.get("expected_facts_hash"),
            }
        )
    gate_summary_path = root / "gate-summary.json"
    if gate_summary_path.is_file() and decision.get("gate_summary_hash") != gate_summary_hash(gate_summary_path):
        issues.append(
            {
                "code": "ROUTE_GATE_SUMMARY_HASH_MISMATCH",
                "path": "/gate_summary_hash",
                "expected": gate_summary_hash(gate_summary_path),
                "actual": decision.get("gate_summary_hash"),
            }
        )
    return issues


def _choose_route(
    *,
    gate_summary: Mapping[str, Any],
    audit: Mapping[str, Any],
    issue_codes: list[str],
    binding_issues: list[dict[str, Any]],
) -> str:
    if binding_issues:
        return "blocked_failure"
    if gate_summary.get("overall_status") == "passed" and not audit.get("blocking"):
        return "accept"
    codes = set(issue_codes)
    if codes & _DISPUTE_CODES:
        return "blocked_gate_dispute"
    if codes & _DESIGN_CODES:
        return "design_revision_required"
    if codes & _DRAFT_CODES:
        return "draft_required"
    if "EXPECTED_ENTITY_MISSING" in codes:
        return "generator_regeneration_required"
    if codes <= _REPAIR_CODES and codes:
        return "local_repair_required"
    if codes & _REPAIR_CODES and not (codes & _GENERATOR_CODES):
        return "local_repair_required"
    if codes & _GENERATOR_CODES:
        return "generator_regeneration_required"
    if audit.get("recommendation") == "revise" and audit.get("blocking"):
        return "generator_regeneration_required"
    return "blocked_failure"


def _gate_issues(gate_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for gate in gate_summary.get("gates", []):
        if not isinstance(gate, Mapping):
            continue
        if gate.get("status") not in {"failed", "blocked", "inconclusive"}:
            continue
        for issue in gate.get("issues", []):
            if isinstance(issue, Mapping):
                issues.append(
                    {
                        "gate": gate.get("name"),
                        "status": gate.get("status"),
                        **dict(issue),
                    }
                )
        if not gate.get("issues"):
            issues.append(
                {
                    "gate": gate.get("name"),
                    "status": gate.get("status"),
                    "code": "GATE_FAILED_WITHOUT_ISSUE",
                    "path": f"/gates/{gate.get('name')}",
                }
            )
    return issues


def _audit_issues(audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    findings = audit.get("findings", [])
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if not isinstance(finding, Mapping):
                continue
            code = finding.get("code") or finding.get("issue_code") or "AUDIT_FINDING"
            result.append(
                {
                    "gate": "audit",
                    "code": str(code),
                    "path": str(finding.get("path", f"/findings/{index}")),
                    "message": str(finding.get("message", "")),
                }
            )
    if audit.get("blocking") and not result:
        result.append(
            {
                "gate": "audit",
                "code": "AUDIT_BLOCKING",
                "path": "/blocking",
            }
        )
    return result


def _owner_stage(route: str) -> str:
    return {
        "accept": "none",
        "design_revision_required": "design_brief",
        "generator_regeneration_required": "generator",
        "local_repair_required": "repair",
        "draft_required": "user_clarification",
        "blocked_gate_dispute": "gate_review",
        "blocked_failure": "orchestrator",
    }[route]


def _allowed_next_action(route: str) -> str:
    return {
        "accept": "compile_or_report_acceptance",
        "design_revision_required": "rerun_design_brief_with_feedback",
        "generator_regeneration_required": "rerun_generator_with_gate_feedback",
        "local_repair_required": "run_local_repair_with_gate_feedback",
        "draft_required": "ask_user_or_write_draft",
        "blocked_gate_dispute": "manual_gate_review",
        "blocked_failure": "stop_with_evidence",
    }[route]


def _has_non_two_storey_evidence(issues: list[Mapping[str, Any]]) -> bool:
    for issue in issues:
        storey = issue.get("expected_storey") or issue.get("actual_storey")
        if isinstance(storey, str) and storey not in {"storey-1", "storey-2"}:
            return True
        path = str(issue.get("path", ""))
        if "level-3" in path or "storey-3" in path:
            return True
    return False


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def decide_route_from_issues(
    issues: Sequence[Issue | Mapping[str, Any]],
    *,
    current_feedback_round: int,
    max_feedback_rounds: int,
    human_review_required: bool = False,
) -> dict[str, Any]:
    """Aggregate normalized Phase 6.4 issues into RouteDecision v2."""

    issue_payloads = [issue_to_dict(issue) for issue in issues]
    blocking = [
        issue
        for issue in issue_payloads
        if issue["severity"] in {"warning", "blocking", "fatal"}
    ]
    route, target_stage = _choose_v2_route(blocking)
    retry_allowed = (
        route
        in {"ask_user", "revise_design_brief", "regenerate_json", "repair_json", "provider_retry"}
        and current_feedback_round < max_feedback_rounds
    )
    final_status = _v2_final_status(route, blocking)
    decision = {
        "schema_version": ROUTE_DECISION_V2_SCHEMA_VERSION,
        "final_status": final_status,
        "route": route,
        "reason": _v2_reason(route, blocking),
        "blocking_issue_ids": [issue["issue_id"] for issue in blocking],
        "retry_allowed": retry_allowed,
        "target_stage": target_stage,
        "max_feedback_rounds": max_feedback_rounds,
        "current_feedback_round": current_feedback_round,
        "human_review_required": human_review_required,
    }
    if route != "accepted":
        decision["source_issue_count"] = len(blocking)
    return decision


def _choose_v2_route(issues: list[dict[str, Any]]) -> tuple[str, str]:
    if not issues:
        return "accepted", "none"
    fatal_runtime = _first_issue(issues, owner="runtime", issue_type="runtime_error")
    if fatal_runtime is not None:
        return "runtime_blocked", "runtime"
    provider_truncation = _first_issue(issues, owner="provider", issue_type="provider_truncation")
    if provider_truncation is not None:
        return "provider_retry", "provider"
    unsupported_schema = _first_issue(
        issues,
        owner="schema",
        issue_type="unsupported_schema_capability",
    )
    if unsupported_schema is not None:
        return "blocked_as_unsupported", "schema"
    unsupported_compiler = _first_issue(
        issues,
        owner="compiler",
        issue_type="compiler_unsupported_feature",
    )
    if unsupported_compiler is not None:
        return "blocked_as_unsupported", "compiler"
    missing_user_fact = _first_issue(
        issues,
        owner="user",
        issue_type="missing_required_fact",
    ) or _first_issue(issues, owner="user", issue_type="draft_unresolved_path")
    if missing_user_fact is not None:
        return "ask_user", "user"
    design_issue = _first_issue(
        issues,
        owner="design_brief",
        issue_type="semantic_mismatch",
    ) or _first_issue(
        issues,
        owner="design_brief",
        issue_type="changed_original_request",
    )
    if design_issue is not None:
        return "revise_design_brief", "design_brief"
    repair_issue = _first_issue(issues, owner="repair", issue_type="invalid_json") or _first_issue(
        issues,
        owner="repair",
        issue_type="schema_mismatch",
    )
    if repair_issue is not None:
        return "repair_json", "repair"
    generator_issue = _first_owned_issue(
        issues,
        owner="generator",
        issue_types={
            "missing_entity",
            "missing_relationship",
            "missing_host",
            "missing_storey_assignment",
            "missing_space_boundary",
            "missing_vertical_connection",
        },
    )
    if generator_issue is not None:
        return "regenerate_json", "generator"
    gate_issue = _first_issue(issues, owner="gate", issue_type="gate_false_positive")
    if gate_issue is not None:
        return "gate_issue", "gate"
    suggested = _first_suggested_route(issues)
    if suggested is not None:
        return suggested, _target_stage_for_v2_route(suggested, issues[0])
    return "runtime_blocked", "runtime"


def _first_issue(
    issues: list[dict[str, Any]],
    *,
    owner: str,
    issue_type: str,
) -> dict[str, Any] | None:
    for issue in issues:
        if issue["owner"] == owner and issue["issue_type"] == issue_type:
            return issue
    return None


def _first_owned_issue(
    issues: list[dict[str, Any]],
    *,
    owner: str,
    issue_types: set[str],
) -> dict[str, Any] | None:
    for issue in issues:
        if issue["owner"] == owner and issue["issue_type"] in issue_types:
            return issue
    return None


def _first_suggested_route(issues: list[dict[str, Any]]) -> str | None:
    for issue in issues:
        route = issue.get("suggested_route")
        if route != "accepted":
            return str(route)
    return None


def _target_stage_for_v2_route(route: str, issue: Mapping[str, Any]) -> str:
    return {
        "accepted": "none",
        "ask_user": "user",
        "revise_design_brief": "design_brief",
        "regenerate_json": "generator",
        "repair_json": "repair",
        "blocked_as_unsupported": str(issue.get("owner", "schema")),
        "gate_issue": "gate",
        "provider_retry": "provider",
        "runtime_blocked": "runtime",
    }[route]


def _v2_final_status(route: str, issues: list[dict[str, Any]]) -> str:
    if route == "accepted":
        return "accepted"
    if any(issue["severity"] == "fatal" for issue in issues):
        return "failed"
    if route == "ask_user":
        return "draft"
    return "blocked"


def _v2_reason(route: str, issues: list[dict[str, Any]]) -> str:
    if route == "accepted":
        return "No blocking or warning issues were found."
    if not issues:
        return f"Route {route} selected without issue evidence."
    first = issues[0]
    return (
        f"Route {route} selected from {len(issues)} issue(s); "
        f"first issue {first['issue_id']} is {first['issue_type']} owned by {first['owner']}."
    )
