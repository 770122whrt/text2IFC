# Roadmap: text2IFC

## Milestones

- [x] **v1.0 Supported Text2IFC Baseline** - Phases 1 through 6.7, shipped
  2026-07-16. See [archived roadmap](milestones/v1.0-ROADMAP.md),
  [requirements](milestones/v1.0-REQUIREMENTS.md), and
  [audit](milestones/v1.0-MILESTONE-AUDIT.md).
- [ ] **v1.1 IFC ChangeSet Repair Pipeline** - Phases 7 through 13, including
  inserted Phases 09.1 and 10.1 through 10.5, in progress
  (11 / 13 phases complete).

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

**Plans:** 4/4 plans executed

Plans:

**Wave 1:**

- [x] **09.1-01** - Versioned TypeRecord index and inheritance-aware extraction.

**Wave 2** *(blocked on Wave 1 completion; plans may run in parallel)*:

- [x] **09.1-02** - Human-readable and deduplicated Prototype resolution.
- [x] **09.1-03** - TypeRecord-backed production semantic authority.

**Wave 3** *(blocked on both Wave 2 plans)*:

- [x] **09.1-04** - LargeBuilding closure, no-GUID UAT and Phase 10 handoff.

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

**Plans:** 5/5 plans executed

- [x] **10-01** - Frozen Window semantic manifest and L2 policy contract.
- [x] **10-02** - Production semantic authority from surviving IFC evidence.
- [x] **10-03** - Compact Provider draft and deterministic Bound ChangeSet 0.2.
- [x] **10-04** - Atomic IFC2X3 semantic authoring and independent reopen/L1/L2.
- [x] **10-05** - LargeBuilding offline and four-path real DeepSeek acceptance.

**Success criteria:**

1. Window repair restores required `IsExternal`, selected instance Psets,
   quantities, material and classification using non-gold model evidence.
2. The LargeBuilding benchmark passes both L1 and the frozen Window L2
   allowlist in offline and real-Provider UAT.
3. Historical v0.1 L1 evidence remains versioned rather than relabelled.

**Evidence:** [Phase 10 validation report](../docs/validation/ifc2x3-changeset/phase10-validation-report.md) and [goal verification](phases/10-window-l2-semantic-fidelity-closure/10-VERIFICATION.md)

### Phase 10.1: Explicit IFC Property Authoring and Validation (INSERTED)

**Status:** Complete — 2026-07-23

**Goal:** When a user explicitly supplies an exact Pset name, property name and
value, deterministically ensure that typed effective property on the intended
Window occurrence, reuse only an explicitly resolved/confirmed existing Type
or create a deterministic system-template Type when none was requested, and
publish only after independent reopened-IFC L2 validation.

**Requirements:** PROP-01, PROP-02, PROP-03, PROP-04, PROP-05

**Depends on:** Phase 10

**Plans:** 4/4 plans complete

- [x] **Wave 1:** `10.1-01` - Versioned exact-property intent and deterministic resolution contract.
- [x] **Wave 2** *(blocked on Wave 1)*: `10.1-02` - Clarification, custom-property confirmation and scope safety.
- [x] **Wave 3** *(blocked on Waves 1-2)*: `10.1-03` - Atomic Pset authoring, manifest binding and dynamic L2 enforcement.
- [x] **Wave 4** *(blocked on Waves 1-3)*: `10.1-04` - LargeBuilding offline/live acceptance, regression and handoff evidence.

**Cross-cutting constraints:**

- Phase 10.1 performs exact lookup only; it does not search aliases, embeddings
  or semantically similar properties.
- Property mutation is occurrence-only. Binding an already authorized existing
  Type and reading its inherited facts remain allowed; modifying a shared Type
  is explicitly deferred and fails closed in this phase.
- Existing Types are never selected by a hard-coded GUID or silent same-size/
  similarity fallback. Exact unique references resolve directly, uncertainty
  asks the user, and absence of Type intent creates a dedicated versioned
  system-template Type.
- Every custom property requires confirmation of exact Pset/property, value,
  IFC value type, unit and scope before it becomes authorized.
