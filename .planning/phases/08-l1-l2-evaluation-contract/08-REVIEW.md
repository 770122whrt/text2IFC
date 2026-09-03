---
phase: 08-l1-l2-evaluation-contract
reviewed: 2026-07-19T04:48:20Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - schemas/agent/ifc-repair-evaluation-0.2.schema.json
  - src/text2ifc_ifc_repair/evaluation_models.py
  - src/text2ifc_ifc_repair/evaluation.py
  - src/text2ifc_ifc_repair/evaluation_policy.py
  - src/text2ifc_ifc_repair/semantic_facts.py
  - src/text2ifc_ifc_repair/registry.py
  - src/text2ifc_ifc_repair/operations/window.py
  - src/text2ifc_ifc_repair/compare.py
  - src/text2ifc_ifc_repair/benchmark_evaluation.py
  - src/text2ifc_ifc_repair/evaluation_projection.py
  - src/text2ifc_ifc_repair/workflow.py
  - tests/ifc_repair/test_evaluation_contract.py
  - tests/ifc_repair/test_evaluation_policy.py
  - tests/ifc_repair/test_l1_evaluator.py
  - tests/ifc_repair/test_benchmark_evaluation.py
  - tests/ifc_repair/test_phase8_large_building.py
  - tests/ifc_repair/test_offline_e2e.py
findings:
  critical: 6
  warning: 4
  info: 0
  total: 10
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-07-19T04:48:20Z  
**Depth:** standard  
**Files Reviewed:** 17  
**Status:** issues_found

## Summary

The implementation has six release-blocking correctness defects. Most importantly, a failed required check can be reclassified as non-mandatory and still validate as a successful Evaluation 0.2 report; L1 role authorization permits duplicate same-role roots; and the production input boundary accepts private-original semantic facts. The real LargeBuilding test does use the frozen IFC and records zero Provider calls, but its passing result does not cover the defects below.

## Critical Issues

### CR-01 (BLOCKER): Required failures can be excluded from aggregation

**File:** `src/text2ifc_ifc_repair/evaluation.py:589`  
**Related:** `src/text2ifc_ifc_repair/evaluation_models.py:95`, `schemas/agent/ifc-repair-evaluation-0.2.schema.json:79`

**Trigger:** A required application, preservation, L1, or L2 check is supplied with `mandatory=false`. `CheckResult` and the schema allow this combination, and `aggregate_status` skips the failed result.

**Impact:** A report with `application.status=failed` can semantically validate with run status `passed`, `complete_repair_success=true`, and `successful_artifact_publishable=true`. This was reproduced through `validate_evaluation_report`.

**Fix:** Enforce applicability/mandatory invariants in both the dataclass and schema: required checks are always mandatory; informational checks are never mandatory; conditional checks are non-mandatory only when status is `not_required`. Also require application and preservation to be mandatory during repair aggregation/deserialization.

**Suggested test:** Serialize a failed required application and each failed required L1/L2 check with `mandatory=false`; validation must reject every case with `invalid_status_transition`.

### CR-02 (BLOCKER): Duplicate same-role roots pass L1 scope authorization

**File:** `src/text2ifc_ifc_repair/evaluation.py:307`

**Trigger:** An application result lists more than one created root of the policy-authorized class under the same role, such as two `IfcWindow` roots both reported as `window`. Authorization checks each root independently but never enforces role cardinality or one-to-one role binding.

**Impact:** An extra collateral `IfcWindow` can pass `l1.scope.created-roots`; the Window measurement adapter evaluates only the last same-role entry. This was reproduced on the controlled IFC fixture with the overall L1 status remaining `passed`.

**Fix:** Validate application role bindings before authorizing changes: each singleton role must resolve to exactly one GlobalId per operation, each GlobalId must have one role, and the actual diff cardinality must match the operation-owned authorization contract. Pass the validated binding to the measurement adapter.

**Suggested test:** Add a second created `IfcWindow` reported as `window` before the legitimate entry; require `l1.scope.created-roots=failed` regardless of list order.

### CR-03 (BLOCKER): Production inputs accept private-original semantic facts

**File:** `src/text2ifc_ifc_repair/benchmark_evaluation.py:48`

**Trigger:** `ProductionEvaluationInputs.expected_facts_by_operation` contains a `SemanticFact` whose `source_kind` is `PRIVATE_ORIGINAL`.

**Impact:** The production-only type accepts the fact and its private value, and the Window policy treats that source as authorized. The claimed production/private separation is therefore not enforced by the type or runtime boundary.

**Fix:** Reject `PRIVATE_ORIGINAL` in `ProductionEvaluationInputs.__post_init__` and again in `evaluate_production`; use a production-specific allowed-source set. Permit private-original facts only inside `BenchmarkEvaluationInputs` after application.

**Suggested test:** Construct production inputs with a private-original canary fact and require immediate rejection before any IFC file is opened.

### CR-04 (BLOCKER): Unreadable repaired IFC raises instead of producing `not_evaluable`

**File:** `src/text2ifc_ifc_repair/benchmark_evaluation.py:167`

**Trigger:** The repaired path is missing/unreadable, or an application role GlobalId cannot be reopened. `evaluate_independent_l1` returns structured non-evaluable checks, but `_evaluate` then unconditionally opens the same path and resolves role entities.

