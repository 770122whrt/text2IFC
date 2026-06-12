# Requirements: text2IFC

**Defined:** 2026-06-11
**Core Value:** Produce valid, inspectable IFC models from explicit structured
requirements.

## v1 Requirements

### BIM JSON Contract

- [x] **JSON-01**: The project defines one versioned BIM JSON contract for
  Phase 1 input.
- [x] **JSON-02**: Invalid BIM JSON is rejected with field-level errors before
  IFC generation.
- [x] **JSON-03**: The contract distinguishes required values from optional
  values without silently inventing missing required data.
- [x] **JSON-04**: The contract covers the supported project hierarchy,
  element families, basic dimensions, and selected common properties.
- [x] **JSON-05**: Existing project JSON artifacts can be converted to the
  versioned contract or rejected with an explicit incompatibility report.

### IFC Generation

- [x] **IFC-01**: Valid Phase 1 BIM JSON generates an IFC2X3 file that
  IfcOpenShell can reopen.
- [x] **IFC-02**: Generated IFC preserves the project, site, building, and
  storey hierarchy.
- [x] **IFC-03**: Generated IFC preserves supported element types and counts.
- [x] **IFC-04**: Generated IFC preserves Phase 1 basic dimensions.
- [x] **IFC-05**: Generated IFC preserves selected Phase 1 common properties.

### Verification

- [x] **VER-01**: Each Phase 1 compiler behavior is introduced with a failing
  automated test before implementation.
- [x] **VER-02**: Generated IFC is checked against IFC2X3 schema-level validity.
- [x] **VER-03**: A repeatable command runs the Phase 1 test suite.

### Documentation

- [x] **DOC-01**: The BIM JSON contract and supported IFC subset are documented
  from the same source used by validation.
- [x] **DOC-02**: Durable documentation is indexed from `docs/README.md`.

### IFC Semantic Graph, Knowledge, and Extraction

- [x] **JSON-06**: BIM JSON 2.0 is a separately versioned IFC2X3-aligned
  semantic entity graph, and BIM JSON 1.0 migrates deterministically to an
  explicit Draft Envelope rather than receiving invented spatial facts.
- [x] **KNOW-01**: A deterministic registry generated from official IFC2X3
  EXPRESS validates class names, inheritance, attributes, relationships,
  selects, and enumerations.
- [x] **KNOW-02**: A deterministic registry generated from official IFC2X3 PSD
  definitions validates standard property-set names, property names, types,
  applicability, and provenance.
- [x] **ENTITY-01**: BIM JSON 2.0 represents semantic IFC objects in
  `entities` with explicit `ifc_class`, stable identity, typed attributes, and
  source provenance.
- [x] **CAP-01**: Every recognized IFC2X3 entity has an explicit generation,
  extraction, compiler-only, or unsupported capability and no unsupported
  entity is silently emitted or dropped.
- [x] **GEO-01**: BIM JSON and generated IFC preserve hierarchical local
  placement and orientation for supported spatial objects.
- [x] **GEO-02**: BIM JSON and generated IFC preserve supported semantic
  geometry plus explicit opening, host-element, and filling-element
  relationships.
- [x] **SPACE-01**: BIM JSON represents supported rooms/spaces with stable
  identity, storey membership, placement, and geometry.
- [x] **DRAFT-01**: Incomplete, ambiguous, extract-only, or unsupported content
  uses a separate Draft Envelope that enumerates every missing fact, loss,
  provenance record, and future clarification target.
- [x] **EXTRACT-01**: Authorized IFC sources are deterministically normalized
  into valid BIM JSON 2.0 or an explicit Draft plus provenance and a complete
  machine-readable loss report.
- [x] **COMPAT-01**: The compiler accepts formal BIM JSON 2.0 within the
  architectural generation profile and preserves the
  Phase 2 guarantees while adding the supported spatial subset.

### Text-to-JSON Baseline

- [ ] **TEXT-01**: The project can generate provenance-linked text and BIM JSON
  2.0 pairs from approved formal ground-truth records without split leakage.
