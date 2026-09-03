---
phase: 12-beam-and-column-operations
plan: "11"
subsystem: structural-independent-proof-validation
tags: [ifc2x3, beam, column, proof, provenance, preservation, tdd]

requires:
  - phase: 12-10
    provides: Public-only structural repair boundary and deterministic mutation
provides:
  - Hash-bound family-neutral Beam/Column Proof validation
  - Independent reopened-IFC L1/L2 and authority replay
  - Exact structural preservation, isolation and no-fallback rejection
  - Historical Door/Window Proof compatibility
affects: [12-12, 12-13, 12-14, 12-15, 12-16]

tech-stack:
  added: []
  patterns:
    - Proof authority is recomputed from retained request, damaged IFC and canonical artifacts
    - Application and saved evaluation role maps are never preservation or occurrence authority
    - Structural live evidence fails closed until transcript-aware Plan 12-14 validation exists

key-files:
  modified:
    - scripts/ifc_repair/validate_success_cases.py
    - scripts/ifc_repair/run_phase12_public_structural_repair.py
    - tests/ifc_repair/test_phase12_success_cases.py
    - tests/ifc_repair/test_structural_evaluation.py

key-decisions:
  - "Structural occurrence identity is derived from the operation contract and reopened damaged/repaired graphs, never application-declared role IDs."
  - "Intent, resolution, semantic manifest and ChangeSet authority are independently replayed from the retained public request and damaged IFC."
  - "Only offline_bound_deterministic is accepted before live transcript validation; case and source-run evidence modes must match exactly."
  - "Existing structural set_occurrence_properties Proof is fail-closed as not curated; functional support remains covered by its earlier plan and is not silently promoted here."

requirements-completed: [OPS-03, OPS-04]

duration: multi-session
completed: 2026-08-11
---

# Phase 12 Plan 11: Family-neutral Strict Independent Proof Validator Summary

**Beam/Column success claims are now accepted only after source/hash checks, reopened IFC2X3 inspection and independent authority/L1/L2/preservation recomputation.**

## Performance

- **Started:** 2026-08-09T16:19:04+08:00
- **Completed:** 2026-08-11T21:41:09+08:00
- **Tasks:** one TDD feature plus adversarial hardening
- **RED checkpoint:** `91c8de22`
- **GREEN checkpoint:** `10d9bdf0`

## Accomplishments

- Reopens original, damaged and repaired IFC2X3 artifacts after complete FILES and source-manifest SHA-256 verification.
- Derives deterministic Beam/Column occurrence identities independently of application role claims and reruns every strict structural L1 check.
- Replays public request parsing, deterministic target resolution, production evidence and semantic manifest construction to bind RepairIntent -> Resolution -> Manifest -> ChangeSet.
- Recomputes exact Type assignment/reuse/generated authority, world axis/section geometry, direct Pset/quantity/material facts and relationship cardinality.
- Rejects duplicate or undeclared semantic relations, unexpected IfcRoot changes, OwnerHistory changes hidden beside relation extensions, partial atomic output and application-authorized preservation spoofing.
- Rejects private-Gold/camelCase leaks, missing/stale artifacts, synthetic fallback and evidence-mode relabeling.
- Keeps historical Door/Window Proof classification and validation behavior green.

## TDD Gate Evidence

### RED

`91c8de22` - `test(12-11): add failing structural proof validation`

- Added structural false-success, threshold, missing/stale artifact, isolation, preservation and independent role-binding fixtures before production implementation.
- The final evidence-mode regression also failed against the pre-fix validator: a source run relabeled as live while the collection claimed offline was incorrectly accepted.

### GREEN

`10d9bdf0` - `feat(12-11): independently validate structural proof`

- Frozen three-file Plan 12-11 gate: **36 passed in 312.55s**.
- Focused evidence-mode binding plus valid structural Proof: **2 passed in 23.48s**.
- Structural implementation regression run during hardening: **93 passed in 124.58s**.
- `compileall` for all modified Python files passed.
- `git diff --check` passed before commit.

## Independent Proof Contract

- Saved `success=true`, saved evaluation JSON and application role maps are evidence only, never acceptance authority.
- The validator hashes and reopens retained artifacts, derives the created product identity from the frozen operation contract and compares the repaired graph against the damaged graph.
- Generated and reused Types, Psets, quantities and materials must match independently replayed request/resolution authority exactly.
- Relationship changes are allowed only for the exact operation-owned endpoint and cardinality contract; unrelated additions, removals, modifications or OwnerHistory edits are blocking.
- Source-run `provider_evidence_mode` is hash-bound to the collection declaration. The sole current structural offline value is `offline_bound_deterministic`; `live` remains rejected with `live_transcript_audit_pending_plan_12_14`.

## Deviations from Plan

### Auto-fixed: source-run evidence-mode authority

- **Found during:** pre-commit adversarial specification review.
- **Issue:** collection metadata alone selected offline/live handling, so an edited collection could relabel a live source run and bypass future transcript checks.
- **Fix:** added the runner-owned evidence mode to its source manifest, required exact source/collection binding and removed acceptance of the weaker `offline_deterministic` spelling.
- **Why required:** this closes T12-12/T12-14 without accepting a malformed Provider output or implementing Plan 12-14 early.

### Hardened: exact graph preservation authority

- **Found during:** adversarial review of the first GREEN implementation.
- **Issue:** broad reachable-root and application-declared allowlists could authorize unrelated or duplicate relations.
- **Fix:** replaced them with per-operation relationship/cardinality contracts, full non-endpoint fingerprints and independent authority replay.

## Explicit Boundaries Carried Forward

- Final deterministic damage/source provenance and private mutation-manifest binding belong to accepted Plan 12-12 benchmark curation; the Plan 12-11 public-run fixture is not final benchmark Proof.
- Full real-provider raw request/response, attempt, selected-profile and no-cache/no-prerecord transcript checks remain fail-closed until Plan 12-14.
- Trailing-whitespace request canonicalization in the offline runner is a Plan 12-12 source-boundary correction; the validator does not add compatibility for a lossy artifact.
- Phase 13 has not started.

## Requirement Tracking Note

Plan 12-11 supplies the strict independent Proof implementation required by OPS-03/OPS-04, but both requirements remain **Pending** until real DeepSeek UAT and Plan 12-16 conditional closure.

## Next Phase Readiness

- Plan 12-12 may now build the fixed d7n/vvo offline matrix and curate only cases accepted by this validator.
- Failed, synthetic, cached or incompletely source-bound runs cannot enter accepted structural Proof.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- All one-defect artifacts are rejected independently of saved success.
- Strict geometry, Type, semantics, preservation and isolation are recomputed from reopened IFC.
- Historical Door/Window collection tests remain green.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-11*
