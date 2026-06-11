---
phase: 02-minimum-bim-json-to-ifc2x3-compiler
plan: 01
subsystem: ifc-compiler-foundation
tags: [ifcopenshell, ifc2x3, tdd, atomic-write, uuid5]
requires:
  - phase-01-bim-json-contract
provides:
  - Validated BIM JSON 1.0 compiler boundary
  - Schema-valid IFC2X3 hierarchy and nine-family occurrence creation
  - Stable recoverable BIM ID to GlobalId mapping
  - In-memory and reopened verification before atomic output replacement
affects:
  - phase-02-geometry
  - phase-02-properties
  - phase-02-cli
tech-stack:
  added: []
  patterns:
    - Phase 1 validation runs before any IFC output work
    - UUIDv5 identities are domain-separated and IFC-compressed
    - Sibling temporary IFC is reopened before os.replace
key-files:
  created:
    - src/text2ifc_compiler/bootstrap.py
    - src/text2ifc_compiler/identity.py
    - src/text2ifc_compiler/geometry.py
    - src/text2ifc_compiler/properties.py
    - tests/compiler/test_compiler_boundary.py
  modified:
    - src/text2ifc_compiler/compiler.py
    - src/text2ifc_compiler/verification.py
key-decisions:
  - "IfcOpenShell owner discovery is used without process-global monkeypatches."
  - "Original BIM IDs are stored in Pset_text2IFCIdentity.BimJsonId."
  - "Stair and roof mandatory shape fields begin as NOTDEFINED until property mapping."
patterns-established:
  - "Artifact requirements are tested after STEP serialization and reopen."
  - "Geometry and selected properties are separate Wave 2 extension modules."
requirements-completed: [IFC-01, IFC-02, IFC-03, VER-01, VER-02]
duration: 7min
completed: 2026-06-11
---

# Phase 2 Plan 01: Compiler Foundation Summary

**Validated BIM JSON now produces an atomically written, schema-valid IFC2X3
hierarchy with exact occurrence counts and stable recoverable identities.**

## Performance

- **Duration:** 7 minutes
- **Tasks:** 2 TDD tasks
- **Focused tests:** 9
- **Repository tests:** 106

## Accomplishments

- Reused Phase 1 diagnostics as the mandatory compiler gate.
- Built IFC2X3 owner metadata, millimetre units, contexts, project hierarchy,
  storey aggregation, and all nine element occurrence classes.
- Added domain-separated UUIDv5 GlobalIds and original BIM ID property sets.
- Added normalized schema verification before and after STEP serialization.
- Protected existing destinations through sibling temporary files and atomic
  replacement.

## Task Commits

1. **RED: Compiler boundary behavior** - `698b76d`
2. **GREEN: Validated IFC2X3 compiler foundation** - `d75919e`
3. **REFACTOR:** Deterministic storey inspection ordering was folded into
   GREEN after reopened IFC exposed unordered aggregate members.

## Test Evidence

- RED: `python -m pytest tests/compiler/test_compiler_boundary.py -q`
  produced `9 failed`, all at the deliberate compiler
  `NotImplementedError`.
- GREEN: the same command produced `9 passed in 16.48s`.
- Compiler suite: `9 passed in 16.93s`.
- Regression: `106 passed in 33.08s`.
- `python -m compileall -q src` passed.
- `git diff --check` passed.

## Security Evidence

- Three invalid-input classes preserve a pre-existing sentinel output.
- An injected reopened-verification failure preserves destination bytes.
- Failure paths leave no sibling temporary artifact.
- Two compilations recover the same unique 22-character GlobalIds for every
  canonical object.

## Decisions Made

- Kept IFC geometry and selected properties as explicit no-op extension points
  so Wave 2 plans can modify separate modules.
- Sorted hierarchy inspection by elevation and BIM ID because IFC aggregate
  member ordering is not a business-order guarantee.
- Used `NOTDEFINED` only for mandatory IFC stair and roof shape attributes; no
  source property is synthesized.

## Deviations from Plan

None. The public compiler result, verifier, hierarchy, identity, and atomic
output behavior match the plan.

## Issues Encountered

IfcOpenShell returned storeys in reverse aggregate-member order after reopen.
The public snapshot now uses deterministic elevation and BIM-ID ordering while
preserving exact names, IDs, and elevations.

## User Setup Required

None.

## Next Phase Readiness

- Plan 02-02 can implement all-family minimum geometry in `geometry.py`.
- Plan 02-03 can implement selected properties independently in
  `properties.py`.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- All planned files exist.
- Focused, compiler, and repository tests pass.
- High threats assigned to this plan have automated evidence.

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Completed: 2026-06-11*

