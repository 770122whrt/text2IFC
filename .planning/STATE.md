---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Phase 12 specification and 16-plan execution contract frozen; ready to execute
last_updated: "2026-08-04T16:56:55.355Z"
progress:
  total_phases: 13
  completed_phases: 11
  total_plans: 53
  completed_plans: 38
  percent: 72
---

# Project State

## Codex Task Pilot Checkpoint — 2026-07-31

```text
Mode: CHECKPOINT
Class: EXPERIMENTAL
Goal: Close Phase 11 only after real DeepSeek output independently reopens and
      passes strict L0/L1/L2, with no synthetic fallback.
Phase: Phase 11 COMPLETE
Routing: direct Phase 11 live-UAT workflow; verification-before-completion
State channel: .planning/STATE.md
Context: COMPLETE - prompt/profile contract repair, live Provider acceptance,
         independent Proof recomputation and regression gates are complete.
Acceptance: Real DeepSeek PASS: complete Stage 1/2 = 1/1; clarified total
            Stage 1/2 = 2/1; unsupported Stage 1/2 = 1/0 with exact
            DOOR_OPERATION_TYPE_UNSUPPORTED. Both published IFC files reopen
            as IFC2X3 and pass strict L0/L1/L2. synthetic fallback = false.
            Proof PASS: 16 cases, 45 operations, 247 files, 48 IFC reopens;
            11 cases strictly recomputed and 5 historical Window cases
            explicitly retained as legacy artifact-only evidence.
Next: Preserve the Phase 11 checkpoint and await user direction. Do not begin
      Phase 12 from this checkpoint.
```

### Handoff boundary

- Branch: `codex/workflow-dataset-links`
- Baseline HEAD: `a20b3e6bf5b6d2d08ca1981583b4254c3efbcd46`
- The worktree is intentionally dirty with the completed Phase 11 Door audit,
  regenerated Proof artifacts, schemas, tests and documentation. Do not reset,
  clean or overwrite these changes.

- Canonical implementation/validation documents:
  - `.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md`
  - `.planning/phases/11-wall-opening-and-door-operations/11-VALIDATION.md`
  - `docs/validation/ifc2x3-changeset/phase11-door-validation-report.md`
- Canonical new authority Proofs:
  - `dataset/processed/proof/ifc-repair-success-cases/door/batch/vvo-five-door-authority-public-repair/`
  - `dataset/processed/proof/ifc-repair-success-cases/mixed/door-window/vvo-authority-triplet-public-repair/`
- The known false-positive candidate is frozen only under
  `tests/fixtures/ifc_repair/phase11-door-known-failure/`; it is not a success
  artifact and must never enter production target resolution.

- Do not revisit without new evidence:
  - the overall two-stage RepairIntent → Bound ChangeSet workflow;
  - retained-Opening geometry targeting without user-supplied GUID/Name;
  - Door L1 thresholds (0.95 overlap, 5 mm center, 0.1 degree axis,
    1 mm nominal dimension);

  - damaged-only production boundary and post-repair-only private comparator;
  - contextual Storey policy documented in the Phase 11 erratum.
- Non-goals for the next conversation:
  - Phase 12 Beam/Column implementation;
  - new Door feature expansion;
  - tolerance relaxation or reduced preservation scope;
  - repository-wide cleanup unrelated to the Phase 11 checkpoint.

## Phase 12 Context Checkpoint — 2026-08-03

```text
Mode: DISCUSSION COMPLETE
Phase: Phase 12 Beam and Column Operations
State: CONTEXT FROZEN; READY FOR RESEARCH AND PLANNING
Requirements: OPS-03 Beam and OPS-04 Column remain pending implementation
Canonical context:
  .planning/phases/12-beam-and-column-operations/12-CONTEXT.md
Scope: Straight horizontal rectangular Beam and straight vertical rectangular
       Column; center-axis placement; exact or deterministic Type; optional
       authorized material; Beam/Column completion of the existing IFC2X3 PSD
       retrieval/index/semantic-authoring path.
Acceptance: Real d7n/vvo IFC2X3 scenes, both structural families, mixed-family
            atomicity, Beam and Column RAG evidence, real DeepSeek complete and
            clarification paths, independent strict L0/L1/L2 Proof validation,
            and no synthetic fallback.
Next: Research and plan Phase 12 from the canonical context. Do not implement
      Phase 12 or begin Phase 13 from this discussion checkpoint.
```

