# Phase 6.4 Feedback Routing Run Report

Generated from run artifacts. This report is the human review entry point.

## Original Input

```text
创建三层建筑并包含楼梯连接。
```

[input.txt](input.txt)

## Transcript

```json
[
  {
    "content": "创建三层建筑并包含楼梯连接。",
    "role": "user"
  }
]
```

[conversation.json](conversation.json)

## Design Brief

- [design-brief/design-brief.json](design-brief/design-brief.json)

## BIM JSON or Draft

- [generator/candidate.json](generator/candidate.json)

## Validation

- [generator/validation.json](generator/validation.json)

## Compiler and Reopen

- [ifc-verification.json](ifc-verification.json)

## Gates

- [gate-summary.json](gate-summary.json)
- [geometry-feedback.json](geometry-feedback.json)

## Audit

- [audit/audit-report.json](audit/audit-report.json)

## Normalized Issues

```json
{
  "issues": [
    {
      "actual_ref": null,
      "evidence": "A non-two-storey assignment is missing without hard-coded room names.",
      "expected_fact_ref": null,
      "issue_id": "issue_three_storey_dynamic_route_0001",
      "issue_type": "missing_storey_assignment",
      "owner": "generator",
      "retryable": true,
      "severity": "blocking",
      "source": "deterministic_gate",
      "suggested_route": "regenerate_json"
    }
  ],
  "schema_version": "text2ifc/issues/1.0"
}
```

[issues.json](issues.json)

## Route Decision

- route: `regenerate_json`
- target_stage: `generator`
- final_status: `blocked`

```json
{
  "blocking_issue_ids": [
    "issue_three_storey_dynamic_route_0001"
  ],
  "current_feedback_round": 0,
  "final_status": "blocked",
  "human_review_required": false,
  "max_feedback_rounds": 2,
  "reason": "Route regenerate_json selected from 1 issue(s); first issue issue_three_storey_dynamic_route_0001 is missing_storey_assignment owned by generator.",
  "retry_allowed": true,
  "route": "regenerate_json",
  "schema_version": "text2ifc/route-decision/2.0",
  "source_issue_count": 1,
  "target_stage": "generator"
}
```

[route-decision.json](route-decision.json)

## Feedback Rounds

```json
{
  "rounds": [
    {
      "attempted_action": "prepare_generator_feedback",
      "input_issue_count": 1,
      "issue_delta": null,
      "issues": [
        {
          "actual_ref": null,
          "evidence": "A non-two-storey assignment is missing without hard-coded room names.",
          "expected_fact_ref": null,
          "issue_id": "issue_three_storey_dynamic_route_0001",
          "issue_type": "missing_storey_assignment",
          "owner": "generator",
          "retryable": true,
          "severity": "blocking",
          "source": "deterministic_gate",
          "suggested_route": "regenerate_json"
        }
      ],
      "max_feedback_rounds": 2,
      "output_issue_count": 1,
      "retry_allowed": true,
      "round_index": 0,
      "route": "regenerate_json",
      "route_decision": {
        "blocking_issue_ids": [
          "issue_three_storey_dynamic_route_0001"
        ],
        "current_feedback_round": 0,
        "final_status": "blocked",
        "human_review_required": false,
        "max_feedback_rounds": 2,
        "reason": "Route regenerate_json selected from 1 issue(s); first issue issue_three_storey_dynamic_route_0001 is missing_storey_assignment owned by generator.",
        "retry_allowed": true,
        "route": "regenerate_json",
        "schema_version": "text2ifc/route-decision/2.0",
        "source_issue_count": 1,
        "target_stage": "generator"
      },
      "schema_version": "text2ifc/feedback-round/1.0",
      "source_stage": "gate",
      "target_stage": "generator",
      "terminal_status": "retry_prepared"
    }
  ],
  "schema_version": "text2ifc/feedback-rounds/1.0"
}
```

[feedback-rounds.json](feedback-rounds.json)

## Final Status

- final_status: `blocked`
- failure_owner: `generator`
- output_type: `none`

## Evidence Paths

- [input.txt](input.txt)
- [conversation.json](conversation.json)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [audit/audit-report.json](audit/audit-report.json)
- [issues.json](issues.json)
- [route-decision.json](route-decision.json)
- [feedback-rounds.json](feedback-rounds.json)
