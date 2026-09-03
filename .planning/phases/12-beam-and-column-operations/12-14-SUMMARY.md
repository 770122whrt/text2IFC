---
phase: 12-beam-and-column-operations
plan: "14"
subsystem: structural-live-proof-curation
tags: [ifc2x3, beam, column, live-proof, transcript, provenance, rollback, tdd]

requires:
  - phase: 12-13
    provides: Preflight-gated live runner with redacted attempt lineage and no-fallback contract
  - phase: 12-12
    provides: Frozen offline structural damage authority and strict Proof validator
provides:
  - Strict live transcript audit independent of runner aggregate booleans
  - Hash-bound live runtime and underlying offline damage authority separation
  - Separate-process candidate validation before install and full-collection validation after install
  - Atomic rollback for rejected candidates and failed post-install validation
  - Frozen `--root` validator CLI and timestamped live-run discovery for Plan 12-15
affects: [12-15, 12-16, structural-live-proof, success-case-validator]

tech-stack:
  added: []
  patterns:
    - Candidate Proof staging outside the accepted collection before subprocess validation
    - Two-authority live transcript plus offline damage provenance validation
    - Provider draft binding followed by deterministic Bound ChangeSet authority validation

key-files:
  created:
    - scripts/ifc_repair/curate_phase12_live_proof.py
    - .planning/phases/12-beam-and-column-operations/12-14-SUMMARY.md
  modified:
    - scripts/ifc_repair/validate_success_cases.py
    - tests/ifc_repair/test_phase12_live_uat.py
    - tests/ifc_repair/test_phase12_success_cases.py

key-decisions:
  - "A live Proof keeps the live runner/source manifest as transcript authority and a separately hash-bound offline manifest as damage replay authority."
  - "The Stage 2 Provider response binds to provider-draft.json; deterministic binder additions are then checked through the runtime applied and Bound ChangeSet chain."
  - "Proof installation requires an exact two-case, zero-legacy candidate verdict and a second successful validation after collection installation."

patterns-established:
  - "Runner evidence remains pending and cannot self-claim Proof acceptance; only the independent curator/validator boundary installs accepted cases."
  - "Failed candidates and the program guard remain in the ignored run workspace and never enter accepted success Proof."

requirements-completed: [OPS-03, OPS-04]

duration: 53 min
completed: 2026-08-17
---

# Phase 12 Plan 14: Strict Live Structural Proof Curation Summary

**Genuine Beam/Column transcripts now enter accepted Proof only after redacted-payload hash recomputation, retained RepairAPI authority binding, offline damage replay, and two separate-process validation gates with rollback.**

## Performance

- **Duration:** 53 min
- **Started:** 2026-08-17T14:46:22Z
- **Completed:** 2026-08-17T15:39:16Z
- **TDD feature:** 1
- **Files created:** 2
- **Files modified:** 4

## Accomplishments

- Reconciled every attempt from raw retained evidence: exact case/Stage ordinals,
  parent lineage, corrections, HTTP success, token usage, Provider identity,
  redacted request/response hashes, prompt profiles, per-profile few-shots and
  no-fallback flags. The runner's aggregate counts and success booleans are
  cross-checks, never authority.
- Required top-level and per-case Proof state to remain
  `pending_plan_12_14`; a runner cannot self-promote its output to accepted
  Proof.
- Bound the final successful Stage 1 response to retained RepairIntent and the
  Stage 2 response to retained `provider-draft.json`. Separately required the
  runtime applied ChangeSet and `changeset/bound-changeset.json` to be
  canonically equal and to preserve the Provider draft's operation authority.
- Preserved the complete RepairAPI runtime tree, raw attempt files, state and
  transition chain, prompt-profile selection, publication bundle, terminal
  evidence/application, preflight evidence and clarification context.
- Kept live transcript/source authority distinct from the exact hash-bound
  Phase 12 offline damage manifest/private mutation evidence. Live case names
  never select or guess deleted target identities.
