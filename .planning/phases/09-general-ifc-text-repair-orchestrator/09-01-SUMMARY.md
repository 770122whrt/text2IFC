---
phase: 09-general-ifc-text-repair-orchestrator
plan: 01
subsystem: ifc-repair-orchestration
tags: [repair-intent, json-schema, prompt-registry, provider-boundary, tdd]

requires:
  - phase: 07-ifc-retrieval-index-and-target-resolution
    provides: TargetQuery and Registry-backed deterministic target capabilities
  - phase: 08-l1-l2-evaluation-contract
    provides: public/private authority boundary and production evidence rules
provides:
  - Exact-versioned text2ifc/ifc-repair-intent/0.1 contract
  - Immutable ordered RepairIntent records with canonical hashes
  - Public-only Registry-driven request-understanding Provider stage
  - Bounded redacted correction attempts and stable typed failures
affects: [09-02-run-state, 09-03-resolution-binding, 09-04-semantic-authority]

tech-stack:
  added: []
  patterns:
    - Draft 2020-12 validation before domain model construction
    - Hash-pinned public prompt with Registry-derived operation capabilities
    - Finite deterministic Provider correction evidence

key-files:
  created:
    - schemas/agent/ifc-repair-intent-0.1.schema.json
    - prompts/agent/ifc-repair-intent-v0.1.md
    - src/text2ifc_ifc_repair/repair_intent.py
    - src/text2ifc_ifc_repair/request_stage.py
    - tests/ifc_repair/test_repair_intent.py
    - tests/ifc_repair/test_request_stage.py
  modified:
    - prompts/agent/registry.json

key-decisions:
  - "Stage 1 accepts only request text, request identity, schema, and Registry-derived public capabilities; it has no resolved IFC or benchmark authority input."
  - "RepairIntent preserves Provider order and explicit Type/Prototype evidence while forbidding resolved target claims and guessed project facts."
  - "All Stage 1 bounds, public source kinds, private canaries, and stable error codes share one immutable policy authority."

patterns-established:
  - "Public intent boundary: schema validate, Registry validate, binding validate, then construct immutable records."
  - "Provider correction: at most two byte-bounded attempts with canonical redacted attempt artifacts."

requirements-completed: [PIPE-01, PIPE-02]

duration: 15 min
completed: 2026-07-20
---

# Phase 9 Plan 1: Versioned RepairIntent and Public Request Understanding Summary

**Exact-versioned, Registry-bound RepairIntent records with a public-only, hash-pinned Provider stage and finite redacted correction evidence**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-19T22:20:43Z
- **Completed:** 2026-07-19T22:36:04Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added the strict `text2ifc/ifc-repair-intent/0.1` schema and deeply frozen domain records for ordered single- and multi-operation requests.
- Added a hash-pinned Stage 1 prompt and adapter whose signature and rendered Provider input expose no original IFC, Gold, mutation mapping, or resolved target context.
- Enforced Registry operation/parameter/class allowlists, canonical request/intent hashes, explicit attribute/Pset/Material and Prototype provenance, byte/count limits, two-attempt correction, and typed fail-closed results.
- Preserved the existing 65,536-token DeepSeek input/output guards unchanged.

## Task Commits

Each TDD gate was committed atomically:

1. **Task 1 RED: freeze the RepairIntent contract and trust boundary** - `dae81dde` (test)
2. **Task 2 GREEN: implement schema, immutable model, prompt, and Provider adapter** - `e5409fa0` (feat)
3. **Task 3 REFACTOR: centralize bounds, provenance, and prompt evidence** - `20ecef01` (refactor)

## Files Created/Modified

- `schemas/agent/ifc-repair-intent-0.1.schema.json` - Exact Draft 2020-12 public intent contract.
- `prompts/agent/ifc-repair-intent-v0.1.md` - Public-only Stage 1 request-understanding instructions.
- `prompts/agent/registry.json` - Hash-pinned RepairIntent template registration; the pre-existing user ChangeSet registration remained unstaged and uncommitted.
- `src/text2ifc_ifc_repair/repair_intent.py` - Frozen records, canonical serialization/hashing, Registry validation, central limits and error codes.
- `src/text2ifc_ifc_repair/request_stage.py` - Bounded Provider adapter, binding checks, redacted attempts, and typed terminal results.
- `tests/ifc_repair/test_repair_intent.py` - Contract, ordering, immutability, provenance, bounds, and rejection coverage.
- `tests/ifc_repair/test_request_stage.py` - Public signature/input, retry, redaction, oversize, multi-operation, and deterministic evidence coverage.

## Decisions Made

- Kept Stage 1 intentionally unaware of IFC candidate/context data; target identity remains a deterministic Phase 7 responsibility after RepairIntent creation.
- Represented user-named Type/Prototype references as provenance-bearing request evidence only, never as an automatically resolved or approved entity.
- Derived supported operation types, target classes, parameter schemas, and capability constraints from `OperationRegistry` instead of Window-specific branches.
- Used canonical JSON and SHA-256 identities for request, prompt, model, and complete intent binding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added the second operation to the RED multi-operation fixture**

- **Found during:** Task 2 GREEN focused test run
- **Issue:** The test constructed a second operation but did not append it to the fake Provider response, so it asserted two operations against a one-operation fixture.
- **Fix:** Appended the prepared operation before invoking Stage 1.
- **Files modified:** `tests/ifc_repair/test_request_stage.py`
- **Verification:** Focused suite passed 20/20 after GREEN and REFACTOR.
- **Committed in:** `e5409fa0`

---

**Total deviations:** 1 auto-fixed bug.
**Impact on plan:** The fix corrected test evidence only and did not expand production scope.

## Issues Encountered

- `prompts/agent/registry.json` already contained an uncommitted user-owned `ifc-repair-changeset.v0.1` entry. The RepairIntent entry was staged as an independently constructed Git index blob; post-commit diff confirms the user entry remains the sole unstaged registry change.

## User Setup Required

None - deterministic acceptance uses fake Providers and requires no external configuration.

## Known Stubs

None. Placeholder/TODO scans found no unresolved implementation stubs in plan-owned files.

## TDD Gate Compliance

- RED `dae81dde` precedes GREEN `e5409fa0`; 18 tests failed because the new production modules did not exist.
- GREEN passed all 18 focused tests.
- REFACTOR `20ecef01` passed 20 focused tests and compileall.

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_repair_intent.py tests\ifc_repair\test_request_stage.py -q` - **20 passed**
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair` - **passed**
- Draft 2020-12 schema self-check - **passed**
- Prompt registry exact hash check - **passed**
- DeepSeek guard check - **65,536 input / 65,536 output unchanged**
- `git diff --check` - **passed**

## Next Phase Readiness

- Plan 09-02 can persist RepairIntent and clarification state without reopening the Stage 1 public/private boundary.
- No blocker remains; target resolution, ChangeSet generation, mutation, application, and L1/L2 evaluation remain intentionally deferred to later Phase 9 plans.

## Self-Check: PASSED

- All seven plan-owned implementation/test artifacts exist.
- RED, GREEN, and REFACTOR commits exist in order.
- Focused tests, compileall, schema, prompt registry, DeepSeek guard, and diff checks pass.
- The user-owned ChangeSet registry hunk remains uncommitted.

---
*Phase: 09-general-ifc-text-repair-orchestrator*
*Completed: 2026-07-20*
