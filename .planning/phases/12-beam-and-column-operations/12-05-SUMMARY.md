---
phase: 12-beam-and-column-operations
plan: "05"
subsystem: structural-geometry
tags: [ifc2x3, beam, column, swept-solid, center-axis, reopen, tdd]

requires:
  - phase: 12-04
    provides: Deterministic structural Type factories and frozen section authority
provides:
  - Repair-local straight rectangular Beam and Column primitive
  - Pure center-axis frame validation with fail-before-mutation boundaries
  - IFC-node-based reopened axis, section and orientation measurement
affects: [12-06, 12-07, 12-08, 12-09, 12-11]

tech-stack:
  added: []
  patterns:
    - Opened-model units, Body context, OwnerHistory and Storey placement are explicit primitive inputs
    - Structural success evidence is recomputed from IfcExtrudedAreaSolid and IfcRectangleProfileDef

key-files:
  created:
    - tests/ifc_repair/test_structural_geometry.py
  modified:
    - src/text2ifc_ifc_repair/geometry.py
    - src/text2ifc_ifc_repair/operations/structural_member.py

key-decisions:
  - "Beam object-local X follows its center axis, Y is the horizontal perpendicular width direction and Z is vertical."
  - "Column object-local X is present only for explicit orientation; a square Column with omitted orientation serializes no RefDirection claim."
  - "Axis extent alone controls extrusion depth; scalar extent and section-rotation fields fail closed."

patterns-established:
  - "Validate every geometry authority before creating an IfcRoot."
  - "Measure the reopened parametric solid instead of using tessellated bounds or volume as acceptance truth."

requirements-completed: [OPS-03, OPS-04]

duration: 4min
completed: 2026-08-06
---

# Phase 12 Plan 05: Repair-Local Structural Geometry Summary

**Straight rectangular Beam and Column solids now preserve the frozen center-axis contract through deterministic IFC2X3 placements and reopened parametric measurements.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-06T00:43:43+08:00
- **Completed:** 2026-08-06T00:47:18+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 3

## Accomplishments

- Added pure frame resolution for arbitrary horizontal XY Beams and vertical Columns.
- Authored `IfcRectangleProfileDef` plus `IfcExtrudedAreaSolid` in the opened model's project units and Body context.
- Placed occurrences relative to the selected Storey and retained its `OwnerHistory` without importing whole-model compiler orchestration.
- Recomputed center-axis endpoints, dimensions and orientation from reopened IFC placement/profile/solid entities.
- Rejected inclined, zero-length, non-rectangular, rotated, scalar-extent, Grid-like, non-finite and unsupported-class requests before creating any `IfcRoot`.
- Required explicit non-square Column orientation while leaving an unoriented square Column without an authored `RefDirection` claim.

## TDD Gate Evidence

### RED

`c0052951` - `test(12-05): add failing structural geometry tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_geometry.py -q`
- Result: collection failed because the planned measurement and member-creation primitives did not exist.

### GREEN

`e4333a9a` - `feat(12-05): author straight rectangular members`

- Plan verification: **14 passed in 7.46s**.
- Structural Type and hosted-opening regressions: **13 passed in 3.99s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

Frame, point, section, placement and IFC measurement helpers were kept inside the two repair-local modules; no separate refactor commit was required.

## Files Created/Modified

- `tests/ifc_repair/test_structural_geometry.py` - Pure-frame, IFC2X3 reopen and zero-Root rejection proof.
- `src/text2ifc_ifc_repair/operations/structural_member.py` - Geometry authority validation and straight-member construction.
- `src/text2ifc_ifc_repair/geometry.py` - IFC-node-based straight rectangular member measurement.

## Decisions Made

- Beam start/end and Column base/top are serialized at profile-centre end faces; profile corners and support faces remain non-authoritative.
- Legitimate support contact is not modified: the primitive does not trim, join, connect, clash-avoid or create structural-analysis relationships.
- The canonical explicit Column orientation is a strict `{x, y}` horizontal direction object; aliases and low-level placement inputs are not accepted.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

The plan traces OPS-03 and OPS-04 and copies them into Summary metadata. Their authoritative project status remains **Pending** until registered operations, strict L0/L1/L2, real DeepSeek UAT and independent Plan 12-16 closure all pass.

## Next Phase Readiness

- Plan 12-06 can bind exact reused/generated Types and optional authorized material/Psets to the new occurrence primitive.
- No Beam/Column operation is registered yet; Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- All plan and adjacent regression tests pass.
- Reopened IFC2X3 measurements match requested center axes and sections.
- Unsupported cases create zero new Roots.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
