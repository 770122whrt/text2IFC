# Phase 6.4 Feedback Routing Run Report

Generated from run artifacts. This report is the human review entry point.

## Original Input

_Missing artifact._



## Transcript

_Missing artifact._



## Design Brief

- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)

## BIM JSON or Draft

- [generator/candidate.json](generator/candidate.json)
- [generator/parsed-output.json](generator/parsed-output.json)

## Validation

- [generator/validation.json](generator/validation.json)
- [semantic-coverage.json](semantic-coverage.json)

## Compiler and Reopen

- [ifc-verification.json](ifc-verification.json)
- [output.ifc](output.ifc)

## Gates

- [gate-summary.json](gate-summary.json)
- [geometry-feedback.json](geometry-feedback.json)

## Audit

- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)

## Normalized Issues

```json
{
  "issues": [],
  "schema_version": "text2ifc/issues/1.0"
}
```

[issues.json](issues.json)

## Route Decision

- route: `accepted`
- target_stage: `none`
- final_status: `accepted`

```json
{
  "blocking_issue_ids": [],
  "current_feedback_round": 0,
  "final_status": "accepted",
  "human_review_required": false,
  "max_feedback_rounds": 2,
  "reason": "No blocking or warning issues were found.",
  "retry_allowed": false,
  "route": "accepted",
  "schema_version": "text2ifc/route-decision/2.0",
  "target_stage": "none"
}
```

[route-decision.json](route-decision.json)

## Feedback Rounds

```json
{
  "rounds": [
    {
      "attempted_action": "none",
      "input_issue_count": 0,
      "issue_delta": null,
      "issues": [],
      "max_feedback_rounds": 2,
      "output_issue_count": 0,
      "retry_allowed": false,
      "round_index": 0,
      "route": "accepted",
      "route_decision": {
        "blocking_issue_ids": [],
        "current_feedback_round": 0,
        "final_status": "accepted",
        "human_review_required": false,
        "max_feedback_rounds": 2,
        "reason": "No blocking or warning issues were found.",
        "retry_allowed": false,
        "route": "accepted",
        "schema_version": "text2ifc/route-decision/2.0",
        "target_stage": "none"
      },
      "schema_version": "text2ifc/feedback-round/1.0",
      "source_stage": "final",
      "target_stage": "none",
      "terminal_status": "accepted"
    }
  ],
  "schema_version": "text2ifc/feedback-rounds/1.0"
}
```

[feedback-rounds.json](feedback-rounds.json)

## Final Status

- final_status: `accepted`
- failure_owner: `None`
- output_type: `ifc`

## Evidence Paths

- [design-brief/design-brief.json](design-brief/design-brief.json)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [gate-summary.json](gate-summary.json)
- [audit/audit-report.json](audit/audit-report.json)
- [issues.json](issues.json)
- [route-decision.json](route-decision.json)
- [feedback-rounds.json](feedback-rounds.json)
- [output.ifc](output.ifc)
