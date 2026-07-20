---
phase: 09-general-ifc-text-repair-orchestrator
plan: 05
subsystem: ifc-repair-api-cli-validation
tags: [repair-api, cli, offline-e2e, largebuilding, deepseek-uat, evaluation-0.2]

requires:
  - phase: 09-general-ifc-text-repair-orchestrator
    provides: RepairIntent, durable run state, resolved ChangeSet orchestration, production evidence, and Evaluation-authoritative publication from Plans 09-01 through 09-04
provides:
  - One RepairAPI facade from caller IFC plus natural text through persisted orchestration
  - Thin human, compact JSON, quiet, non-interactive, and resumable CLI modes
  - Deterministic general success/rollback and honest LargeBuilding L1/L2 evidence
  - Opt-in redacted DeepSeek UAT with fixed 65536 guards and structured failure evidence
affects: [phase-10-window-l2, phase-11-operations, phase-12-operations, phase-13-scale]

tech-stack:
  added: []
  patterns:
    - CLI renders one typed RunResult and delegates all behavior to RepairAPI
    - Live UAT evidence is additive and never overrides deterministic Evaluation 0.2 gates

key-files:
  created:
    - src/text2ifc_ifc_repair/api.py
    - src/text2ifc_ifc_repair/cli.py
    - scripts/ifc_repair/repair.py
    - scripts/ifc_repair/run_phase9_live_uat.py
    - tests/ifc_repair/test_repair_cli.py
    - tests/ifc_repair/test_phase9_offline_e2e.py
    - tests/ifc_repair/test_phase9_large_building.py
    - docs/validation/ifc2x3-changeset/phase9-validation-report.md
  modified:
    - docs/validation/ifc2x3-changeset/README.md

key-decisions:
  - "RepairAPI is the only IFC path plus text facade; CLI source contains no indexing, Provider-stage, Audit, apply, or evaluation implementation."
  - "LargeBuilding retains the observed L1 passed, L2 not_evaluable, L3 not_required result and exposes only a diagnostic candidate."
  - "The single live UAT is reported as Stage 1 structured failure with Stage 2 not reached, rather than being mislabeled a two-stage or L1/L2 success."

patterns-established:
  - "Terminal rendering: human output is concise, JSON is one bounded canonical object, quiet emits no normal output, and non-interactive never reads stdin."
  - "Acceptance evidence: fake Provider call counts and caller source hashes are asserted, while live Provider evidence remains separately labeled and redacted."

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

duration: 24 min
completed: 2026-07-20
---

# Phase 09 Plan 05: Interactive CLI, offline acceptance, and opt-in live UAT Summary

**One public IFC-plus-text API now powers a thin resumable CLI, deterministic success/rollback acceptance, honest LargeBuilding L1/L2 diagnostics, and separately labeled DeepSeek evidence.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-07-19T23:42:40Z
- **Completed:** 2026-07-20T00:06:54Z
- **Tasks:** 5
- **Files modified:** 9

## Accomplishments

- Added `RepairAPI` as the only public facade composing Stage 1, source validation, fingerprint-bound indexing, durable run state, deterministic resolution, Stage 2, `RepairOrchestrator`, and terminal publication.
- Added a CLI with stable exit classes, Chinese-first compact human rendering, one-object JSON, quiet mode, non-interactive safety, same-run clarification selection/detail/cancel, and EOF fail-safe behavior.
- Proved a fully publishable offline path (`1/1/1/1` calls), multi-operation rollback (`1/1/1/0`), source immutability, and zero network dependency.
- Ran LargeBuilding through the public API and observed L1 `passed`, L2 `not_evaluable`, L3 `not_required`, diagnostic-only retention, and unchanged source hashes.
- Ran the one authorized DeepSeek UAT and retained its honest Stage 1 structured failure: two Stage 1 attempts, zero Stage 2 attempts, no successful IFC, and no L1/L2 success claim.

## Task Commits

1. **Task 1 RED: freeze CLI behavior** - `169c5f9d` (test)
2. **Task 2 GREEN: implement RepairAPI-backed CLI** - `08fbb012` (feat)
3. **Task 3: deterministic general and LargeBuilding flows** - `bfe20e6b` (test), strengthened by `7708d810` (fix)
4. **Task 4: opt-in DeepSeek UAT route** - `561dc9c6` (feat)
5. **Task 5: validation report and index** - `9b800cf9` (docs)

## Files Created/Modified