- Provider output remains a draft. Only deterministic resolution, Binder,
  atomic application, reopen and L1/L2 gates can publish an IFC.
- Initial acceptance covers scalar `IfcPropertySingleValue` properties on the
  Window pipeline while keeping operation-neutral interfaces for later entity
  families.

**Success criteria:**

1. Exact standard `Pset.Property` requests resolve offline against the checked-
   in IFC2X3 property registry and enforce applicable class, template type,
   IFC value type and unit requirements.
2. Unknown/custom properties never crash or silently pass: they require a
   durable confirmation and then enter the same typed manifest and L2 path.
3. Existing Type reuse is explicit or user-confirmed; a request with no Type
   creates and binds a deterministic dedicated Window Type, while an ambiguous
   Type pauses instead of silently selecting a neighbor Type.
4. Occurrence edits cannot mutate other occurrences sharing a Type; an explicit
   shared-Type mutation request is reported as deferred and writes nothing.
5. The applicator creates or updates one direct Pset/property without duplicate
   relationships, rolls back atomically on failure, and independently reopens
   the IFC before requested-property L2.
6. LargeBuilding passes deterministic acceptance and an opt-in real DeepSeek
   exact-property UAT without RAG, Gold leakage or synthetic fallback.

### Phase 10.2: IFC2X3 Property Knowledge Retrieval and Resolution (INSERTED)

**Status:** Complete — 2026-07-24

**Goal:** Resolve non-exact multilingual property requests to evidence-bearing
standard or project-property candidates, authorize only deterministic standard
matches, clarify genuine uncertainty/custom facts, and emit only the exact
typed property contract already proven by Phase 10.1.

**Requirements:** RAG-01, RAG-02, RAG-03, RAG-04

**Depends on:** Phase 10.1

**Success criteria:**

1. IFC2X3 official properties and current-project properties have versioned,
   provenance-bearing searchable records with exact applicability and types.
2. Exact, reviewed-alias, keyword and local Qdrant/BGE-M3 retrieval produce
   bounded evidence; vectors improve recall but are never an authority.
3. Unique exact/reviewed-alias matches and measured keyword/vector consensus
   may resolve locally; low-confidence, conflicting and custom candidates
   produce bounded clarification/confirmation.
4. Retrieval output is candidate evidence only and cannot bypass Phase 10.1
   confirmation, Binder, atomic authoring, reopened L2 or publication gates.
5. One generic occurrence-property operation supports Wall, WallStandardCase,
   Door and Window scalar properties with target-local copy-on-write, while one
   real LargeBuilding Window DeepSeek UAT passes with knowledge health ready.

**Evidence:** [Phase 10.2 validation](phases/10.2-ifc2x3-property-knowledge-retrieval-and-resolution/10.2-VALIDATION.md)

### Phase 10.3: Batch Window Repair and Dataset Benchmark Hygiene (INSERTED)

**Status:** Complete — 2026-07-24

**Goal:** Prove a genuine five-Window transaction on a larger IFC while making
dataset and benchmark identities reproducible and non-destructive.

**Requirements:** DATA-01, DATA-02, BATCH-01, BATCH-02, BATCH-03, BATCH-04,
BATCH-05

**Depends on:** Phases 10, 10.1 and 10.2

**Plans:** 1 plan in 4 waves

- [x] **Wave 1:** Dataset audit, inventory classification and benchmark manifest.
- [x] **Wave 2:** Five-chain mutation and Gold-free batch public projection.
- [x] **Wave 3:** Unified atomic ChangeSet, per-operation L1/L2 and rollback.
- [x] **Wave 4:** Larger IFC compatibility matrix, real DeepSeek UAT and closure.

**Success criteria:**

1. Dataset manifests are hash/schema/path validated without moving or deleting
   existing files, and processed outputs receive an explicit review class.
2. One mutation of `vvo.ifc` removes five valid Window/Opening chains and
   produces one source-bound damaged IFC while preserving all host walls.
3. One bounded user request produces one RepairIntent and one unified,
   five-operation ChangeSet with no private Ground Truth in Provider input.
4. One atomic apply publishes a reopened IFC only when all five operations pass
   independent L1 and L2; any failure suppresses partial success.
