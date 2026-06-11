# Phase 2: Minimum BIM JSON to IFC2X3 Compiler - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning
**Source:** PRD Express Path (`02-SPEC.md`)

<domain>
## Phase Boundary

Phase 2 compiles validated BIM JSON 1.0 into a minimum, reopenable, schema-valid
IFC2X3 model. It preserves hierarchy, containment, all nine supported element
classes and counts, required basic dimensions, selected properties, and stable
identity mapping.

Exact placement, openings, filling relationships, materials, topology,
georeferencing, language parsing, and agent behavior remain outside this phase.
</domain>

<decisions>
## Implementation Decisions

### Compiler boundary

- **D-01:** Run `validate_document` before importing compiler behavior; invalid
  input returns the existing structured diagnostics and must not create or
  overwrite the requested IFC output.
- **D-02:** Successful file output is written through a temporary file and
  atomically replaces the destination only after the generated model passes
  required verification.
- **D-03:** The public compiler accepts only `bim-json/1.0`, `IFC2X3`, and
  `MILLIMETRE`; it never inserts missing hierarchy, storeys, dimensions, or
  references.

### IFC content

- **D-04:** Preserve the exact project, site, building, and storey names and
  storey elevations, using project-to-site-to-building-to-storey aggregation
  and element-to-storey spatial containment.
- **D-05:** Compile all nine kinds to the corresponding IFC2X3 classes and
  preserve counts without dropping or duplicating elements.
- **D-06:** Required dimensions must be measurable within 1 mm. Stair-flight
  `rise` and `run` are total vertical and total horizontal extents in Phase 2.
- **D-07:** Exact source placement is not represented by BIM JSON 1.0.
  Generated elements may use deterministic synthetic placement as long as
  dimensions and storey containment remain correct.

### Properties and identity

- **D-08:** Preserve each selected property with its original type and value.
  Use compatible IFC2X3 attributes or common property sets first; otherwise
  retain the original value in a deterministic text2IFC property set.
- **D-09:** Derive unique stable IFC GlobalIds from BIM JSON IDs and retain the
  original BIM JSON ID in a retrievable IFC field or property.

### Verification and tests

- **D-10:** Reopen every generated test IFC and verify hierarchy, containment,
  class counts, dimensions, properties, and identity through public verifier
  helpers rather than test-only internal state.
- **D-11:** Run `ifcopenshell.validate` and normalize its results; the complete
  fixture must have zero schema errors and a deliberately invalid IFC fixture
  must produce at least one stable issue.
- **D-12:** Every compiler feature follows RED-GREEN-REFACTOR TDD. The canonical
  commands are `python -m pytest tests/compiler -q` and
  `python -m pytest tests -q`.

### the agent's Discretion

- Exact Python package and module boundaries for compiler and verifier.
- Which documented IfcOpenShell API use cases create each minimum geometry.
- Deterministic synthetic placement spacing and ordering.
- Internal result dataclasses or immutable mappings.
- Exact custom property-set name for values without a standard IFC2X3 target.
- Exact CLI flag spelling and JSON output envelope, provided exit codes and
  atomic-output requirements remain testable.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Locked Phase 2 behavior

- `.planning/phases/02-minimum-bim-json-to-ifc2x3-compiler/02-SPEC.md` -
  requirements, boundaries, dimension semantics, and acceptance criteria.
- `.planning/REQUIREMENTS.md` - IFC-01..05 and VER-01..03 definitions.
- `.planning/ROADMAP.md` - phase goal, dependencies, and deferred fidelity work.

### Canonical input contract

- `schemas/bim-json/1.0/schema.json` - only structural truth for compiler input.
- `src/text2ifc_contract/validation.py` - public structural and semantic gate.
- `tests/contract/fixtures/complete.json` - all-family valid input fixture.
- `docs/reference/bim-json-1.0.md` - generated human contract reference.

### IFC schema and current prototype

- `schemas/ifc/IFC2X3_TC1.exp` - official IFC2X3 TC1 EXPRESS schema.
- `scripts/ifc_pipeline/roundtrip.py` - prototype to replace, including fallback
  behavior that must not cross the canonical compiler boundary.
- `tests/test_json_to_ifc.py` - three existing prototype checks to migrate or
  supersede.
- `.planning/phases/01-bim-json-1-0-contract-and-validator/01-VERIFICATION.md`
  - verified Phase 1 boundary and available regression evidence.
</canonical_refs>

<specifics>
## Specific Ideas

- Use the complete Phase 1 fixture as the primary all-family compiler test.
- Verify dimensions from the reopened IFC, not from compiler-side bookkeeping.
- Keep semantic determinism separate from byte determinism: stable GlobalIds
  and content are required, while STEP header timestamps may differ.
- An invalid input test should pre-create a sentinel output and prove the
  sentinel bytes remain unchanged.
</specifics>

<deferred>
## Deferred Ideas

- Exact local coordinates and orientation - Phase 4.
- Openings and door/window fill relationships - Phase 4.
- Material assignment, layer sets, colours, and styles - Phase 4.
- Detailed stair decomposition and tread/riser topology - Phase 4.
- IFC4/IFC4X3 output - outside the current milestone.
- Natural-language generation and clarification - Phases 3 and 5.
</deferred>

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Context gathered: 2026-06-11 via PRD Express Path*