- `src/text2ifc_ifc_repair/api.py` - Public start/continue/read facade and durable pipeline composition.
- `src/text2ifc_ifc_repair/cli.py` - Thin arguments, interactive answer parsing, typed rendering, redaction, and exit mapping.
- `scripts/ifc_repair/repair.py` - Public command entry point.
- `scripts/ifc_repair/run_phase9_live_uat.py` - Offline config check and explicitly opt-in live evidence route.
- `tests/ifc_repair/test_repair_cli.py` - 18 human/machine/quiet/interactive/error contract tests.
- `tests/ifc_repair/test_phase9_offline_e2e.py` - General publishable and atomic rollback fixtures with exact call counts.
- `tests/ifc_repair/test_phase9_large_building.py` - Actual damaged Window through public API with observed Evaluation 0.2 levels.
- `docs/validation/ifc2x3-changeset/phase9-validation-report.md` - Reproducible commands, versions, hashes, matrices, UAT evidence, and future boundaries.
- `docs/validation/ifc2x3-changeset/README.md` - Additive Phase 9 report index preserving all existing entries.

## Decisions Made

- Provider environment loading moved behind `RepairAPI.from_environment`, keeping CLI free of Provider construction and pipeline authority.
- No `orchestrator.py` modification was required; the public facade composes the existing state machine and injects only documented stage seams.
- A failed live Stage 1 cannot call Stage 2 safely. The actual `2/0` attempt count is evidence of fail-closed binding, not a successful two-stage UAT.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Validation fidelity] Replaced a status-only LargeBuilding fixture with the actual Window application/evaluation path**
- **Found during:** Task 5 final evidence review
- **Issue:** The first LargeBuilding test froze non-publication but did not prove actual L1/L2 level output.
- **Fix:** Prepared the damaged Window only in private test setup, passed only damaged IFC plus natural text to `RepairAPI`, used the real apply/evaluate path, and asserted L1/L2/L3 plus diagnostic retention.
- **Files modified:** `tests/ifc_repair/test_phase9_large_building.py`
- **Verification:** `1 passed in 16.50s`; final focused suite `21 passed in 17.82s`.
- **Committed in:** `7708d810`

**Total deviations:** 1 auto-fixed (1 Rule 1).
**Impact on plan:** The correction strengthened the required gate without changing Window authoring, Evaluation expectations, or public architecture.

## Issues Encountered

- The real DeepSeek UAT was configured and completed in about 60 seconds but failed closed in Stage 1. Attempt 1 omitted required opening parameters; attempt 2 failed model fingerprint binding. Stage 2/application/evaluation were correctly not reached. Evidence: `dataset/processed/ifc-repair/phase9-live-uat/uat-20260719T235252588248Z/`.
- Existing unrelated working-tree changes emit CRLF warnings during `git diff --check`; the command exits 0 and no unrelated file was staged.

## Verification

- CLI/offline/LargeBuilding focused: **21 passed in 17.82s**.
- Full IFC repair suite: **356 passed, 1 skipped in 128.58s**.
- Security/Prompt/canary focused: **45 passed in 3.36s**.
- Six Phase 9 JSON schemas: Draft 2020-12 self-check passed.
- Prompt hashes: Stage 1 `sha256:d8e48f...a4e1c`; Stage 2 `sha256:958f7f...3de44`.
- `compileall`: exit 0.
- Live config inspection: `ready`, both guards `65536`, no secret/base URL output.
- LargeBuilding original SHA-256: `102f8123...bb725`, unchanged; caller damaged SHA-256: `309a1657...225b3`, unchanged.
- `git diff --check`: exit 0.

## Known Stubs

None. Empty collections in tests and typed defaults are intentional data structures; no placeholder/TODO/FIXME path prevents the plan goal.

## Threat Flags

None. The new public file-input and Provider surfaces are explicitly covered by T-09-05A/B/C and their plan-required redaction, bounded-output, answer-validation, source-binding, and opt-in gates.

## User Setup Required

None for deterministic acceptance. Live DeepSeek configuration was present and inspected without exposing credentials.

## Next Phase Readiness

- Phase 9 is complete and provides the public API/CLI orchestration foundation for Phase 10.
- Phase 10 owns Window L2 authoring closure; Phases 11/12 own Opening/Door/Beam/Column; Phase 13 owns vector/128k; L3 and curved walls remain later work.

## Self-Check: PASSED

- All nine owned implementation/test/documentation files and this Summary exist.
- All six task/deviation commits resolve and contain only Plan 09-05-owned paths.
- STATE.md and ROADMAP.md are absent from every Plan 09-05 task commit.

---
*Phase: 09-general-ifc-text-repair-orchestrator*
*Completed: 2026-07-20*
