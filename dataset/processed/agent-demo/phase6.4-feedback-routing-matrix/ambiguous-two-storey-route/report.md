# Phase 6.4 Feedback Routing Run Report

Generated from run artifacts. This report is the human review entry point.

## Original Input

```text
创建一个两层空间，布局随意。
```

[input.txt](input.txt)

## Transcript

```json
[
  {
    "content": "创建一个两层空间，布局随意。",
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
      "evidence": "Design Brief over-specified ambiguous layout.",
      "expected_fact_ref": null,
      "issue_id": "issue_ambiguous_two_storey_route_0001",
      "issue_type": "changed_original_request",
      "owner": "design_brief",
      "retryable": true,
      "severity": "blocking",
      "source": "audit",
      "suggested_route": "revise_design_brief"
    }
  ],
  "schema_version": "text2ifc/issues/1.0"
}
```

[issues.json](issues.json)

## Route Decision

- route: `revise_design_brief`
- target_stage: `design_brief`
- final_status: `blocked`

```json
{
  "blocking_issue_ids": [
    "issue_ambiguous_two_storey_route_0001"
  ],
  "current_feedback_round": 0,
  "final_status": "blocked",
  "human_review_required": false,
  "max_feedback_rounds": 2,
  "reason": "Route revise_design_brief selected from 1 issue(s); first issue issue_ambiguous_two_storey_route_0001 is changed_original_request owned by design_brief.",
  "retry_allowed": true,
  "route": "revise_design_brief",
  "schema_version": "text2ifc/route-decision/2.0",
  "source_issue_count": 1,
  "target_stage": "design_brief"
}
```

[route-decision.json](route-decision.json)

## Feedback Rounds

```json
{
  "rounds": [
    {
      "attempted_action": "prepare_design_brief_feedback",
      "input_issue_count": 1,
      "issue_delta": null,
      "issues": [
        {
          "actual_ref": null,
          "evidence": "Design Brief over-specified ambiguous layout.",
          "expected_fact_ref": null,
          "issue_id": "issue_ambiguous_two_storey_route_0001",
          "issue_type": "changed_original_request",
          "owner": "design_brief",
          "retryable": true,
          "severity": "blocking",
          "source": "audit",
          "suggested_route": "revise_design_brief"
        }
      ],
      "max_feedback_rounds": 2,
      "output_issue_count": 1,
      "retry_allowed": true,
      "round_index": 0,
      "route": "revise_design_brief",
      "route_decision": {
        "blocking_issue_ids": [
          "issue_ambiguous_two_storey_route_0001"
        ],
        "current_feedback_round": 0,
        "final_status": "blocked",
        "human_review_required": false,
        "max_feedback_rounds": 2,
        "reason": "Route revise_design_brief selected from 1 issue(s); first issue issue_ambiguous_two_storey_route_0001 is changed_original_request owned by design_brief.",
        "retry_allowed": true,
        "route": "revise_design_brief",
        "schema_version": "text2ifc/route-decision/2.0",
        "source_issue_count": 1,
        "target_stage": "design_brief"
      },
      "schema_version": "text2ifc/feedback-round/1.0",
      "source_stage": "audit",
      "target_stage": "design_brief",
      "terminal_status": "retry_prepared"
    }
  ],
  "schema_version": "text2ifc/feedback-rounds/1.0"
}
```

[feedback-rounds.json](feedback-rounds.json)

## Final Status

- final_status: `blocked`
- failure_owner: `design_brief`
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
