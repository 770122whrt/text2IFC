# Phase 4: High-fidelity IFC Round Trip - Specification

**Created:** 2026-06-15
**Ambiguity score:** 0.14 (gate: <= 0.20)
**Requirements:** 9 locked

## Goal

Phase 4 raises the text -> BIM JSON -> IFC path from "reopenable output" to
measurably correct generated IFC and then expands source IFC fidelity for
materials, types, topology, complex geometry, and broader product classes with
explicit loss accounting.

## Background

Phase 2.5 made BIM JSON 2.0 a formal IFC2X3 semantic entity graph with
placement, spaces, openings, void/fill relationships, and bounded extrusion
geometry. Phase 3 built the text-to-json dataset and baseline. Phase 5 built a
Chinese-first clarification Agent and a simple-room IFC acceptance artifact.

The post-Phase-5 live Mimo experiment proved that the model can produce formal
BIM JSON 2.0 and a reopenable IFC file. It also exposed a critical quality
gap: the generated IFC can be structurally valid while still being spatially
wrong. In `mimo-live-simple-room-v2`, all four walls exist, but east/west walls
were not rotated and wall rectangle placement used an implicit profile-origin
assumption incorrectly. A viewer may show only three useful walls or disconnected
walls even though schema validation and reopen checks pass.

Phase 4 therefore starts with a generated-IFC correctness gate before expanding
high-fidelity source round-trip behavior. This prevents later material,
topology, and complex geometry work from building on unreliable generated
spatial output.

## Requirements

1. **Generated IFC correctness gate**: Generated demo IFC files must pass
   spatial, relationship, attribute, and IFC-structure checks after BIM JSON
   validation and IFC reopen.
   - Current: Phase 5 checks JSON validity, compile success, and reopen success,
     but it does not prove that walls form a closed room or that openings lie
     on their host walls.
   - Target: Phase 4 Wave 0 adds a reusable generated-IFC quality gate that
     fails malformed room geometry even when IFC opens successfully.
   - Acceptance: The gate fails the current disconnected simple-room geometry
     and passes corrected `simple-room-fixed` and `two-room-suite` artifacts.

2. **Two-case text-json-ifc evidence**: Wave 0 must contain at least two
   complete text -> Agent prompt -> Agent JSON -> IFC cases.
   - Current: `mimo-live-simple-room-v2` contains one successful triple artifact
     but no geometry-correctness report and no second structure.
   - Target: `simple-room-fixed` and `two-room-suite` each include user input,
     provider prompt, raw provider output, candidate BIM JSON, diagnostics,
     markdown report, and compiled IFC.
   - Acceptance: Both case directories contain `input.txt`, `prompt-used.md`,
     `raw-response.txt`, `candidate.json`, `diagnostics.json`, `report.md`, and
     `output.ifc`, and both reports state pass/fail metrics.

3. **Quantified robustness metrics**: Phase 4 must record measurable quality
   outcomes rather than relying on visual inspection.
   - Current: Phase 3 has text-to-json evaluation metrics, but Phase 5 live
     Mimo artifacts do not record spatial correctness, attribute correctness,
     IFC hierarchy correctness, or repair iteration counts as first-class
     metrics.
   - Target: Every Phase 4 generated demo run records parse validity, BIM JSON
     validity, geometry gate pass rate, attribute accuracy, relationship
     accuracy, IFC structure pass rate, compile/reopen success, and iteration
     count.
   - Acceptance: A machine-readable experiment record exists for each Wave 0
     case and a markdown summary reports the metrics and error classes.

4. **Prompt and Agent drift control**: Model/provider output must be constrained
   to BIM JSON 2.0 semantics and rejected when it invents unsupported geometry,
   raw IFC, hidden defaults, or disconnected spatial relations.
   - Current: Prompt v2 can produce a valid simple-room JSON, but it did not
     encode rectangle-profile origin semantics or wall direction constraints.
   - Target: Prompt v3 and provider diagnostics explicitly state wall layout
     conventions, forbid raw IFC/STEP and low-level helper objects, and treat
     geometry-gate failures as repair feedback or Draft clarification targets.
   - Acceptance: Tests prove prompt assets preserve the geometry-output
     contract, and failed geometry checks produce actionable diagnostics rather
     than silent acceptance.

