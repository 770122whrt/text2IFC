import pytest

from text2ifc_agent.issues import Issue
from text2ifc_agent.route_decision import (
    ROUTE_DECISION_V2_SCHEMA_VERSION,
    decide_route_from_issues,
)


@pytest.mark.parametrize(
    ("issue", "route", "target_stage", "final_status"),
    [
        (
            Issue(
                issue_id="issue_user_missing",
                source="semantic_validation",
                severity="blocking",
                owner="user",
                issue_type="missing_required_fact",
                evidence="Wall thickness is required but absent.",
                suggested_route="ask_user",
                retryable=True,
            ),
            "ask_user",
            "user",
            "draft",
        ),
        (
            Issue(
                issue_id="issue_design_changed",
                source="audit",
                severity="blocking",
                owner="design_brief",
                issue_type="changed_original_request",
                evidence="Design Brief changed the original request.",
                suggested_route="revise_design_brief",
                retryable=True,
            ),
            "revise_design_brief",
            "design_brief",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_missing_door",
                source="audit",
                severity="blocking",
                owner="generator",
                issue_type="missing_entity",
                evidence="Expected IfcDoor is missing.",
                suggested_route="regenerate_json",
                retryable=True,
            ),
            "regenerate_json",
            "generator",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_repair_schema",
                source="schema_validation",
                severity="blocking",
                owner="repair",
                issue_type="schema_mismatch",
                evidence="Candidate has a repairable schema mismatch.",
                suggested_route="repair_json",
                retryable=True,
            ),
            "repair_json",
            "repair",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_schema_unsupported",
                source="semantic_validation",
                severity="blocking",
                owner="schema",
                issue_type="unsupported_schema_capability",
                evidence="The requested semantic fact is not supported by BIM JSON.",
                suggested_route="blocked_as_unsupported",
                retryable=False,
            ),
            "blocked_as_unsupported",
            "schema",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_compiler_unsupported",
                source="compiler",
                severity="blocking",
                owner="compiler",
                issue_type="compiler_unsupported_feature",
                evidence="The compiler cannot emit this IFC feature.",
                suggested_route="blocked_as_unsupported",
                retryable=False,
            ),
            "blocked_as_unsupported",
            "compiler",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_provider_length",
                source="provider",
                severity="blocking",
                owner="provider",
                issue_type="provider_truncation",
                evidence="Provider returned finish_reason=length.",
                suggested_route="provider_retry",
                retryable=True,
            ),
            "provider_retry",
            "provider",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_gate_false_positive",
                source="deterministic_gate",
                severity="warning",
                owner="gate",
                issue_type="gate_false_positive",
                evidence="Gate applicability is disputed.",
                suggested_route="gate_issue",
                retryable=False,
            ),
            "gate_issue",
            "gate",
            "blocked",
        ),
        (
            Issue(
                issue_id="issue_runtime_error",
                source="runtime",
                severity="fatal",
                owner="runtime",
                issue_type="runtime_error",
                evidence="Runtime exception interrupted the run.",
                suggested_route="runtime_blocked",
                retryable=False,
            ),
            "runtime_blocked",
            "runtime",
            "failed",
        ),
    ],
)
def test_route_decision_v2_maps_issue_to_target_stage(issue, route, target_stage, final_status):
    decision = decide_route_from_issues(
        [issue],
        current_feedback_round=0,
        max_feedback_rounds=2,
    )

    assert decision["schema_version"] == ROUTE_DECISION_V2_SCHEMA_VERSION
    assert decision["final_status"] == final_status
    assert decision["route"] == route
    assert decision["target_stage"] == target_stage
    assert decision["blocking_issue_ids"] == [issue.issue_id]


def test_route_decision_v2_accepts_when_no_blocking_or_warning_issues():
    decision = decide_route_from_issues(
        [],
        current_feedback_round=0,
        max_feedback_rounds=2,
    )

    assert decision["final_status"] == "accepted"
    assert decision["route"] == "accepted"
    assert decision["target_stage"] == "none"
    assert decision["retry_allowed"] is False


@pytest.mark.parametrize(
    "issue",
    [
        Issue(
            issue_id="issue_audit_blocks",
            source="audit",
            severity="blocking",
            owner="audit",
            issue_type="semantic_mismatch",
            evidence="Audit found semantic mismatch.",
            suggested_route="revise_design_brief",
            retryable=True,
        ),
        Issue(
            issue_id="issue_gate_blocks",
            source="deterministic_gate",
            severity="blocking",
            owner="generator",
            issue_type="missing_relationship",
            evidence="A deterministic gate failed.",
            suggested_route="regenerate_json",
            retryable=True,
        ),
        Issue(
            issue_id="issue_draft_unresolved",
            source="schema_validation",
            severity="blocking",
            owner="user",
            issue_type="draft_unresolved_path",
            evidence="Draft contains unresolved required paths.",
            suggested_route="ask_user",
            retryable=True,
        ),
    ],
)
def test_blocking_audit_gate_and_draft_issues_cannot_be_accepted(issue):
    decision = decide_route_from_issues(
        [issue],
        current_feedback_round=0,
        max_feedback_rounds=2,
    )

    assert decision["final_status"] != "accepted"
    assert decision["route"] != "accepted"