5. Larger BIMNet IFC compatibility and a real DeepSeek five-Window UAT are
   recorded with prompt size, timing and honest success/failure evidence.

**Evidence:** [Phase 10.3 validation report](../docs/validation/ifc2x3-changeset/phase10.3-five-window-batch-validation-report.md)

### Phase 10.4: Comparator 0.2 Scalable Preservation Gate (INSERTED)

**Status:** Complete - 2026-07-24

**Goal:** Make Evaluation 0.2 complete on BIMNet-scale IFC2X3 files without
weakening the blocking global preservation guarantee or changing L1/L2
publication semantics.

**Requirements:** CMP-01, CMP-02, CMP-03, CMP-04, CMP-05

**Depends on:** Phases 8 and 10.3

**Plans:** 1 plan in 5 sequential waves

- [x] **Wave 1:** Baseline instrumentation and fail-closed RED contracts.
- [x] **Wave 2:** Complete cycle-safe, memoized root fingerprint engine.
- [x] **Wave 3:** Production integration and authorized-neighborhood caches.
- [x] **Wave 4:** Legacy equivalence, security and performance regression.
- [x] **Wave 5:** Fresh AdvancedProject comparator and Production acceptance.

**Cross-cutting constraints:**

- Global preservation remains blocking; timeout or incomplete evidence never
  passes.
- Evaluation 0.2 statuses, check identifiers, report shape and L2 rules remain
  compatible.
- Full IfcDiff is diagnostic by default; a known pre-publication contradiction
  fails closed.
- This phase adds no new IFC operation family.

**Success criteria:**

1. Complete global root fingerprints detect the unauthorized-change fault
   corpus while reusing shared subgraph calculations.
2. Policy-derived target/host neighborhoods retain deep structural and geometry
   checks while shared representation subgraphs use per-run memoization.
3. vvo and LargeBuilding produce equivalent comparison/evaluation outcomes;
   vvo runtime regresses by no more than 20%.
4. Three fresh AdvancedProject comparator runs have median preservation time at
   most 120 seconds and peak RSS at most 4 GiB; one fresh full Production replay
   completes within 180 seconds.
5. The saved real DeepSeek ChangeSet is reapplied in a new directory and
   reaches an honest publication decision.

**Evidence:** [Phase 10.4 validation report](../docs/validation/ifc2x3-changeset/phase10.4-comparator-0.2-validation-report.md)

### Phase 10.5: Window Occurrence Fidelity and Validation Acceleration (INSERTED)

**Status:** Complete — 2026-07-26

**Goal:** Given a complete authorized natural-language request and a damaged
IFC2X3 model, restore the selected Window/Opening geometry, relationships,
effective occurrence scalar properties and relevant quantities to Ground Truth
semantic equivalence, while keeping full Production evaluation within 180
seconds.

**Requirements:** WFID-01, WFID-02, WFID-03, WFID-04, WFID-05, WFID-06

**Depends on:** Phases 7, 8, 9, 09.1 and 10 through 10.4

**Plans:** 3/3 plans executed

- [x] **Wave 1:** `10.5-01` - Complete occurrence input, authorized
  exact-occurrence/cohort reuse, reusable bundles, and atomic Window/Opening
  semantic authoring.
- [x] **Wave 2** *(blocked on Wave 1)*: `10.5-02` - Ground Truth occurrence
  comparator, blocking fidelity integration, and human-readable IFC comparison.
- [x] **Wave 3** *(blocked on Waves 1-2)*: `10.5-03` - Validation cache,
  bounded parallel evaluation, offline acceptance matrix, AdvancedProject
  performance gates and real DeepSeek no-fallback UAT.

**Cross-cutting constraints:**

- Every authored fact is explicit, deterministically derived, Type-inherited,
  copied from an explicitly authorized occurrence, or taken from an explicitly
  authorized unanimous Type cohort. Retrieval never invents a value.
- Contextual/identity facts are recomputed or explicitly overridden and are
  never copied blindly.
- Window/Opening effective semantic equivalence is blocking; GUID, STEP,
  serialization, ownership-graph and low-level geometry-node differences remain
  diagnostic `authoring_exactness`.