- Staged exactly complete and clarification/resume candidates outside accepted
  Proof, invoked the family-neutral validator through a separate Python
  process, required exact candidate IDs/counts with two independently
  recomputed and zero legacy cases, then installed and revalidated the full
  collection. Either validation failure rolls back all installed bytes.
- Left the deterministic program guard uncurated as failure evidence and added
  the frozen `--root` CLI spelling plus timestamped run-directory discovery
  required by Plans 12-15 and 12-16.

## TDD Gate Evidence

### RED

1. **Commit `2917660e`** — initial transcript and live/base damage contract.
   - Focused command: 21 expected failures in 44.38s.
   - CLI alias command: 1 expected failure in 2.07s because `main` accepted no
     argv and exposed no `--root` synonym.
2. **Commit `42a77e12`** — public curator subprocess/rollback plus routing and
   response-binding defects.
   - Focused command: 2 failed and 2 passed in 2.77s; the expected failures
     were missing exact profile routing and the missing public `curate` seam.
3. **Commit `72e5a212`** — strict install boundary, forged validator summaries,
   and Provider-draft binding.
   - Focused command: 7 expected failures in 4.93s.
4. **Commit `6ac82506`** — Provider identity, usage binding, per-profile
   few-shot coverage and proof self-attestation rejection.
   - Focused command: 4 expected failures in 2.41s.
5. **Commit `8193c53b`** — frozen Plan 12-15 timestamped run-root seam.
   - Focused command: 1 expected failure in 3.75s from looking for
     `live-uat-result.json` only at the parent root.

### GREEN

- **Commit `09be4156`** — strict transcript-aware live Proof curator and
  family-neutral validator integration.
- Transcript audit focused result: **28 passed in 2.95s**.
- Live/base/subprocess focused result: **11 passed in 67.27s**.
- Frozen plan automated command after the final change:
  **107 passed in 157.19s**.
- Existing accepted Proof validator regression: **passed**, 22 cases, 57
  operations, 361 checked files, 66 IFC reopens, 17 independently recomputed,
  5 documented legacy cases and zero errors.
- Related collection-validator regression: **5 passed in 140.89s**.
- Compile: both changed scripts passed repository `.venv` `compileall`.
- Diff: owned files passed `git diff --check`.
- Network: no live DeepSeek command, external Provider call, cached replay or
  other network transport was invoked.

The RED commits precede the GREEN commit. No REFACTOR commit was required.

## Acceptance Boundary

The candidate subprocess verdict must satisfy all of the following before any
accepted Proof path is created:

- process exit code zero, JSON `status=passed`, and `errors=[]`;
- exactly the two frozen live candidate IDs and exactly two case summaries;
- exactly two independently recomputed cases and zero legacy cases;
- each candidate reports live Provider evidence and a strictly recomputed live
  transcript.

After installation, a second subprocess validates the updated full collection.
Any exception removes only the two newly installed case directories and
restores the original collection manifest bytes.

## Task Commits

1. **RED live curation contract** — `2917660e` (`test`)
2. **RED subprocess and provenance gates** — `42a77e12` (`test`)
3. **RED strict installation boundary** — `72e5a212` (`test`)
4. **RED transcript self-attestation gaps** — `6ac82506` (`test`)
5. **RED timestamped run discovery** — `8193c53b` (`test`)
6. **GREEN strict live Proof curation** — `09be4156` (`feat`)

## Files Created/Modified

- `scripts/ifc_repair/curate_phase12_live_proof.py` — transcript/runtime audit,
  candidate staging, subprocess verdict parsing, Proof install and rollback.
- `scripts/ifc_repair/validate_success_cases.py` — live transcript authority,
  explicit base-damage authority, prompt registry binding and `--root` CLI.
- `tests/ifc_repair/test_phase12_live_uat.py` — one-defect transcript and
  Provider response/runtime authority tests.
- `tests/ifc_repair/test_phase12_success_cases.py` — live/base validator,
  public curator, subprocess, forged-verdict, rollback and timestamped-root
  tests.

## Decisions Made

