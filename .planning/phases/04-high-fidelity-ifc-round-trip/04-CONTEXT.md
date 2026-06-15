# Phase 4: High-fidelity IFC Round Trip - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>

## Phase Boundary

Phase 4 starts by hardening generated IFC correctness for the text -> BIM JSON
-> IFC path, then expands high-fidelity IFC round-trip support. The central
product risk is not merely invalid files; it is valid IFC that encodes the
wrong building. Therefore Phase 4 must add quantitative gates that catch
spatial, relationship, attribute, and structure errors before proceeding to
materials, type reuse, topology, complex geometry, and broader classes.

</domain>

<decisions>

## Implementation Decisions

### D-01 Generated Correctness First

Phase 4 Wave 0 precedes all high-fidelity source work. It fixes and measures
generated demo IFC correctness because source fidelity is not meaningful if the
generation path cannot produce a simple spatially correct room.

### D-02 Two Demo Cases

Wave 0 uses two required demo cases:

- `simple-room-fixed`: one rectangular room with four enclosing walls, one
  south-wall door, and one north-wall window.
- `two-room-suite`: two adjacent rooms with a shared wall, one external door,
  one internal door, and two windows.

### D-03 Quantified Metrics

Every generated demo records parse validity, BIM JSON validity, compile
success, reopen success, geometry gate pass/fail, attribute accuracy,
relationship accuracy, IFC structure pass/fail, repair iteration count, and
error classes.

### D-04 Agent Drift Guardrail

The model/provider layer must output BIM JSON 2.0 semantics only. It must not
output raw IFC, STEP text, low-level IFC helper objects, hidden defaults, or
unverified geometry repairs. Geometry failures become repair feedback or Draft
clarification targets.

### D-05 Profile Origin Convention

Wave 0 records and tests the rectangle-profile convention: generated rectangle
profiles are interpreted around their local profile origin. Wall layout must
therefore use explicit center-origin or representation-local position rules,
not an unspoken lower-left-corner assumption.

### D-06 Checker Over Visual Judgment

Viewer inspection is useful but not sufficient. Acceptance depends on
IfcOpenShell-based checks over world geometry, relationships, attributes, and
spatial structure.

### D-07 No Silent Fidelity Loss

Materials, type objects, connection topology, mapped geometry, BRep,
tessellation, and unsupported classes must be preserved accurately or reported
as losses. Box substitution is not allowed unless explicitly represented as a
lossy proxy and excluded from formal fidelity claims.

### D-08 Dataset Split Integrity

Phase 4 continues to respect Phase 3 scene-family splits. Any benchmark or
training-related export must preserve train/validation/test separation.

### D-09 Continuous Experiment Records

Prompt changes, live model behavior, failed checks, repair loops, and metric
changes are durable project artifacts. A future session must be able to inspect
what failed, what changed, and whether error rates improved.

</decisions>

<canonical_refs>

## Canonical References

### Phase Contracts

- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-SPEC.md` -
  Defines BIM JSON 2.0 semantic graph, placement, geometry, Draft/loss
  boundary, and no-substitution rules.
- `.planning/phases/03-text-to-json-dataset-and-baseline/03-SPEC.md` -
  Defines split-safe text-to-json targets and evaluation boundaries.
- `.planning/phases/05-multi-turn-clarification-agent/05-SPEC.md` - Defines
  Agent state, missing facts, provider boundary, and final IFC demo acceptance.
- `.planning/phases/04-high-fidelity-ifc-round-trip/04-SPEC.md` - Locks Phase
  4 requirements and acceptance criteria.

### Current Evidence

- `dataset/processed/agent-demo/mimo-live-simple-room-v2/` - Live Mimo
  text/JSON/IFC artifact that validates and compiles but exposed the need for
  geometry topology checks.
- `prompts/agent/mimo-bim-json-v2.md` - Current live prompt that succeeded at
  formal JSON but did not encode all geometry-layout conventions.
- `prompts/agent/mimo-bim-json-iterations.md` - Prompt iteration and live test
  history.

### Code and Tests

- `src/text2ifc_compiler/geometry.py` - IFC geometry and placement emission.
- `src/text2ifc_contract/placement.py` - Parent-relative placement validation
  and world-transform derivation.
- `scripts/agent/run_clarification_demo.py` - Existing deterministic simple
  room Agent demo.
- `tests/compiler/test_v2_geometry.py` - Current placement and geometry
  compiler checks.
- `tests/agent/test_clarification_demo.py` - Current Agent demo tests.

### Data and Reports

- `dataset/splits/bimnet-scene-splits.json` - Phase 3 split manifest.
- `dataset/processed/bim-json-2.0/extraction-audit.json` - Phase 2.5 source
  extraction audit.
- `docs/architecture/text2json-rag-finetune-decision.md` - Notes that
  material, type, topology, and complex geometry fidelity remain Phase 4.

</canonical_refs>

<specifics>

## Specific Ideas

- Add `scripts/ifc_quality/check_generated_ifc.py` for reusable quality gates.
- Store case expectations as JSON sidecars under each generated demo case.
- Generate a markdown report per case and a phase-level experiment summary.
- Add prompt v3 with explicit wall layout conventions and geometry repair
  feedback fields.
- Use stable diagnostic codes for geometry failures, for example:
  `WALL_NOT_ORTHOGONAL_TO_EXPECTED_AXIS`, `ROOM_ENCLOSURE_OPEN`,
  `OPENING_OUTSIDE_HOST_WALL`, `MISSING_SPATIAL_CONTAINMENT`,
  `ATTRIBUTE_MISMATCH`.
- Preserve every failed live run as an experiment record if it is secret-safe.

</specifics>

<deferred>

## Deferred Ideas

- Full IFC4/IFC4X3 output.
- Model fine-tuning and deployment.
- 100 percent exact BIMNet geometry reconstruction.
- Browser-based 3D review UI for generated IFC. Phase 4 may use screenshots or
  manual viewer notes, but automated acceptance is through IfcOpenShell checks.

</deferred>

---

*Phase: 04-high-fidelity-ifc-round-trip*
*Context gathered: 2026-06-15*