- Global preservation and IfcOpenShell validation remain complete and
  fail-closed. Acceleration may change scheduling/reuse only.
- Private Ground Truth remains evaluator-only and never enters either Provider
  prompt.

**Success criteria:**

1. One bounded request can express exact scalar Psets, Window/Opening
   quantities, one reusable bundle, per-operation overrides, and an explicitly
   authorized exact occurrence or unanimous same-Type cohort.
2. Exact-reference ambiguity, empty/conflicting cohorts, missing values,
   unsupported authoring, timeout, cache corruption and worker failure clarify
   or fail closed and publish no successful IFC.
3. A private comparator classifies every supported Ground Truth fact as
   `matched`, `not_in_user_text`, `unsupported_authoring`, `wrong_value`, or
   `ownership_only` and reports independent geometry, L2 semantic, occurrence
   fidelity and authoring-exactness statuses.
4. Single complete-input, exact-reference, cohort, and five-Window shared-bundle
   offline cases pass reopened IFC2X3, global preservation, L1/L2 and occurrence
   fidelity; the five-Window path remains one atomic ChangeSet.
5. AdvancedProject cold and warm full Production runs each complete within 180
   seconds and 4 GiB without reducing checks, and one real DeepSeek run records
   honest success or failure with no fallback.

**Evidence:** [Phase 10.5 validation report](../docs/validation/ifc2x3-changeset/phase10.5-window-fidelity-validation-report.md)

### Phase 11: Wall Opening and Door Operations

**Status:** Complete — 2026-07-31. All five plans pass deterministic and real
Provider acceptance. The 2026-07-29 correction rejects relationship-only false
positives: Door geometry must overlap its Opening, use the contextual
Opening-elevation Storey and satisfy exact fill/void/type topology. The
damaged-only authority rerun proves that private Ground Truth is unavailable
during repair. Real DeepSeek run `uat-20260731T224900289758Z` used no synthetic
fallback: the complete case used Stage 1/2 = 1/1, the clarification/resume case
used total Stage 1/2 = 2/1, and unsupported complex generation stopped at
Stage 1/2 = 1/0 with exact `DOOR_OPERATION_TYPE_UNSUPPORTED`. Both published
IFC files independently reopen as IFC2X3 and pass strict L0/L1/L2. The checked-
in Proof collection passes as 16 cases, 45 operations, 247 files and 48 IFC
reopens; 11 cases are independently recomputed and five older Window cases are
explicitly identified as legacy artifact-only evidence.

**Goal:** Extend the Registry with opening-only, Door+Opening and
Door-into-existing-Opening operations without copying the Window pipeline,
while adding per-operation RepairIntent routing and token-bounded prompt
profiles.

**Requirements:** OPS-01, OPS-02

**Depends on:** Phases 10.1, 10.2 and 10.5

**Specification:** [Phase 11 SPEC](phases/11-wall-opening-and-door-operations/11-SPEC.md)

**Implementation research:** [Phase 11 RESEARCH](phases/11-wall-opening-and-door-operations/11-RESEARCH.md)

**Validation strategy:** [Phase 11 VALIDATION](phases/11-wall-opening-and-door-operations/11-VALIDATION.md)

**Plans:** 5 sequential plans

1. [11-01 — Versioned routing, prompt profiles and authority contracts](phases/11-wall-opening-and-door-operations/11-01-PLAN.md)
2. [11-02 — Opening/DoorStyle index and deterministic Door resolution](phases/11-wall-opening-and-door-operations/11-02-PLAN.md)
3. [11-03 — Shared hosted-opening core and deterministic IFC authoring](phases/11-wall-opening-and-door-operations/11-03-PLAN.md)
4. [11-04 — Door/Opening L1, L2 and occurrence fidelity](phases/11-wall-opening-and-door-operations/11-04-PLAN.md)
5. [11-05 — Dataset matrix, real DeepSeek UAT and Proof publication](phases/11-wall-opening-and-door-operations/11-05-PLAN.md)

**Execution sequence:**

