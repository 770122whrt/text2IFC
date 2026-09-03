---
phase: 08-l1-l2-evaluation-contract
plan: 04
subsystem: evaluation
tags: [benchmark, privacy, allowlist, canary, largebuilding, publication, tdd]

requires:
  - phase: 08-l1-l2-evaluation-contract
    plan: 01
    provides: immutable Evaluation 0.2 hierarchy and strict L1/L2 aggregation
  - phase: 08-l1-l2-evaluation-contract
    plan: 02
    provides: operation-owned L2 policies and typed semantic evidence
  - phase: 08-l1-l2-evaluation-contract
    plan: 03
    provides: independent reopened-IFC L1 authorization and preservation
provides:
  - Type-separated production and benchmark-private post-application evaluators
  - Positive allowlisted public projection with whole-bundle private-canary scanning
  - Diagnostic-only retention and strict non-publication for non-passing candidates
  - Frozen zero-Provider LargeBuilding L1-pass/L2-fail acceptance evidence
affects: [phase-09, phase-10, repair-publication, benchmark-evaluation]

tech-stack:
  added: []
  patterns:
    - Gold enters only through BenchmarkEvaluationInputs after application
    - Public reports are constructed from a positive field allowlist
    - Semantic roles permit recreated GUIDs while preserving private expected/actual evidence

key-files:
  created:
    - src/text2ifc_ifc_repair/benchmark_evaluation.py
    - src/text2ifc_ifc_repair/evaluation_projection.py
    - tests/ifc_repair/test_benchmark_evaluation.py
    - tests/ifc_repair/test_phase8_large_building.py
    - docs/validation/ifc2x3-changeset/phase8-validation-report.md
  modified:
    - src/text2ifc_ifc_repair/workflow.py
    - tests/ifc_repair/test_offline_e2e.py
    - docs/validation/ifc2x3-changeset/README.md

key-decisions:
  - "ProductionEvaluationInputs has no original IFC, Gold, or private mutation mapping field; benchmark-private data is composed only after application."
  - "Public evaluation copies stable statuses, categories, safe source kinds, and remediation flags only; dynamic fact-key suffixes and private values/IDs/paths are never projected."
  - "A non-passing repaired IFC is moved to diagnostic/repaired-candidate.ifc and has no successful output path."
  - "LargeBuilding acceptance bypasses the Provider stage entirely and preserves the source SHA-256."

patterns-established:
  - "Private detailed report plus independently built public allowlist projection, followed by raw-byte canary scanning of every public/runtime artifact."
  - "Authorized original Material/Pset/quantity/Classification facts activate L2 checks; genuinely absent conditional facts remain not_required."

requirements-completed:
  - VAL-01
  - VAL-02
  - VAL-03
  - VAL-04
  - VAL-05

duration: 37min
completed: 2026-07-19
---

# Phase 8 Plan 4: Private Benchmark Evaluation and LargeBuilding Acceptance Summary

**Evaluation 0.2 now isolates Gold behind a post-application benchmark boundary, emits a useful canary-scanned public projection, rejects publication of L2-incomplete candidates, and reproduces LargeBuilding with L1 pass and zero Provider calls.**

## Performance

- **Duration:** 37 min
- **Started:** 2026-07-19T03:56:13Z
- **Completed:** 2026-07-19T04:33:39Z
- **Tasks:** 5
- **Files modified:** 8 implementation/test/documentation files, plus this summary

## Accomplishments

- Added structurally separate `ProductionEvaluationInputs` and `BenchmarkEvaluationInputs`; original IFC and mutation role mapping are accepted only by the private evaluator after deterministic application.
- Compared recreated Window semantic roles without original GUID reuse, while retaining private expected/actual values, provenance, original IDs, and source path in private evidence.
- Added one positive public projection that retains status/check/category/remediation utility, removes dynamic Gold-bearing fact suffixes, and scans raw bytes across the complete Provider/public bundle.
- Derived terminal success and publication from strict Evaluation 0.2 aggregation; failed/partial/not-evaluable candidates exist only as immutable diagnostic evidence.
- Proved the frozen LargeBuilding case with source hash unchanged, Provider calls `0`, L1 `passed`, L2 `failed`, L3 `not_required`, and complete/publishable `false` without semantic authoring changes.

