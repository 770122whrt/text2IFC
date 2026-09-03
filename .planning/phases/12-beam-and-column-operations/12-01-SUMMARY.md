---
phase: 12-beam-and-column-operations
plan: "01"
subsystem: prompts
tags: [ifc2x3, beam, column, prompt-profiles, selected-routing, sha256]

requires:
  - phase: 11-wall-opening-and-door-operations
    provides: selected compact/full operation-profile routing and hash-bound few-shots
provides:
  - Reserved canonical beam.add and column.add compact/full prompt contracts
  - Four complete, clarification, exact-Type-reuse and unsupported sentinels per structural family
  - External prompt-registry hash enforcement before selected full profiles enter Stage 2
affects: [12-07-beam-operation, 12-08-column-operation, phase12-live-uat]

tech-stack:
  added: []
  patterns: [reserved operation profiles, registry-bound selected profile hashes, compact Stage 1 and selected full Stage 2]

key-files:
  created:
    - prompts/agent/ifc-repair-profiles/beam.add.json
    - prompts/agent/ifc-repair-profiles/column.add.json
    - tests/ifc_repair/test_structural_prompt_profiles.py
  modified:
    - prompts/agent/registry.json
    - src/text2ifc_ifc_repair/prompt_profiles.py
    - tests/ifc_repair/test_operation_prompt_profiles.py

key-decisions:
  - "Beam/Column profiles remain reserved prompt contracts; add_beam/add_column are not registered as executable operations until Plans 12-07/12-08."
  - "Every selected full operation profile, including historical profiles, must match its external prompts/agent/registry.json path and SHA-256 before Stage 2."
  - "Structural prompt facts use Storey-local millimetre center axes and rectangular sections only; low-level placement, GUID and generated-Type identity remain program-derived."

patterns-established:
  - "Reserved-profile TDD: test Stage 1 routing with a test-local registry while proving the production default registry remains unchanged."
  - "Double hash boundary: few-shots are hash-bound by their profile and selected profiles are hash-bound by the external prompt registry."

requirements-completed: [OPS-03, OPS-04]

duration: 23 min
completed: 2026-08-04
---

# Phase 12 Plan 01: Structural Prompt Profiles and Selected Routing Summary

**Canonical Beam/Column prompt profiles with eight hash-bound sentinels, one-call compact Stage 1 routing, and externally verified selected-only Stage 2 loading**

## Performance

- **Duration:** 23 min
- **Started:** 2026-08-04T16:28:06Z
- **Completed:** 2026-08-04T16:52:04Z
- **Tasks:** 1 TDD feature (RED/GREEN; no refactor required)
- **Files modified:** 14

## Accomplishments

- Added reserved `beam.add` and `column.add` profiles with canonical Storey-local millimetre center-axis and rectangular-section slots, optional authorized semantics, and explicit unsupported boundaries.
- Added complete, grouped-clarification, exact-Type-reuse and unsupported few-shots for each family without compatibility aliases or program-derived IFC identity/placement fields.
- Proved Beam-only and Column-only Stage 1 extraction each use exactly one Provider call, while Stage 2 selection excludes unrelated Beam/Column, Window and Door full payloads.
- Bound all selected full profiles to external registry paths and SHA-256 hashes while leaving `add_beam` and `add_column` absent from the executable default registry.

## TDD Evidence

### RED

- Added nine structural routing/profile tests before production artifacts existed.
- Focused run failed with seven intended failures: missing `beam.add.json`/`column.add.json` assertions and `UNKNOWN_PROFILE_ID` selection errors.
- No import, syntax or test-infrastructure failure occurred.

### GREEN

- Added two profiles, eight sentinel examples, external registry records and selected-profile registry/hash validation.
- Plan verification passed: `20 passed in 9.53s`.
- Prompt registry regression passed: `11 passed in 8.26s`.
- Focused compile and `git diff --check` passed.

### REFACTOR

- Not needed; the GREEN implementation is one generic selected-profile binding check plus declarative profile artifacts.

## Task Commits

Each TDD gate was committed atomically:

1. **RED: failing structural profile routing tests** - `70652c21` (test)
2. **GREEN: hash-bound structural prompt profiles** - `74c27935` (feat)

## Files Created/Modified

- `prompts/agent/ifc-repair-profiles/beam.add.json` - Canonical reserved Beam compact/full profile.
- `prompts/agent/ifc-repair-profiles/column.add.json` - Canonical reserved Column compact/full profile.
- `prompts/agent/ifc-repair-few-shots/beam-add-*.json` - Four sentinel Beam outcomes.
- `prompts/agent/ifc-repair-few-shots/column-add-*.json` - Four sentinel Column outcomes.
- `prompts/agent/registry.json` - External path/hash records for all selected operation profiles.
- `src/text2ifc_ifc_repair/prompt_profiles.py` - Fail-closed external registry validation before full profile selection.
- `tests/ifc_repair/test_structural_prompt_profiles.py` - One-call routing, canonical slot, exclusion, union, schema and hash tests.
- `tests/ifc_repair/test_operation_prompt_profiles.py` - Exact additive profile inventory synchronized from seven to nine.

## Decisions Made

- Kept structural definitions test-local for the Stage 1 capture tests so the production default Registry still exposes no `add_beam` or `add_column` operation before Plans 12-07/12-08.
- Applied external path/hash validation generically to every selected operation profile instead of adding Beam/Column branches or trusting a runtime-computed hash alone.
- Kept optional material and Pset/quantity semantics as existing canonical intent channels; omitted semantics neither clarify nor authorize inference.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Synchronized the historical exact profile inventory assertion**
- **Found during:** Task 12-01-01 focused historical regression
- **Issue:** Adding two reserved profiles correctly changed the complete compact catalog from seven profiles to nine, so the historical exact-count assertion failed while all leakage assertions remained green.
- **Fix:** Updated only the exact expected count from 7 to 9; retained the historical assertions that compact Stage 1 payloads contain neither `user_text` nor `EXAMPLE_ONLY` few-shot bodies.
- **Files modified:** `tests/ifc_repair/test_operation_prompt_profiles.py`
- **Verification:** The complete plan command passed 20 tests, including all historical selected-provider/profile tests.
- **Committed in:** `74c27935`

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug).
**Impact on plan:** Required additive inventory maintenance only; no historical routing, hash, Door/Window contract or executable operation was weakened.

## Issues Encountered

- The first GREEN draft had an extra closing brace in the two new complete few-shot JSON files. The existing loader rejected them as `FEW_SHOT_JSON_INVALID`; both files were corrected, all eight examples were parsed independently, hashes were recomputed and the focused suite passed before the GREEN commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Reserved structural profiles are ready for the Beam operation registration in Plan 12-07 and Column operation registration in Plan 12-08.
- Plan 12-02 may proceed with structural occurrence/Type indexing; no executable structural operation has been enabled and no Phase 13 work has begun.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-04*

## Self-Check: PASSED

- All declared key created files exist.
- RED `70652c21` precedes GREEN `74c27935` in Git history.
- No goal-blocking stubs were found; `null placeholder` appears only in explicit fail-closed prompt guidance.
- Plan verification, prompt-registry regression, compile and diff checks are green.
