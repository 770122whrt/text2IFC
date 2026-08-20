# Requirements: text2IFC v1.1 IFC ChangeSet Repair Pipeline

**Defined:** 2026-07-18  
**Core Value:** Given an IFC file and explicit request, produce a traceable
semantic ChangeSet and an L1/L2-validated IFC result.

## v1.1 Requirements

### Target Retrieval

- [x] **TGT-01**: User can index an IFC2X3 file into stable element records
  containing GUID, class, Name/LongName/Tag/ObjectType/type aliases and storey.
- [x] **TGT-02**: User requests can identify targets using any compatible
  combination of exact GUID, project label/name/type, storey, grid/space,
  direction/position, relationship and geometry constraints.
- [x] **TGT-03**: The system produces a versioned structured `TargetQuery`
  before ChangeSet generation instead of asking the Generator to search raw IFC.
- [x] **TGT-04**: Candidate results include deterministic scores and field-level
  evidence, and zero/multiple/conflicting matches stop or request clarification.
- [x] **TGT-05**: The system packages deterministic top-K candidates within an
  explicit context byte/token budget without dropping the best exact match.

### Repair Pipeline

- [x] **PIPE-01**: User can run one CLI/API command with IFC path plus natural-
  language request and receive a terminal result and evidence directory.
- [x] **PIPE-02**: A successful run publishes the semantic ChangeSet and the
  deterministically compiled IFC2X3 output.
- [x] **PIPE-03**: Provider input contains only public bounded request, spec,
  target context and contracts, never raw private ground truth.
- [x] **PIPE-04**: Ambiguous, unsupported, Provider-invalid, Audit-failed or
  application-failed runs cannot publish an IFC as a successful repair.

### Validation

- [x] **VAL-01**: Every repair report exposes mandatory L1 geometry/
  relationship status with structured evidence.
- [x] **VAL-02**: Every supported operation defines a mandatory L2 semantic-
  fidelity allowlist with structured matched/mismatched/unavailable facts.
- [x] **VAL-03**: Evaluation statuses support `passed`, `failed`, `partial`,
  `not_required` and `not_evaluable` rather than forcing unknown facts to pass.
- [x] **VAL-04**: Synthetic benchmark runs compare repaired IFC with private
  original ground truth without exposing that ground truth to the Provider.
- [x] **VAL-05**: Production runs evaluate L2 from request, surviving IFC facts
  and approved prototypes and disclose facts that cannot be evaluated.

### Window Fidelity

- [x] **WIN-01**: Window repair restores the frozen Window L2 facts including
  type, host/storey, `IsExternal`, selected Psets/quantities, material and
  classification when resolvable from non-gold evidence.
- [x] **WIN-02**: The LargeBuilding Window case passes both L1 and L2 in
  deterministic and real-Provider evidence runs.

### Explicit Property Authoring

- [x] **PROP-01**: A user can explicitly provide an exact Pset name, property
  name and scalar value that Stage 1 preserves as a versioned, provenance-
  bearing typed property intent instead of flattening it into free text.
- [x] **PROP-02**: Exact standard properties are validated offline against the
  checked-in IFC2X3 registry, while every unknown/custom property requires
  confirmation of its exact name, value, IFC value type, unit and scope.
- [x] **PROP-03**: Property mutation is limited to the target occurrence.
  Existing Type reuse requires an exact unique user reference or affirmative
  candidate confirmation; uncertainty asks the user, no Type intent creates a
  deterministic dedicated system-template Type, and direct shared-Type
  mutation is deferred.
- [x] **PROP-04**: The unified ChangeSet atomically creates or updates the
  authorized direct Pset/property and any required dedicated template Type
  without duplicate relationships; any authoring/reopen failure publishes no
  successful IFC.
- [x] **PROP-05**: Every explicitly requested property becomes a mandatory
  dynamic L2 fact and the Window LargeBuilding path passes offline and real-
  Provider exact-property acceptance without RAG or private Ground Truth.

### Property Knowledge Retrieval

- [x] **RAG-01**: IFC2X3 official properties and current-project properties are
  available as versioned searchable records with provenance, applicability,
  value type, unit/template metadata and standard/custom identity.
- [x] **RAG-02**: Non-exact Chinese/English property phrases produce bounded,
  ranked candidates through exact, reviewed-alias, keyword and rebuildable
  local vector retrieval; vector evidence improves recall but is never the
  authoritative source.
- [x] **RAG-03**: Unique applicable exact/reviewed-alias matches and measured
  keyword/vector consensus may resolve locally. Low-confidence, low-margin,
  conflicting and custom candidates require bounded clarification/
  confirmation and cannot be silently selected.
- [x] **RAG-04**: Retrieval supplies candidates only; the exact Phase 10.1
  property contract, Binder, atomic authoring and reopened L2 remain the sole
  authorization and publication path.
- [ ] **RAG-05**: The active natural-language property runtime filters
  versioned public IFC2X3/property records by target-class applicability,
  scalar template, value/unit/scope compatibility and provenance before a
  bounded multilingual vector Top-K; historical reviewed aliases remain
  readable evidence but are not loaded, embedded, prompted or authorized.
