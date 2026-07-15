# Phase 6.4 Feedback Routing Run Report

Generated from run artifacts. This report is the human review entry point.

## Original Input

```text
创建当前编译器不支持的复杂楼梯。
```

[input.txt](input.txt)

## Transcript

```json
[
  {
    "content": "创建当前编译器不支持的复杂楼梯。",
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
      "evidence": "Compiler cannot emit this feature yet.",
      "expected_fact_ref": null,
      "issue_id": "issue_unsupported_compiler_feature_0001",
      "issue_type": "compiler_unsupported_feature",
      "owner": "compiler",
      "retryable": false,
      "severity": "blocking",
      "source": "compiler",
      "suggested_route": "blocked_as_unsupported"
    }
  ],
  "schema_version": "text2ifc/issues/1.0"
}
```

[issues.json](issues.json)

## Route Decision

- route: `blocked_as_unsupported`
- target_stage: `compiler`
- final_status: `blocked`

```json
{
  "blocking_issue_ids": [
    "issue_unsupported_compiler_feature_0001"
  ],
  "current_feedback_round": 0,
  "final_status": "blocked",
  "human_review_required": false,
  "max_feedback_rounds": 2,
  "reason": "Route blocked_as_unsupported selected from 1 issue(s); first issue issue_unsupported_compiler_feature_0001 is compiler_unsupported_feature owned by compiler.",
  "retry_allowed": false,
  "route": "blocked_as_unsupported",
  "schema_version": "text2ifc/route-decision/2.0",
  "source_issue_count": 1,
  "target_stage": "compiler"
}
```

[route-decision.json](route-decision.json)

## Feedback Rounds

```json
{
  "rounds": [
    {
      "attempted_action": "stop_unsupported",
      "input_issue_count": 1,
      "issue_delta": null,
      "issues": [
        {
          "actual_ref": null,
          "evidence": "Compiler cannot emit this feature yet.",
          "expected_fact_ref": null,
          "issue_id": "issue_unsupported_compiler_feature_0001",
          "issue_type": "compiler_unsupported_feature",
          "owner": "compiler",
          "retryable": false,
          "severity": "blocking",
          "source": "compiler",
          "suggested_route": "blocked_as_unsupported"
        }
      ],
      "max_feedback_rounds": 2,
      "output_issue_count": 1,
      "retry_allowed": false,
      "round_index": 0,
      "route": "blocked_as_unsupported",
      "route_decision": {
        "blocking_issue_ids": [
          "issue_unsupported_compiler_feature_0001"
        ],
        "current_feedback_round": 0,
        "final_status": "blocked",
        "human_review_required": false,
        "max_feedback_rounds": 2,
        "reason": "Route blocked_as_unsupported selected from 1 issue(s); first issue issue_unsupported_compiler_feature_0001 is compiler_unsupported_feature owned by compiler.",
        "retry_allowed": false,
        "route": "blocked_as_unsupported",
        "schema_version": "text2ifc/route-decision/2.0",
        "source_issue_count": 1,
        "target_stage": "compiler"
      },
      "schema_version": "text2ifc/feedback-round/1.0",
      "source_stage": "compiler",
      "target_stage": "compiler",
      "terminal_status": "blocked"
    }
  ],
  "schema_version": "text2ifc/feedback-rounds/1.0"
}
```

[feedback-rounds.json](feedback-rounds.json)

## Final Status

- final_status: `blocked`
- failure_owner: `compiler`
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