## Phase 12 Planning Checkpoint - 2026-08-03

```text
Mode: PLAN COMPLETE
Phase: Phase 12 Beam and Column Operations
State: SPECIFICATION AND PLAN FROZEN; READY TO EXECUTE
Requirements: OPS-03 Beam and OPS-04 Column remain pending implementation
Canonical specification:
  .planning/phases/12-beam-and-column-operations/12-SPEC.md
Planning evidence:
  .planning/phases/12-beam-and-column-operations/12-RESEARCH.md
  .planning/phases/12-beam-and-column-operations/12-PATTERNS.md
  .planning/phases/12-beam-and-column-operations/12-VALIDATION.md
Plans: 12-01 through 12-16 in sixteen sequential waves
TDD: 12-01 through 12-14 are one-feature canonical TDD plans;
     12-15 performs real DeepSeek execution and independent curation;
     12-16 performs regression, reporting and conditional state closure.
Validation: Plan Checker PASS after two bounded revisions. All sixteen plans,
            OPS-03/OPS-04, SPEC requirements 1-16, frozen G/P/T/R/O/F/V
            decisions and threats T12-01..T12-14 are covered.
Next: Execute Phase 12 only from 12-01 and only when explicitly authorized.
      Do not start Phase 13 or reopen the frozen Door workflow, structural
      geometry thresholds, Ground Truth isolation, Storey policy or RAG
      authority model.
```

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 12 — Beam and Column Operations
execution contract are frozen and ready to execute. Phase 11 remains closed
with real DeepSeek and independently recomputed Proof evidence.

## Current Position

Phase: 12 (Beam and Column Operations) — EXECUTING
Plan: 2 of 16

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 11 complete
- Plan: 11-01 through 11-05 complete
- Status: Opening/Door contracts, indexing, deterministic resolution, IFC
  authoring, strict geometry/Storey L1, L2 and occurrence fidelity are
  implemented. Seven offline cases
  cover LargeBuilding, vvo, AdvancedProject, generated Type, five-Door atomic
  repair and two-Door/two-Window mixed repair. All are independently curated
  with three-way L0/L1/L2 release evidence. Real DeepSeek then passed the
  complete, clarification/resume and deterministic unsupported contracts with
  no fallback; both publishable cases independently reopen and pass L0/L1/L2.

- Progress: 11 / 13 phases complete
- Requirements: WFID-01..06 and OPS-01..02 complete; OPS-03..04 pending
- Last activity: 2026-08-03 - Phase 12 SPEC, research, pattern map, Nyquist
  validation contract and sixteen sequential plans were frozen. Fourteen
  one-feature TDD plans precede the standard real DeepSeek execution and
  evidence-gated closure plans. Material is optional unless explicitly
  requested or inherited through explicitly authorized exact Type reuse.

- Phase 11 closure evidence: accepted live run
  `uat-20260731T224900289758Z` passed all three contracts. Two live successes
  were curated into the Proof collection. The current independent verifier
  passes 16 cases, 45 operations, 247 hash-bound files and 48 IFC reopens.
  The complete `tests/ifc_repair` regression passes 688 tests with 1 expected
  skip in 1099.76 seconds. A broader repository-wide 1599-test attempt produced
  no failure before the 1204-second command limit, so that separate attempt is
  recorded as a timeout rather than reported as a repository-wide pass.

- Phase 11 design decisions were confirmed on 2026-07-28 and are frozen in
  `11-CONTEXT.md` and `11-SPEC.md`. Five sequential implementation plans,
  research, pattern map and validation strategy are complete. Plans 11-01
  through 11-05 are implemented and validated; the final scoped checkpoint is
  the only remaining repository bookkeeping step in this handoff record.

- The live failure analysis changed the input contract, not the frozen Door
  workflow. Stage 1 now receives exact intent schemas and is explicitly told
  to omit program-derived and unknown fields. Immutable Door profile v0.2
  few-shots demonstrate complete, clarification, Type reuse and unsupported
  paths. No alias such as `center_offset_from_wall_start_mm` and no relocated
  `door.threshold_height_mm` compatibility was added.

