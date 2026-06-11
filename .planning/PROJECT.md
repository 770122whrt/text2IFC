# text2IFC

## What This Is

text2IFC is a research and engineering project that converts natural-language
building requirements into valid IFC building models. The system uses a
validated BIM JSON representation and deterministic IfcOpenShell generation,
with a future multi-turn agent for missing information.

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

### Active

- [ ] Define a versioned BIM JSON contract.
- [ ] Validate BIM JSON before IFC generation.
- [ ] Build a minimum IFC2X3 compiler from the validated contract.
- [ ] Build a Text-to-JSON dataset pipeline and measurable baseline.
- [ ] Complete the first Text-to-JSON-to-IFC end-to-end loop.

### Out of Scope

- IFC generation in Phase 1 - Phase 1 only defines and validates the contract.
- Precise local placement and global coordinates in Phase 2 - deferred to
  the high-fidelity Phase 4.
- Opening and filling relationships in Phase 2 - deferred to Phase 4.
- Direct natural-language-to-IFC generation - BIM JSON remains the contract.
- Fine-tuning before the deterministic compiler and evaluation contract are
  stable.

## Context

- Dataset: 25 IFC2X3 Coordination View models, split into 18 train and 7 test.
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
| Use BIM JSON between text and IFC | Validation and debugging are possible before IFC generation | Pending |
| Target IFC2X3 first | Matches all current source models | Pending |
| Make Phase 1 the unique BIM JSON contract | Stabilize the boundary before compiler and model work | Pending |
| Build the minimum compiler in Phase 2 | Establish deterministic output before Text-to-JSON | Pending |
| Build Text-to-JSON in Phase 3 | Reach an early end-to-end text2IFC baseline | Pending |
| Defer exact placement and openings to Phase 4 | Prevent the minimum compiler from becoming a full reconstruction project | Pending |
| Use TDD and GSD phase artifacts | Keep behavior and planning traceable | Pending |

---
*Last updated: 2026-06-11 after project planning initialization*
