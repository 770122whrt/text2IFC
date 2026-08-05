---
phase: 12-beam-and-column-operations
plan: "09"
subsystem: structural-evaluation-atomicity
tags: [ifc2x3, l1, l2, atomicity, beam, column, window, door, tdd]

requires:
  - phase: 12-07
    provides: Registered Beam operation and structural conflict domain
  - phase: 12-08
    provides: Registered Column operation and base-Storey policy
provides:
  - Frozen structural L1 threshold policy and reopened measurement checks
  - Exact structural product, containment and Type relationship gates
  - Real Beam/Column support-contact and four-family atomic transaction evidence
  - Fail-closed structural L2 type/value/scope evidence
affects: [12-10, 12-11, 12-12, 12-15, 12-16]

tech-stack:
  added: []
  patterns:
    - Operation adapters extract reopened IFC evidence while a pure policy comparator owns numeric thresholds
    - Common evaluator qualifies repeated structural check IDs per operation and aggregates every mandatory result

key-files:
  created:
    - tests/ifc_repair/test_structural_atomicity.py
  modified:
    - src/text2ifc_ifc_repair/evaluation_policy.py
    - src/text2ifc_ifc_repair/operations/beam.py
    - src/text2ifc_ifc_repair/operations/column.py
    - src/text2ifc_ifc_repair/operations/structural_member.py

key-decisions:
  - "Axis-point 5 mm, direction/tilt 0.1 degree and member/section 1 mm limits are immutable inclusive thresholds."
  - "Approximate volume and mesh resemblance are absent from structural success checks."
  - "A non-square Column profile orientation uses the frozen 0.1 degree angular grade; square orientation omission remains exact."
  - "The existing metadata-driven audit/apply/evaluation pipeline remains unchanged because its all-or-none gates already cover structural operations once adapters expose evidence."

patterns-established:
  - "Structural effect authorization declares exact created/modified role and IFC-class pairs, including optional occurrence semantic relationships."
  - "Legitimate Beam/Column support contact is allowed; same-axis duplicate overlap fails audit before application."

requirements-completed: [OPS-03, OPS-04]

duration: 13min
completed: 2026-08-06
---

# Phase 12 Plan 09: Strict Structural Evaluation and Mixed Atomicity Summary

**Beam and Column now contribute strict reopened L1 evidence to the common evaluator, while real Beam+Column and Window+Door+Beam+Column ChangeSets preserve one all-or-none transaction.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-06T01:47:00+08:00
- **Completed:** 2026-08-06T02:00:20+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 5 including the RED test file

## Accomplishments

- Added one immutable structural L1 precision policy with inclusive 5 mm axis-point, 0.1 degree direction/tilt and 1 mm member/section limits.
- Compared only reopened center-axis geometry, rectangular dimensions and declared profile orientation; volume and mesh proxies are diagnostic-only by construction.
- Required one exact physical product, one exact Storey containment and one exact declared structural Type binding.
- Added family-neutral structural effect authorization for occurrence, Type, containment and optional Pset/quantity/material/classification relationships.
- Verified a real d7n Beam/Column support contact applies and independently passes global L1 in one transaction.
- Verified same-axis duplicates fail audit before mutation and a Column postcondition fault suppresses the whole Beam/Column output.
- Extended the checked-in real vvo Window/Door Proof input in memory with Beam and Column operations and verified all six operations publish one reopened IFC2X3 candidate.
- Proved requested structural L2 value-type and semantic-scope mismatches are non-passing and mandatory.

## TDD Gate Evidence

### RED

`f679f09d` - `test(12-09): add failing structural evaluation tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_atomicity.py tests\ifc_repair\test_apply_transaction.py -q`
- Result: collection failed because the frozen structural L1 policy and comparator did not exist.

### GREEN

`9e2cd40f` - `feat(12-09): enforce strict structural evaluation`

- Plan verification: **13 passed in 42.14s**.
- Structural, semantic, L1/benchmark, Window/Door and mixed-atomicity regressions: **151 passed in 129.20s**.
- Focused compileall passed.
- `git diff --check` passed.
- Ruff was unavailable in the repository environment (`No module named ruff`) and was not installed or substituted.

### REFACTOR

Beam and Column adapters delegate their identical reopened measurement and relationship logic to `structural_l1_comparison_report`; threshold calculation and effect authorization remain pure functions in the evaluation policy module.

## Deviations from Plan

### Auto-added: shared structural comparison helper

- **Found during:** GREEN implementation of identical Beam and Column evidence callbacks.
- **Issue:** placing the full comparison independently in both registered operations would duplicate threshold and relationship behavior.
- **Fix:** added the minimal shared helper to the existing structural member module and kept operation adapters as family declarations.
- **Why required:** this preserves the plan's operation-neutral, metadata-driven evaluation seam without changing any frozen family contract.

### No changes required in common audit/apply/evaluation modules

- **Found during:** fault-injection and real mixed-family integration.
- **Issue:** the plan listed these files as candidate modification points, but their existing conflict-domain, in-memory transaction, reopen, global-diff, L1/L2 aggregation and terminal publication behavior already passed every structural test.
- **Disposition:** left them unchanged and added only the missing registered structural evidence. Modifying them without a failing contract would have risked frozen Window/Door behavior.

## Issues Encountered

- Initial test ChangeSets omitted their new operation evidence references from the top-level evidence declaration. Audit correctly rejected them; the test fixtures were corrected rather than weakening audit.
- Exact L2 mismatches are represented as either `failed` or `not_evaluable` depending on available authority. Tests now assert the frozen release rule: only `passed` is acceptable.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

Plan 12-09 supplies strict structural evaluation and atomicity coverage, but authoritative OPS-03 and OPS-04 remain **Pending** until real DeepSeek UAT, independent Proof recomputation and Plan 12-16 closure pass.

## Next Phase Readiness

- Plan 12-10 can build deterministic structural damage and prove that original IFC/private mapping never enter the public repair boundary.
- Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Every frozen numeric threshold passes at its boundary and fails immediately beyond it.
- Exact product/Storey/Type and requested semantic mismatches are blocking.
- Real two-family and four-family transactions reopen; injected audit/application/postcondition faults publish none.
- Historical Window/Door and common evaluation behavior remain green.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
