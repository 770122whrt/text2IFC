---
phase: 09-general-ifc-text-repair-orchestrator
plan: 03
subsystem: ifc-repair-orchestration
tags: [phase7-resolution, bounded-context, unified-changeset, provider-boundary, tdd]

requires:
  - phase: 07-ifc-retrieval-index-and-target-resolution
    provides: fingerprinted SQLite index, deterministic TargetResolution, and bounded public target context
  - phase: 09-general-ifc-text-repair-orchestrator
    provides: versioned RepairIntent and durable clarification/run contracts from Plans 09-01 and 09-02
provides:
  - Stable operation-by-operation deterministic resolution with exact source/index/model compatibility
  - Separate formal Type evidence and stored user-authorized Prototype evidence
  - Hash-pinned Stage 2 prompt over resolved bounded public authority only
  - Exact unified ChangeSet operation/cardinality/target/scope/evidence binding before Audit or apply
affects: [09-04-semantic-authority, 09-05-cli, phase-10-window-l2]

tech-stack:
  added: []
  patterns:
    - Resolve every operation deterministically before any Provider ChangeSet call
    - Validate exact operation ID/cardinality/set equality and operation-scoped authority
    - Preserve finite Provider correction attempts as immutable evidence

key-files:
  created:
    - prompts/agent/ifc-repair-changeset-v0.2.md
    - src/text2ifc_ifc_repair/resolution_flow.py
    - src/text2ifc_ifc_repair/orchestrator.py
    - tests/ifc_repair/test_resolution_flow.py
    - tests/ifc_repair/test_general_changeset_stage.py
    - tests/ifc_repair/test_orchestrator_resolution.py
  modified:
    - prompts/agent/registry.json
    - src/text2ifc_ifc_repair/provider_stage.py

key-decisions:
  - "Stage 2 receives only complete operation-scoped resolved contexts; exact operation ID, cardinality, target, scope, evidence, request, and model bindings are deterministic gates."
  - "Ifc formal Type binding and stored explicit user Prototype authorization are distinct evidence kinds; similarity and proximity never authorize semantics."
  - "Plan 09-03 persists the unified ChangeSet and intentionally stops before Audit/apply/evaluation, which remain injected seams for downstream plans."

patterns-established:
  - "All-or-nothing resolution: one non-exact operation prevents the entire unified Stage 2 call."
  - "Resolved authority union: envelope scope/evidence equals the exact union of per-operation authorized sets."

requirements-completed: [PIPE-01, PIPE-02, PIPE-03]

duration: 14 min
completed: 2026-07-20
---

# Phase 09 Plan 03: Deterministic resolution and bound unified ChangeSet orchestration Summary

**RepairIntent operations now cross into one unified ChangeSet only through fingerprint-bound Phase 7 contexts and exact per-operation authority checks.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-07-19T23:02:02Z
- **Completed:** 2026-07-19T23:15:53Z
- **Tasks:** 4
- **Files modified:** 8

## Accomplishments

- Resolved single and multiple RepairIntent operations in stable order against exact Phase 7 source/index compatibility, with bounded public contexts and resumable clarification evidence.
- Kept formal IFC Type authority separate from explicit stored user Prototype authorization; name/storey/nearby/similarity facts remain display-only.
- Added the hash-pinned `ifc-repair-changeset.v0.2` prompt and a bounded Stage 2 that rejects partial, duplicate, stale, cross-operation, private, Prototype-reselecting, and STEP-shaped output.
- Persisted resolution and one valid unified ChangeSet while leaving Audit, apply, and evaluation disconnected as required by the phase boundary.

## Task Commits

1. **Task 1 RED: freeze resolution gating and clarification routing** - `c93cb0c1` (test)
2. **Task 2 GREEN: implement reusable Phase 7 resolution orchestration** - `01a88931` (feat)
3. **Task 3 RED: freeze Stage 2 complete binding and adversarial rejection** - `a37cc2d9` (test)
4. **Task 4 GREEN/REFACTOR: register and bind resolved-context Stage 2** - `84dd8d5f` (feat)

## Files Created/Modified

- `src/text2ifc_ifc_repair/resolution_flow.py` - Pure Phase 7 resolution adapter, bounded context construction, clarification candidates, and semantic authorization evidence.
- `src/text2ifc_ifc_repair/orchestrator.py` - Initial start/continue stage runner through ChangeSet persistence only.
- `src/text2ifc_ifc_repair/provider_stage.py` - Existing v0.1 provider baseline plus resolved-context v0.2 generation, correction evidence, and exact binding validation.
- `prompts/agent/ifc-repair-changeset-v0.2.md` - Single/multiple operation prompt that forbids search, reselection, semantic guessing, private evidence, and STEP output.
- `prompts/agent/registry.json` - Precisely staged v0.2 registration and hash; the user's pre-existing unstaged v0.1 hunk was preserved and excluded.
- `tests/ifc_repair/test_resolution_flow.py` - Exact/non-exact, stale/budget/evidence, formal Type, and Prototype authorization coverage.
- `tests/ifc_repair/test_orchestrator_resolution.py` - Zero Stage2/Audit/apply assertions for every non-exact status and immutable resume coverage.
- `tests/ifc_repair/test_general_changeset_stage.py` - Multi-operation success and adversarial fail-closed Stage 2 coverage.

## Decisions Made

- Stage 2 is a formatter/proposer over deterministic authority, never a target resolver or Prototype selector.
- Operation IDs are preserved from RepairIntent through ChangeSet; exact set and cardinality equality prevent subset application and reordered substitution.
- Corrected Provider attempts are bounded to two total attempts and cannot bypass schema, private-canary, or binding validation.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The STEP-output adversarial fixture was rejected by the existing Provider structured-output guard before Stage 2 diagnostics were written. The Stage 2 boundary now converts that exception into a stable fail-closed diagnostic while preserving the finite-attempt rule.
- The shared working tree already contained the user's `ifc-repair-changeset.v0.1` registry hunk. Interactive hunk staging selected only v0.2; post-commit inspection confirmed v0.1 remains unstaged and unchanged.

## Known Stubs

- `src/text2ifc_ifc_repair/orchestrator.py:30` retains injected Audit/apply callables but deliberately does not invoke them. This is the explicit Plan 09-03 boundary; Plan 09-04 connects semantic authority, Audit, apply, and evaluation.

## Verification

- New Plan 09-03 focused suite: **33 passed**.
- Phase 7 target query/context and existing Provider regressions: **19 passed**.
- `python -m compileall -q src/text2ifc_ifc_repair`: exit 0.
- Prompt registry exact hash: `sha256:958f7f38be22d7c89a90112dcd811620c706a209ec4dc506b4980e395693de44`.
- `git diff --check`: exit 0.
- TDD history: RED `c93cb0c1` -> GREEN `01a88931` -> RED `a37cc2d9` -> GREEN `84dd8d5f`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 09-04 can consume the resolved operations and unified ChangeSet to construct production semantic facts and connect deterministic Audit/apply/evaluation.
- No blocker remains in the 09-03-owned boundary.

## Self-Check: PASSED

- All eight owned implementation/test files and this Summary exist.
- All four TDD task commits resolve in Git and occur in the required RED/GREEN order.
- The user's unstaged `ifc-repair-changeset.v0.1` registry hunk remains outside every 09-03 commit.

---
*Phase: 09-general-ifc-text-repair-orchestrator*
*Completed: 2026-07-20*
