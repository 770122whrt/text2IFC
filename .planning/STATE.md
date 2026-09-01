---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Phase 12.1 Plan 07 live evidence partial; R1 genuine run stopped at H3 after 9/12
last_updated: "2026-09-01T00:00:00Z"
progress:
  total_phases: 13
  completed_phases: 11
  total_plans: 63
  completed_plans: 57
  percent: 90
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

## Phase 12 Real UAT and Phase 12.1 Planning Checkpoint — 2026-08-21

```text
Mode: EXECUTION IN PROGRESS
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
Trigger: Genuine Phase 12 DeepSeek UAT
Current authority: Phase 12 Plans 12-01 through 12-14 complete; Stage 1 scope,
                   Type-intent and transaction-clause correction baselines are
                   implemented and pushed.
Live evidence: dataset/processed/ifc-repair-runs/phase12-live/
               uat-20260820T135432218011Z
Observed result: The complete Beam+Column case produced valid Stage 1
                 natural_language_property claims for IfcBeam/IfcColumn and
                 phrase "load bearing", then failed before Stage 2 with
                 PROPERTY_NOT_RESOLVED. Clarification/resume and the repair-only
                 program guard passed. No live structural success was curated.
Root boundary: The default production resolver had vector_index=None and the
               remaining local path relied on historical reviewed-alias text.
               This is a property-resolution architecture gap, not an IFC
               property-name alias to add and not evidence that Stage 1 chose
               the wrong target/value.
Frozen correction: target-class applicability -> multilingual vector Top-K ->
                   separate bounded Stage 1.5 LLM reranker -> deterministic
                   admissibility -> program-constructed ExactPropertyIntent ->
                   existing Binder/Stage 2/atomic IFC authoring.
Requirements: RAG-05, RAG-06, RAG-07, OPS-03 and OPS-04 remain pending.
Plans: 12.1-01 through 12.1-05 complete; 12.1-06 through 12.1-07 pending in sequence.
Contract amendment: Phase 12.1 adds no hash/fingerprint authorization or
                    acceptance gate. Stable IDs, explicit versions and persisted
                    candidate membership connect the stages. Each new gate must
                    protect a named product failure; existing source/private-Gold
                    isolation and historical accepted-Proof mechanisms are unchanged.
Next: Execute 12.1-06 only. Do not start Phase 13. If a new deterministic live
      defect appears after the frozen offline admission gates, preserve it and
      stop for user discussion before any patch or retry.
```

## Phase 12.1 Plan 06 Re-admission Blocker — 2026-08-24

```text
Mode: EXECUTION BLOCKED — OFFLINE EVIDENCE CORRECTED
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
State: PLAN 12.1-06 INCOMPLETE; PLAN 12.1-07 BLOCKED
Implementation checkpoints: 2a87020b, 4d2cd7d3
Correction checkpoint: b8cf328e
Production boundary: BGE_M3_UNAVAILABLE remains fail closed; production live
                     runtime construction has no alias/fallback.
Stage boundary: Stage 1 / property_resolution / Stage 2 are independently
                recorded; Stage 1.5 uses immutable template identity and
                wrapped live transports delegate explicit provider evidence.
Proof boundary: validator-to-curator report 0.2 requires strict Stage 1.5
                recomputation for property-bearing live success cases;
                historical property artifacts remain current-ineligible.
Evaluation: Independent review proved the prior Candidate 60/60 was an
            answer-equivalent replay oracle. b8cf328e removes that replay from
            scoring. Real local BAAI/bge-m3 + Qdrant now reports supported
            Top-K recall = 1.0 but blocks semantic Candidate scoring with
            INDEPENDENT_STAGE15_CANDIDATE_OUTPUT_REQUIRED.
Preflight: 0.3 implementation/execution at 4d2cd7d3 is complete and recorded
           six zero-count checks with tests/knowledge + tests/ifc_repair =
           1100 pass. That artifact is rejected as Plan 06 admission because
           its 60-case Candidate evidence was later shown invalid.
Proof validation: existing accepted Proof report 0.2 passed read-only; no
                  current strict Stage 1.5 live success was curated.
Live status: NOT RUN. No genuine DeepSeek call and no new Proof curation.
Next: Resolve the frozen R12 evidence conflict: Plan 06 requires independent
      Stage 1.5 Candidate outputs, but this task forbids a genuine DeepSeek call
      and no pre-Gold frozen Candidate output exists. Do not start Plan 07 or
      Phase 13 and do not restore replay/alias authority.
```

