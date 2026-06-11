---
phase: 02-minimum-bim-json-to-ifc2x3-compiler
plan: 03
subsystem: ifc-properties
tags: [ifcopenshell, property-sets, ifc2x3-enums, tdd]
requires:
  - phase-02-compiler-foundation
provides:
  - Standard common-property mappings for selected booleans
  - Exact predefined-type fallback preservation
  - Safe compatible slab, stair, and roof occurrence enums
affects:
  - phase-02-complete-acceptance
  - phase-03-text-to-json-evaluation
tech-stack:
  added: []
  patterns:
    - Standard IFC mapping plus exact source fallback
    - Explicit enum allowlists prevent invalid schema assignments
key-files:
  created:
    - tests/compiler/test_properties.py
  modified:
    - src/text2ifc_compiler/properties.py
key-decisions:
  - "Boolean source values remain IFC booleans in family common psets."
  - "Every predefined_type is stored in Pset_text2IFCProperties."
  - "USERDEFINED-like values are not assigned without required supporting facts."
patterns-established:
  - "Missing optional properties create no semantic property set."
requirements-completed: [IFC-05, VER-01, VER-02, VER-03]
duration: 4min
completed: 2026-06-11
---

# Phase 2 Plan 03: Selected Property Fidelity Summary

**Selected boolean and predefined-type properties now round-trip from canonical
BIM JSON through reopened IFC2X3 without coercion or silent loss.**

## Performance

- **Duration:** 4 minutes
- **Tasks:** 2 TDD tasks
- **Property tests:** 16
- **Compiler tests:** 28
- **Repository tests:** 125

## Accomplishments

- Mapped wall `is_external` and wall/column/beam `load_bearing` to compatible
  IFC2X3 common property sets.
- Preserved exact source `predefined_type` strings in one deterministic custom
  property set.
- Populated compatible slab, stair, and roof occurrence enums through explicit
  allowlists.
- Kept custom values schema-valid by retaining required stair/roof
  `NOTDEFINED` values and leaving incompatible optional attributes unset.
- Proved missing optional properties remain absent and compilation does not
  mutate the source document.

## Task Commits

1. **RED: Selected property fidelity** - `2d147a0`
2. **GREEN: Standard and fallback property mapping** - `0ac4fd8`
3. **REFACTOR:** Not required.

## Test Evidence

- RED: `python -m pytest tests/compiler/test_properties.py -q` produced
  `15 failed, 1 passed`.
- GREEN: the same command produced `16 passed in 6.40s`.
- Compiler suite: `28 passed in 50.50s`, below the 60-second limit.
- Regression: `125 passed in 75.03s`.
- `python -m compileall -q src` and `git diff --check` passed.

## Mapping Evidence

- `is_external` -> `Pset_WallCommon.IsExternal`
- `load_bearing` -> family `Pset_*Common.LoadBearing`
- every `predefined_type` ->
  `Pset_text2IFCProperties.PredefinedType`
- compatible slab -> `IfcSlab.PredefinedType`
- compatible stair -> `IfcStair.ShapeType`
- compatible roof -> `IfcRoof.ShapeType`

## Deviations from Plan

None.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Plan 02-04 can now verify the complete fixture through one CLI path and prove
the negative IFC validator behavior.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Standard, custom, true, false, and absent cases are covered.
- Generated outputs remain schema-valid.
- Compiler suite remains under the phase runtime limit.

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Completed: 2026-06-11*

