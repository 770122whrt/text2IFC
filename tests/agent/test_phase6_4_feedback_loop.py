import json

from text2ifc_agent.feedback_loop import (
    FEEDBACK_ROUNDS_SCHEMA_VERSION,
    plan_feedback_round,
    write_feedback_artifacts,
    write_feedback_rounds,
)
from text2ifc_agent.issues import Issue


def _issue(
    issue_id="issue_missing_door",
    *,
    owner="generator",
    issue_type="missing_entity",
    route="regenerate_json",
    retryable=True,
    evidence="Expected element is missing.",
):
    return Issue(
        issue_id=issue_id,
        source="audit",
        severity="blocking",
        owner=owner,
        issue_type=issue_type,
        evidence=evidence,
        suggested_route=route,
        retryable=retryable,
    )


def test_feedback_round_contract_and_persistence(tmp_path):
    round_record = plan_feedback_round(
        source_stage="audit",
        issues=[_issue()],
        previous_issue_count=3,
        current_feedback_round=0,
    )

    assert round_record["round_index"] == 0
    assert round_record["source_stage"] == "audit"
    assert round_record["input_issue_count"] == 3
    assert round_record["output_issue_count"] == 1
    assert round_record["issue_delta"] == 2
    assert round_record["route"] == "regenerate_json"
    assert round_record["target_stage"] == "generator"
    assert round_record["retry_allowed"] is True
    assert round_record["attempted_action"] == "prepare_generator_feedback"
    assert round_record["terminal_status"] == "retry_prepared"

    path = write_feedback_rounds(tmp_path, [round_record])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == FEEDBACK_ROUNDS_SCHEMA_VERSION
    assert payload["rounds"][0]["route_decision"]["route"] == "regenerate_json"


def test_feedback_round_stops_when_issue_count_does_not_improve():
    round_record = plan_feedback_round(
        source_stage="repair",
        issues=[_issue()],
        previous_issue_count=1,
        current_feedback_round=1,
    )

    assert round_record["issue_delta"] == 0
    assert round_record["retry_allowed"] is False
    assert round_record["attempted_action"] == "stop_non_improving"
    assert round_record["terminal_status"] == "blocked_non_improving"


def test_feedback_round_stops_after_default_two_round_limit():
    round_record = plan_feedback_round(
        source_stage="generator",
        issues=[_issue()],
        previous_issue_count=3,
        current_feedback_round=2,
    )

    assert round_record["max_feedback_rounds"] == 2
    assert round_record["retry_allowed"] is False
    assert round_record["attempted_action"] == "stop_attempt_limit"
    assert round_record["terminal_status"] == "blocked_attempt_limit"


def test_feedback_round_does_not_automatically_retry_user_fact_routes():
    round_record = plan_feedback_round(
        source_stage="design_brief",
        issues=[
            _issue(
                issue_id="issue_user_missing",
                owner="user",
                issue_type="missing_required_fact",
                route="ask_user",
            )
        ],
        previous_issue_count=None,
        current_feedback_round=0,
    )

    assert round_record["route"] == "ask_user"
    assert round_record["target_stage"] == "user"
    assert round_record["retry_allowed"] is False
    assert round_record["attempted_action"] == "stop_for_user_input"
    assert round_record["terminal_status"] == "draft"


def test_feedback_round_dispatch_boundaries_for_supported_routes():
    cases = [
        (
            _issue(
                owner="design_brief",
                issue_type="changed_original_request",
                route="revise_design_brief",
            ),
            "design_brief",
            "prepare_design_brief_feedback",
        ),
        (_issue(route="regenerate_json"), "generator", "prepare_generator_feedback"),
        (
            _issue(owner="repair", issue_type="schema_mismatch", route="repair_json"),
            "repair",
            "prepare_repair_feedback",
        ),
        (
            _issue(owner="schema", issue_type="unsupported_schema_capability", route="blocked_as_unsupported", retryable=False),
            "schema",
            "stop_unsupported",
        ),
        (
            _issue(owner="gate", issue_type="gate_false_positive", route="gate_issue", retryable=False),
            "gate",
            "stop_gate_review",
        ),
        (
            _issue(owner="runtime", issue_type="runtime_error", route="runtime_blocked", retryable=False),
            "runtime",
            "stop_runtime_blocked",
        ),
    ]

    for issue, target_stage, attempted_action in cases:
        round_record = plan_feedback_round(
            source_stage="audit",
            issues=[issue],
            previous_issue_count=3,
            current_feedback_round=0,
        )
        assert round_record["target_stage"] == target_stage
        assert round_record["attempted_action"] == attempted_action


def test_feedback_artifacts_append_rounds_instead_of_overwriting(tmp_path):
    first = write_feedback_artifacts(
        tmp_path,
        source_stage="audit",
        issues=[_issue(issue_id="issue_round_1")],
        current_feedback_round=0,
    )
    second = write_feedback_artifacts(
        tmp_path,
        source_stage="geometry_gate",
        issues=[_issue(issue_id="issue_round_2")],
        previous_issue_count=2,
        current_feedback_round=1,
    )

    payload = json.loads(
        (tmp_path / "feedback-rounds.json").read_text(encoding="utf-8")
    )
    assert [record["round_index"] for record in payload["rounds"]] == [0, 1]
    assert payload["rounds"][0] == first
    assert payload["rounds"][1] == second


def test_equal_issue_count_can_retry_when_issue_set_changed(tmp_path):
    first_issue = _issue(
        issue_id="issue_opening_bounds",
        issue_type="geometry_invalid",
    )
    second_issue = _issue(
        issue_id="issue_space_placement",
        issue_type="semantic_mismatch",
    )
    write_feedback_artifacts(
        tmp_path,
        source_stage="gate",
        issues=[first_issue],
        current_feedback_round=0,
    )

    second = write_feedback_artifacts(
        tmp_path,
        source_stage="audit",
        issues=[second_issue],
        previous_issue_count=1,
        current_feedback_round=1,
    )

    assert second["issue_delta"] == 0
    assert second["retry_allowed"] is True
    assert second["attempted_action"] == "prepare_generator_feedback"
    assert second["terminal_status"] == "retry_prepared"


def test_same_issue_code_can_retry_when_structured_evidence_changed(tmp_path):
    write_feedback_artifacts(
        tmp_path,
        source_stage="audit",
        issues=[
            _issue(
                issue_type="geometry_invalid",
                evidence="OPENING_FILLING_ORIENTATION_MISMATCH: opening vs host",
            )
        ],
        current_feedback_round=0,
    )

    second = write_feedback_artifacts(
        tmp_path,
        source_stage="audit",
        issues=[
            _issue(
                issue_type="geometry_invalid",
                evidence="OPENING_FILLING_ORIENTATION_MISMATCH: filling vs opening",
            )
        ],
        previous_issue_count=1,
        current_feedback_round=1,
    )

    assert second["issue_set_changed"] is True
    assert second["retry_allowed"] is True
    assert second["attempted_action"] == "prepare_generator_feedback"
