# Phase 2: Minimum BIM JSON to IFC2X3 Compiler - Specification

**Created:** 2026-06-11
**Ambiguity score:** 0.12 (gate: <= 0.20)
**Requirements:** 9 locked

## Goal

Compile any valid `bim-json/1.0` document into an IFC2X3 file whose hierarchy,
supported element counts, basic dimensions, selected properties, and source
identity mapping are automatically verifiable.

## Background

Phase 1 now provides a canonical BIM JSON contract, deterministic validation,
and a complete fixture covering all nine supported element families. The
repository also has a prototype `create_ifc_from_json` function and three tests
for storey elevation, wall common properties, and door/window dimensions.

The prototype consumes an older informal JSON shape, inserts fallback values,
supports only partial geometry, and does not validate input or IFC schema
conformance. Phase 2 replaces that prototype boundary with a compiler that
accepts only validated BIM JSON 1.0 and produces a minimum, inspectable IFC2X3
model. Exact source placement and relational fidelity remain separate work.

## Requirements

1. **Validated compiler boundary**: Compilation accepts only valid
   `bim-json/1.0` input.
   - Current: The prototype consumes informal dictionaries and supplies
     fallback hierarchy, storey, and geometry values.
   - Target: The compiler runs the Phase 1 validator first and returns
     structured validation diagnostics without creating or replacing an IFC
     output when input is invalid.
   - Acceptance: A valid complete fixture compiles; missing required data,
     duplicate IDs, and unresolved storey references each fail before IFC
     creation, and an existing output file is not overwritten.

2. **Reopenable IFC2X3 output**: Successful compilation creates an IFC2X3 file
   that IfcOpenShell can reopen.
   - Current: The prototype can write selected IFC2X3 models but has no
     canonical compiler API or atomic-output guarantee.
   - Target: One public compiler API and CLI produce an atomically replaced IFC
     file with `FILE_SCHEMA(('IFC2X3'))`.
   - Acceptance: IfcOpenShell reopens the output, reports schema `IFC2X3`, and
     the output contains one `IfcProject`.

3. **Hierarchy and containment fidelity**: Project, site, building, storeys,
   and element-to-storey references are preserved.
   - Current: The prototype may create a default storey or attach unresolved
     elements to the first storey.
   - Target: Names and storey elevations match BIM JSON exactly; project, site,
     building, and storeys use the correct IFC aggregation chain; every
     element is spatially contained in its referenced storey.
   - Acceptance: Automated inspection recovers the exact hierarchy names,
     elevations, storey count, and element containment mapping from the
     complete fixture.

4. **Supported element class and count fidelity**: All nine BIM JSON element
   kinds compile to their corresponding IFC2X3 entity classes.
   - Current: Prototype geometry and creation behavior is incomplete for
     columns, beams, slabs, stairs, stair flights, and roofs.
   - Target: `wall`, `column`, `beam`, `slab`, `door`, `window`, `stair`,
     `stair_flight`, and `roof` create `IfcWall`, `IfcColumn`, `IfcBeam`,
     `IfcSlab`, `IfcDoor`, `IfcWindow`, `IfcStair`, `IfcStairFlight`, and
     `IfcRoof` respectively, without dropping or duplicating elements.
   - Acceptance: Per-class IFC entity counts exactly equal per-kind BIM JSON
     counts for the complete fixture and for empty-family fixtures.

5. **Basic dimension fidelity**: Every supported element has measurable
   geometry or schema attributes that preserve its required BIM JSON
   dimensions.
   - Current: The prototype creates wall geometry and door/window overall
     dimensions but omits most other family geometry.
   - Target: Wall, column, beam, slab, door, window, stair, stair flight, and
     roof dimensions can be recovered from the generated IFC within 1 mm.
     For Phase 2, stair-flight `rise` and `run` mean total vertical and total
     horizontal extents.
   - Acceptance: Family-specific tests compare every required source dimension
     with generated IFC measurements and pass at an absolute tolerance of
     1 mm.

6. **Selected property fidelity**: Phase 1 selected properties are preserved
   without coercion or silent loss.
   - Current: Only wall `is_external` and `load_bearing` have prototype tests.
   - Target: `is_external`, `load_bearing`, and `predefined_type` values allowed
     by the BIM JSON kind can be retrieved unchanged from the generated IFC.
     Standard IFC2X3 attributes or common property sets are used when
     compatible; otherwise the original string remains retrievable through a
     deterministic text2IFC property.
   - Acceptance: Parameterized tests set every allowed selected property and
     recover the same value and type from the reopened IFC.

7. **Traceable stable identity**: BIM JSON object IDs map reproducibly to IFC
   identities.
   - Current: Prototype entities receive generated identities unrelated to BIM
     JSON IDs.
   - Target: Project, site, building, storey, and element IFC `GlobalId` values
     are deterministically derived from BIM JSON IDs, while the original ID is
     retrievable from the IFC object.
   - Acceptance: Compiling the same document twice produces the same
     BIM-ID-to-GlobalId mapping, all GlobalIds are unique, and each original
     BIM JSON ID is recoverable.

