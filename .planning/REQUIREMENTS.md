# Requirements: text2IFC

**Defined:** 2026-06-11
**Core Value:** Produce valid, inspectable IFC models from explicit structured
requirements.

## v1 Requirements

### BIM JSON Contract

- [ ] **JSON-01**: The project defines one versioned BIM JSON contract for
  Phase 1 input.
- [ ] **JSON-02**: Invalid BIM JSON is rejected with field-level errors before
  IFC generation.
- [ ] **JSON-03**: The contract distinguishes required values from optional
  values without silently inventing missing required data.
- [ ] **JSON-04**: The contract covers the supported project hierarchy,
  element families, basic dimensions, and selected common properties.
- [ ] **JSON-05**: Existing project JSON artifacts can be converted to the
  versioned contract or rejected with an explicit incompatibility report.

### IFC Generation

- [ ] **IFC-01**: Valid Phase 1 BIM JSON generates an IFC2X3 file that
  IfcOpenShell can reopen.
- [ ] **IFC-02**: Generated IFC preserves the project, site, building, and
  storey hierarchy.
- [ ] **IFC-03**: Generated IFC preserves supported element types and counts.
- [ ] **IFC-04**: Generated IFC preserves Phase 1 basic dimensions.
- [ ] **IFC-05**: Generated IFC preserves selected Phase 1 common properties.

### Verification

- [ ] **VER-01**: Each Phase 1 compiler behavior is introduced with a failing
  automated test before implementation.
- [ ] **VER-02**: Generated IFC is checked against IFC2X3 schema-level validity.
- [ ] **VER-03**: A repeatable command runs the Phase 1 test suite.

### Documentation

- [ ] **DOC-01**: The BIM JSON contract and supported IFC subset are documented
  from the same source used by validation.
- [ ] **DOC-02**: Durable documentation is indexed from `docs/README.md`.

### Text-to-JSON Baseline

- [ ] **TEXT-01**: The project can generate provenance-linked text and BIM JSON
  pairs from approved IFC sources.
- [ ] **TEXT-02**: A structured-output baseline converts natural language into
  BIM JSON 1.0 without generating raw IFC text.
- [ ] **TEXT-03**: Text-to-JSON output is evaluated with field-level,
  collection-level, and document-validity metrics.
- [ ] **E2E-01**: At least one natural-language request completes the validated
  Text-to-JSON-to-IFC pipeline.

## Later Requirements

### Geometric and Relational Fidelity

- **GEO-01**: Preserve exact local placement and orientation.
- **GEO-02**: Preserve opening and filling relationships.
- **GEO-03**: Preserve material assignments and layer details.
- **GEO-04**: Preserve supported topology and connection relationships.

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
| JSON-01 | Phase 1 | Pending |
| JSON-02 | Phase 1 | Pending |
| JSON-03 | Phase 1 | Pending |
| JSON-04 | Phase 1 | Pending |
| JSON-05 | Phase 1 | Pending |
| DOC-01 | Phase 1 | Pending |
| DOC-02 | Phase 1 | Pending |
| IFC-01 | Phase 2 | Pending |
| IFC-02 | Phase 2 | Pending |
| IFC-03 | Phase 2 | Pending |
| IFC-04 | Phase 2 | Pending |
| IFC-05 | Phase 2 | Pending |
| VER-01 | Phase 2 | Pending |
| VER-02 | Phase 2 | Pending |
| VER-03 | Phase 2 | Pending |
| TEXT-01 | Phase 3 | Pending |
| TEXT-02 | Phase 3 | Pending |
| TEXT-03 | Phase 3 | Pending |
| E2E-01 | Phase 3 | Pending |
| GEO-01 | Phase 4 | Deferred |
| GEO-02 | Phase 4 | Deferred |
| GEO-03 | Phase 4 | Deferred |
| GEO-04 | Phase 4 | Deferred |
| AGENT-01 | Phase 5 | Deferred |
| AGENT-02 | Phase 5 | Deferred |
| AGENT-03 | Phase 5 | Deferred |
| MODEL-01 | Phase 6 | Deferred |
| MODEL-02 | Phase 6 | Deferred |
| DEPLOY-01 | Phase 6 | Deferred |

**Coverage:**
- actionable requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after project planning initialization*
