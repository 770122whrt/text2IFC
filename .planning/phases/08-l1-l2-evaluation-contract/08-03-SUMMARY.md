---
phase: 08-l1-l2-evaluation-contract
plan: 03
subsystem: evaluation
tags: [l1, ifcopenshell, preservation, authorization, topology, tolerances, tdd]

requires:
  - phase: 08-l1-l2-evaluation-contract
    plan: 01
    provides: immutable five-state Evaluation 0.2 check/level/aggregation records
  - phase: 08-l1-l2-evaluation-contract
    plan: 02
    provides: operation-owned Registry policy and Window evaluation adapter seam
provides:
  - Independent reopened-IFC created/modified/removed root and relationship facts
  - Three-way Registry policy, ChangeSet scope, and actual-diff authorization
  - Stable evidence-bearing Window L1 geometry/topology/containment/tolerance checks
  - Compatibility projection that prevents legacy callers from publishing failed L1 artifacts
affects: [08-04, phase-09, phase-10, repair-publication, future-operation-l1-policies]

tech-stack:
  added: []
  patterns:
    - Applicator changes bind generated role identities but never authorize effects
    - Operation adapters own L1 roles/classes/relations and normalized measurements
    - Common L1 evaluation consumes deterministic compact before/after diff evidence

key-files:
  created:
    - tests/ifc_repair/test_l1_evaluator.py
  modified:
    - src/text2ifc_ifc_repair/compare.py
    - src/text2ifc_ifc_repair/evaluation.py
    - src/text2ifc_ifc_repair/operations/window.py

key-decisions:
  - "Actual effects come only from independently reopened before/after IFC models; Applicator output supplies role-to-GlobalId bindings, not authority."
  - "An effect passes scope only when its actual class/kind/endpoints match operation-owned Registry policy and the operation target is inside ChangeSet scope."
  - "Legacy evaluate_repair_application fields remain available, but complete/publishable success is additionally gated by the structured independent L1 result."
  - "Scope evidence retains compact before/after fingerprints and key normalized fields under a fixed size bound instead of embedding unbounded raw root attributes."

patterns-established:
  - "Stable L1 IDs: l1.output.*, l1.source.*, l1.scope.*, and operation-owned l1.window.* checks."
  - "Unmeasurable mandatory operation geometry returns not_evaluable CheckResults rather than raising or passing."

requirements-completed:
  - VAL-01
  - VAL-03

duration: 33min
completed: 2026-07-19
---

# Phase 8 Plan 3: Independent L1 Authorization and Preservation Evaluation Summary

**Reopened IFC evidence now independently authorizes every actual root and relationship effect through Registry policy plus ChangeSet intent, while stable Window L1 checks reject collateral, malformed, misplaced, duplicated, or unmeasurable repairs.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-07-19T03:16:44Z
- **Completed:** 2026-07-19T03:50:07Z
- **Tasks:** 3
- **Files modified:** 4 code/test files, plus this summary

## Accomplishments

- Added deterministic actual `IfcRoot` differencing from independently reopened IFCs, separating roots and relationships while retaining the original `compare_ifc_models` compatibility behavior.
- Cross-checked actual change kind/class/relationship endpoints against operation-owned Window authorization policy, ChangeSet target scope, and Applicator role bindings; self-reported collateral Wall changes remain unauthorized.
- Converted existing Window dimensions, placement, geometry-fit, Host/Opening/Filling topology, containment, duplicate-chain, volume, and tolerance measurements into Evaluation 0.2 `CheckResult` records.
- Added common readability, schema, source fingerprint, created/modified/removed scope, and relationship checks with deterministic ordering and bounded before/after evidence.
- Made unreadable output and unmeasurable mandatory geometry non-passing without changing Window authoring or broadening its mutation scope.

## TDD Evidence

- **RED:** 13 controlled IFC tests failed because `evaluate_independent_l1` was absent; the real IFC2X3 Window application fixture itself reopened and applied successfully.
- **GREEN:** Independent diff authorization, normalized Window checks, and the legacy publication gate made 13 focused tests and 16 focused/compare/Window tests pass.
- **REFACTOR:** Frozen exact check IDs, compact evidence bounds, explicit compatibility projection, and `not_evaluable` geometry fallback expanded the focused suite to 14 and passed 18 L1/compare/offline tests.

## Task Commits

Each TDD gate was committed atomically:

1. **Task 1: RED - freeze three-way authorization and L1 taxonomy** - `51b19693` (test)
2. **Task 2: GREEN - implement actual-diff authorization and checks** - `a8ce04e7` (feat)
3. **Task 3: REFACTOR - stabilize evidence and compatibility** - `9ed91f48` (refactor)

## Files Created/Modified

- `src/text2ifc_ifc_repair/compare.py` - Original 0.1 comparator plus deterministic actual root/relation diff facts and strict L1 compatibility gate.
- `src/text2ifc_ifc_repair/evaluation.py` - Common reopened-IFC L1 evaluator, three-way authorization, structured checks, compact evidence, and deterministic ordering.
- `src/text2ifc_ifc_repair/operations/window.py` - Window-owned L1 authorization policy and normalized measurement checks; authoring logic retained unchanged.
- `tests/ifc_repair/test_l1_evaluator.py` - Controlled valid/fault IFC fixtures covering all required L1 categories and Applicator self-report rejection.