| Wave | Plan | Blocking outcome |
|---:|---|---|
| 1 | 11-01 | RepairIntent 0.5, Prompt Profile 0.1, Manifest 0.3 and ChangeSet 0.4 are frozen and selected-profile prompts work |
| 2 | 11-02 | Opening/Type evidence and all blocking Door facts resolve or clarify deterministically |
| 3 | 11-03 | Opening-only and both Door IFC operations apply atomically on the shared hosted-opening core |
| 4 | 11-04 | Independent L1/L2/occurrence/global gates pass for single, batch and mixed operations |
| 5 | 11-05 | Real datasets, AdvancedProject and real DeepSeek produce reproducible accepted evidence |

**Cross-cutting constraints:**

- Stage 1 records component/action routing in each RepairIntent operation; the
  runtime then loads only referenced operation contracts and few-shots.
- Exact `IfcDoorStyle` reuse preserves that Type unchanged. Without reuse, the
  compiler creates only a supported dedicated single-swing/explicitly
  `NOTDEFINED` style.
- Public target selection must not require an IFC GlobalId. Descriptive
  selectors resolve against the current IFC index; a duplicate DoorStyle name
  may be narrowed by an explicit formal OperationType, otherwise it clarifies.
- Missing optional Door features are omitted; missing blocking facts clarify;
  requested unsupported features fail in deterministic capability code.
- Space may resolve target/viewpoint but Phase 11 does not author
  `IfcRelSpaceBoundary`.
- Existing Door replacement/deletion, project-coordinate placement, complex
  generated Door styles and curved walls remain deferred.
- For vvo multi-storey host walls, direct wall containment may be a base
  Storey while the retained Opening world elevation belongs to an upper
  Storey. Phase 11 records this as an IFC authoring exception and uses the
  unique contextual Opening-elevation Storey; missing, conflicting or
  equidistant candidates fail closed.

**Success criteria:**

1. `add_opening_to_wall` has its own target/parameter/L1/L2 contracts.
2. `add_door_with_opening_to_wall` and
   `fill_existing_opening_with_door` restore host/opening/filling topology,
   exact or generated Door Type, viewpoint-aware operation semantics and
   required L2 facts.
3. Family/action routing selects only relevant operation prompt profiles and
   few-shots; unsupported capability is rejected by program logic rather than
   improvised by the Provider.
4. Five-Door and mixed Window/Door cases remain one transaction with
   independently evaluated L1/L2 and all-or-nothing publication.
5. LargeBuilding, vvo and AdvancedProject offline cases plus complete and
   clarification-driven real DeepSeek paths pass reopened-IFC validation,
   occurrence fidelity and full-model preservation.

### Phase 12: Beam and Column Operations

**Status:** Live acceptance blocked - 2026-08-21. Plans 12-01 through 12-14 are
complete. The genuine Plan 12-15 DeepSeek run preserved a valid Stage 1
Beam/Column property claim but failed before Stage 2 with
`PROPERTY_NOT_RESOLVED`; no live success was curated. Stage 1 scope, Type intent
and transaction-clause corrections are implemented on the current branch, but
they do not satisfy Wave 15 acceptance. Property authority correction and final
closeout move through inserted Phase 12.1; Phase 13 remains unstarted.

**Goal:** Prove the common ChangeSet architecture across non-opening structural
elements.

**Requirements:** OPS-03, OPS-04

**Depends on:** Phases 8, 9 and 11; uses the property contract proven in Phase
10.1 and the optional retrieval interface evaluated in Phase 10.2

**Specification:** [Phase 12 SPEC](phases/12-beam-and-column-operations/12-SPEC.md)

**Implementation research:** [Phase 12 RESEARCH](phases/12-beam-and-column-operations/12-RESEARCH.md)

**Pattern map:** [Phase 12 PATTERNS](phases/12-beam-and-column-operations/12-PATTERNS.md)

**Validation strategy:** [Phase 12 VALIDATION](phases/12-beam-and-column-operations/12-VALIDATION.md)

**Plans:** 14/16 primary plans complete; Wave 15 acceptance blocked

