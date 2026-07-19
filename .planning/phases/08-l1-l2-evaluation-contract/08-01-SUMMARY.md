---
phase: 08-l1-l2-evaluation-contract
plan: 01
subsystem: evaluation
tags: [json-schema, dataclasses, l1, l2, aggregation, compatibility]

requires: []
provides:
  - Evaluation 0.2 exact Draft 2020-12 JSON Schema
  - Immutable evidence/check/level/operation/run domain records
  - Exhaustive strict L1/L2 aggregation and non-gating L3 construction
  - Explicit non-assuring reader projection for evaluation 0.1
affects: [08-02, 08-03, 08-04, phase-09, phase-10]

tech-stack:
  added: []
  patterns:
    - Frozen dataclass domain records validated before aggregation
    - Canonical schema-backed JSON serialization with semantic re-aggregation
    - Legacy reports preserved through an explicit assurance-unavailable projection

key-files:
  created:
    - schemas/agent/ifc-repair-evaluation-0.2.schema.json
    - src/text2ifc_ifc_repair/evaluation_models.py
    - src/text2ifc_ifc_repair/evaluation.py
    - tests/ifc_repair/test_evaluation_contract.py
  modified: []

key-decisions:
  - "Mandatory status precedence is failed > partial > not_evaluable > passed; policy-approved optional not_required children are disclosed but do not lower the parent."
  - "L3 is always emitted as not_required in v1.1 and is excluded from operation and run success aggregation."
  - "Evaluation 0.1 remains byte-for-data readable, but its compatibility projection forces L1/L2 assurance and publication success to unavailable/false."

patterns-established:
  - "Semantic validation re-aggregates serialized children and rejects mismatched parent status/booleans with invalid_status_transition."
  - "All checks and hierarchy nodes retain a non-empty reason and provenance-bearing evidence."

requirements-completed:
  - VAL-01
  - VAL-03

duration: 13min
completed: 2026-07-19
---

# Phase 8 Plan 1: Versioned Evaluation Domain and Strict Aggregation Summary

**Evaluation 0.2 now exposes deterministic evidence-bearing L1/L2/L3 results, requires every mandatory L1 and L2 gate to pass before publication, and reads 0.1 without inventing semantic assurance.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-07-19T02:29:35Z
- **Completed:** 2026-07-19T02:42:26Z
- **Tasks:** 3
- **Files modified:** 4 contract/test files, plus this summary

## Accomplishments

- Added an exact `text2ifc/ifc-repair-evaluation/0.2` schema with closed five-state statuses, required hierarchy, reasons, evidence, policy IDs, and no undeclared fields.
- Added frozen domain records plus one total aggregation function that makes application, preservation, and every mandatory operation's L1/L2 status jointly gate success and publication.
- Added canonical round-trip serialization, semantic revalidation, stable machine error codes, non-gating L3 construction, and an explicit legacy 0.1 assurance-unavailable projection.
- Proved the contract with 58 focused tests, including all 25 two-status precedence pairs, strict mandatory failure cases, schema rejection, canonical nested evidence ordering, and legacy compatibility.

## TDD Evidence

- **RED:** 34 tests collected and failed because `text2ifc_ifc_repair.evaluation_models` did not exist; no production file existed at this gate.
- **GREEN:** The minimal schema, immutable model, aggregation, serialization, validation, and compatibility implementation made all 34 tests pass.
- **REFACTOR:** Centralized serialized aggregate checks, canonicalized nested evidence values, enforced status/ID construction invariants, and expanded the suite to 58 passing tests.

## Task Commits

Each TDD gate was committed atomically:

1. **Task 1: RED - freeze contract behavior** - `40b1b19d` (test)
2. **Task 2: GREEN - implement evaluation 0.2** - `2471e7e5` (feat)
3. **Task 3: REFACTOR - harden canonical aggregation** - `af55f0ff` (refactor)

## Files Created/Modified

- `schemas/agent/ifc-repair-evaluation-0.2.schema.json` - Exact Draft 2020-12 run/operation/level/check/evidence hierarchy.
- `src/text2ifc_ifc_repair/evaluation_models.py` - Frozen records, closed status enum, and stable contract errors.
- `src/text2ifc_ifc_repair/evaluation.py` - Pure aggregation, L3 boundary, canonical serialization, schema validation, and 0.1 compatibility reading.
- `tests/ifc_repair/test_evaluation_contract.py` - RED/GREEN/REFACTOR contract, truth-table, schema, round-trip, and legacy tests.

## Decisions Made

- Used one order-independent status precedence table for checks, levels, operations, and runs; `failed` dominates `partial`, which dominates `not_evaluable`.
- Treated optional `not_required` checks as satisfied at their parent while retaining the child result and evidence in the report.
- Derived both `complete_repair_success` and `successful_artifact_publishable` from the same strict mandatory aggregate; diagnostic retention remains independent.
- Reconstructed serialized reports through the same aggregation functions so a syntactically valid report cannot forge parent status or success booleans.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- One ad-hoc PowerShell schema-ID assertion expanded `$id` as a shell variable. The plan's exact schema-validation command was rerun unchanged and passed; this did not affect implementation or evidence.

## Known Stubs

None. The created/modified files contain no TODO/FIXME/placeholder behavior or unwired empty report values.

## User Setup Required

None - no external service configuration required.

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_evaluation_contract.py -q` - **58 passed**
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair` - **passed**
- Draft 2020-12 `check_schema` for `ifc-repair-evaluation-0.2.schema.json` - **passed**
- TDD commit order - **RED `40b1b19d` -> GREEN `2471e7e5` -> REFACTOR `af55f0ff`**

## Next Phase Readiness

- Plan 08-02 can add operation-owned L2 policies and evidence resolution against the stable `EvidenceFact`, `CheckResult`, and aggregation boundary.
- No blockers; IFC measurement, benchmark Gold access, workflow publication, and Window semantic repair remain deliberately out of scope.

## Self-Check: PASSED

- All four contract/test artifacts and this summary exist on disk.
- RED, GREEN, and REFACTOR commits `40b1b19d`, `2471e7e5`, and `af55f0ff` exist in git history.
- Final focused pytest, compileall, and Draft 2020-12 schema validation all passed after the REFACTOR commit.

---
*Phase: 08-l1-l2-evaluation-contract*
*Completed: 2026-07-19*
