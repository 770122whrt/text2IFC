---
phase: 08-l1-l2-evaluation-contract
fixed_at: 2026-07-19T05:37:00Z
review_path: .planning/phases/08-l1-l2-evaluation-contract/08-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 8: Code Review Fix Report

**Fixed at:** 2026-07-19T05:37:00Z
**Source review:** `.planning/phases/08-l1-l2-evaluation-contract/08-REVIEW.md`
**Iteration:** 1

**Summary:**

- Findings in scope: 10
- Fixed: 10
- Skipped: 0
- Post-merge regression stabilization: `90a929de`
- Verification: four reported regressions passed (`4 passed`); Phase 8 focused six files passed (`147 passed`).

## Fixed Issues

### CR-01: Required failures can be excluded from aggregation

**Files modified:** `schemas/agent/ifc-repair-evaluation-0.2.schema.json`, `src/text2ifc_ifc_repair/evaluation_models.py`, `src/text2ifc_ifc_repair/evaluation.py`, `tests/ifc_repair/test_evaluation_contract.py`
**Commit:** 239816a5
**Status:** fixed: requires human verification
**Applied fix:** Required, informational, and conditional checks now enforce mandatory-state invariants in the domain model, schema, deserialization, and aggregation. Application and preservation are always mandatory run gates.

### CR-02: Duplicate same-role roots pass L1 scope authorization

**Files modified:** `src/text2ifc_ifc_repair/evaluation.py`, `src/text2ifc_ifc_repair/operations/window.py`, `tests/ifc_repair/test_l1_evaluator.py`
**Commits:** 01c42409, 90a929de
**Status:** fixed: requires human verification
**Applied fix:** Operation-owned role cardinality and one-role-per-GlobalId validation reject duplicate roots independent of report ordering. Immutable evidence remains intact and tests consume it through the canonical thaw path.

### CR-03: Production inputs accept private-original semantic facts

**Files modified:** `src/text2ifc_ifc_repair/benchmark_evaluation.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commit:** 5195b195
**Status:** fixed: requires human verification
**Applied fix:** Production inputs use a dedicated evidence-source allowlist and reject `PRIVATE_ORIGINAL` during construction and again at the production evaluator entrypoint.

### CR-04: Unreadable repaired IFC raises instead of producing not_evaluable

**Files modified:** `src/text2ifc_ifc_repair/benchmark_evaluation.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commit:** e7229126
**Status:** fixed: requires human verification
**Applied fix:** IFC open and role-resolution failures become structured evaluator-input evidence with mandatory L2 `not_evaluable` results and a non-publishable report.

### CR-05: Pset extraction errors become not_required

**Files modified:** `src/text2ifc_ifc_repair/semantic_facts.py`, `src/text2ifc_ifc_repair/benchmark_evaluation.py`, `tests/ifc_repair/test_evaluation_policy.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commit:** e7229126
**Status:** fixed: requires human verification
**Applied fix:** Pset extraction raises a typed error; Pset, quantity, Material, and Classification extraction failures produce mandatory `not_evaluable` checks rather than verified absence.

### CR-06: Operation role mappings are flattened across the run

**Files modified:** `src/text2ifc_ifc_repair/benchmark_evaluation.py`, `src/text2ifc_ifc_repair/evaluation_policy.py`, `src/text2ifc_ifc_repair/operations/window.py`, `src/text2ifc_ifc_repair/workflow.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commit:** 5195b195
**Status:** fixed: requires human verification
**Applied fix:** Application and private role maps are keyed by operation ID, and policy metadata declares the evaluated semantic role instead of using a run-global hard-coded Window role.

### WR-01: Workflow canary coverage omits private semantic values

**Files modified:** `src/text2ifc_ifc_repair/evaluation_projection.py`, `src/text2ifc_ifc_repair/workflow.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commits:** 6c027aa5, 90a929de
**Status:** fixed: requires human verification
**Applied fix:** The final full-bundle scan uses private-original L2 values and semantic-role IDs. Tokens already authorized by the damaged IFC or application-produced candidate are excluded from the Gold-only set without reducing the final scan scope.

### WR-02: Early workflow failures still emit Evaluation 0.1

**Files modified:** `src/text2ifc_ifc_repair/workflow.py`, `src/text2ifc_ifc_repair/evaluation_projection.py`, `tests/ifc_repair/test_offline_e2e.py`
**Commits:** 6c027aa5, ecec02fa
**Status:** fixed: requires human verification
**Applied fix:** Early failures now emit a hierarchical Evaluation 0.2 terminal public contract with application, preservation, L1/L2/L3, explicit non-publication, diagnostics, and accurate Provider-call count.

### WR-03: Frozen evaluation records retain mutable nested evidence

**Files modified:** `src/text2ifc_ifc_repair/evaluation_models.py`, `src/text2ifc_ifc_repair/evaluation.py`, `tests/ifc_repair/test_evaluation_contract.py`
**Commit:** 239816a5
**Applied fix:** Evidence values are detached into deeply immutable canonical JSON containers and thawed defensively for serialization or test inspection.

### WR-04: Adversarial contract tests miss confirmed boundary cases

**Files modified:** `tests/ifc_repair/test_evaluation_contract.py`, `tests/ifc_repair/test_l1_evaluator.py`, `tests/ifc_repair/test_benchmark_evaluation.py`
**Commits:** 239816a5, 01c42409, 5195b195, 90a929de
**Applied fix:** Added regressions for mandatory downgrade attempts, duplicate same-role roots, private-original production inputs, per-operation mappings, immutable evidence access, and Gold-only canary classification.

## Verification

- Reported post-merge regressions: `4 passed in 34.30s`
- Tightened canary-source rerun: `2 passed in 32.23s`
- Phase 8 focused suite: `147 passed in 36.04s`
- Modified-file compileall: passed
- `git diff --check`: passed

---

_Fixed: 2026-07-19T05:37:00Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