- [x] **Wave 1:** [12-01 - Structural prompt profiles and selected routing](phases/12-beam-and-column-operations/12-01-PLAN.md)
- [x] **Wave 2** *(blocked on Wave 1)*: [12-02 - Structural occurrence and Type index](phases/12-beam-and-column-operations/12-02-PLAN.md)
- [x] **Wave 3** *(blocked on Wave 2)*: [12-03 - Structural occurrence property and RAG authority integration](phases/12-beam-and-column-operations/12-03-PLAN.md)
- [x] **Wave 4** *(blocked on Wave 3)*: [12-04 - Deterministic structural Type factories](phases/12-beam-and-column-operations/12-04-PLAN.md)
- [x] **Wave 5** *(blocked on Wave 4)*: [12-05 - Repair-local straight rectangular member geometry](phases/12-beam-and-column-operations/12-05-PLAN.md)
- [x] **Wave 6** *(blocked on Wave 5)*: [12-06 - Exact-Type and optional material/Pset preservation](phases/12-beam-and-column-operations/12-06-PLAN.md)
- [x] **Wave 7** *(blocked on Wave 6)*: [12-07 - Registered add_beam resolution and application](phases/12-beam-and-column-operations/12-07-PLAN.md)
- [x] **Wave 8** *(blocked on Wave 7)*: [12-08 - Registered add_column resolution and application](phases/12-beam-and-column-operations/12-08-PLAN.md)
- [x] **Wave 9** *(blocked on Wave 8)*: [12-09 - Strict structural evaluation and mixed atomicity](phases/12-beam-and-column-operations/12-09-PLAN.md)
- [x] **Wave 10** *(blocked on Wave 9)*: [12-10 - Structural mutation and private-Gold isolation](phases/12-beam-and-column-operations/12-10-PLAN.md)
- [x] **Wave 11** *(blocked on Wave 10)*: [12-11 - Family-neutral strict independent Proof validator](phases/12-beam-and-column-operations/12-11-PLAN.md)
- [x] **Wave 12** *(blocked on Wave 11)*: [12-12 - d7n/vvo offline runner and curated strict Proof contract](phases/12-beam-and-column-operations/12-12-PLAN.md)
- [x] **Wave 13** *(blocked on Wave 12)*: [12-13 - Live transcript, preflight and no-fallback contract](phases/12-beam-and-column-operations/12-13-PLAN.md)
- [x] **Wave 14** *(blocked on Wave 13)*: [12-14 - Live Proof curation acceptance contract](phases/12-beam-and-column-operations/12-14-PLAN.md)
- **Wave 15 — BLOCKED** *(all offline gates passed; genuine live complete case failed before Stage 2)*: [12-15 - Execute and independently curate real DeepSeek structural UAT](phases/12-beam-and-column-operations/12-15-PLAN.md)
- **Wave 16 — DEFERRED TO PHASE 12.1 CLOSEOUT** *(still blocked on accepted live evidence)*: [12-16 - Regress, report and conditionally close Phase 12](phases/12-beam-and-column-operations/12-16-PLAN.md)

Corrective subplans [12-15A](phases/12-beam-and-column-operations/12-15A-PLAN.md),
[12-15B](phases/12-beam-and-column-operations/12-15B-PLAN.md) and
[12-15C](phases/12-beam-and-column-operations/12-15C-PLAN.md) produced the
current Stage 1 scope, structural Type-intent and transaction-clause baseline.
They are prerequisite implementation history, not accepted Wave 15 live Proof.

**Cross-cutting constraints:**

- Stage 1 keeps the existing single compact classification/extraction call;
  Stage 2 receives only selected full operation profiles and few-shots.
- Noncanonical Provider fields fail closed. No compatibility aliases are
  added to accommodate model output.
- Missing Type-reuse intent creates one dedicated deterministic structural
  Type; exact Type reuse remains unchanged. Material and Psets are optional
  unless explicitly requested or exactly authorized.
- Structural L1 requires axis endpoints/base/top within 5 mm,
  direction/horizontal-or-vertical tilt within 0.1 degrees, section/member
  dimensions within 1 mm, and exact containment/Type cardinality.
- Vector/RAG recall remains discovery only; executable property values require
  exact typed authority.
- Damaged/public production input is isolated from original/private Gold.
  `d7n` and `vvo` prove cross-scene BIMNet compatibility only.