5. **Spatial topology validation**: The quality gate must verify simple
   architectural topology in compiled IFC, not just source JSON fields.
   - Current: BIM JSON validation checks placement vectors and relationship
     endpoints but does not inspect compiled IFC world geometry or wall
     adjacency.
   - Target: The checker derives world bounding boxes or equivalent geometric
     evidence from IfcOpenShell and checks wall orientation, enclosure,
     host-opening fit, door/window placement, and space coverage.
   - Acceptance: A deliberately unrotated east/west wall case fails with stable
     error codes, and corrected cases pass within documented tolerances.

6. **Attribute correctness**: User-visible facts must survive the full path.
   - Current: Door/window dimensions are tested in earlier compiler slices, but
     Phase 5 live artifacts do not compare expected facts against generated IFC
     and JSON in a single report.
   - Target: The gate compares room sizes, wall thickness, storey elevation,
     door/window dimensions, sill height, names, and selected properties against
     per-case expected facts.
   - Acceptance: Reports include expected-vs-actual tables and fail when a
     required fact is missing or numerically outside tolerance.

7. **IFC structure correctness**: Generated IFC must preserve project hierarchy,
   spatial containment, and opening/filling relationships.
   - Current: Reopen success does not prove correct aggregation, containment,
     void/fill endpoints, or product-to-space/storey structure.
   - Target: The gate checks `IfcProject`, `IfcSite`, `IfcBuilding`,
     `IfcBuildingStorey`, `IfcSpace`, product containment, `IfcRelVoidsElement`,
     and `IfcRelFillsElement` endpoints.
   - Acceptance: Missing containment, wrong host wall, or orphaned opening
     produces a failing diagnostic.

8. **High-fidelity source inventory**: Phase 4 must quantify what source IFC
   fidelity exists in the 25 authorized BIMNet files before implementing broad
   support.
   - Current: Phase 2.5 extraction records losses, and Phase 3 projects
     supported-scope targets, but Phase 4-specific fidelity metrics are not
     summarized for materials, types, topology, mapped geometry, BRep,
     tessellation, and broader product classes.
   - Target: A fidelity inventory groups source facts by support strategy:
     preserve now, add in Phase 4, report as loss, or defer.
   - Acceptance: A machine-readable inventory and markdown report cover all 25
     BIMNet files without scene-family leakage or unsupported fact fabrication.

9. **Loss-explicit fidelity expansion**: Materials, type reuse, connection
   topology, complex geometry, and broader product classes must either preserve
   source facts accurately or report losses explicitly.
   - Current: These facts are deferred from Phase 2.5 and omitted from Phase 3
     formal supported-scope targets with sidecars.
   - Target: Phase 4 adds selected support incrementally while retaining the
     no-substitution rule: unsupported BRep, mapped geometry, tessellation, or
     product classes cannot be replaced with boxes or proxies and called
     successful.
   - Acceptance: Each new fidelity feature has RED/GREEN tests, generated
     references or capability metadata, source-side loss accounting, and
     reopened IFC verification where generation is supported.

## Boundaries

**In scope:**

- A Wave 0 generated-IFC correctness gate for text -> BIM JSON -> IFC demos.
- Corrected `simple-room-fixed` and new `two-room-suite` demo artifacts.
- Quantified experiment records and markdown reports for generated demos.
- Prompt v3 and diagnostics that constrain Agent output for geometry-sensitive
  generation.
- IfcOpenShell-based spatial, attribute, relationship, and IFC-structure
  checks for generated output.
- All-25 BIMNet high-fidelity source inventory.
- Incremental support for selected materials, layer sets, type reuse,
  connection topology, complex/mapped geometry, and broader product classes.
- Explicit Draft/loss handling for unsupported source facts.

**Out of scope:**

- Raw STEP/IFC generation by the language model - BIM JSON remains the only
  model output contract.