- Real live execution also exposed two deterministic evidence bugs unrelated
  to LLM wording: Door canonicalization metadata was incorrectly treated as
  independent semantic authority, and the host relationship recorded the GUID
  value type instead of `IfcWall`. Both boundaries were corrected and covered
  by regression tests before the accepted rerun.

- Phase 11 uses additive RepairIntent 0.5, Prompt Profile 0.1, IFC Index 0.4,
  Semantic Manifest 0.3 and Bound ChangeSet 0.4 contracts. Historical
  RepairIntent, Manifest and ChangeSet schema files remain immutable;
  Provider draft remains 0.2.

- The 2026-07-29 Door audit found that relation-only postconditions accepted a
  reused mapped Door displaced outside its retained Opening and assigned it to
  the host wall's base Storey. Production L1 now requires projected overlap
  >= 0.95, center deviation <= 5 mm, axis deviation <= 0.1 degrees, dimension
  deviation <= 1 mm, exact fill/void topology and the Storey resolved from the
  Opening's world elevation. All seven offline cases were regenerated.

- The first independent re-review rejected the initial helper-only Ground
  Truth boundary because its outer benchmark runner still constructed public
  inputs from original/deleted-object facts. The authoritative rerun now uses
  `run_phase11_public_triplet_repair.py`, whose only inputs are the damaged IFC,
  a frozen geometry-only public request bundle and an output directory.
  Original IFC and private mutation mapping are introduced only by the
  post-repair comparator. The same rerun also closed an undeclared generated
  Window Type-relation Root and made undeclared added Roots release-blocking.

- AdvancedProject retains full schema validation and full-model diff. A fresh
  cold run passed the unchanged 180-second request-to-publication gate at
  166.807 seconds (36.876 seconds application plus 129.931 seconds
  evaluation); warm evaluation was 43.516 seconds. Independently reopened
  models and an isolated validation worker remove duplicate parsing and avoid
  worker-pool failure; no evidence scope or tolerance was reduced.

## Carried Context

- v1.0 shipped and remains archived with 722-test verification.
- Phase 7 supplies the deterministic SQLite index and bounded target context
  for Wall, Door, Window and contextual Space records; vector retrieval remains
  disabled behind an extension seam.

- Phase 8 supplies Evaluation 0.2 with independent mandatory L1/L2 gates,
  evaluator-only benchmark Gold and privacy-safe public projection.

- Phase 9 supplies one public IFC-plus-text API/CLI, versioned RepairIntent,
  resumable clarification, deterministic target resolution, bound unified
  ChangeSet generation, production semantic authority, all-or-nothing apply,
  and crash-recoverable terminal publication.

- Phase 10 upgrades the LargeBuilding Window path to a bound ChangeSet 0.2,
  atomic semantic authoring, Production L1/L2 pass and successful publication.

- Phase 09.1 separates TypeRecord authority from occurrence-direct facts. The
  41-occurrence LargeBuilding Window Style no longer raises a false
  `PROTOTYPE_TYPE_FACT_CONFLICT`.

- Four real DeepSeek paths publish validated IFC results, including exact Type
  name without GUID and a one-candidate dimensions confirmation. All four pass
  Production and private benchmark L1/L2 with no synthetic fallback.

- Current DeepSeek input/output guards remain 65,536 tokens. The 128k
  experiment remains Phase 13.

- Phase 10.1 uses the existing checked-in IFC2X3 official property registry for
  case-sensitive exact lookup only. It does not implement aliases, embeddings,
  vector search or RAG.

- Exact property mutation is limited to the target occurrence. Existing
  authorized Type facts may be inherited, but existing Types are reused only
  after exact unique resolution or affirmative candidate confirmation. Missing
  Type intent creates a deterministic dedicated system-template Type; ambiguous
  Type intent asks the user; shared-Type mutation is deferred.

- Phase 10.1 real DeepSeek UAT passed both the exact standard property and
  confirmed custom property paths with no synthetic fallback. Production L1/L2
  passed for both.

