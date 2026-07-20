# Roadmap: text2IFC

## Milestones

- [x] **v1.0 Supported Text2IFC Baseline** - Phases 1 through 6.7, shipped
  2026-07-16. See [archived roadmap](milestones/v1.0-ROADMAP.md),
  [requirements](milestones/v1.0-REQUIREMENTS.md), and
  [audit](milestones/v1.0-MILESTONE-AUDIT.md).
- [ ] **v1.1 IFC ChangeSet Repair Pipeline** - Phases 7 through 13, in progress
  (3 / 7 phases complete).

## Current Cycle: v1.1 IFC ChangeSet Repair Pipeline

**Goal:** Given an existing or damaged IFC2X3 file plus a natural-language
request, produce a bound semantic ChangeSet, deterministically apply it, and
publish an IFC result with mandatory L1 and L2 evidence.

### Phase 7: IFC Retrieval Index and Target Resolution

**Status:** Complete — 2026-07-19

**Goal:** Resolve human target descriptions to unique IFC entities using
deterministic, explainable evidence rather than relying on `Name` alone.

**Requirements:** TGT-01, TGT-02, TGT-03, TGT-04, TGT-05

**Depends on:** v1.0 baseline and the Window repair prototype

**Success criteria:**

1. One indexing command extracts stable identity, aliases, type, storey,
   spatial, relationship and geometry summaries from an IFC2X3 file.
2. Exact GUID, Name/Tag/type, grid/space, direction and geometry constraints can
   be combined in one versioned `TargetQuery`.
3. Candidate rankings include field-level evidence and never silently resolve
   zero-match, ambiguous or conflicting selectors.
4. Compact top-K context remains deterministic and token-budgeted.

**Evidence:** [Phase 7 validation report](../docs/validation/ifc2x3-changeset/phase7-validation-report.md)

### Phase 8: L1/L2 Evaluation Contract

**Status:** Complete — 2026-07-20

**Goal:** Make repair success mean both physical correctness and required BIM
semantic fidelity, while explicitly deferring L3 exactness.

**Requirements:** VAL-01, VAL-02, VAL-03, VAL-04, VAL-05

**Depends on:** Phase 7 target identity contract

**Success criteria:**

1. Versioned reports expose `passed`, `failed`, `partial`, `not_required` and
   `not_evaluable` for each level.
2. L1 validates geometry, host/topology, scope and preservation.
3. Operation-specific L2 allowlists validate type, storey, key Psets,
   quantities, material, classification and other required semantics.
4. Benchmark ground truth is private evaluator-only; production evaluation can
   use request, surviving model facts and prototypes without gold leakage.
5. L3 remains documented and `not_required` for v1.1.

**Evidence:** [Phase 8 validation report](../docs/validation/ifc2x3-changeset/phase8-validation-report.md), [goal verification](phases/08-l1-l2-evaluation-contract/08-VERIFICATION.md), and [security audit](phases/08-l1-l2-evaluation-contract/08-SECURITY.md)

### Phase 9: General IFC + Text Repair Orchestrator

**Status:** Complete — 2026-07-20

**Goal:** Provide one supported programmatic entry point from IFC + request to
ChangeSet + IFC + evidence.

**Requirements:** PIPE-01, PIPE-02, PIPE-03, PIPE-04

**Depends on:** Phases 7 and 8

**Plans:** 5 plans in 5 sequential waves

- [x] **Wave 1:** `09-01` - Versioned RepairIntent and public request-understanding stage.
- [x] **Wave 2** *(blocked on Wave 1)*: `09-02` - Durable run and clarification state machine.
- [x] **Wave 3** *(blocked on Waves 1-2)*: `09-03` - Deterministic resolution and bound unified ChangeSet orchestration.
- [x] **Wave 4** *(blocked on Waves 1-3)*: `09-04` - Production semantic authority, atomic application, and publication.
- [x] **Wave 5** *(blocked on Waves 1-4)*: `09-05` - Interactive CLI, offline acceptance, and opt-in live UAT.

**Cross-cutting constraints:**

- Both Agent stages and every public artifact are bounded and Gold-free.
- One run owns one unified, all-or-nothing ChangeSet transaction.
- Source IFC bytes remain unchanged; run transitions and detailed evidence are
  versioned, immutable, and resumable.
- Evaluation 0.2 is the only successful-artifact publication authority.
- Window L2 authoring remains Phase 10; later entity operations and vector/128k
  expansion remain outside Phase 9.

**Success criteria:**

1. CLI/API accepts an IFC path and natural-language request and returns a
   structured terminal status and immutable run directory.
2. Agent receives only bounded public request/spec/context/contracts.
3. Ambiguous, unsupported or failed validation paths publish no misleading IFC
   success artifact.
4. Successful runs publish ChangeSet, repaired/modified IFC, L1/L2 reports,
   provider trace and hash manifest.

