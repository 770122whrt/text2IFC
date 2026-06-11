# Phase 1: BIM JSON 1.0 Contract and Validator - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning
**Source:** User discussion plus `01-SPEC.md`

<domain>
## Phase Boundary

Phase 1 defines the canonical `bim-json/1.0` document, validates it without
opening IFC files, audits all existing processed JSON artifacts, and publishes
reference documentation from the same machine-readable contract.

IFC generation remains in Phase 2. Natural-language parsing remains in Phase 3.
Precise placement, openings, materials, and topology remain in Phase 4.
</domain>

<decisions>
## Implementation Decisions

### Contract shape

- **D-01:** Use one normalized `bim-json/1.0` document instead of preserving the
  repository's three incompatible JSON shapes.
- **D-02:** Store supported building elements in one `elements` array with a
  required `kind` discriminator, stable `id`, and `storey_id`.
- **D-03:** The Phase 1 hierarchy is one project, one site, one building, one or
  more storeys, and the supported element families listed in `01-SPEC.md`.
- **D-04:** The initial contract accepts `IFC2X3` and explicit
  `MILLIMETRE` length units. Other target schemas and implicit unit conversion
  are rejected.

### Validation

- **D-05:** JSON Schema Draft 2020-12 is the canonical structural contract.
  Python classes must not become a second independently maintained schema.
- **D-06:** Structural errors and semantic errors share one public diagnostic
  shape: `code`, JSON Pointer-like `path`, and `message`.
- **D-07:** IDs are unique across storeys and elements, and every
  `storey_id` resolves to a declared storey.
- **D-08:** Validation is deterministic and never inserts required values.

### Migration and documentation

- **D-09:** Migration reads the existing files in place, writes only under a
  dedicated `dataset/processed/bim-json-1.0/` output root, and reports every
  discovered top-level model as `converted` or `rejected`.
- **D-10:** Out-of-contract source data may be omitted only when the audit
  records the omission. Missing required Phase 1 data rejects the whole model;
  elements are never silently dropped.
- **D-11:** Human reference documentation is rendered from the JSON Schema and
  checked byte-for-byte in tests.

### the agent's Discretion

- Exact Python module boundaries and internal helper names.
- Exact prose wording in generated reference documentation.
- Whether migration diagnostics use dataclasses, typed dictionaries, or plain
  immutable mappings internally, provided serialized output is stable.
</decisions>

<canonical_refs>
## Canonical References

### Product and phase scope

- `.planning/PROJECT.md` - project value, constraints, and phase boundaries.
- `.planning/REQUIREMENTS.md` - Phase 1 requirement IDs.
- `.planning/phases/01-bim-json-1-0-contract-and-validator/01-SPEC.md` -
  acceptance criteria and locked scope.

### Current implementation and data

- `scripts/ifc_pipeline/roundtrip.py` - current informal JSON consumer and its
  silent fallback behavior.
- `dataset/processed/ifc_parsed_data.json` - 25 legacy basic parser records.
- `dataset/processed/ifc_parsed_enhanced.json` - 25 legacy enhanced records.
- `dataset/processed/roundtrip_json/` - 3 round-trip JSON documents.
</canonical_refs>

<specifics>
## Specific Ideas

- Prefer a normalized `elements` array because Text-to-JSON evaluation and
  multi-turn correction can address one stable element shape instead of a
  different top-level collection contract per family.
- Use deterministic generated IDs such as `storey-0001` and `wall-0001` only
  during migration, and record their source in the audit.
- Keep validation independent from IfcOpenShell so invalid model output is
  rejected before compiler execution.
</specifics>

<deferred>
## Deferred Ideas

- IFC2X3 creation and schema validation: Phase 2.
- Text generation, structured LLM output, and Text-to-JSON metrics: Phase 3.
- Exact coordinates, orientation, openings, materials, and topology: Phase 4.
- Multi-turn clarification state: Phase 5.
</deferred>

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Context gathered: 2026-06-11*
