# Phase 6.4 Feedback Routing Run Report

Generated from run artifacts. This report is the human review entry point.

## Original Input

```text
创建两层建筑，但楼梯位置不知道。
```

[input.txt](input.txt)

## Transcript

```json
[
  {
    "content": "创建两层建筑，但楼梯位置不知道。",
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
      "evidence": "Stair location is required from the user.",
      "expected_fact_ref": null,
      "issue_id": "issue_clarification_two_storey_route_0001",
      "issue_type": "missing_required_fact",
      "owner": "user",
      "retryable": true,
      "severity": "blocking",
      "source": "semantic_validation",
      "suggested_route": "ask_user"
    }
  ],
  "schema_version": "text2ifc/issues/1.0"
}
```

[issues.json](issues.json)

## Route Decision

- route: `ask_user`
- target_stage: `user`
- final_status: `draft`

```json
{
  "blocking_issue_ids": [
    "issue_clarification_two_storey_route_0001"
  ],
  "current_feedback_round": 0,
  "final_status": "draft",
  "human_review_required": false,
  "max_feedback_rounds": 2,
  "reason": "Route ask_user selected from 1 issue(s); first issue issue_clarification_two_storey_route_0001 is missing_required_fact owned by user.",
  "retry_allowed": false,
  "route": "ask_user",
  "schema_version": "text2ifc/route-decision/2.0",
  "source_issue_count": 1,
  "target_stage": "user"
}
```

[route-decision.json](route-decision.json)

## Feedback Rounds

```json
{
  "rounds": [
    {
      "attempted_action": "stop_for_user_input",
      "input_issue_count": 1,
      "issue_delta": null,
      "issues": [
        {
          "actual_ref": null,
          "evidence": "Stair location is required from the user.",
          "expected_fact_ref": null,
          "issue_id": "issue_clarification_two_storey_route_0001",
          "issue_type": "missing_required_fact",
          "owner": "user",
          "retryable": true,
          "severity": "blocking",
          "source": "semantic_validation",
          "suggested_route": "ask_user"
        }
      ],
      "max_feedback_rounds": 2,
      "output_issue_count": 1,
      "retry_allowed": false,
      "round_index": 0,
      "route": "ask_user",
      "route_decision": {
        "blocking_issue_ids": [
          "issue_clarification_two_storey_route_0001"
        ],
        "current_feedback_round": 0,
        "final_status": "draft",
        "human_review_required": false,
        "max_feedback_rounds": 2,
        "reason": "Route ask_user selected from 1 issue(s); first issue issue_clarification_two_storey_route_0001 is missing_required_fact owned by user.",
        "retry_allowed": false,
        "route": "ask_user",
        "schema_version": "text2ifc/route-decision/2.0",
        "source_issue_count": 1,
        "target_stage": "user"
      },
      "schema_version": "text2ifc/feedback-round/1.0",
      "source_stage": "design_brief",
      "target_stage": "user",
      "terminal_status": "draft"
    }
  ],
  "schema_version": "text2ifc/feedback-rounds/1.0"
}
```

[feedback-rounds.json](feedback-rounds.json)

## Final Status

- final_status: `draft`
- failure_owner: `user`
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