- `raw_request_sha256` and `raw_response_sha256` remain non-recomputable
  records because unredacted payloads must not be persisted. The curator
  independently recomputes the retained redacted request/response hashes and
  rejects any mismatch.
- Clarification keeps the initial request and feedback as separate hash-bound
  inputs; the effective request after answer is bound through the retained API
  context, RepairIntent and Bound ChangeSet.
- Provider profile evidence is validated against the current registered
  profile selection and exact versions/hashes. No Door/Window profile or
  few-shot may leak into structural live evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Separated live and damage provenance authority**

- **Found during:** RED validator review.
- **Issue:** The existing validator treated every Phase 12 source manifest as
  an offline damage manifest and keyed frozen damage targets from the live case
  ID, allowing either false rejection or provenance relabeling.
- **Fix:** Added an exact hash-bound `base_damage_contract`; live transcript
  evidence remains the source authority while only original/damaged/private
  mutation evidence is reused for offline damage replay.
- **Files modified:** curator, validator and success-case tests.
- **Committed in:** `09be4156`.

**2. [Rule 2 - Missing Critical] Preserved Provider draft as a distinct runtime artifact**

- **Found during:** RED response-lineage review.
- **Issue:** A Stage 2 Provider draft is not the final Bound ChangeSet because
  deterministic binding adds registered authority.
- **Fix:** Bind the transcript response to retained `provider-draft.json`, then
  verify its immutable operation projection through the canonically equal
  runtime applied/Bound ChangeSet pair and semantic manifest chain.
- **Files modified:** curator, validator and both test files.
- **Committed in:** `09be4156`.

**3. [Rule 3 - Blocking] Aligned frozen later-plan CLI commands**

- **Found during:** Plan 12-15/12-16 command review.
- **Issue:** Later frozen commands use validator `--root` and pass the live-run
  parent directory, while the validator exposed only `--collection-root` and
  the runner writes a timestamped child directory.
- **Fix:** Added an argparse synonym to the same destination and deterministic
  latest timestamped-run discovery that audits the selected run rather than a
  stale parent-level result.
- **Files modified:** curator, validator and success-case tests.
- **Committed in:** `09be4156`.

---

**Total deviations:** 3 auto-fixed (2 missing correctness/security contracts,
1 blocking frozen-command alignment).
**Impact on plan:** All changes close required acceptance seams without
changing Provider schemas, compatibility aliases, Door/Window workflows,
geometry thresholds, private Ground Truth, Storey/RAG authority or Phase 13.

## Issues Encountered

- Git continued to report that the user-level global ignore file was
  unreadable. It did not affect exact-path staging, commits, status or tests.
- Ruff is not installed in the repository `.venv`; the required compile,
  focused tests, plan test gate, validator regression and diff checks all ran
  with the project `.venv` instead.

## Known Stubs

None. The curator uses the real subprocess validator path and real filesystem
transaction boundary; tests inject only the subprocess result seam and never
claim injected evidence as live Provider proof.

## Scope and Security

- Threat T12-11 is mitigated by raw-ledger reconciliation and rejecting runner
  self-acceptance claims.
- Threat T12-12 is mitigated by FILES/source-manifest hashes, independently
  recomputed redacted transcript hashes and runtime artifact lineage.
- Threat T12-14 is mitigated by exact Provider identity, HTTP/usage metadata
  and all false fallback flags.
- No secrets or unredacted Provider payloads are persisted, and no real
  Provider/network call occurred in Plan 12-14.

## User Setup Required

None for Plan 12-14. Real credentials and Provider execution remain exclusively
owned by Plan 12-15.

## Next Plan Readiness

Plan 12-15 can run the frozen live command, point the curator at the parent
`phase12-live` directory, and receive either two independently accepted live
cases or a fail-closed result with the source run and program guard preserved.

## Self-Check: PASSED

- All four owned implementation/test files and this Summary exist.
- All five RED commits and the later GREEN commit resolve in the repository in
  the required order.
- The final plan test gate, collection validator regression, compile and diff
  checks passed; the accepted Proof collection and unrelated dirty worktree
  files were not modified.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-17*
