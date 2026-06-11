# Phase 1: BIM JSON 1.0 Contract and Validator - Specification

**Created:** 2026-06-11
**Ambiguity score:** 0.13 (gate: <= 0.20)
**Requirements:** 7 locked

## Goal

Replace the repository's incompatible informal JSON structures with one
versioned `bim-json/1.0` contract that accepts valid Phase 1 building data,
rejects invalid data with field-level diagnostics, and classifies every
existing JSON artifact as converted or explicitly incompatible.

## Background

The repository currently contains multiple JSON shapes:

- `dataset/processed/ifc_parsed_data.json`
- `dataset/processed/ifc_parsed_enhanced.json`
- `dataset/processed/roundtrip_json/*.json`

The structures use different property names and element representations.
`scripts/ifc_pipeline/roundtrip.py` accepts dictionaries directly and relies on
fallback values, so there is no stable boundary between future Text-to-JSON
output and IFC generation. Phase 1 creates that boundary before compiler,
agent, or fine-tuning work continues.

## Requirements

1. **Canonical version identifier**: Every canonical document identifies
   itself as `bim-json/1.0`.
   - Current: Existing JSON files identify IFC schema versions but do not
     identify a BIM JSON contract version.
   - Target: One canonical document format has a required contract version and
     an explicit IFC target schema.
   - Acceptance: A document without `bim-json/1.0`, or with an unsupported
     contract version, fails validation before downstream processing.

2. **Phase 1 domain coverage**: The contract represents the minimum data needed
   by the Phase 2 compiler.
   - Current: Supported fields vary between parser outputs and round-trip JSON.
   - Target: The contract covers project, site, building, units, storeys, and
     the supported element families: walls, columns, beams, slabs, doors,
     windows, stairs, stair flights, and roofs. It includes basic dimensions
     and the selected properties `is_external`, `load_bearing`, and
     `predefined_type` where applicable.
   - Acceptance: One complete fixture containing every supported element family
     validates successfully, while a fixture using an unsupported element
     family is rejected with a field path and reason.

3. **Identity and reference integrity**: Contract-owned objects have stable
   identifiers and valid references.
   - Current: Existing JSON commonly relates elements to storeys by display
     name, and duplicate names are not prevented.
   - Target: Storeys and elements have unique IDs; element-to-storey references
     use IDs; all references resolve within the document.
   - Acceptance: Duplicate IDs and missing storey references each produce a
     deterministic validation failure that identifies the offending field.

4. **Field-level validation diagnostics**: Invalid input produces structured,
   actionable errors.
   - Current: Invalid data reaches IfcOpenShell calls or receives fallback
     values, producing late or silent failures.
   - Target: Validation returns a collection of errors containing a machine
     code, field path, and human-readable message.
   - Acceptance: Tests for a missing required field, wrong type, invalid enum,
     non-positive dimension, duplicate ID, and unresolved reference each
     assert the corresponding error code and field path.

5. **No silent invention of required data**: Required building information is
   never created by an implicit default.
   - Current: `roundtrip.py` supplies fallback names, dimensions, and a default
     storey during IFC generation.
   - Target: Required contract fields must be supplied by the producer or
     reported as missing. Optional fields are explicitly marked in the
     contract.
   - Acceptance: Removing each required field from a valid fixture causes
     validation to fail; no validator or migration result inserts a required
     value without recording its provenance.

6. **Existing artifact migration audit**: Existing project JSON is converted
   to BIM JSON 1.0 or rejected explicitly.
   - Current: The three existing JSON sources cannot be consumed through one
     interface.
   - Target: Every top-level model in
     `ifc_parsed_data.json`, `ifc_parsed_enhanced.json`, and
     `roundtrip_json/*.json` receives a migration result with source,
     disposition, and diagnostics. Successful results validate as BIM JSON
     1.0.
   - Acceptance: A repeatable migration audit exits successfully, reports a
     disposition for every discovered model, validates every converted result,
     and contains no unclassified model or uncaught exception.

