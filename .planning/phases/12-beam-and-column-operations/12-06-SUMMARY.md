---
phase: 12-beam-and-column-operations
plan: "06"
subsystem: structural-semantics
tags: [ifc2x3, exact-type, material, pset, authority, atomicity, tdd]

requires:
  - phase: 12-04
    provides: Deterministic structural Type factories
  - phase: 12-05
    provides: Structural occurrence primitive and stable occurrence roles
provides:
  - Exact/generated structural Type binding without shared-Type mutation
  - Type forward-graph fingerprint across maps, Psets and inherited material
  - Strict explicit material reuse/create and reused-Type conflict preflight
  - Optional occurrence-direct Pset/material isolation
affects: [12-07, 12-08, 12-09, 12-11]

tech-stack:
  added: []
  patterns:
    - Type binding extends only IfcRelDefinesByType inverse membership
    - Exact material labels are authority, never grade/strength inference

key-files:
  modified:
    - src/text2ifc_ifc_repair/type_templates.py
    - src/text2ifc_ifc_repair/operations/structural_member.py
    - src/text2ifc_ifc_repair/semantic_authoring.py
    - tests/ifc_repair/test_structural_type_authoring.py

key-decisions:
  - "A Type preservation fingerprint excludes inverse occurrence membership but includes the complete forward graph and associated material resources."
  - "Explicit label authority reuses one exact IfcMaterial or creates only that label when absent; duplicate labels fail closed."
  - "An explicit material matching reused-Type inheritance is satisfied without a direct duplicate; a mismatch is a blocking conflict."

patterns-established:
  - "Preflight every material assignment and reused-Type conflict before Pset or association mutation."
  - "Generated Types remain semantically empty while authorized facts attach only to the created occurrence."

requirements-completed: [OPS-03, OPS-04]

duration: 5min
completed: 2026-08-06
---

# Phase 12 Plan 06: Exact Type and Optional Semantics Summary

**Structural Type reuse now preserves the complete Type authority graph, while material and Pset authoring occurs only from explicit bound occurrence authority.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-06T00:53:54+08:00
- **Completed:** 2026-08-06T00:58:30+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 4

## Accomplishments

- Added family-neutral Beam/Column Type binding with stable created/modified roles for later registered operations.
- Proved exact Type reuse changes only `IfcRelDefinesByType.RelatedObjects`, not Type identity, maps, Psets or inherited material.
- Prevented occurrence-direct material/Pset facts on a reference occurrence from being copied to a new occurrence.
- Kept omitted material/Psets absent without clarification.
- Added exact material-label resolution: reuse one exact entity, create only the exact absent label, or reject duplicate labels.
- Preserved matching Type-inherited material without a redundant direct relationship and rejected mismatched explicit material before semantic mutation.
- Proved generated Types do not absorb explicitly authorized occurrence material or Psets.

## TDD Gate Evidence

### RED

`22429e98` - `test(12-06): add failing structural semantic tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_type_authoring.py -q`
- Result: collection failed because Type authority fingerprinting and structural binding did not exist.

### GREEN

`d7f675b4` - `feat(12-06): preserve structural type semantics`

- Plan verification: **29 passed in 4.17s** across structural Type, property authoring and transaction suites.
- Historical generated-Type plus Door/Window application regressions: **8 passed in 25.10s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

Material preflight and exact-label resolution were added to the existing operation-neutral semantic compiler; no family-specific semantic branch or separate refactor commit was needed.

## Files Modified

- `src/text2ifc_ifc_repair/type_templates.py` - Type authority forward-graph fingerprint.
- `src/text2ifc_ifc_repair/operations/structural_member.py` - Exact/generated Type relationship binding and stable semantic target role.
- `src/text2ifc_ifc_repair/semantic_authoring.py` - Exact material authority, inheritance satisfaction and conflict preflight.
- `tests/ifc_repair/test_structural_type_authoring.py` - Preservation, absence, explicit semantics, ambiguity and atomic preflight matrix.

## Decisions Made

- A `request:/...` material assignment must contain an exact non-empty `IfcMaterial` label and canonical typed assignment fields. No aliases or descriptive grade parsing are accepted.
- Existing `resource:guid/step` authority remains exact; the label path does not weaken it or fall back from an invalid resource.
- Multiple direct materials, multiple Type materials or multiple exact-label resources are ambiguous and fail closed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

The plan traces OPS-03 and OPS-04 and copies them into Summary metadata. Their authoritative project status remains **Pending** until registered Beam/Column operations, strict L0/L1/L2, real DeepSeek UAT and independent Plan 12-16 closure pass.

## Next Phase Readiness

- Plan 12-07 can register `add_beam` using the shared geometry and Type/semantic binding primitives.
- No structural operation is registered yet; Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Exact Type fingerprint remains unchanged after occurrence binding.
- Omitted and inherited semantics remain correctly absent/direct-free.
- Explicit Pset/material facts are exact and conflict preflight leaves no semantic mutation.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
