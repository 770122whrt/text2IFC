---
phase: 12-beam-and-column-operations
plan: "12"
subsystem: structural-offline-proof-curation
tags: [ifc2x3, beam, column, dataset, proof, atomicity, tdd]

requires:
  - phase: 12-11
    provides: Family-neutral independent structural Proof validator
provides:
  - Fixed d7n/vvo Beam/Column and four-family offline matrix
  - Source/hash-bound curated structural Proof
  - Independently verified rollback and final publication contracts
  - Cross-scene same-family BIMNet evidence scope
affects: [12-13, 12-14, 12-15, 12-16]

key-files:
  added:
    - scripts/ifc_repair/run_phase12_offline.py
    - scripts/ifc_repair/curate_phase12_structural_proof.py
    - dataset/processed/proof/ifc-repair-success-cases/structural
    - dataset/processed/proof/ifc-repair-success-cases/mixed/door-window-beam-column
  modified:
    - scripts/ifc_repair/run_phase12_public_structural_repair.py
    - scripts/ifc_repair/validate_success_cases.py
    - schemas/ifc/knowledge/property_aliases.json
    - tests/ifc_repair/test_phase12_dataset_e2e.py

key-decisions:
  - "Only the exact six-success/two-rollback matrix is eligible for curation; subset runs are partial."
  - "Reviewed exact LoadBearing phrases resolve through canonical property authority; arbitrary LLM synonyms remain unsupported."
  - "A repaired IFC is published only after application, L1/L2 and preservation gates all pass."
  - "Rollback inputs and stable first causes are independently bound to frozen hashes, sizes and ChangeSet fingerprints."

requirements-completed: [OPS-03, OPS-04]

duration: multi-session
completed: 2026-08-12
---

# Phase 12 Plan 12: Offline Structural Matrix and Curated Proof Summary

**The fixed d7n/vvo structural matrix now produces six strictly accepted cases, two independently verified rollbacks and no partial or synthetic success.**

## Checkpoints

- **RED:** `9082a4d6` - `test(12-12): add failing structural dataset proof matrix`
- **GREEN:** `202fee4f` - `feat(12-12): curate strict structural proof matrix`

## Fixed Matrix

Accepted cases:

1. d7n Beam with reviewed natural-language `LoadBearing` authority;
2. d7n Column with reviewed natural-language `LoadBearing` authority;
3. d7n atomic Beam plus Column;
4. vvo Beam with explicitly requested material;
5. vvo Column with material intentionally absent;
6. vvo atomic Door, Window, Beam and Column ChangeSet.

Expected rollback cases:

1. d7n duplicate same-axis structural addition;
2. vvo four-family batch with a duplicate same-axis Beam.

Both rollbacks reopen the actual damaged IFC2X3 input, bind its frozen SHA-256
and byte size to the ChangeSet base fingerprint, require
`STRUCTURAL_SAME_AXIS_OVERLAP`, record `published=false`, and contain no
`repaired.ifc`.

## Strict Proof Evidence

- Phase 12 curated cases: **6 cases / 12 accepted operations**.
- Full installed collection: **22 cases / 57 operations / 361 hash-bound files / 66 IFC reopens**.
- Every Phase 12 accepted case uses `offline_bound_deterministic` and
  `synthetic_fallback_used: false`.
- Evidence scope is exactly `cross_scene_same_family_bimnet`; it is not
  cross-dataset generalization and is not live Provider evidence.
- Source/damage provenance is bound to frozen d7n/vvo files and deterministic
  mutation replay; private mutation evidence remains evaluator-only.
- Curator acceptance is transactional: exact matrix validation precedes copy,
  the candidate collection is independently validated, and the installed full
  collection is validated again.

## TDD and Verification

- Frozen three-file Plan 12-12 gate: **38 passed in 506.63s**.
- Focused final-gate failure tests: **3 passed in 39.66s**.
- Separate-process full collection validation: **passed; 22 cases, 57
  operations, 361 files, 66 IFC reopens**.
- Modified Python files passed `compileall`.
- `git diff --check` passed before the GREEN checkpoint.
- Independent standards and frozen-spec reviews finished GREEN with no
  remaining HIGH or MEDIUM findings.

## Adversarial Hardening Closed

- A subset matrix can no longer report complete coverage or enter curation.
- Rollback summaries cannot self-authorize input integrity or failure cause.
- Phase 12 damage validation cannot be disabled by editing a manifest schema.
- Frozen d7n/vvo identity and deterministic mutation output are independently
  replayed and compared.
- Candidate IFC files are deleted on application, evaluation, preservation or
  finalization failure; final failure records converge to `published=false`
  and `output=null`.
- `os.replace(candidate, repaired)` is the final success-path publication
  action, preventing an orphan final IFC after metadata-finalization failure.

## Scope and Compatibility

- The two natural-language aliases are exact, human-reviewed inputs for
  Beam/Column `LoadBearing`; they do not accept unknown synonyms or repair
  malformed LLM output.
- No Door/Window workflow, geometry threshold, Ground Truth boundary or
  Storey policy was redesigned.
- No material is authored when the user did not request one and no authorized
  inherited material exists.
- Phase 13 has not started.

## Requirement Tracking Note

Plan 12-12 supplies the offline Proof required by OPS-03 and OPS-04, but both
requirements remain pending final closure until real DeepSeek UAT and Plan
12-16 complete.

## Next Plan

Execute Plan 12-13 only: freeze and test the live transcript, preflight and
no-fallback evidence contract before any real Provider call.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-12*