- [ ] **TEXT-02**: A structured-output baseline converts natural language into
  formal BIM JSON 2.0 without generating raw IFC text.
- [ ] **TEXT-03**: Text-to-JSON output is evaluated with field-level,
  collection-level, and document-validity metrics.
- [ ] **E2E-01**: At least one spatial natural-language request completes the
  validated Text-to-JSON-to-IFC pipeline.

## Later Requirements

### Geometric and Relational Fidelity

- **GEO-03**: Preserve material assignments and layer details.
- **GEO-04**: Preserve supported topology and connection relationships.
- **GEO-05**: Preserve supported arbitrary profiles, BReps, tessellation, and
  reusable mapped geometry.
- **IFC-06**: Expand beyond the Phase 2.5 architectural generation profile
  with schema-aware support for selected structural, furnishing, and MEP
  classes.

### Natural-language Agent

- **AGENT-01**: Convert natural language into valid BIM JSON.
- **AGENT-02**: Ask targeted questions for missing required values.
- **AGENT-03**: Maintain multi-turn clarification state.
- **MODEL-01**: Evaluate fine-tuning against prompt-only and structured-output
  baselines.
- **MODEL-02**: Expand training data only from license-reviewed sources with
  provenance manifests.
- **DEPLOY-01**: Package the selected model and deterministic compiler behind
  a repeatable deployment interface.

## Out of Scope

| Feature | Reason |
|---|---|
| Raw language-model generation of STEP text | Too fragile and difficult to validate |
| IFC4/IFC4x3 output in Phases 1-3 | Current compiler target is IFC2X3 |
| Exact geometry reconstruction in Phase 2 | Deferred to the fidelity phase |
| Model fine-tuning in Phase 1 | Compiler and evaluation contracts must stabilize first |

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| JSON-01 | Phase 1 | Complete |
| JSON-02 | Phase 1 | Complete |
| JSON-03 | Phase 1 | Complete |
| JSON-04 | Phase 1 | Complete |
| JSON-05 | Phase 1 | Complete |
| DOC-01 | Phase 1 | Complete |
| DOC-02 | Phase 1 | Complete |
| IFC-01 | Phase 2 | Complete |
| IFC-02 | Phase 2 | Complete |
| IFC-03 | Phase 2 | Complete |
| IFC-04 | Phase 2 | Complete |
| IFC-05 | Phase 2 | Complete |
| VER-01 | Phase 2 | Complete |
| VER-02 | Phase 2 | Complete |
| VER-03 | Phase 2 | Complete |
| JSON-06 | Phase 2.5 | Complete |
| KNOW-01 | Phase 2.5 | Complete |
| KNOW-02 | Phase 2.5 | Complete |
| ENTITY-01 | Phase 2.5 | Complete |
| CAP-01 | Phase 2.5 | Complete |
| GEO-01 | Phase 2.5 | Complete |
| GEO-02 | Phase 2.5 | Complete |
| SPACE-01 | Phase 2.5 | Complete |
| DRAFT-01 | Phase 2.5 | Complete |
| EXTRACT-01 | Phase 2.5 | Complete |
| COMPAT-01 | Phase 2.5 | Complete |
| TEXT-01 | Phase 3 | Pending |
| TEXT-02 | Phase 3 | Pending |
| TEXT-03 | Phase 3 | Pending |
| E2E-01 | Phase 3 | Pending |
| GEO-03 | Phase 4 | Deferred |
| GEO-04 | Phase 4 | Deferred |
| GEO-05 | Phase 4 | Deferred |
| IFC-06 | Phase 4 | Deferred |
| AGENT-01 | Phase 5 | Deferred |
| AGENT-02 | Phase 5 | Deferred |
| AGENT-03 | Phase 5 | Deferred |
| MODEL-01 | Phase 6 | Deferred |
| MODEL-02 | Phase 6 | Deferred |
| DEPLOY-01 | Phase 6 | Deferred |

**Coverage:**
- tracked requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-12 after Phase 2.5 verification*