- [ ] **RAG-06**: A separate bounded Property Resolution stage between Stage 1
  and Stage 2 lets the configured LLM rerank only the offered Top-K and return
  one offered candidate, clarification or unsupported; malformed output gets
  at most one schema-correction attempt and no compatibility normalization.
- [ ] **RAG-07**: Program code independently checks the selected record and
  evidence for membership, hashes, class/template/type/unit/scope and frozen
  retrieval-quality policy, then constructs ExactPropertyIntent from the
  authoritative record plus original user facts; vector Top-1/margin and LLM
  text are never directly authorable.

### Batch Repair and Dataset Hygiene

- [x] **DATA-01**: User can run a read-only deterministic audit that validates
  dataset manifest paths, hashes, IFC schemas and duplicate identities and
  classifies processed artifacts without deleting or moving files.
- [x] **DATA-02**: A versioned benchmark manifest binds selected larger IFC2X3
  files to source hashes, reproducible model/chain metrics, project splits,
  roles and suitability evidence.
- [x] **BATCH-01**: One source IFC can be damaged in a single deterministic
  mutation by removing exactly five valid Window/Opening chains while
  preserving source bytes, host walls and closed target regions.
- [x] **BATCH-02**: One bounded natural-language request produces one ordered
  RepairIntent and one unified ChangeSet containing exactly five Window repair
  operations without private Ground Truth in Provider input.
- [x] **BATCH-03**: Five operations apply as one all-or-nothing IFC
  transaction; one invalid operation or failed mandatory evaluation suppresses
  the successful IFC artifact.
- [x] **BATCH-04**: Every operation has independent L1/L2 evidence and the
  aggregate publication decision passes only when all five operations pass.
- [x] **BATCH-05**: The `vvo.ifc` five-Window chain passes deterministic
  end-to-end acceptance, larger IFC compatibility is measured, and a real
  DeepSeek batch UAT records success or honest failure without fallback.

### IFC Type Authority

- [x] **TYPE-01**: The retrieval index distinguishes occurrence-direct facts
  from Type-inherited facts and retains source provenance for IFC2X3 Type
  objects such as `IfcWindowStyle`.
- [x] **TYPE-02**: Users can authorize a unique Prototype through a human-
  readable Type name or an evidence-bearing deduplicated clarification choice
  without being required to provide an IFC GUID.
- [x] **TYPE-03**: Production evidence reads only authorized Type facts and the
  LargeBuilding shared Window Style no longer fails because occurrence-specific
  storey/level values were aggregated as Type facts.

### Scalable Preservation Comparator

- [x] **CMP-01**: Evaluation 0.2 public statuses, check identifiers, report
  shape and fail-closed publication behavior remain compatible while the
  comparator implementation is optimized.
- [x] **CMP-02**: The blocking global preservation gate compares every IFC root
  through complete cycle-safe fingerprints, reuses shared subgraph work, and
  rejects duplicate or empty root GUIDs.
- [x] **CMP-03**: Policy-derived authorized repair neighborhoods retain deep
  structural, geometry, wall and volume checks, while per-run memoization
  prevents repeated expansion of shared representation subgraphs.
- [x] **CMP-04**: STEP reorder, unauthorized attribute/placement/geometry/Pset/
  relationship mutations, cache contamination and timeout tests prove
  semantic equivalence or fail closed; Full IfcDiff remains diagnostic by
  default.
- [x] **CMP-05**: Three fresh AdvancedProject comparator evaluations meet the
  120-second preservation and 4-GiB peak-RSS budgets; one fresh full Production
  replay completes within 180 seconds and honestly evaluates the saved real
  DeepSeek ChangeSet.

### Window Occurrence Fidelity and Validation Acceleration

- [x] **WFID-01**: One bounded public request can express complete supported
  Window/Opening occurrence semantics through exact/natural scalar property
  intents, scalar quantity intents, reusable bundles and per-operation
  overrides with public provenance.
- [x] **WFID-02**: An exact surviving occurrence or explicitly authorized
  unanimous same-Type cohort can supply occurrence-direct values; ambiguous,
  missing or conflicting evidence clarifies rather than guesses, and contextual
  facts are recomputed or explicitly overridden.
- [x] **WFID-03**: One shared semantic bundle expands into isolated
  operation-local assignments for a unified five-Window ChangeSet; one invalid
  member rolls back the transaction and neither shared Types nor surviving
  occurrences are modified.
- [x] **WFID-04**: A private Window/Opening Ground Truth comparator classifies
  every supported fact as `matched`, `not_in_user_text`,
  `unsupported_authoring`, `wrong_value` or `ownership_only`, and exposes
  independent geometry/relationship, L2 semantic, occurrence-fidelity and
  authoring-exactness results.
