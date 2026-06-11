---
phase: 02-minimum-bim-json-to-ifc2x3-compiler
plan: 02
subsystem: ifc-geometry
tags: [ifcopenshell, geometry, dimensions, placement, tdd]
requires:
  - phase-02-compiler-foundation
provides:
  - Measurable minimum geometry for seven solid families
  - IFC attributes for door and window dimensions
  - Deterministic synthetic placement for all nine families
  - Public reopened-IFC dimension measurement
affects:
  - phase-02-complete-acceptance
  - phase-04-high-fidelity-placement
tech-stack:
  added: []
  patterns:
    - Geometry API inputs convert millimetres to SI metres once
    - Reopened tessellated bounds verify solid dimensions
key-files:
  created:
    - tests/compiler/test_geometry.py
  modified:
    - src/text2ifc_compiler/geometry.py
    - src/text2ifc_compiler/verification.py
key-decisions:
  - "Seven three-dimensional families use rectangular dimension envelopes."
  - "Door and window preserve only provided width and height attributes."
  - "Synthetic X placement follows source order at ten-metre intervals."
patterns-established:
  - "Measurement does not depend on IFC profile or representation subtype."
requirements-completed: [IFC-03, IFC-04, VER-01, VER-02, VER-03]
duration: 5min
completed: 2026-06-11
---

# Phase 2 Plan 02: All-Family Geometry Summary

**All nine supported element families now preserve required basic dimensions
within 1 mm in reopened IFC2X3 output.**

## Performance

- **Duration:** 5 minutes
- **Tasks:** 2 TDD tasks
- **Geometry tests:** 3
- **Compiler tests:** 12
- **Repository tests:** 109

## Accomplishments

- Added one explicit `mm_to_m` boundary for IfcOpenShell geometry APIs.
- Added closed rectangular BRep envelopes for wall, column, beam, slab, stair,
  stair flight, and roof.
- Preserved door/window width and height through IFC occurrence attributes
  without inventing thickness.
- Added deterministic placements to every element and public dimension
  measurement from reopened IFC.
- Proved single-family documents create no extra IFC element classes.

## Task Commits

1. **RED: All-family geometry fidelity** - `ebd4a3c`
2. **GREEN: Minimum geometry and reopened measurement** - `393eb82`
3. **REFACTOR:** Not required.

## Test Evidence

- RED: `python -m pytest tests/compiler/test_geometry.py -q` produced
  `2 failed, 1 passed`; failures were missing measurement behavior and missing
  placements.
- GREEN: the same command produced `3 passed in 11.43s`.
- Compiler suite: `12 passed in 42.06s`, below the 60-second phase limit.
- Regression: `109 passed in 69.57s`.
- `python -m compileall -q src` and `git diff --check` passed.

## Dimension Evidence

- Wall: length, thickness, height.
- Column: width, depth, height.
- Beam: length, width, height.
- Slab: length, width, thickness.
- Door/window: width and height.
- Stair: length, width, height.
- Stair flight: total run, width, and total rise.
- Roof: length, width, thickness.

Every value is compared at an absolute tolerance of 1 mm after STEP
serialization and reopen.

## Deviations from Plan

None.

## Issues Encountered

None. The research spike accurately predicted the SI geometry and millimetre
attribute boundaries.

## User Setup Required

None.

## Next Phase Readiness

Plan 02-03 can add selected properties without modifying geometry or compiler
orchestration.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- All family counts and dimensions pass reopened inspection.
- Generated output still passes IFC2X3 validation.
- Compiler suite remains under the phase runtime limit.

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Completed: 2026-06-11*

