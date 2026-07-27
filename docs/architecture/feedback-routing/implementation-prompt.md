# Codex Prompt: Implement Language Policy and Feedback Routing for Text2IFC

> Document type: implementation prompt. The sibling `design.md` owns the architecture decisions.

You are working inside the Text2IFC repository.

The current project has already implemented a basic natural-language-to-BIM-JSON-to-IFC workflow, including BIM JSON schemas, Draft Envelope, IFC2X3 compiler, deterministic gates, Audit Agent, prompt registry, report generation, CLI/session DB, and several simple-room or two-room demos.

The next task is NOT to keep patching one specific two-storey case. The goal is to introduce a clear language policy and a structured feedback-routing layer so that validation, gate, compiler, provider, runtime, and audit failures can be normalized into machine-readable issues and routed back to the correct workflow stage.

Please follow the instructions below carefully.

---

## 1. Overall Goal

Implement or prepare a feedback-capable workflow:

```text
Generate
  -> Validate
  -> Compile
  -> Gate
  -> Audit
  -> Normalize Issues
  -> Route Decision
  -> Feedback Target
```

Do not implement large-scale refactoring unless necessary.

Do not introduce RAG, fine-tuning, or deployment changes in this task.

Do not hard-code special fixes for only one two-storey case.

---

## 2. Language Policy

Adopt the following language policy across the workflow.

### 2.1 English-only for core workflow

Use English for:

- System interaction messages;
- CLI prompts and status messages;
- Agent prompts;
- Prompt registry content;
- JSON keys;
- Enum values;
- Issue types;
- Route decisions;
- Structured logs;
- Test names;
- File names;
- Internal module names;
- Error codes;
- Machine-readable artifacts.

### 2.2 Chinese allowed only for documents

Chinese is allowed for:

- Human-readable research documents;
- Architecture notes;
- Experiment discussion documents;
- Chinese project reports;
- Optional `message_zh` fields in artifacts.

Do not use Chinese as JSON keys, enum values, route names, issue types, or control fields.

### 2.3 Preserve Chinese user input

The system must still support Chinese building requirements as raw user input.

The original user input must be preserved as-is, but internal prompts, intermediate system instructions, structured fields, workflow routing, and machine-readable outputs should use English.

---

## 3. Do Not Continue Case-specific Patching

Do not hard-code fixes only for the current two-storey case.

If an existing two-storey run failed because it missed `IfcSpace`, `IfcDoor`, `IfcWindow`, `IfcSlab`, `IfcRoof`, `IfcStair`, host-wall relations, storey assignments, or vertical connections, convert those failures into general issue types and regression tests.

The target is not:

```text
Make this one case pass by adding special handling.
```

The target is:

```text
Convert validation/gate/audit feedback into structured issues and route decisions.
```

---

## 4. Inspect Existing Implementation First

Before writing new code, inspect the current repository and identify existing modules related to:

- schema validation;
- semantic validation;
- compiler;
- reopen check;
- geometry gate;
- deterministic gates;
- audit;
- route decision;
- report generation;
- trace artifacts;
- expected facts;
- CLI workflow;
- provider response handling.

Reuse existing structures where possible.

Avoid duplicating concepts that already exist.

---

## 5. Implement a Structured Issue Model

Create or update a structured issue model that can represent failures from schema validation, semantic validation, compiler, reopen check, geometry gate, deterministic gate, audit, provider, and runtime.

The issue model should contain at least:

```json
{
  "issue_id": "issue_0001",
  "source": "audit",
  "severity": "blocking",
  "owner": "generator",
  "issue_type": "missing_entity",
  "expected_fact_ref": "expected_facts.storeys[1].vertical_connections.stair",
  "actual_ref": "candidate_bim_json.elements",
  "evidence": "The user requested a two-storey building with a stair, but the candidate BIM JSON does not contain any IfcStair or stair-like element.",
  "suggested_route": "regenerate_json",
  "retryable": true,
  "message_zh": "用户要求两层建筑之间有楼梯，但当前候选 BIM JSON 缺少楼梯实体。"
}
```

Use English keys and English enum values.

`message_zh` is optional and should only be used for human-readable reports.

---

## 6. Required Issue Enums

Use these enum values, or adapt existing ones to match them closely.

### 6.1 `source`

```text
schema_validation
semantic_validation
compiler
reopen_check
geometry_gate
deterministic_gate
audit
provider
runtime
```

### 6.2 `severity`

```text
info
warning
blocking
fatal
```

### 6.3 `owner`

```text
user
design_brief
generator
repair
schema
compiler
gate
audit
provider
runtime
```