- Claiming 100 percent BIMNet geometry reconstruction - Phase 4 expands
  fidelity but preserves loss honesty.
- Replacing unsupported BRep, mapped geometry, or tessellation with simplified
  boxes without reporting loss - this would corrupt training truth.
- Phase 6 fine-tuning, deployment, or model serving - Phase 4 produces the
  correctness and fidelity foundation.
- IFC4/IFC4X3 output - Phase 4 continues to target IFC2X3.
- Silent compiler repair of invalid Agent output - repair is allowed only when
  recorded as a diagnostic, prompt iteration, or deterministic transformation
  with provenance.

## Constraints

- IFC2X3 remains the target schema.
- BIM JSON Schema remains the structural truth; any new semantic checks are
  validation/checker layers, not a second structural model.
- Every implementation behavior with defined inputs and outputs follows TDD:
  RED test, GREEN implementation, then refactor.
- Generated artifact directories must not contain live provider secrets,
  request headers, private endpoints, or token values.
- Quality reports must be machine-readable and human-readable.
- Tolerances for geometry checks must be explicit and documented.
- BIMNet data handling must preserve train/validation/test scene-family
  separation from Phase 3.

## Acceptance Criteria

- [ ] Current disconnected simple-room geometry is captured by a failing RED
      test before the fix.
- [ ] `simple-room-fixed` passes parse, BIM JSON validation, compile, reopen,
      spatial topology, attribute, relationship, and IFC-structure checks.
- [ ] `two-room-suite` passes the same checks and includes at least two spaces,
      one shared wall, one external door, one internal door, and two windows.
- [ ] Each Wave 0 case writes input, prompt, raw output, candidate JSON,
      diagnostics, report, and IFC artifacts.
- [ ] Wave 0 reports parse validity, schema validity, geometry gate result,
      attribute accuracy, relationship accuracy, IFC structure result,
      compile/reopen success, and iteration count.
- [ ] Prompt v3 records rectangle-profile center-origin and wall-direction
      conventions and is preserved with an iteration log.
- [ ] All-25 BIMNet Phase 4 inventory records material/type/topology/geometry
      support status without leaking scene families across splits.
- [ ] Every added high-fidelity feature includes source extraction behavior,
      generation behavior where supported, loss behavior where unsupported, and
      reopened IFC verification.
- [ ] Phase 4 final summary reports quantitative improvements, residual error
      classes, and readiness or blockers for Phase 6.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.86 | 0.75 | met | Wave 0 plus fidelity expansion is measurable. |
| Boundary Clarity | 0.78 | 0.70 | met | Generated correctness and source fidelity are separated. |
| Constraint Clarity | 0.78 | 0.65 | met | IFC2X3, no raw IFC, no silent loss, TDD, and secret safety are explicit. |
| Acceptance Criteria | 0.82 | 0.70 | met | Pass/fail checks and metrics are concrete. |
| **Ambiguity** | **0.14** | **<= 0.20** | met | Ready for planning. |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| 1 | Researcher | What did Phase 5 prove and what broke? | Mimo can produce valid JSON/IFC, but generated room geometry can be spatially wrong. |
| 2 | Simplifier | What is the irreducible Phase 4 entry gate? | Fix and measure generated IFC correctness before source high-fidelity expansion. |
| 3 | Boundary Keeper | Should Wave 0 be a Phase 5 patch or Phase 4 prerequisite? | Make it Phase 4 Wave 0 because high-fidelity work depends on correct generated spatial output. |
| 4 | Failure Analyst | What would make a verifier reject the output? | Valid-but-disconnected walls, openings off host walls, wrong attributes, orphaned containment, or unreported losses. |
| 5 | Seed Closer | What additional demo should Wave 0 include? | Add `two-room-suite` to test multiple spaces, shared wall, internal/external doors, windows, and containment. |
| 6 | Seed Closer | What is the project-level objective? | Improve text-json-ifc fault tolerance, lower error rate, and record metrics/experiments continuously. |

---

*Phase: 04-high-fidelity-ifc-round-trip*
*Spec created: 2026-06-15*
*Next step: execute Phase 4 plans in wave order.*