- [x] **WFID-05**: Content-addressed validation reuse and bounded parallel
  evaluation produce evidence identical to sequential execution and make
  AdvancedProject cold and warm full Production runs complete within 180
  seconds and 4 GiB without reducing comparison or validation scope.
- [x] **WFID-06**: Reproducible explicit-input, exact-reference, cohort,
  conflict and atomic five-Window cases plus one real DeepSeek UAT record
  source/damaged/repaired hashes, Window names/GUIDs, public input, Agent and
  ChangeSet artifacts, comparison results, timing/RSS and honest no-fallback
  outcomes.

### Operation Expansion

- [x] **OPS-01**: User can add a wall opening without a filling element through
  a registered opening-specific ChangeSet operation.
- [x] **OPS-02**: User can add a Door with a new wall Opening or restore a Door
  into one surviving empty Opening, with exact/generated Type policy,
  viewpoint-aware operation semantics and required L1/L2 evidence through
  registered Door-specific operations.
- [ ] **OPS-03**: User can add a Beam with operation-specific placement,
  containment, type/material and L1/L2 semantics.
- [ ] **OPS-04**: User can add a Column with operation-specific placement,
  containment, type/material and L1/L2 semantics.

### Scale and Context

- [ ] **SCALE-01**: User can run indexed target retrieval on BIMNet-scale IFC
  files with measured latency, memory, candidate recall and token usage.
- [ ] **SCALE-02**: A dedicated near-limit UAT verifies or rejects 128k Provider
  input behavior before any default-budget change.

## Future Requirements

- L3 authoring/identity exactness: original GlobalId, STEP ID, exact placement/
  representation graph, serialization order and byte-identical IFC.
- Curved, segmented and free-form wall modification.
- Statistical repeated-run Provider reliability beyond coverage-oriented UAT.

## Out of Scope for v1.1

| Feature | Reason |
|---|---|
| L3 authoring exactness | Explicitly deferred; semantic equivalence is the current product goal |
| Model-authored STEP | Deterministic IfcOpenShell compilation remains mandatory |
| Sending whole IFC JSON to the LLM | Retrieval index and bounded context are the scalability boundary |
| Silent best-candidate guessing | Ambiguity must be visible or clarified |
| Default 128k input immediately | Requires dedicated tokenizer/API/end-to-end evidence |

## Traceability

| Requirement | Phase | Status |
|---|---:|---|
| TGT-01 | 7 | Complete |
| TGT-02 | 7 | Complete |
| TGT-03 | 7 | Complete |
| TGT-04 | 7 | Complete |
| TGT-05 | 7 | Complete |
| VAL-01 | 8 | Complete |
| VAL-02 | 8 | Complete |
| VAL-03 | 8 | Complete |
| VAL-04 | 8 | Complete |
| VAL-05 | 8 | Complete |
| PIPE-01 | 9 | Complete |
| PIPE-02 | 9 | Complete |
| PIPE-03 | 9 | Complete |
| PIPE-04 | 9 | Complete |
| TYPE-01 | 09.1 | Complete |
| TYPE-02 | 09.1 | Complete |
| TYPE-03 | 09.1 | Complete |
| WIN-01 | 10 | Complete |
| WIN-02 | 10 | Complete |
| PROP-01 | 10.1 | Complete |
| PROP-02 | 10.1 | Complete |
| PROP-03 | 10.1 | Complete |
| PROP-04 | 10.1 | Complete |
| PROP-05 | 10.1 | Complete |
| RAG-01 | 10.2 | Complete |
| RAG-02 | 10.2 | Complete |
| RAG-03 | 10.2 | Complete |
| RAG-04 | 10.2 | Complete |
| RAG-05 | 12.1 | Pending |
| RAG-06 | 12.1 | Pending |
| RAG-07 | 12.1 | Pending |
| DATA-01 | 10.3 | Complete |
| DATA-02 | 10.3 | Complete |
| BATCH-01 | 10.3 | Complete |
| BATCH-02 | 10.3 | Complete |
| BATCH-03 | 10.3 | Complete |
| BATCH-04 | 10.3 | Complete |
| BATCH-05 | 10.3 | Complete |
| CMP-01 | 10.4 | Complete |
| CMP-02 | 10.4 | Complete |
| CMP-03 | 10.4 | Complete |
| CMP-04 | 10.4 | Complete |
| CMP-05 | 10.4 | Complete |
| WFID-01 | 10.5 | Complete |
| WFID-02 | 10.5 | Complete |
| WFID-03 | 10.5 | Complete |
| WFID-04 | 10.5 | Complete |
| WFID-05 | 10.5 | Complete |
| WFID-06 | 10.5 | Complete |
| OPS-01 | 11 | Complete |
| OPS-02 | 11 | Complete |
| OPS-03 | 12 | Pending |
| OPS-04 | 12 | Pending |
| SCALE-01 | 13 | Pending |
| SCALE-02 | 13 | Pending |

**Coverage:** 55 requirements, 55 mapped, 0 unmapped.

---
*Last updated: 2026-08-21 after freezing Phase 12.1 property-resolution requirements*