- Real DeepSeek starts only after all offline gates pass, never uses synthetic,
  cached or prerecorded fallback, and cannot close the phase until a separate
  validator reopens and recomputes strict Proof.

**Success criteria:**

1. Beam and Column operations use operation-specific target, placement,
   containment, type/material and L2 contracts.
2. Structural additions pass IFC2X3 reopen, L1 geometry/relationship and L2
   semantic checks.
3. Common orchestration remains free of Window/Door-specific fields.

### Phase 12.1: Property Resolution RAG and Reranker Correction

**Status:** In progress - Plans 12.1-01 through 12.1-06 complete; Plan 12.1-07
is unstarted and awaits an explicit Go/No-Go.

**Goal:** Replace active reviewed-alias/local-consensus property authorization
with class-applicable multilingual vector retrieval, one independent bounded
Property Resolution Provider stage, deterministic admissibility and
program-constructed ExactPropertyIntent, then finish Phase 12 live acceptance.

**Requirements:** RAG-05, RAG-06, RAG-07, OPS-03, OPS-04

**Depends on:** Phase 10.1 exact property authority, Phase 10.2 historical
knowledge/vector baseline, Phase 12 Plans 12-01 through 12-14 and the current
12-15A/B/C correction baseline

**Context:** [Phase 12.1 CONTEXT](phases/12.1-property-resolution-rag-reranker/12.1-CONTEXT.md)

**Specification:** [Phase 12.1 SPEC](phases/12.1-property-resolution-rag-reranker/12.1-SPEC.md)

**Implementation research:** [Phase 12.1 RESEARCH](phases/12.1-property-resolution-rag-reranker/12.1-RESEARCH.md)

**Validation strategy:** [Phase 12.1 VALIDATION](phases/12.1-property-resolution-rag-reranker/12.1-VALIDATION.md)

**Plans:** 6/7 plans executed

- [x] **Wave 1:** [12.1-01 - Additive Stage 1.5 schemas, policy contract and Prompt](phases/12.1-property-resolution-rag-reranker/12.1-01-PLAN.md)
- [x] **Wave 2:** [12.1-02 - Alias-free multilingual vector runtime](phases/12.1-property-resolution-rag-reranker/12.1-02-PLAN.md)
- [x] **Wave 3:** [12.1-03 - Bounded Property Resolution Provider stage](phases/12.1-property-resolution-rag-reranker/12.1-03-PLAN.md)
- [x] **Wave 4:** [12.1-04 - Admissibility gate and ExactPropertyIntent construction](phases/12.1-property-resolution-rag-reranker/12.1-04-PLAN.md)
- [x] **Wave 5:** [12.1-05 - Durable public API integration and clarification resume](phases/12.1-property-resolution-rag-reranker/12.1-05-PLAN.md)
- [x] **Wave 6:** [12.1-06 - Frozen retrieval evaluation, Stage 1.5 offline contract, five-family regression and zero-network preflight](phases/12.1-property-resolution-rag-reranker/12.1-06-PLAN.md) — real local BGE-M3/Qdrant retrieval, five-family/offline full-chain and preflight 0.4 passed; Stage 1.5 semantic capability is explicitly not evaluated here. See [summary](phases/12.1-property-resolution-rag-reranker/12.1-06-SUMMARY.md).
- [ ] **Wave 7** *(blocked on explicit Go/No-Go)*: [12.1-07 - Genuine 60-case Stage 1.5 semantic evaluation, four-case DeepSeek UAT, independent Proof, IFCCompare and closeout](phases/12.1-property-resolution-rag-reranker/12.1-07-PLAN.md)

**Cross-cutting constraints:**

- `property_aliases.json` remains historical evidence only. No new reviewed
  alias, phrase table, keyword family branch or Provider-output compatibility
  mapping is permitted.
- Explicit canonical `Pset.Property` requests retain the exact no-RAG path.
  Natural-language claims follow Stage 1 claim extraction -> deterministic
  class/template eligibility -> multilingual vector Top-K -> independent Stage
  1.5 -> deterministic admissibility -> program ExactPropertyIntent -> Stage 2.
