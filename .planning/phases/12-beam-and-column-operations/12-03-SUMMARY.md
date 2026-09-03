---
phase: 12-beam-and-column-operations
plan: "03"
subsystem: semantic-authoring
tags: [ifc2x3, psd, rag, beam, column, semantic-authority, tdd]

requires:
  - phase: 12-02
    provides: Source-bound Beam/Column occurrence and Type indexes
provides:
  - Beam/Column scopes in the generic occurrence-property operation
  - Exact applicable PSD, IFC value-type and semantic-scope preconditions
  - Beam/Column semantic role authoring through the shared IFC2X3 path
  - Canonical structural LoadBearing authority and reopen tests
affects: [12-04, 12-07, 12-08, structural-semantic-authoring]

tech-stack:
  added: []
  patterns:
    - PSD applicability and exact IFC type are checked before property mutation
    - Structural semantic roles extend policy data without a family-specific writer

key-files:
  created:
    - tests/ifc_repair/test_structural_property_authoring.py
  modified:
    - src/text2ifc_ifc_repair/operations/occurrence_property.py
    - src/text2ifc_ifc_repair/semantic_authoring.py
    - tests/ifc_repair/test_occurrence_property_operation.py

key-decisions:
  - "Existing resolver rejection of vector-only, cross-class and noncanonical property paths is retained; no structural alias or normalization layer is added."
  - "Structural property assignments must name one exact applicable PSD path, its exact IFC data type and an allowed target/family occurrence scope."

patterns-established:
  - "One-defect authority matrix: each cross-class, mistyped or wrong-scope assignment fails with one stable precondition code."
  - "Semantic role mapping: beam_occurrence and column_occurrence receive namespaced roles while the authoring engine remains shared."

requirements-completed: [OPS-03, OPS-04]

duration: 5min
completed: 2026-08-06
---

# Phase 12 Plan 03: Structural Property and RAG Authority Summary

**Beam and Column LoadBearing facts now resolve and author through the shared IFC2X3 PSD path while vector-only, cross-class and noncanonical evidence remains non-authoritative.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-06T00:22:46+08:00
- **Completed:** 2026-08-06T00:27:00+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 4

## Accomplishments

- Added `IfcBeam` and `IfcColumn` to the operation-neutral occurrence-property registry scope.
- Proved canonical `Pset_BeamCommon.LoadBearing=true` and `Pset_ColumnCommon.LoadBearing=true` resolve as exact `IfcBoolean` facts.
- Enforced exact source/fact path equality, PSD applicability, IFC data type and family/target semantic scope before mutation.
- Added shared `beam_occurrence` and `column_occurrence` semantic role naming; both properties survive IFC2X3 serialization and reopen.
- Preserved existing resolver behavior: vector-only recall, cross-class PSDs, synonymous paths and a string pretending to be a Boolean cannot authorize a Bound ChangeSet.

## TDD Gate Evidence

### RED

`62e4adc1` - `test(12-03): add failing structural property tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_property_authoring.py -q`
- Result: **6 failed, 3 passed**.
- Intended failures: missing structural target classes, missing defect preconditions and unsupported Beam/Column semantic scopes.
- Existing vector-only, cross-class, noncanonical-path and wrong-value rejection checks already passed, proving no resolver compatibility patch was needed.

### GREEN

`d1e3989d` - `feat(12-03): bind structural property authority`

- Plan verification: **20 passed in 3.32s** across structural property authoring, historical occurrence-property and binding-security tests.
- Adjacent request-stage regression: **12 passed in 6.24s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

No separate refactor commit was needed. Scope-to-role behavior was converted to a bounded policy mapping while preserving Window/Opening/Door names.

## Files Created/Modified

- `tests/ifc_repair/test_structural_property_authoring.py` - Canonical resolution, one-defect authority, vector-only rejection and IFC reopen matrix.
- `src/text2ifc_ifc_repair/operations/occurrence_property.py` - Structural target scopes and exact PSD/type/scope preconditions.
- `src/text2ifc_ifc_repair/semantic_authoring.py` - Shared Beam/Column semantic role mapping.
- `tests/ifc_repair/test_occurrence_property_operation.py` - Historical registry expectation and per-class applicable PSD regression coverage.

## Decisions Made

- `LoadBearing` acceptance uses the canonical Beam/Column PSD paths extracted by Stage 1; the program does not add unreviewed natural-language aliases.
- Top-K/vector candidates remain discovery evidence and never enter an executable assignment.
- The precondition validates the exact bound assignment again so a forged cross-class Pset, value type or scope fails before authoring.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated historical occurrence-property assertions for the expanded and stricter public contract**

- **Found during:** GREEN verification.
- **Issue:** The historical test expected the old four-class registry and reused `Pset_WindowCommon` across Wall/Door fixtures, which conflicts with the newly required class-specific applicability check.
- **Fix:** Added Beam/Column to the historical supported-class matrix and selected each fixture's applicable canonical common Pset.
- **Files modified:** `tests/ifc_repair/test_occurrence_property_operation.py`.
- **Verification:** Plan suite 20 passed; request-stage suite 12 passed.
- **Committed in:** `d1e3989d`.

---

**Total deviations:** 1 auto-fixed (1 correctness bug in historical expectations).
**Impact on plan:** Required to test the frozen class-applicability contract; no production scope expansion beyond Plan 12-03.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

The plan traces OPS-03 and OPS-04 and therefore copies them into Summary metadata. Their authoritative project status remains **Pending** until Plan 12-16 independently validates full operations, strict L0/L1/L2 and real DeepSeek evidence.

## Next Phase Readiness

- Plan 12-04 can add compiler-owned deterministic `IfcBeamType` and `IfcColumnType` factories using the now-authorized structural semantic path.
- No structural geometry operation is executable yet; Door/Window contracts remain unchanged and Phase 13 has not started.

## Self-Check: PASSED

- Created structural property test file exists.
- RED and GREEN commits are present in order.
- All named plan, security, request-stage, compile and diff checks pass.
- Key link now contains both `IfcBeam` and `IfcColumn` in the occurrence-property source.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