## Decisions Made

- Kept common L1 unaware of Window field names: the Registry-dispatched comparison adapter supplies authorization roles/classes/relations and normalized check payloads.
- Treated exact relationship endpoint deltas as authorization evidence for modified containment/type relations; a role/class match alone cannot authorize endpoint drift.
- Kept full normalized snapshots internal to differencing and projected compact hashes plus key fields into evidence, preserving before/after accountability without report-size dependence on relationship fan-out.
- Added independent L1 status to the legacy 0.1 dictionary as an additive compatibility projection and used it to gate both complete success and publication.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced repeated full-LargeBuilding fault evaluation with a compact real IFC fixture**
- **Found during:** Task 2 GREEN focused run
- **Issue:** Every injected fault recomputed normalized geometry over the full LargeBuilding model; the first GREEN run exceeded 124 seconds before producing results.
- **Fix:** Extracted the real IFC2X3 Project/Storey/target Wall geometry into a compact module-scoped model, then applied the unchanged production Window operation and fault mutations to that reopened IFC.
- **Files modified:** `tests/ifc_repair/test_l1_evaluator.py`
- **Verification:** 13 focused tests completed in 5.20 seconds and the LargeBuilding Window regression separately passed in the 16-test GREEN gate.
- **Committed in:** `a8ce04e7`

**2. [Rule 1 - Test Bug] Corrected compact-fixture fault targets and representation mutation**
- **Found during:** Task 2 GREEN focused run
- **Issue:** The compact fixture initially omitted the unrelated Wall/PropertySet needed for wrong-host/deletion faults and used a rectangle-profile mutation although the real Opening used an arbitrary polyline profile; path-bearing evidence also made rewrite equality differ.
- **Fix:** Added preserved out-of-scope roots, mutated the actual polyline coordinates, used a missing path for unreadability, and made repaired-artifact evidence references path-neutral.
- **Files modified:** `tests/ifc_repair/test_l1_evaluator.py`, `src/text2ifc_ifc_repair/evaluation.py`
- **Verification:** The next focused run passed 13/13 and the STEP-rewrite equality assertion passed.
- **Committed in:** `a8ce04e7`

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking issue, 1 Rule 1 test bug).
**Impact on plan:** Both fixes made the required controlled IFC suite deterministic and fast without changing production authoring, authorization scope, or public mutation capability.

## Issues Encountered

- Full-model normalized comparison is intentionally more expensive than the compact focused fixture. The existing LargeBuilding regression remained in the GREEN gate and passed; REFACTOR acceptance used the plan-specified focused/compare/offline suite.

## Known Stubs

None. No TODO/FIXME/placeholder behavior or unwired empty L1 output was found in the created/modified files.

## Threat Mitigations

- **T-08-03A:** Applicator self-report cannot authorize collateral drift; actual diffs require both Registry policy and ChangeSet scope.
- **T-08-03B:** Relationship endpoint, cardinality, missing-chain, extra-relation, duplicate-chain, wrong-host, and containment checks are explicit failures.
- **T-08-03C:** Comparison is GlobalId/role normalized and STEP-order neutral; dimensions, placement, orientation, and volume use versioned Window tolerances.

## User Setup Required

None - no external services or configuration required.

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_l1_evaluator.py -q` - **14 passed**
- `.venv\Scripts\python -m pytest tests\ifc_repair\test_l1_evaluator.py tests\ifc_repair\test_compare.py tests\ifc_repair\test_window_application.py -q` - **16 passed** (GREEN gate)
- `.venv\Scripts\python -m pytest tests\ifc_repair\test_l1_evaluator.py tests\ifc_repair\test_compare.py tests\ifc_repair\test_offline_e2e.py -q` - **18 passed** (REFACTOR gate)
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair` - **passed**
- Common-module Window-field scan - **no matches**
- Stub-marker scan and `git diff --check` - **passed**
- TDD commit order - **RED `51b19693` -> GREEN `a8ce04e7` -> REFACTOR `9ed91f48`**

## Next Phase Readiness

- Plan 08-04 can consume deterministic L1 status/check evidence beside private benchmark L2 evaluation and public report projection.
- Phase 9 can rely on `successful_artifact_publishable` being false for any non-passing independent L1 result.
- Phase 10 remains responsible for Window semantic authoring; this plan changed no authoring behavior.

## Self-Check: PASSED

- All four planned code/test artifacts and this summary exist on disk.
- RED, GREEN, and REFACTOR commits `51b19693`, `a8ce04e7`, and `9ed91f48` exist in git history.
- Fresh focused, REFACTOR regression, compileall, diff, stub, and common-module boundary checks passed before summary creation.

---
*Phase: 08-l1-l2-evaluation-contract*
*Completed: 2026-07-19*