**Evidence:** [Phase 9 validation report](../docs/validation/ifc2x3-changeset/phase9-validation-report.md), [goal verification](phases/09-general-ifc-text-repair-orchestrator/09-VERIFICATION.md), [security audit](phases/09-general-ifc-text-repair-orchestrator/09-SECURITY.md), and [clean code review](phases/09-general-ifc-text-repair-orchestrator/09-REVIEW.md)

### Phase 09.1: IFC Type Evidence and Prototype Resolution Correction (INSERTED)

**Goal:** Correct IFC Type/occurrence semantic authority and make Prototype
resolution human-readable before Window L2 authoring begins.

**Requirements:** TYPE-01, TYPE-02, TYPE-03

**Depends on:** Phases 7 and 9

**Plans:** 3/4 plans executed

Plans:

**Wave 1:**

- [x] **09.1-01** - Versioned TypeRecord index and inheritance-aware extraction.

**Wave 2** *(blocked on Wave 1 completion; plans may run in parallel)*:

- [x] **09.1-02** - Human-readable and deduplicated Prototype resolution.
- [x] **09.1-03** - TypeRecord-backed production semantic authority.

**Wave 3** *(blocked on both Wave 2 plans)*:

- [ ] **09.1-04** - LargeBuilding closure, no-GUID UAT and Phase 10 handoff.

**Cross-cutting constraints:**

- Type objects remain separate from editable occurrence targets and every fact
  retains explicit current-IFC provenance.
- Similarity may retrieve candidates but cannot authorize a Type without an
  explicit unique name or stored affirmative user answer.
- Historical run evidence stays immutable; v0.2 indexes rebuild rather than
  reinterpret v0.1 evidence.
- Phase 09.1 cannot author Phase 10 Window semantics or weaken Evaluation 0.2
  publication gates.

**Success criteria:**

1. Direct occurrence properties are never mislabeled as inherited Type facts,
   and IFC2X3 `IfcWindowStyle` facts have explicit provenance.
2. A user can authorize a unique Type by human-readable name or confirm a
   deduplicated Type candidate without supplying a GUID; similarity alone does
   not authorize selection.
3. The LargeBuilding 41-occurrence Window Style case builds production
   evidence without `PROTOTYPE_TYPE_FACT_CONFLICT`, reaches the real L2
   comparator, and preserves fail-closed publication behavior.

### Phase 10: Window L2 Semantic Fidelity Closure

**Goal:** Upgrade the proven Window repair from L1-only to required L1+L2.

**Requirements:** WIN-01, WIN-02

**Depends on:** Phases 8, 9 and 09.1

**Success criteria:**

1. Window repair restores required `IsExternal`, selected instance Psets,
   quantities, material and classification using non-gold model evidence.
2. The LargeBuilding benchmark passes both L1 and the frozen Window L2
   allowlist in offline and real-Provider UAT.
3. Historical v0.1 L1 evidence remains versioned rather than relabelled.

### Phase 11: Wall Opening and Door Operations

**Goal:** Extend the Registry with opening-only and Door+Opening operations
without copying the Window pipeline.

**Requirements:** OPS-01, OPS-02

**Depends on:** Phase 10

**Success criteria:**

1. `add_opening_to_wall` has its own target/parameter/L1/L2 contracts.
2. `add_door_with_opening_to_wall` restores host, opening, door type, swing/
   operation semantics and required L2 facts.
3. Mixed Window/Door cases remain transactionally scoped and independently
   evaluated.

### Phase 12: Beam and Column Operations

**Goal:** Prove the common ChangeSet architecture across non-opening structural
elements.

**Requirements:** OPS-03, OPS-04

**Depends on:** Phases 8 and 9; uses Registry patterns validated in Phase 11

**Success criteria:**

1. Beam and Column operations use operation-specific target, placement,
   containment, type/material and L2 contracts.
2. Structural additions pass IFC2X3 reopen, L1 geometry/relationship and L2
   semantic checks.
3. Common orchestration remains free of Window/Door-specific fields.

### Phase 13: Large IFC Context and 128k Experiment

**Goal:** Validate retrieval and Provider behavior on BIMNet-scale files before
changing the default input budget.

**Requirements:** SCALE-01, SCALE-02

**Depends on:** Phases 7 through 12

**Success criteria:**

1. Large-IFC indexing and retrieval have measured latency, memory, candidate
   recall and context-size evidence.
2. A dedicated near-limit experiment distinguishes Provider context window,
   client input guard and reserved output budget.
3. The 64k default changes to 128k only if tokenizer, API and end-to-end
   evidence pass; otherwise the bounded retrieval path remains authoritative.

## Requirement Coverage

| Phase | Requirements |
|---|---|
| 7 | TGT-01..05 |
| 8 | VAL-01..05 |
| 9 | PIPE-01..04 |
| 10 | WIN-01..02 |
| 11 | OPS-01..02 |
| 12 | OPS-03..04 |
| 13 | SCALE-01..02 |

**Coverage:** 22 committed requirements, 22 mapped, 0 unmapped.
