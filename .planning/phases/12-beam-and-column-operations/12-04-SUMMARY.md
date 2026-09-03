---
phase: 12-beam-and-column-operations
plan: "04"
subsystem: type-authoring
tags: [ifc2x3, beam-type, column-type, deterministic-authority, tamper-evidence, tdd]

requires:
  - phase: 12-03
    provides: Exact structural property and semantic authority path
provides:
  - Compiler-owned deterministic IfcBeamType and IfcColumnType templates
  - Dedicated structural Type factories bound to authorized rectangular sections
  - Structural class/template/version/digest/section/content tamper rejection
  - Exact Type reuse preservation and nearby-Type non-selection proof
affects: [12-05, 12-06, 12-07, 12-08]

tech-stack:
  added: []
  patterns:
    - Generated structural Types validate both outer derivation hash and fixed factory contract
    - No-reuse intent produces a dedicated deterministic Type independent of project similarity

key-files:
  created:
    - src/text2ifc_ifc_repair/operations/structural_member.py
    - tests/ifc_repair/test_structural_type_authoring.py
  modified:
    - src/text2ifc_ifc_repair/type_templates.py

key-decisions:
  - "Beam and Column use separate compiler template IDs with one shared versioned structural factory implementation."
  - "Generated structural Types carry only deterministic identity/label, NOTDEFINED formal type and authorized section digest; no material, Pset or representation is inferred."

patterns-established:
  - "Structural generated-Type template: exact class plus normalized rectangle section and section digest."
  - "Defense in depth: a recomputed outer digest cannot authorize a changed template ID, version, section or extra Provider content."

requirements-completed: [OPS-03, OPS-04]

duration: 3min
completed: 2026-08-06
---

# Phase 12 Plan 04: Deterministic Structural Type Factories Summary

**Dedicated deterministic `IfcBeamType` and `IfcColumnType` factories now derive only from compiler-owned templates and authorized rectangular sections.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-08-06T00:32:49+08:00
- **Completed:** 2026-08-06T00:36:00+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 3

## Accomplishments

- Extended `ensure_bound_type` to permit generated `IfcBeamType` and `IfcColumnType` only through registered factories.
- Added deterministic, family-specific template IDs and a normalized authorized rectangular-section digest.
- Proved two nearby same-size project Types do not affect no-reuse generation or trigger clarification.
- Preserved exact compatible Type identity and serialization unchanged; a family mismatch still fails before mutation.
- Rejected class, template ID, template version, raw digest, section and extra Provider-content tampering before any new `IfcRoot` is created.

## TDD Gate Evidence

### RED

`8ad10e20` - `test(12-04): add failing structural type tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_type_authoring.py -q`
- Result: **8 failed, 3 passed**.
- Intended failures: missing structural factory module for generation and tamper cases.
- Existing exact Type reuse and family-mismatch protections passed before implementation.

### GREEN

`bbd24d96` - `feat(12-04): add deterministic structural type factories`

- Plan verification: **12 passed in 1.52s** across structural and historical generated-Type authority tests.
- Door application regression: **4 passed in 19.85s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

No separate refactor commit was needed. Beam and Column wrappers share one bounded private implementation while retaining distinct class, section-key and template contracts.

## Files Created/Modified

- `src/text2ifc_ifc_repair/operations/structural_member.py` - Structural templates, normalized sections and generated Type factories.
- `tests/ifc_repair/test_structural_type_authoring.py` - Determinism, nearby-Type isolation, exact reuse and tamper matrix.
- `src/text2ifc_ifc_repair/type_templates.py` - Registered structural generated-Type classes in the existing fail-closed dispatcher.

## Decisions Made

- Generated Beam/Column Types intentionally have no representation map in this wave; Plan 12-05 owns occurrence geometry, and no project Type geometry is cloned or rescaled.
- The factory compares the complete compiler payload after independently checking the authorized section, so additional Provider template fields fail even if a digest is recomputed.
- Existing Type reuse remains a direct exact-identity path; similarity candidates are never consulted.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The plan context references `tests/ifc_repair/test_door_type_authoring.py`, but that file does not exist in the repository. The actual existing generated-Type regression files are `test_generated_type_authority.py` and `test_door_application.py`; both relevant suites were run. This documentation reference drift did not require creating a compatibility test file or changing production scope.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

The plan traces OPS-03 and OPS-04 and copies them into Summary metadata. Their authoritative project status remains **Pending** until Plan 12-16 independently closes complete operations, strict L0/L1/L2 and real DeepSeek Proof.

## Next Phase Readiness

- Plan 12-05 can extend `structural_member.py` with the repair-local center-axis rectangular geometry primitive.
- Type generation is available but no Beam/Column operation is registered or executable yet; Phase 13 has not started.

## Self-Check: PASSED

- Structural member module and structural Type test file exist.
- RED and GREEN commits exist in order.
- All named plan, Door regression, compile and diff checks pass.
- Generated structural Types contain no unrequested material, Pset or representation map.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