## Phase 12.1 R12/R13 Evaluation Boundary Amendment — 2026-08-26

```text
Mode: CONTRACT AMENDED; ZERO-NETWORK RE-ADMISSION IN PROGRESS
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
Trigger: Independent review proved that a zero-network deterministic Stage 1.5
         semantic Candidate score is either unavailable or Gold-equivalent.
Resolution: Treat the prior state as an evaluation-contract conflict, not a
            production regression or a reason to restore aliases.
Plan 06 owns: unchanged 60-case real local BGE-M3/Qdrant retrieval metrics;
              Stage 1.5 Prompt/parser/orchestration constraints; deterministic
              admissibility; five-family/public full-chain regression; fresh
              zero-skip/zero-timeout/zero-substitution/zero-network preflight.
Plan 06 report: retrieval_capability=evaluated;
                stage_1_5_semantic_evaluation_status=not_evaluated_offline.
Plan 07 owns: the unchanged 60-case genuine Provider Stage 1.5 semantic
              evaluation, followed by the separate four-case DeepSeek E2E
              matrix, independent Proof, IFCCompare and Phase 12/12.1 closure.
Gold boundary: retrieval Top-K and, in Plan 07, Provider decisions must be
               durably persisted before evaluator-only Gold is opened. The
               Provider never receives Gold/expected/authorize/private truth.
Amendment-time state: Plan 06 remained incomplete pending contract review,
                      evaluator report 0.3 alignment and fresh necessary
                      zero-network checks.
Live status: NOT RUN. Plan 07 requires a separate Go/No-Go after Plan 06 closes.
```

## Phase 12.1 Plan 06 Offline Admission Complete — 2026-08-26

```text
Mode: CHECKPOINT; PLAN 06 COMPLETE; LIVE NOT RUN
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
State: PLAN 12.1-06 COMPLETE; PLAN 12.1-07 UNSTARTED
Summary: .planning/phases/12.1-property-resolution-rag-reranker/12.1-06-SUMMARY.md
Retrieval: report 0.3 passed on the unchanged 60-case corpus using the real
           local production BGE-M3/Qdrant runtime. Supported Top-K recall=1.0;
           empty Top-K=2; policy/ineligible/alias/private/network counts=0.
Semantic boundary: retrieval_capability=evaluated;
                   stage_1_5_semantic_evaluation_status=not_evaluated_offline;
                   semantic scored count=0 and no deterministic oracle/replay.
Preflight: 0.4 passed all seven gates; 89 focused and 1105 complete-suite tests
           passed with zero failure, skip, substitution, timeout or network.
Offline chain: six accepted structural/mixed cases and two expected atomic
               rollbacks; deterministic Provider/runtime fixtures remain
               plumbing evidence only.
Proof boundary: existing accepted Proof validator 0.2 passed read-only; no new
                Proof was curated and final IFCCompare remains Plan 07.
Live status: NOT RUN. DeepSeek transport calls=0; synthetic fallback=false.
Next: Stop at this checkpoint and await explicit Go/No-Go for 12.1-07. Plan 07
      must rerun fresh preflight, compare frozen fixtures to the Plan 06 Git
      checkpoint, then run genuine semantic evaluation before separate E2E.
      Do not start Phase 13.
```

## Phase 12.1 / Repair Milestone R1 Handoff Checkpoint — 2026-09-01