### 6.4 `issue_type`

```text
missing_required_fact
ambiguous_user_requirement
changed_original_request
invalid_json
schema_mismatch
draft_unresolved_path
unsupported_schema_capability
compiler_unsupported_feature
compile_error
reopen_error
missing_entity
missing_relationship
missing_host
missing_storey_assignment
missing_space_boundary
missing_vertical_connection
geometry_invalid
semantic_mismatch
provider_truncation
provider_format_error
gate_false_positive
runtime_error
```

### 6.5 `suggested_route`

```text
accepted
ask_user
revise_design_brief
regenerate_json
repair_json
blocked_as_unsupported
gate_issue
provider_retry
runtime_blocked
```

---

## 7. Implement RouteDecision

Create or update a `RouteDecision` model that aggregates normalized issues into a workflow route.

The route decision should contain at least:

```json
{
  "final_status": "blocked",
  "route": "regenerate_json",
  "reason": "Audit found blocking missing entities required by expected facts.",
  "blocking_issue_ids": ["issue_0001", "issue_0002"],
  "retry_allowed": true,
  "target_stage": "generator",
  "max_feedback_rounds": 2,
  "current_feedback_round": 0,
  "human_review_required": false,
  "message_zh": "Audit 发现缺少用户需求中要求的关键实体，建议回到 Generator 重新生成 BIM JSON。"
}
```

Use English keys and enum values.

### 7.1 `final_status`

```text
accepted
draft
blocked
failed
```

### 7.2 `target_stage`

```text
user
design_brief
generator
repair
schema
compiler
gate
provider
runtime
none
```

---

## 8. Route Decision Rules

Implement route decision rules with the following logic.

### 8.1 Missing user facts

```text
if owner == "user" and issue_type == "missing_required_fact":
    route = "ask_user"
    target_stage = "user"
```

### 8.2 Design brief error

```text
if owner == "design_brief" and issue_type in ["semantic_mismatch", "changed_original_request"]:
    route = "revise_design_brief"
    target_stage = "design_brief"
```

### 8.3 Generator missing entities or relationships

```text
if owner == "generator" and issue_type in [
    "missing_entity",
    "missing_relationship",
    "missing_host",
    "missing_storey_assignment",
    "missing_space_boundary",
    "missing_vertical_connection"
]:
    route = "regenerate_json"
    target_stage = "generator"
```

### 8.4 Repairable JSON errors

```text
if owner == "repair" and issue_type in ["invalid_json", "schema_mismatch"]:
    route = "repair_json"
    target_stage = "repair"
```

### 8.5 Unsupported schema capability

```text
if owner == "schema" and issue_type == "unsupported_schema_capability":
    route = "blocked_as_unsupported"
    target_stage = "schema"
```

### 8.6 Unsupported compiler feature

```text
if owner == "compiler" and issue_type == "compiler_unsupported_feature":
    route = "blocked_as_unsupported"
    target_stage = "compiler"
```

### 8.7 Provider truncation

```text
if owner == "provider" and issue_type == "provider_truncation":
    route = "provider_retry"
    target_stage = "provider"
```

### 8.8 Gate false positive

```text
if owner == "gate" and issue_type == "gate_false_positive":
    route = "gate_issue"
    target_stage = "gate"
```

### 8.9 Audit blocking must prevent acceptance

```text
if any issue has source == "audit" and severity in ["blocking", "fatal"]:
    final_status must not be "accepted"
```

### 8.10 Gate failure must prevent acceptance

```text
if any deterministic gate has blocking or fatal failure:
    final_status must not be "accepted"
```

---

## 9. Feedback Loop Scope

Do not implement an unlimited automatic loop.

Implement or prepare for a bounded feedback loop:

```text
max_feedback_rounds = 2
```

For the first implementation, it is acceptable to only generate `issues.json`, `route-decision.json`, and `report.md` without automatically re-running the full workflow.

The workflow should make the next step explicit:

```text
Generate
  -> Validate
  -> Compile
  -> Gate
  -> Audit
  -> Normalize Issues
  -> Route Decision
  -> Report next target
```

Automatic retry can be added later after issue normalization and route decisions are stable.

---

## 10. Expected Output Artifacts

Add or stabilize the following artifacts:

```text
issues.json
route-decision.json
feedback-rounds.json
case-result.json
report.md
```

### 10.1 `issues.json`

Contains all normalized issues.

### 10.2 `route-decision.json`

Contains final route decision.

### 10.3 `feedback-rounds.json`

Contains each feedback round, including generation result, validation result, issues, and route decision.

