---
phase: 12-beam-and-column-operations
plan: "08"
subsystem: column-operation
tags: [ifc2x3, column, registry, storey, orientation, application, tdd]

requires:
  - phase: 12-01
    provides: Frozen column.add prompt profile
  - phase: 12-05
    provides: Straight rectangular member geometry
  - phase: 12-06
    provides: Structural Type and semantic binding
  - phase: 12-07
    provides: Common structural resolution and Storey targets
provides:
  - Default-registry add_column operation through the common lifecycle
  - Strict non-square orientation clarification and square omission policy
  - Base-Storey-only containment for Columns crossing upper Storeys
  - Reopened contained and typed Column application proof
affects: [12-09, 12-10, 12-11, 12-12]

tech-stack:
  added: []
  patterns:
    - Column orientation is canonical occurrence geometry and is explicitly projected out of Type section authority
    - A vertical Column is contained exactly once by its axis-base Storey even when its top crosses upper Storeys

key-files:
  created:
    - src/text2ifc_ifc_repair/operations/column.py
    - tests/ifc_repair/test_column_resolution.py
    - tests/ifc_repair/test_column_application.py
  modified:
    - src/text2ifc_ifc_repair/operations/__init__.py
    - src/text2ifc_ifc_repair/operations/structural_member.py
    - src/text2ifc_ifc_repair/structural_resolution.py
    - tests/ifc_repair/test_beam_resolution.py
    - tests/ifc_repair/test_selected_provider_profiles.py
    - tests/ifc_repair/test_structural_prompt_profiles.py

key-decisions:
  - "A non-square Column without explicit canonical orientation clarifies; a square Column preserves omission and invents no direction."
  - "Column occurrence orientation never enters the IfcColumnType section fingerprint."
  - "Automatic split-at-Storey intent is rejected before mutation; one Column keeps one base-Storey containment."

patterns-established:
  - "Both structural families are now executable in the compact Stage 1 operation catalog."
  - "Unsupported inclined/Grid/round/analysis/split requests return stable deterministic capability codes."

requirements-completed: [OPS-04]

duration: 12min
completed: 2026-08-06
---

# Phase 12 Plan 08: Registered Column Operation Summary

**`add_column` now resolves, audits, applies and reopens one exact vertical rectangular IFC2X3 Column with one Type and exactly one axis-base Storey containment.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-06T01:27:00+08:00
- **Completed:** 2026-08-06T01:39:23+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 9 including two RED test files

## Accomplishments

- Registered `add_column` with `column.add`, strict target/intent/canonical schemas, semantic role, Type factory and physical-only capability metadata.
- Resolved complete square and explicitly oriented non-square Columns without adding a common Column dispatcher branch.
- Returned grouped clarification at `/parameters/section/orientation` when a non-square section has no authoritative direction.
- Preserved square-section orientation omission and authored the requested non-square RefDirection exactly.
- Published one reopened IFC2X3 Column with one `IfcColumnType` and exactly one base-Storey containment even when the top reaches upper Storeys.
- Kept omitted material and Psets absent; rejected inclined, Grid, round, analysis and automatic Storey-split requests before mutation.
- Explicitly separated occurrence orientation from the frozen Type section fingerprint without adding aliases or compatibility normalization.

## TDD Gate Evidence

### RED

`60549c8e` - `test(12-08): add failing column operation tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_column_resolution.py tests\ifc_repair\test_column_application.py -q`
- Result: collection failed because the planned registered Column module did not exist.

### GREEN

`0578e2d2` - `feat(12-08): register deterministic column operation`

- Plan verification: **5 passed in 13.86s**.
- Column plus Beam/profile/Type/geometry/index/Registry/request/provider/audit regressions: **89 passed in 41.46s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

The shared structural Type boundary now projects the canonical occurrence section onto the exact family Type section keys. It validates Column orientation strictly but does not store that occurrence-only fact in the Type template or fingerprint.

## Deviations from Plan

### Auto-fixed: temporal executable-family assertions

- **Found during:** Beam and provider/profile regression after Column registration.
- **Issue:** earlier tests correctly froze the Wave 7 state where only Beam was registered; they became stale when Wave 8 intentionally registered Column.
- **Fix:** advanced those assertions to require both completed structural families and retained all prompt-profile content checks.
- **Why required:** this is the planned temporal transition of the Registry and Stage 1 catalog, not a scope or workflow change.

## Issues Encountered

- The first GREEN run exposed that canonical Column occurrence orientation was being passed to the stricter Type-section validator. The occurrence-to-Type boundary now accepts only the canonical orientation shape, validates it, and projects only `shape`, `width_mm` and `depth_mm` into Type authority.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

Plan 12-08 supplies the registered OPS-04 operation, but authoritative OPS-03 and OPS-04 remain **Pending** until strict L0/L1/L2, real DeepSeek UAT and independent Plan 12-16 closure pass.

## Next Phase Readiness

- Plan 12-09 can evaluate both registered structural families with strict geometry, containment, Type and mixed-transaction atomicity gates.
- Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Default Registry reopens square and oriented Columns with exact Type and base-Storey cardinality.
- Clarification and unsupported paths publish nothing.
- Beam and common request/provider/audit behavior remain green.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
