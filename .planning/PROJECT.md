# text2IFC

## What This Is

text2IFC is a research and engineering project that converts natural-language
building requirements into valid IFC building models. The system uses a
validated BIM JSON representation and deterministic IfcOpenShell generation,
with a first multi-turn clarification Agent for missing information.

## Core Value

Produce IFC models that are structurally valid, inspectable, and traceable to
explicit user requirements instead of generating fragile IFC text directly.

## Requirements

### Validated

- IFC2X3 source files can be opened with IfcOpenShell.
- Existing structured JSON can generate IFC2X3 files.
- Storey elevation, selected wall properties, and door/window dimensions have
  automated tests.
- Large IFC and research files are published through Git LFS.
- The Phase 3 Text-to-JSON-to-IFC baseline loop is complete.
- The Phase 5 Chinese-first clarification Agent demo writes a reopenable IFC2X3
  file.

### Active

- [x] Define and validate BIM JSON 1.0.
- [x] Build a minimum IFC2X3 compiler from the validated contract.
- [x] Define BIM JSON 2.0 as an IFC2X3-aligned semantic entity graph.
- [x] Build deterministic IFC2X3 declaration and property-set registries from
  official buildingSMART sources.
- [x] Extract supported ground truth from authorized IFC with explicit losses.
- [x] Build a Text-to-JSON dataset pipeline and measurable baseline.
- [x] Complete the first Text-to-JSON-to-IFC end-to-end loop.
- [x] Complete the first multi-turn clarification Agent demo to IFC.
- [x] Establish generated-IFC correctness gates for spatial, content,
  attribute, relationship, and IFC-structure quality.
- [x] Preserve selected high-fidelity IFC material/type/topology details and
  report unsupported complex geometry as explicit losses.
- [ ] Build multi-agent prompt traceability, then expand approved data, compare
  model approaches, and package deployment.
- [ ] Build an interactive Chinese-first CLI that lets the user participate in
  the real Mimo multi-agent clarification loop and produces a traceable IFC.

### Out of Scope

- IFC generation in Phase 1 - Phase 1 only defines and validates the contract.
- Precise local placement and global coordinates were outside completed
  Phase 2 and are now assigned to inserted Phase 2.5.
- Opening and filling relationships were outside completed Phase 2 and are
  now assigned to inserted Phase 2.5.
- Direct natural-language-to-IFC generation - BIM JSON remains the contract.
- Fine-tuning before the deterministic compiler and evaluation contract are
  stable.

## Context

- Dataset: 25 authorized BIMNet IFC2X3 models. Existing 18/7 file folders are
  source organization only; model splits must be rebuilt by scene family.
- External fixtures: 10 CC BY 4.0 buildingSMART IFC4/IFC4X3 samples for
  cross-schema and relationship testing.
- IFC schema: `schemas/ifc/IFC2X3_TC1.exp`.
- Current prototype: `scripts/ifc_pipeline/roundtrip.py`.
- Current tests: `tests/test_json_to_ifc.py`.
- IfcOpenShell 0.8.5 is available through the project-local dependency path
  `.deps/python312` in the current development environment.
- Existing scripts and Chinese documentation contain encoding inconsistencies
  and should not be treated as authoritative contracts.

## Constraints

- **Compatibility**: Phase 1 targets IFC2X3 because all current dataset files
  declare IFC2X3.
- **Reliability**: New behavior follows TDD with a demonstrated failing test
  before implementation.
- **Data**: The current 25 models are insufficient for reliable end-to-end
  model fine-tuning.
- **Generation**: IFC output is created through IfcOpenShell, not raw string
  concatenation.
- **Publishing**: IFC, PDF, and ZIP files remain under Git LFS.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Use BIM JSON between text and IFC | Validation and debugging are possible before IFC generation | Adopted |
| Target IFC2X3 first | Matches all current BIMNet source models | Adopted |
| Make JSON Schema the unique BIM JSON structural truth | Stabilize the boundary before compiler and model work | Adopted |
| Build the minimum compiler in Phase 2 | Establish deterministic output before Text-to-JSON | Complete |
| Make Phase 2.5 a breaking BIM JSON 2.0 contract | IFC class identity, placement, relationships, and Draft semantics cannot be added safely as a minor revision | Adopted |
| Build official-source IFC2X3 knowledge first | Schema correctness cannot depend on model memory or retrieval | Adopted |
| Build Text-to-JSON in Phase 3 | Reach an early end-to-end text2IFC baseline | Complete |
| Build multi-turn clarification in Phase 5 | Missing natural-language facts should produce questions, not fabrication | Complete |
| Start Phase 4 with generated-IFC correctness gates | A reopenable IFC can still be spatially wrong; high-fidelity work needs a reliable text-json-ifc gate first | Adopted |
| Defer materials, complex geometry, and topology to Phase 4 | Keep generated correctness separate from full IFC source fidelity | Adopted |
| Start Phase 6 with prompt registry and multi-agent traceability | Fine-tuning and deployment decisions need reproducible prompt inputs, repair attempts, metrics, and audits | Adopted |
| Insert Phase 6.2 for interactive CLI before service/API work | The user needs to participate in clarification turns and inspect intermediate inputs/outputs before API packaging | Adopted |
| Use TDD and GSD phase artifacts | Keep behavior and planning traceable | Adopted |

---
*Last updated: 2026-06-23 after Phase 6.2 interactive CLI planning*