### 10.4 `case-result.json`

Contains a compact experiment-level summary.

Recommended structure:

```json
{
  "case_id": "controlled_two_storey_001",
  "input_language": "zh",
  "workflow_language": "en",
  "prompt_language": "en",
  "document_language": "zh",
  "clarification_count": 0,
  "output_type": "formal_bim_json",
  "schema_pass": true,
  "compiler_pass": true,
  "reopen_pass": true,
  "gate_pass": false,
  "audit_pass": false,
  "final_status": "blocked",
  "route": "regenerate_json",
  "failure_owner": "generator",
  "blocking_issue_count": 2,
  "evidence_paths": {
    "issues": "issues.json",
    "route_decision": "route-decision.json",
    "report": "report.md"
  }
}
```

---

## 11. Regression Tests

Add regression tests based on existing complex two-storey failures, but do not hard-code the specific case.

The tests should verify the following general rules:

1. If expected facts require spaces but candidate output misses `IfcSpace`, final status must not be `accepted`.
2. If expected facts require doors but candidate output misses `IfcDoor`, final status must not be `accepted`.
3. If expected facts require windows but candidate output misses `IfcWindow`, final status must not be `accepted`.
4. If a multi-storey building requires slabs but candidate output misses `IfcSlab`, final status must not be `accepted`.
5. If a two-storey building requires vertical connection but candidate output misses stair or stair-like relation, final status must not be `accepted`.
6. If Draft contains unresolved paths, the route must be `ask_user` or `blocked_as_unsupported`, not `accepted`.
7. If deterministic gates pass but Audit returns a blocking issue, final status must not be `accepted`.
8. If provider output is truncated, final status must not be `accepted`.
9. If compiler reports unsupported feature, route should be `blocked_as_unsupported`.
10. If schema validation fails due to minor repairable errors, route may be `repair_json`.

---

## 12. Two-storey Benchmark Plan

Prepare three two-storey benchmark cases.

### 12.1 Controlled Two-storey

All facts are explicit.

Use this to determine whether the current pipeline can produce accepted IFC when no user information is missing.

### 12.2 Clarification Two-storey

Some facts are intentionally missing.

Use this to test whether the workflow routes to `ask_user`.

### 12.3 Ambiguous Two-storey

The input is natural and underspecified.

Use this to test whether the system avoids silent fabrication and routes to Draft, ask_user, or blocked_as_unsupported.

---

## 13. Report Requirements

Update `report.md` so that it clearly shows:

- Original user input;
- Input language;
- Workflow language;
- Prompt language;
- Design Brief;
- Candidate BIM JSON or Draft summary;
- Validation result;
- Compiler result;
- Gate result;
- Audit result;
- Normalized issues;
- Route decision;
- Feedback rounds;
- Final status;
- Evidence paths.

The report may be written in Chinese, but all structured field names and route names should remain in English.

---

## 14. Implementation Order

Please implement in this order:

1. Inspect current route decision, audit, gate, validation, report, and trace modules.
2. Identify existing structures that can be reused.
3. Add or normalize the Issue model.
4. Add or normalize the RouteDecision model.
5. Convert schema/compiler/gate/audit/provider/runtime failures into Issue objects.
6. Generate `issues.json`.
7. Generate `route-decision.json`.
8. Update `report.md` to display issues and route decision.
9. Add regression tests for missing entity, unresolved Draft, Audit blocking, provider truncation, and unsupported compiler feature.
10. Prepare controlled two-storey benchmark artifacts.
11. Do not perform large-scale refactoring unless necessary.
12. Do not introduce RAG, fine-tuning, or deployment changes in this task.

---

## 15. Success Criteria

This task is successful if:

1. System prompts and workflow messages are in English.
2. Structured artifacts use English keys and enum values.
3. Chinese is not used as a machine-readable control field.
4. Existing validation/gate/audit/compiler/provider/runtime failures can be normalized into Issue objects.
5. A RouteDecision can be generated from Issue objects.
6. Audit blocking findings prevent final acceptance.
7. Gate blocking findings prevent final acceptance.
8. Draft unresolved paths cannot be accepted silently.
9. Existing two-storey failures become general regression tests.
10. `report.md` clearly explains final status and next route.
11. The project is closer to a feedback-capable workflow rather than a purely linear workflow.

---

## 16. Final Reminder

Do not optimize for making one single two-storey example pass.

Optimize for a general mechanism:

```text
Failure -> Structured Issue -> Route Decision -> Correct Feedback Target
```

The main contribution of this task is to make Text2IFC more diagnosable, testable, and feedback-capable.