## TDD Evidence

- **RED 1:** Benchmark/privacy tests failed during collection because `benchmark_evaluation` did not exist; only tests were committed.
- **GREEN 1:** Private evaluator, allowlisted projection, workflow status, canary scan, and diagnostic retention made 9 focused tests pass.
- **RED 2:** LargeBuilding acceptance failed during collection because the zero-Provider benchmark entrypoint did not exist; no production file changed.
- **GREEN 2:** A frozen deterministic ChangeSet path bypassed Provider generation and made the LargeBuilding acceptance pass without authoring changes.
- **REFACTOR:** Centralized public metadata/check-ID allowlisting, changed bundle scanning to raw bytes, removed private paths from the public manifest, documented exact evidence, and kept the full repair suite green.

## Task Commits

1. **Task 1: RED - freeze Gold isolation and diagnostic publication** - `1cb0dd6d` (test)
2. **Task 2: GREEN - implement private/public Evaluation 0.2 workflow** - `e09f0b32` (feat)
3. **Task 3: RED - freeze LargeBuilding honest baseline** - `013ff433` (test)
4. **Task 4: GREEN - connect zero-Provider LargeBuilding evidence** - `611df39c` (feat)
5. **Task 5: REFACTOR - finalize privacy scanning and validation evidence** - `0be46648` (refactor)

## Files Created/Modified

- `src/text2ifc_ifc_repair/benchmark_evaluation.py` - Production/benchmark input contracts, role-bound semantic extraction, strict L1/L2/L3 aggregation, and private report construction.
- `src/text2ifc_ifc_repair/evaluation_projection.py` - Positive public allowlist, safe difference categories, dynamic ID normalization, and whole-bundle canary scanner.
- `src/text2ifc_ifc_repair/workflow.py` - Post-application private evaluation, public evidence writing, zero-Provider benchmark path, and diagnostic-only candidate retention.
- `tests/ifc_repair/test_benchmark_evaluation.py` - Gold type isolation, recreated-role equivalence, public usefulness/privacy, canary, and terminal-state tests.
- `tests/ifc_repair/test_phase8_large_building.py` - Frozen source immutability, zero Provider calls, conditional semantic activation, and honest L1/L2/L3 acceptance.
- `tests/ifc_repair/test_offline_e2e.py` - Evaluation 0.2 evidence-bundle and diagnostic publication regression.
- `docs/validation/ifc2x3-changeset/phase8-validation-report.md` - Exact versions, commands, results, observed categories, and Phase 10 gaps.
- `docs/validation/ifc2x3-changeset/README.md` - Phase 8 validation report index link.

## Decisions Made

- Kept Gold impossible to pass through the production dataclass rather than relying on runtime deletion/redaction.
- Used semantic role equality plus typed fact comparison; original and repaired GUID equality remains an L3 observation only.
- Preserved `private_original` only as a safe public provenance source-kind label; no private value, entity ID, source reference, path, mapping token, or dynamic fact-key suffix is public.
- Treated the deterministic offline ChangeSet as frozen evaluation evidence and counted no Provider invocation, rather than calling a fake Provider for LargeBuilding acceptance.
- Reported original Material values `Glass` and `Sash` as activated and passing under current inherited/type evidence; did not invent a material failure when the evaluator found equivalence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Existing integration bug] Normalized whitespace-bearing IFC Pset labels at the benchmark boundary**
- **Found during:** Task 2 GREEN real offline workflow
- **Issue:** LargeBuilding contains Pset/property labels such as `Analytical Properties`; the existing typed fact constructor rejects whitespace in stable fact keys before policy filtering.
- **Fix:** Added evaluator-local deterministic key tokenization while preserving the original typed value, Pset path, inheritance, source, and provenance. `semantic_facts.py` remained untouched because it was outside this executor's ownership.
- **Files modified:** `src/text2ifc_ifc_repair/benchmark_evaluation.py`
- **Verification:** Focused benchmark/offline suite passed 9/9 and LargeBuilding activated its original Pset/quantity evidence.
- **Committed in:** `e09f0b32`

