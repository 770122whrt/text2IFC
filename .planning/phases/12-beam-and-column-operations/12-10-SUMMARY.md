---
phase: 12-beam-and-column-operations
plan: "10"
subsystem: structural-mutation-ground-truth-isolation
tags: [ifc2x3, beam, column, mutation, ground-truth, benchmark, tdd]

requires:
  - phase: 12-09
    provides: Strict structural L1/L2 evaluation and atomic publication
provides:
  - Deterministic d7n/vvo Beam/Column mutation with evaluator-private snapshots
  - Damaged-IFC/public-request-only structural repair runner
  - Benchmark monotonicity guard that cannot promote failed production
  - Standard semantic-manifest 0.3 support for Beam/Column scopes
affects: [12-11, 12-12, 12-13, 12-14, 12-15, 12-16]

tech-stack:
  added: []
  patterns:
    - Structural mutation stages output atomically and keeps identities, STEP ids, geometry and semantics private
    - Handler-owned physical relationships remain evaluable manifest facts but are not rebound by generic semantic authoring

key-files:
  created:
    - scripts/ifc_repair/run_phase12_public_structural_repair.py
    - tests/ifc_repair/test_phase12_ground_truth_isolation.py
  modified:
    - src/text2ifc_ifc_repair/mutation.py
    - src/text2ifc_ifc_repair/benchmark_evaluation.py
    - src/text2ifc_ifc_repair/semantic_authoring.py
    - src/text2ifc_ifc_repair/apply.py
    - scripts/ifc_repair/mutate.py

key-decisions:
  - "The public runner accepts exactly damaged IFC, public request bundle and output root; private original/mutation mapping is not representable at that boundary."
  - "Generated structural Type assignments retain type_inherited ownership even when their canonical source is deterministic_derived."
  - "Beam/Column handlers own host/storey physical authoring; the full facts remain in the standard manifest and L2 expectations."
  - "Missing IfcOpenShell by_guid raises RuntimeError in 0.8.5; tests use a local safe lookup rather than monkeypatching dependency semantics."

requirements-completed: [OPS-03, OPS-04]

duration: 72min
completed: 2026-08-09
---

# Phase 12 Plan 10: Structural Mutation and Private-Gold Isolation Summary

**Beam/Column damage is deterministic and source-bound, while the real public repair process has no path to original IFC, removed identities, private geometry or Gold mappings.**

## Performance

- **Duration:** 72 min
- **Started:** 2026-08-09T14:32:17+08:00
- **Completed:** 2026-08-09T15:43:52+08:00
- **Tasks:** 1 TDD feature plus one runner-exposed contract correction
- **Implementation checkpoint:** `b5f27dea`

## Accomplishments

- Added exact deterministic removal of selected `IfcBeam`/`IfcColumn` occurrences while preserving IFC2X3 schema, source bytes, shared Types, Storeys and unrelated Roots.
- Split mutation evidence into a public count/hash report and an evaluator-private manifest containing target GUID/STEP identity, Type, Storey, axis, section and direct semantic snapshots.
- Added a public-only Beam/Column runner whose callable signature is exactly `damaged_ifc`, `public_request_bundle` and `output_root`.
- Added recursive public-bundle canary rejection for private/original/mutation/deleted/Gold fields without echoing their values.
- Made benchmark evaluation compute production first and reject any private-Gold result that could promote a failed production outcome.
- Corrected the shared semantic manifest builder to emit schema 0.3 for Beam/Column scopes and preserve deterministic generated Type ownership.
- Declared Beam/Column host/storey facts as handler-owned authoring effects. They stay in the standard manifest and L2 authority but are not applied twice after the structural handler creates containment.

## TDD Gate Evidence

### RED

`188be000` - `test(12-10): add failing structural isolation tests`

- Exact mutation, hash stability, shared-entity preservation, public-runner signature, canary isolation and benchmark non-promotion tests failed before implementation.

### GREEN

`b5f27dea` - `feat(12-10): isolate structural mutation and public repair`

- Plan verification: **12 passed in 23.08s**.
- Mutation/benchmark/semantic-authoring/Beam/Column/transaction regression: **100 passed in 106.07s**.
- Focused contract regressions for deterministic Type ownership and handler-owned containment: **2 passed in 6.20s**.
- `compileall -q src tests scripts` passed.
- `git diff --cached --check` passed before commit.

## Real Standard-Manifest Smoke

A fresh public-only d7n run used one Beam plus one Column in one bound ChangeSet and the standard semantic-manifest builder, not a runner-local manifest.

- Runner terminal status: `passed`; one atomic ChangeSet; `synthetic_fallback_used=false`.
- Both manifests: `text2ifc/ifc-repair-semantic-manifest/0.3`.
- Both Type assignments: `ownership=type_inherited`, `source_kind=deterministic_derived`.
- Reopened deltas: Beam +1, Column +1, BeamType +1, ColumnType +1.
- Beam: exact `(100000,100000,3000)` to `(103000,104000,3000)` axis and `300 x 500 mm` section.
- Column: exact `(110000,110000,0)` to `(110000,110000,6000)` axis, `(0,1)` orientation and `400 x 600 mm` section.
- Each occurrence has one Level 1 containment and one correct Type binding; direct material and Pset counts are zero because the request omitted them.
- Both operations: L1 `passed`, L2 `passed`, L3 `not_required`.
- IFC2X3 schema preserved; normalized comparison reports zero unexpected changed IDs.

The smoke directory was intentionally deleted after evidence review; accepted offline Proof is created only by Plans 12-11/12-12.

## Deviations from Plan

### Auto-fixed: standard structural semantic-manifest application

- **Found during:** real public runner smoke after the Plan 10 isolation implementation.
- **Issue:** the shared builder selected manifest 0.2 for Beam/Column scopes, then treated deterministic generated Types as occurrence-direct; after that correction, generic semantic authoring tried to bind handler-owned host/storey relationships a second time.
- **Fix:** extended the existing 0.3 scope selection, preserved `relationship:type` ownership, and introduced a registry-declared handler-owned fact filter in the common apply seam.
- **Why required:** the public runner could not pass using the repository's standard manifest contract otherwise. No LLM alias, fallback, tolerance change or family-specific branch was added to the common orchestrator.

### Corrected: IfcOpenShell absent-GUID assertion

- **Found during:** GREEN structural mutation test.
- **Issue:** IfcOpenShell 0.8.5 raises `RuntimeError` when `file.by_guid()` does not find an entity; the RED test incorrectly expected `None`.
- **Fix:** added a test-local optional lookup helper. The product code and dependency behavior were not monkeypatched.

## Ground Truth Boundary

- Production never receives the original IFC, mutation manifest, removed GUID/STEP ids, private geometry or private comparator.
- Public artifacts expose only authorized request, damaged-model resolution, generated authority, application and evaluation evidence.
- Private benchmark inputs are introduced only after production evaluation and cannot alter publication authority.

## Requirement Tracking Note

Plan 12-10 supplies the isolation implementation required by OPS-03/OPS-04, but both requirements remain **Pending** until real DeepSeek UAT, independent Proof recomputation and Plan 12-16 closure pass.

## Next Phase Readiness

- Plan 12-11 can implement the family-neutral independent Proof validator and must distrust runner summaries and application-declared changed IDs.
- Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- d7n/vvo mutation tests prove deterministic hashes and exact authorized deletion.
- Public runner signature and canaries exclude private Gold channels.
- A failed production result cannot be promoted by benchmark-only evidence.
- Standard manifest, reopened IFC, L1/L2 and preservation passed in a fresh real-scene smoke.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-09*
