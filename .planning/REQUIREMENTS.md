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

- [ ] **PIPE-01**: User can run one CLI/API command with IFC path plus natural-
  language request and receive a terminal result and evidence directory.
- [ ] **PIPE-02**: A successful run publishes the semantic ChangeSet and the
  deterministically compiled IFC2X3 output.
- [ ] **PIPE-03**: Provider input contains only public bounded request, spec,
  target context and contracts, never raw private ground truth.
- [ ] **PIPE-04**: Ambiguous, unsupported, Provider-invalid, Audit-failed or
  application-failed runs cannot publish an IFC as a successful repair.

### Validation

- [ ] **VAL-01**: Every repair report exposes mandatory L1 geometry/
  relationship status with structured evidence.
- [ ] **VAL-02**: Every supported operation defines a mandatory L2 semantic-
  fidelity allowlist with structured matched/mismatched/unavailable facts.
- [ ] **VAL-03**: Evaluation statuses support `passed`, `failed`, `partial`,
  `not_required` and `not_evaluable` rather than forcing unknown facts to pass.
- [ ] **VAL-04**: Synthetic benchmark runs compare repaired IFC with private
  original ground truth without exposing that ground truth to the Provider.
- [ ] **VAL-05**: Production runs evaluate L2 from request, surviving IFC facts
  and approved prototypes and disclose facts that cannot be evaluated.

### Window Fidelity

- [ ] **WIN-01**: Window repair restores the frozen Window L2 facts including
  type, host/storey, `IsExternal`, selected Psets/quantities, material and
  classification when resolvable from non-gold evidence.
- [ ] **WIN-02**: The LargeBuilding Window case passes both L1 and L2 in
  deterministic and real-Provider evidence runs.

### Operation Expansion

- [ ] **OPS-01**: User can add a wall opening without a filling element through
  a registered opening-specific ChangeSet operation.
- [ ] **OPS-02**: User can add a Door with its wall Opening and required L1/L2
  semantics through a registered Door-specific operation.
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
| VAL-01 | 8 | Pending |
| VAL-02 | 8 | Pending |
| VAL-03 | 8 | Pending |
| VAL-04 | 8 | Pending |
| VAL-05 | 8 | Pending |
| PIPE-01 | 9 | Pending |
| PIPE-02 | 9 | Pending |
| PIPE-03 | 9 | Pending |
| PIPE-04 | 9 | Pending |
| WIN-01 | 10 | Pending |
| WIN-02 | 10 | Pending |
| OPS-01 | 11 | Pending |
| OPS-02 | 11 | Pending |
| OPS-03 | 12 | Pending |
| OPS-04 | 12 | Pending |
| SCALE-01 | 13 | Pending |
| SCALE-02 | 13 | Pending |

**Coverage:** 22 requirements, 22 mapped, 0 unmapped.

---
*Last updated: 2026-07-18 after v1.1 roadmap creation*