**2. [Rule 1 - Test contract bug] Removed the RED expectation for a root-level repaired IFC**
- **Found during:** Task 2 GREEN diagnostic publication integration
- **Issue:** The initial RED file expected both `repaired.ifc` and `diagnostic/repaired-candidate.ifc`, contradicting D-21's diagnostic-only rule for non-passing candidates.
- **Fix:** Required the root-level candidate to be absent and retained only `diagnostic/repaired-candidate.ifc`.
- **Files modified:** `tests/ifc_repair/test_offline_e2e.py`
- **Verification:** Focused workflow test verifies no root/successful repaired path and a hashed diagnostic candidate.
- **Committed in:** `e09f0b32`

---

**Total deviations:** 2 auto-fixed (2 Rule 1 correctness issues).
**Impact on plan:** Both fixes were necessary to execute real IFC evidence and enforce the locked publication contract; no semantic authoring or future operation scope was added.

## Issues Encountered

- `workflow.py`, `test_offline_e2e.py`, and the validation README began as shared historical baselines in a heavily dirty main worktree. Their content was preserved and only the planned integration points were changed; unrelated files were never staged.
- A broad stub-scan command encountered an unrelated access-denied dataset directory. The owned-file marker scan was rerun directly and found no TODO/FIXME/placeholder stubs.

## Known Stubs

None. No TODO/FIXME/placeholder behavior or unwired empty public/private evaluation result remains in the created or modified files.

## Threat Mitigations

- **T-08-04A:** Gold is type-separated, enters only after application, public output is positive-allowlisted, private paths are omitted from the public manifest, and full public/runtime files are scanned for canaries.
- **T-08-04B:** Strict Evaluation 0.2 status determines both completion and publication; non-passing candidates are diagnostic-only.
- **T-08-04C:** Private mutation/application role mappings bind semantic roles across recreated GUIDs; identity equality remains non-gating L3 evidence.

No unplanned network endpoint, authentication path, schema trust boundary, or external file-write surface was introduced.

## User Setup Required

None - all acceptance is deterministic and offline; no Provider credentials or external services are required.

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_benchmark_evaluation.py tests\ifc_repair\test_phase8_large_building.py tests\ifc_repair\test_offline_e2e.py -q` - **10 passed in 64.74s**
- `.venv\Scripts\python -m pytest tests\ifc_repair -q` - **191 passed in 216.24s**
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\agent` - **passed**
- `git diff --check` - **passed**
- Owned-file stub marker scan - **0 findings**
- TDD commit order - **RED `1cb0dd6d` -> GREEN `e09f0b32` -> RED `013ff433` -> GREEN `611df39c` -> REFACTOR `0be46648`**

## Next Phase Readiness

- Phase 9 can consume `status`, `complete_repair_success`, and `successful_artifact_publishable` without receiving benchmark-private data.
- Phase 10 can use the observed Pset/quantity/`IsExternal`/Classification/label remediation categories to restore Window semantics.
- Door, Opening-only, Beam, Column, L3 exactness, vector matching, and 128k experiments remain explicitly deferred.

## Self-Check: PASSED

- All eight planned implementation/test/documentation artifacts and this summary exist on disk.
- All five TDD task commits exist in git history in the required order.
- Fresh final focused pytest, full repair pytest, compileall, diff check, privacy/static scans, and source SHA-256 checks passed.
- No STATE.md, ROADMAP.md, REQUIREMENTS.md, or PROJECT.md file was modified by this executor.

---
*Phase: 08-l1-l2-evaluation-contract*
*Completed: 2026-07-19*