- Vector score/rank/margin are retained retrieval evidence. Neither Top-1 nor a
  large margin can auto-authorize a property; the bounded LLM reranks offered
  candidates, and code only decides whether its selection is executable.
- The frozen 60 cases support three separate claims: Plan 06 retrieval
  capability, Plan 07 genuine Stage 1.5 semantic capability, and separate
  four-case E2E repair viability. Deterministic Stage 1.5 doubles are contract/
  plumbing evidence only and never semantic Candidate evidence.
- The common path covers existing property-capable Window, Door,
  Wall/WallStandardCase, Beam and Column occurrences. Wall remains
  property-only; no `add_wall` operation is added.
- Door/Window workflows, geometry thresholds, Type/material authority, Storey
  policy, Ground Truth isolation and atomic publication remain frozen.
- Any new deterministic defect found by live UAT stops execution for discussion;
  no patch-and-retry, synthetic/cached fallback or Phase 13 work is allowed.

**Success criteria:**

1. Active natural-language resolution has no alias authority and production
   vector health/configured versions are reusable, public and fail-closed.
2. Stage 1.5 selects only offered class-applicable candidates or asks/declines;
   code constructs the only executable ExactPropertyIntent.
3. Plan 06 real-BGE/Qdrant retrieval evaluation passes its frozen Top-K/family/
   leakage gates and explicitly reports Stage 1.5 semantics not evaluated;
   Window/Door/Wall/Beam/Column offline chains preserve existing contracts.
4. Plan 07 genuine 60-case Stage 1.5 semantic evaluation, separate four-case
   DeepSeek E2E matrix, independent Proof, IFCCompare and final regressions all
   pass before Phase 12/12.1 and OPS-03/04 close.

### Phase 13: Large IFC Context and 128k Experiment

**Goal:** Validate retrieval and Provider behavior on BIMNet-scale files before
changing the default input budget.

**Requirements:** SCALE-01, SCALE-02

**Depends on:** Phases 7 through 12.1, including inserted Phases 09.1, 10.1,
10.2 and the completed Phase 12/12.1 acceptance chain

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
| 09.1 | TYPE-01..03 |
| 10 | WIN-01..02 |
| 10.1 | PROP-01..05 |
| 10.2 | RAG-01..04 |
| 10.3 | DATA-01..02, BATCH-01..05 |
| 10.4 | CMP-01..05 |
| 10.5 | WFID-01..06 |
| 11 | OPS-01..02 |
| 12 | OPS-03..04 |
| 12.1 | RAG-05..07, OPS-03..04 |
| 13 | SCALE-01..02 |

**Coverage:** 55 committed requirements, 55 mapped, 0 unmapped.

## Delivery Sequence and Deferred Horizon

The v1.1 sequence is intentionally layered:

1. Phases 7-09.1 established target/Type evidence and public orchestration.
2. Phase 10 proved one complete Window L1/L2 repair.
3. Phase 10.1 adds exact user-requested scalar Psets without retrieval.
4. Phase 10.2 evaluates property knowledge retrieval/RAG against the exact
   Phase 10.1 output contract.
5. Phase 10.3 proves that the same bounded contract remains atomic and
   verifiable for five Window operations on larger IFC2X3 files.
6. Phase 10.4 makes the unchanged blocking preservation contract practical on
   BIMNet-scale files before operation expansion.
7. Phase 10.5 closes Window/Opening occurrence-fact coverage and full
   validation runtime before the Window reference implementation is reused.
8. Phases 11-12 expand the same Registry/ChangeSet/evaluation architecture to
   Opening, Door, Beam and Column operations.
9. Phase 12.1 replaces historical alias authority with a bounded vector/LLM
   property-resolution stage and completes Phase 12 acceptance without
   changing Door/Window or structural operation contracts.
10. Phase 13 measures near-limit context and 128k behavior before changing the
   bounded 64k default.

Post-v1.1 work remains explicitly uncommitted: existing Wall mutation beyond
straight-wall openings, Space/room editing, curved/free-form walls, additional
MEP/structural families, and L3 authoring/identity exactness. Each requires its
own operation and evaluation contract rather than an implicit extension of the
Window path.