```text
Mode: CHECKPOINT / HANDOFF
Class: EXPERIMENTAL
State: PARTIAL; safe code and documentation checkpoint for a new conversation
Implementation checkpoint: 223e46e7
Plan 07 evidence: the frozen four genuine cases completed their case contracts
                  with 11 Provider calls (Stage 1=4, Stage 1.5=4, Stage 2=3).
                  Three repaired outputs reopened and passed recorded L0/L1/L2;
                  the unsupported-program guard stopped before mutation.
Plan 07 boundary: acceptance_eligible=false, proof_acceptance_eligible=false,
                  proof_validation_status=pending_plan_12_14. This is not final
                  Proof or Phase closure.
R1 evidence: fresh ordered genuine run r1-20260901T055419268779Z passed E1-E4,
             M1-M3, H1 and H2, then stopped fail-closed at H3 with
             LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED. H4 and A1 were not run.
             Calls before stop: Stage 1=12, Stage 1.5=11, Stage 2=10.
R1 boundary: nine successful cases retain repaired IFC and recorded L0/L1/L2;
             R1 Proof 0.3, final IFCCompare and Phase closure were not run.
Handoff: docs/handoffs/repair-milestone-r1-checkpoint-2026-09-01.md
Matrix: docs/validation/repair-milestone-r1/
        plan07-r1-genuine-execution-matrix-2026-09-01.md
Next: Start the next conversation from the handoff. Diagnose H3 target
      resolution before any further live call. Do not splice runs, claim 12/12,
      close Phase 12/12.1, or start Phase 13.
```

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 12.1 — Property Resolution RAG and Reranker Correction.
Phase 12 Beam/Column implementation and live/Proof infrastructure are present,
Plan 06 offline admission is complete, and the Plan 07 four-case genuine run
completed its case contracts. Final Proof/IFCCompare closure remains pending.
The separate R1 ordered run is partial at 9/12 and stopped at H3; H4 and A1 were
not executed. Phase 11 remains closed with real DeepSeek and independently
recomputed Proof evidence.

## Current Position

Phase: 12.1 (Property Resolution RAG and Reranker Correction) — IN PROGRESS
Plan: 6 of 7 complete; Plan 07 in progress with partial live evidence

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

- Progress: 11 / 13 major phases complete; 57 / 63 milestone plans complete.
- Requirements: RAG-01..04, WFID-01..06 and OPS-01..02 remain complete;
  RAG-05..07 and OPS-03..04 are pending.
- Last activity: 2026-09-01 - Plan 07 retained genuine Provider evidence and
  completed the frozen four case contracts, but its top-level Proof eligibility
  remains false/pending and final IFCCompare/Phase closure were not run. The
  separate fresh R1 ordered run passed nine cases with repaired IFC plus
  recorded L0/L1/L2, then stopped fail-closed at H3 because target resolution
  offered no candidate; H4 and A1 were not executed. See the checkpoint handoff
  and genuine execution matrix before resuming.

- Phase 11 closure evidence: accepted live run
  `uat-20260731T224900289758Z` passed all three contracts. Two live successes
  were curated into the Proof collection. The current report-0.2 verifier
  passes the expanded accepted collection with 22 cases, 57 operations, 361
  checked files and 66 IFC reopens; 17 cases are strictly recomputed and five
  retain explicit legacy limitations. The Phase 11 accepted artifacts remain
  unchanged. The rejected preflight 0.3 full-suite execution passed 1100 tests,
  but it is not Plan 06 admission because R12 Candidate evidence was invalid.

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

Begin the next conversation with
`docs/handoffs/repair-milestone-r1-checkpoint-2026-09-01.md` and its linked
execution matrix. Preserve the partial R1 run and diagnose H3 target resolution
before any further live call. Do not represent the current evidence as R1
12/12, final Proof, IFCCompare, Phase 12/12.1 closure or Phase 13 readiness.

---
*Last updated: 2026-09-01 at the partial Plan 07 / R1 handoff checkpoint*

## Accumulated Context

### Roadmap Evolution

- Phase 10.3 inserted after Phase 10: Batch Window Repair and Dataset Benchmark Hygiene (URGENT)
- Phase 10.4 inserted after Phase 10.3: Comparator 0.2 Scalable Preservation Gate
- Phase 10.5 inserted after Phase 10.4: Window Occurrence Fidelity and Validation Acceleration
