---
phase: 09-general-ifc-text-repair-orchestrator
plan: 04
subsystem: ifc-repair-orchestration
tags: [production-authority, atomic-application, evaluation-0.2, immutable-artifacts, security]

requires:
  - phase: 08-l1-l2-evaluation-contract
    provides: ProductionEvaluationInputs, independent L1/L2 gates, public projection, and publishable authority
  - phase: 09-general-ifc-text-repair-orchestrator
    provides: RepairIntent, resolved operation contexts, user Prototype authorization, and unified bound ChangeSet from Plans 09-01 through 09-03
provides:
  - Operation-scoped production semantic expectations with closed authority precedence and applicability evidence
  - One complete Audit/apply transaction followed by source hash, candidate hash, and IFC2X3 reopen verification
  - Evaluation 0.2-authoritative canonical success promotion with diagnostic-only non-pass retention
  - Bounded relative-path manifest and whole-public-bundle private-canary enforcement
affects: [09-05-cli, phase-10-window-l2, phase-11-operations, phase-12-operations]

tech-stack:
  added: []
  patterns:
    - Production authority is explicit request, current target/Host/Type relationships, formal or user-approved Prototype, then registered deterministic policy
    - apply_changeset owns the single complete Audit plus staged transaction; orchestration never performs a duplicate Audit
    - Canonical IFC promotion is derived only from public Evaluation 0.2 successful_artifact_publishable

key-files:
  created:
    - src/text2ifc_ifc_repair/production_evidence.py
    - src/text2ifc_ifc_repair/run_artifacts.py
    - tests/ifc_repair/test_production_evidence.py
    - tests/ifc_repair/test_orchestrator_application.py
    - tests/ifc_repair/test_orchestrator_terminal_matrix.py
    - tests/ifc_repair/test_orchestrator_security.py
  modified:
    - src/text2ifc_ifc_repair/orchestrator.py

key-decisions:
  - "Production semantic construction has no Gold/original/mutation parameter and rejects private, similarity, vector, name/storey, and Provider-only authority kinds."
  - "Missing mandatory semantic authority terminates as not_evaluable; conditional absence is not_required only when its category absence was explicitly verified."
  - "The existing apply_changeset boundary remains the one Audit plus one atomic apply authority, preventing a second preflight call in the orchestrator."
  - "Evaluation 0.2 successful_artifact_publishable is the sole canonical success authority; terminal labels and candidate presence cannot promote an IFC."

patterns-established:
  - "Operation ownership: candidate facts, selected facts, conflicts, applicability, and public evidence pointers remain keyed by ChangeSet operation ID."
  - "Artifact promotion: candidate IFC stays inside the run directory, is hash/reopen verified, and moves atomically to exactly one successful or diagnostic path."

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

duration: 16 min
completed: 2026-07-20
---

# Phase 09 Plan 04: Production semantic authority, atomic application, and publication Summary

**Authorized operation-scoped L2 facts now feed one audited atomic IFC2X3 transaction whose candidate is published only when public Evaluation 0.2 explicitly permits it.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-07-19T23:21:16Z
- **Completed:** 2026-07-19T23:36:51Z
- **Tasks:** 4
- **Files modified:** 7

## Accomplishments

- Built a generic Registry/policy-driven production evidence constructor that preserves source references, operation IDs, public provenance, deterministic conflict rationale, and explicit applicability decisions without Window branches.
- Enforced the fixed authority order and rejected cross-operation facts, arbitrary similar/name/storey/vector candidates, unapproved Prototypes, LLM/common-knowledge claims, unsupported sources, and private original/mutation inputs.
- Connected the bound ChangeSet to the existing single Audit/apply transaction, verified source immutability plus candidate path/hash/IFC2X3 reopen, then invoked production Evaluation 0.2.
- Added immutable public terminal evidence, diagnostic candidate retention, canonical successful promotion, bounded content-hash manifests, path containment, non-overwrite behavior, and complete private-canary scans.

## Task Commits

1. **Task 1 RED: freeze production semantic authority and applicability** - `8321d194` (test)
2. **Task 2 GREEN/REFACTOR: implement the production fact builder** - `99c18732` (feat)
3. **Task 3 RED: freeze atomic application and complete terminal matrix** - `6e4960db` (test)
4. **Task 4 GREEN/REFACTOR: wire transaction, Evaluation, and immutable publication** - `69f89534` (feat)

## Files Created/Modified

- `src/text2ifc_ifc_repair/production_evidence.py` - Closed production authority builder, deterministic conflict resolution, operation scoping, and required/conditional applicability decisions.
- `src/text2ifc_ifc_repair/run_artifacts.py` - Atomic Evaluation/evidence writing, candidate containment/reopen/hash checks, canonical or diagnostic promotion, and bounded manifest generation.
- `src/text2ifc_ifc_repair/orchestrator.py` - Existing resolution/Stage 2 runner extended through one complete transaction, production evaluation, and terminal publication.
- `tests/ifc_repair/test_production_evidence.py` - Four-tier authority, provenance, applicability, cross-operation, unsupported-source, future-family seam, and private-boundary coverage.
- `tests/ifc_repair/test_orchestrator_application.py` - Multi-operation all-or-nothing transaction, source immutability, call-count, reopen, and publication coverage.
- `tests/ifc_repair/test_orchestrator_terminal_matrix.py` - Clarification through full-pass terminal table with failed/partial/not-evaluable anti-promotion cases.
- `tests/ifc_repair/test_orchestrator_security.py` - Constructor/signature, canary, path escape, symlink, candidate hash tamper, and manifest security coverage.

## Decisions Made

- Production precedence intentionally excludes Phase 8's benchmark-only `PRIVATE_ORIGINAL` tier even though that enum remains available to the separate benchmark adapter.
- Formal IFC Type binding and stored explicit user Prototype authorization remain different source kinds and retain different provenance strings.
- Unverified conditional absence is not silently downgraded to `not_required`; orchestration stops with a public `not_evaluable` terminal evaluation before canonical publication.
- Door, Opening, Beam, and Column remain future Registry consumers only; this plan added no operation implementation or family-specific orchestration branch.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The shared repository `.pytest-tmp` directory was locked by another Windows process during final verification. No shared directory was deleted or modified; all gates were rerun successfully with a unique system-temp `--basetemp`.

## Verification

- Plan 09-04 focused authority/application/terminal/security suite: **39 passed**.
- Phase 8 Evaluation 0.2 policy/contract and apply transaction regressions: **115 passed**.
- Phase 9 resolution and bound Stage 2 regressions: **33 passed**.
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair`: exit 0.
- `git diff --check`: exit 0; only pre-existing line-ending warnings were emitted.
- TDD history: RED `8321d194` -> GREEN `99c18732` -> RED `6e4960db` -> GREEN `69f89534`.

## Known Stubs

None. The owned production and test files contain no TODO/FIXME/placeholder or empty UI/data-source stubs.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 09-05 can expose this single Python authority through the interactive/non-interactive CLI and realistic offline/live acceptance evidence.
- Current Window L2 authoring gaps remain honestly non-publishable and stay assigned to Phase 10; this plan does not claim or manufacture Window L2 success.

## Self-Check: PASSED

- All seven owned implementation/test files and this Summary exist.
- All four TDD task commits resolve in Git in the required RED/GREEN/RED/GREEN order.
- Commit file inspection contains only the seven Plan 09-04-owned code/test paths; STATE.md, ROADMAP.md, and shared baseline files are absent.

---
*Phase: 09-general-ifc-text-repair-orchestrator*
*Completed: 2026-07-20*
