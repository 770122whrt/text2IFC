---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Phase 11 implementation and offline validation complete; live UAT externally blocked
last_updated: "2026-07-28T00:00:00+08:00"
progress:
  total_phases: 13
  completed_phases: 10
  total_plans: 32
  completed_plans: 31
  percent: 97
---

# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Finish Phase 11 real DeepSeek UAT and curate Door Proof after
the external Codex execution quota permits the already-authorized network run.

## Current Position

Phase: 10.5 (Window Occurrence Fidelity and Validation Acceleration) — COMPLETE
Plan: 3 of 3 complete

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 11 in progress
- Plan: 11-01 through 11-04 complete; 11-05 offline work complete, live UAT pending
- Status: Opening/Door contracts, indexing, deterministic resolution, IFC
  authoring, L1/L2 and occurrence fidelity are implemented. LargeBuilding and
  vvo source-bound offline runs pass. The live command was rejected before any
  Provider call because the Codex execution quota was exhausted.
- Progress: 10 / 13 phases complete
- Requirements: WFID-01..06 complete
- Last activity: 2026-07-26 - 583 IFC repair tests passed; AdvancedProject
  cold/warm full validation passed at 62.687/23.562 seconds and about
  2.24/2.25 GB peak RSS; real DeepSeek r21 passed RepairIntent 0.4,
  ChangeSet 0.3, Production/private L1/L2 and occurrence fidelity
- Phase 11 design decisions were confirmed on 2026-07-28 and are frozen in
  `11-CONTEXT.md` and `11-SPEC.md`. Five sequential implementation plans,
  research, pattern map and validation strategy are complete. Plans 11-01
  through 11-04 are implemented and committed; Plan 11-05 awaits only real
  DeepSeek evidence and final Proof/checkpoint closure.

- Phase 11 uses additive RepairIntent 0.5, Prompt Profile 0.1, IFC Index 0.4,
  Semantic Manifest 0.3 and Bound ChangeSet 0.4 contracts. Historical
  RepairIntent, Manifest and ChangeSet schema files remain immutable;
  Provider draft remains 0.2.

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

After the user confirms the Chinese execution summary and Goal authorization,
create one Phase 11 Goal and execute plans 11-01 through 11-05 sequentially.
Run the real DeepSeek UAT only after the complete offline matrix is green;
report any Provider or dataset blocker honestly without fallback.

---
*Last updated: 2026-07-28 after Phase 11 planning and historical-change checkpoint*

## Accumulated Context

### Roadmap Evolution

- Phase 10.3 inserted after Phase 10: Batch Window Repair and Dataset Benchmark Hygiene (URGENT)
- Phase 10.4 inserted after Phase 10.3: Comparator 0.2 Scalable Preservation Gate
- Phase 10.5 inserted after Phase 10.4: Window Occurrence Fidelity and Validation Acceleration