8. **IFC schema-level verification**: Generated output passes repeatable
   IFC2X3 validation.
   - Current: Existing tests reopen files and inspect selected values but do
     not run the installed IfcOpenShell validation API.
   - Target: A verifier runs `ifcopenshell.validate` against every generated
     test file and reports normalized validation issues.
   - Acceptance: The complete fixture produces zero schema validation errors;
     a deliberately invalid IFC fixture proves the verifier detects errors.

9. **TDD and repeatable phase command**: Every compiler behavior is introduced
   by a demonstrated RED test and included in one repeatable regression
   command.
   - Current: Three prototype tests exist, but they target the informal JSON
     consumer and do not cover all Phase 2 requirements.
   - Target: Phase 2 tests are organized around the canonical compiler and
     verifier, with RED and GREEN commits recorded per plan.
   - Acceptance: `python -m pytest tests/compiler -q` and
     `python -m pytest tests -q` both exit with code 0 after implementation.

## Boundaries

**In scope:**

- Public BIM JSON 1.0 to IFC2X3 compiler API
- File-oriented compiler CLI with validation failure diagnostics
- IFC project, site, building, storey hierarchy and spatial containment
- Correct IFC classes and counts for all nine supported element kinds
- Minimum measurable geometry for required family dimensions
- Selected common properties and deterministic fallback property storage
- Stable BIM JSON ID to IFC GlobalId mapping
- IfcOpenShell schema-level verification and normalized diagnostics
- Atomic output replacement and full automated regression coverage

**Out of scope:**

- Exact local coordinates, orientation, or source placement - Phase 4
- Wall openings and door/window filling relationships - Phase 4
- Material assignments, layers, colours, and styles - Phase 4
- Structural connections, topology, and detailed stair decomposition - Phase 4
- Georeferencing and global coordinates - Phase 4
- IFC4 or IFC4X3 output - the current compiler target is IFC2X3
- Natural-language parsing, clarification, or model calls - Phases 3 and 5
- Byte-identical IFC STEP files - semantic identity and content are required,
  while header timestamps and serialization details may differ

## Constraints

- IfcOpenShell 0.8.5 is the compiler and verification runtime.
- The compiler must consume the Phase 1 validator rather than duplicate BIM
  JSON structural checks.
- Length input and output use explicit millimetres; no implicit unit conversion
  is permitted.
- Required dimensions and hierarchy values must never receive fallback data.
- Generated geometry may use deterministic synthetic placement because exact
  placement is outside this phase, but placement must not change measured
  dimensions or storey containment.
- No compiler path may mutate the input BIM JSON document.
- The complete Phase 2 test suite must finish within 60 seconds on the current
  development machine.

## Acceptance Criteria

- [ ] Invalid BIM JSON returns structured diagnostics and leaves no new or
  overwritten IFC output.
- [ ] The complete fixture compiles to a reopenable IFC2X3 file.
- [ ] Project, site, building, storey names, elevations, and aggregation match.
- [ ] Every generated element is contained in its referenced storey.
- [ ] IFC class counts match all nine BIM JSON element-kind counts.
- [ ] Every required family dimension is recoverable within 1 mm.
- [ ] Every selected property is recoverable unchanged.
- [ ] BIM JSON IDs map to unique, stable IFC GlobalIds and remain recoverable.
- [ ] IfcOpenShell validation reports zero errors for the complete fixture.
- [ ] A deliberately invalid IFC file is rejected by the verifier.
- [ ] The compiler CLI writes atomically and uses stable exit codes.
- [ ] Phase-specific and complete repository test commands exit with code 0.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.93 | 0.75 | Met | One validated compiler outcome |
| Boundary Clarity | 0.92 | 0.70 | Met | Fidelity work remains explicitly deferred |
| Constraint Clarity | 0.83 | 0.65 | Met | Runtime, units, tolerance, and no-fallback rules locked |
| Acceptance Criteria | 0.84 | 0.70 | Met | Twelve automated pass/fail criteria |
| **Ambiguity** | **0.12** | **<= 0.20** | **Met** | Ready for implementation discussion and planning |

## Post-Verification Discovery

Phase 2 correctly met its locked minimum-compiler scope using deterministic
synthetic placement. A later audit of 25 BIMNet and 10 buildingSMART IFC files
found that BIM JSON 1.0 cannot represent explicit IFC class identity, source
placement, spaces, or opening/filling relationships. Those facts do not
invalidate this completed specification; they define the inserted BIM JSON
2.0 Phase 2.5 prerequisite for spatial Text-to-JSON training.

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| Auto 1 | Researcher | What exists and what is missing? | Reuse IfcOpenShell and prior tests, replace informal JSON boundary |
| Auto 2 | Simplifier | What is the irreducible compiler? | Hierarchy, nine classes, basic dimensions, selected properties |
| Auto 3 | Boundary Keeper | What remains outside Phase 2? | Exact placement, openings, materials, topology, and language work |
| Auto 4 | Failure Analyst | What failures invalidate the result? | Fallback data, partial output, lost elements/properties, schema errors |
| Auto 5 | Seed Closer | How are stair-flight dimensions interpreted? | `rise` and `run` are total extents in Phase 2 |

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Spec created: 2026-06-11*
*Next step: implementation decisions and Phase 2 planning*