**Impact:** Production/benchmark evaluation raises `FileNotFoundError` or a GUID lookup error and emits no Evaluation 0.2 report or diagnostic publication decision. A missing repaired file was reproduced as an uncaught `FileNotFoundError`.

**Fix:** Treat model open and role resolution as evaluator inputs with structured outcomes. When unavailable, create mandatory L2 `not_evaluable` checks, aggregate the run as unsuccessful/non-publishable, and retain the L1 evidence.

**Suggested test:** Call both evaluation entrypoints with a missing repaired IFC and with a missing reported Window GUID; assert a valid 0.2 report with non-passing L1/L2 rather than an exception.

### CR-05 (BLOCKER): Pset extraction errors become `not_required`

**File:** `src/text2ifc_ifc_repair/semantic_facts.py:566`  
**Related:** `src/text2ifc_ifc_repair/benchmark_evaluation.py:378`

**Trigger:** `ifcopenshell.util.element.get_psets` raises for an original, surviving, or repaired entity. Both helpers catch every exception and return an empty mapping.

**Impact:** The evaluator cannot distinguish extraction failure from verified absence. Conditional Pset/quantity facts can therefore become `not_required`, allowing a level to pass even though applicability was not evaluable.

**Fix:** Return an extraction result that distinguishes `absent` from `error`, or propagate a typed extraction error into mandatory `not_evaluable` checks. Only a successful empty extraction may activate `not_required`.

**Suggested test:** Mock `get_psets` to raise for a policy containing only conditional Pset/quantity checks; assert `not_evaluable` and non-publishable, not `not_required`/passed.

### CR-06 (BLOCKER): Operation role mappings are flattened across the run

**File:** `src/text2ifc_ifc_repair/benchmark_evaluation.py:173`  
**Related:** `src/text2ifc_ifc_repair/benchmark_evaluation.py:395`

**Trigger:** A ChangeSet contains multiple operations with the same semantic role names. `_application_role_mapping` returns one global `role -> GlobalId` dictionary, and `_evaluate` looks up hard-coded `window` roles for every operation.

**Impact:** Earlier operations are evaluated against the last operation's repaired Window; private mappings have the same run-global shape. This can assign L2 evidence to the wrong operation and produce incorrect per-operation and run statuses.

**Fix:** Key application and private role maps by `operation_id`, then resolve the evaluated semantic role through operation-owned policy metadata rather than a hard-coded Window role.

**Suggested test:** Evaluate two Window operations with different semantic values and reversed application order; each operation must retain its own expected/actual evidence and status.

## Warnings

### WR-01 (WARNING): Workflow canary coverage omits private semantic values

**File:** `src/text2ifc_ifc_repair/workflow.py:520`

**Trigger:** A private Material, Pset, quantity, classification, or label value appears in a public/runtime artifact.

**Impact:** `_private_boundary_canaries` scans original IDs, a path, and role tokens, but not Gold semantic values. The whole-bundle check therefore cannot detect the value-leak category exercised only by the isolated projection unit test.

**Fix:** Derive canaries from the private semantic facts used for evaluation, including representative typed values and identifiers, and scan the finalized public/runtime file set.

**Suggested test:** Put a unique original Pset/material value in the real workflow fixture and assert it is present privately and absent from every non-private file.

### WR-02 (WARNING): Early workflow failures still emit Evaluation 0.1

**File:** `src/text2ifc_ifc_repair/workflow.py:399`

**Trigger:** Provider validation/execution or application fails before benchmark evaluation.

**Impact:** The workflow writes a 0.1-shaped failure without `status`, five-state hierarchy, or `successful_artifact_publishable`. Downstream consumers cannot use one terminal Evaluation 0.2 contract for all Phase 8 outcomes.

**Fix:** Add a schema-valid 0.2 failure constructor with required application/preservation/operation evidence, or define and validate a separate versioned pre-application failure contract that explicitly sets publication false.

**Suggested test:** Assert the invalid-live-provider and application-failure bundles use the declared terminal schema and expose an explicit non-publishable state.

### WR-03 (WARNING): Frozen evaluation records retain mutable nested evidence

**File:** `src/text2ifc_ifc_repair/evaluation_models.py:35`

**Trigger:** `expected_value`, `actual_value`, or a nested mapping is mutated after constructing a frozen record.

**Impact:** The supposedly immutable evaluation can change after aggregation/validation, so later serialization may not represent the evidence that was evaluated.

**Fix:** Canonicalize evidence values to deeply immutable JSON structures at construction, or store canonical serialized bytes and expose defensive copies.

**Suggested test:** Attempt to mutate a nested evidence dictionary after report construction and assert the report cannot change.

### WR-04 (WARNING): Adversarial contract tests miss the confirmed boundary cases

**File:** `tests/ifc_repair/test_l1_evaluator.py:239`  
**Related:** `tests/ifc_repair/test_benchmark_evaluation.py:124`, `tests/ifc_repair/test_evaluation_contract.py:212`

**Trigger:** The current tests cover an unreported extra root, inspect only the production constructor signature, and always create required checks with `mandatory=true`.

**Impact:** The three principal regressions in CR-01 through CR-03 pass the current suite.

**Fix:** Add the concrete regression tests described in CR-01, CR-02, and CR-03 and keep them at the public schema/evaluator entrypoints.

---

_Reviewed: 2026-07-19T04:48:20Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