- Phase 10.2 adds bounded IFC2X3 property knowledge retrieval. Qdrant/BGE-M3
  improve recall but do not authorize writes; Stage 2 receives only exact typed
  facts. The LargeBuilding natural-language `IsExternal` UAT passed real
  Stage 1/2, reopen, L1 and L2.

- Private Gold remains evaluator-only. It passes L2 for exact original Type
  reuse and intentionally reports an authoring difference for a no-Type
  system-template fallback; this does not override the Production publication
  contract.

- Phase 10.3 adds source-bound dataset/benchmark manifests and proves one
  five-Window request can become one unified, all-or-nothing ChangeSet. Both
  deterministic and real DeepSeek runs passed five independent L1/L2 gates.

- The same-wall two-Window case is supported through operation-specific
  overlap checks and aggregate host-wall volume evaluation. An injected
  overlap rejects the entire transaction.

- Phase 10.4 replaces repeated whole-model representation expansion with a
  fail-closed, memoized candidate-certificate plus semantic-fingerprint
  comparator. AdvancedProject now completes global preservation in a
  39.638-second median with 1.083-GB peak RSS.

- A minimal evaluator-alignment follow-up closed the AdvancedProject replay.
  Approved mapped Window frames may be centred and contained within the
  opening while retaining nominal dimensions; occurrence-direct material
  associations take precedence over Type materials. The unchanged saved
  DeepSeek ChangeSet now passes application, global preservation, five
  independent L1/L2 gates and publication.

- The Window success Proof collection now freezes three complementary accepted
  baselines: LargeBuilding single-Window effective semantic replication, vvo
  five-Window atomic repair, and AdvancedProject five-Window large-model
  preservation. Nine IFC copies reopen as IFC2X3, and every copied artifact is
  source- and SHA-256-bound.

- Phase 10.5 treats Window/Opening effective occurrence scalar properties and
  relevant quantities as blocking repair fidelity while keeping GUID, STEP,
  serialization, ownership-graph and geometry-node differences diagnostic.

- Missing occurrence values may be supplied directly, deterministically
  derived, copied from one explicitly authorized occurrence, or taken from an
  explicitly authorized unanimous same-Type cohort. An explicitly authorized
  reused Type may satisfy an effective inherited value; a difference from
  Ground Truth occurrence-direct ownership remains an L3 diagnostic.

- Phase 10.5 retains the complete Production evaluator and requires
  AdvancedProject request-to-publication time at or below 180 seconds and peak
  RSS at or below 4 GiB. Cache/parallel acceleration may not reduce evidence
  scope and fails closed.

- Phase 10.5 real DeepSeek r21 passed with one Stage 1 and one Stage 2 call,
  RepairIntent 0.4, Bound ChangeSet 0.3, Production/private L1/L2 and
  occurrence fidelity. The repaired IFC reopens as IFC2X3 and no synthetic
  fallback was used.

- AdvancedProject final cold/warm full evaluation completed in 62.687/23.562
  seconds with approximately 2.24/2.25 GB process-tree peak RSS. Cold cache
  was miss/miss; warm cache was hit/hit; both runs repeated the full diff.

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 authoring/identity exactness is deferred without a compatibility
  commitment.

- Automatic similarity/vector-based Prototype authorization is not enabled;
  Phase 9 permits only formal binding or explicit user authorization.

- IFC index/extractor v0.2 now stores referenced Types separately and treats
  duplicate or unreliable Type GlobalIds as diagnostic-only evidence.

## Next Action

Phase 11 is closed and Phase 12 is fully specified and planned. The next
authorized workflow is execution of
`.planning/phases/12-beam-and-column-operations/12-01-PLAN.md`, followed
strictly by 12-02 through 12-16. Do not start execution without user direction,
and do not start Phase 13.

---
*Last updated: 2026-08-03 at the Phase 12 specification-and-plan checkpoint*

## Accumulated Context

### Roadmap Evolution

- Phase 10.3 inserted after Phase 10: Batch Window Repair and Dataset Benchmark Hygiene (URGENT)
- Phase 10.4 inserted after Phase 10.3: Comparator 0.2 Scalable Preservation Gate
- Phase 10.5 inserted after Phase 10.4: Window Occurrence Fidelity and Validation Acceleration