7. **Discoverable single-source documentation**: Human documentation and
   machine validation describe the same contract.
   - Current: Methodology notes and Python dictionaries describe overlapping
     but inconsistent data shapes.
   - Target: The machine-readable contract is canonical; generated or checked
     reference documentation lists the supported fields, required status,
     types, enums, and constraints. The documentation is linked from
     `docs/README.md`.
   - Acceptance: A documentation consistency check fails when the checked
     reference differs from the machine-readable contract, and the current
     reference passes that check.

## Boundaries

**In scope:**

- `bim-json/1.0` version and target IFC schema metadata
- project, site, building, units, and storey data
- supported Phase 1 element families
- basic dimensions and selected common properties
- unique IDs and storey references
- deterministic validation errors
- migration audit for all current processed JSON sources
- indexed contract reference documentation
- automated tests for every required behavior

**Out of scope:**

- IFC file generation - implemented in Phase 2 after the contract is stable
- exact placement and orientation - implemented in Phase 4
- openings, filling relationships, materials, and topology - implemented in
  Phase 4
- natural-language parsing or LLM calls - implemented in Phase 3
- clarification conversations - implemented in Phase 5
- external IFC4 or IFC4X3 conversion into the IFC2X3 truth set - the newly
  downloaded samples are cross-schema test inputs only

## Constraints

- The canonical contract version is `bim-json/1.0`.
- The initial target IFC schema value is `IFC2X3`.
- Length units are explicit in the document; no implicit unit conversion is
  allowed.
- Validation must run without opening or writing an IFC file.
- New behavior follows RED-GREEN-REFACTOR TDD.
- Existing source JSON is never overwritten by migration.
- Validation and migration must be deterministic for identical input.

## Acceptance Criteria

- [ ] A complete fixture containing every supported element family validates.
- [ ] Missing contract version and unsupported contract version are rejected.
- [ ] Missing required fields are rejected without inserted fallback values.
- [ ] Wrong types, invalid enums, and non-positive dimensions return field-level
  errors.
- [ ] Duplicate IDs and unresolved storey references return deterministic
  errors.
- [ ] Every existing processed JSON model is reported as converted or rejected.
- [ ] Every converted existing model validates as `bim-json/1.0`.
- [ ] The migration process does not modify source JSON files.
- [ ] Contract reference documentation is linked from `docs/README.md`.
- [ ] The documentation consistency check passes.
- [ ] The complete Phase 1 test command exits with code 0.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.94 | 0.75 | Met | One contract and validator outcome |
| Boundary Clarity | 0.90 | 0.70 | Met | Compiler, fidelity, text, and agent work separated |
| Constraint Clarity | 0.82 | 0.65 | Met | Version, target schema, units, TDD, and determinism locked |
| Acceptance Criteria | 0.82 | 0.70 | Met | Eleven pass/fail criteria |
| **Ambiguity** | **0.13** | **<= 0.20** | **Met** | Ready for planning |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| 1 | Researcher | What should be built before Text-to-IFC model work? | Stabilize structured JSON before model work |
| 2 | Simplifier | Full fidelity or minimum loop first? | Use a minimum staged route |
| 2 | Simplifier | One contract or compatibility with multiple shapes? | Establish one `bim-json/1.0` contract |
| 3 | Boundary Keeper | Where does Text-to-JSON belong? | Independent Phase 3 before the agent and fine-tuning |
| 3 | Boundary Keeper | Where does source-level IFC fidelity belong? | Dedicated Phase 4 |
| 4 | Failure Analyst | How should external data enter the project? | License and provenance review before use |
| 4 | Failure Analyst | What happens to incompatible existing JSON? | Explicit rejection report, never silent omission |

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Spec created: 2026-06-11*
*Next step: Phase 1 planning and TDD task decomposition*
