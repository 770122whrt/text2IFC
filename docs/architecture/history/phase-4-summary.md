# Phase 4 Summary: High-fidelity IFC Round Trip

**Date:** 2026-06-16
**Status:** Complete - verified 2026-06-16

## Executive Decision

Phase 4 establishes enough correctness and fidelity infrastructure to start
Phase 6 model/data experiments, but only with a supported-scope contract:

- Natural language and providers must output BIM JSON 2.0 semantics, not raw
  IFC, STEP, or low-level compiler objects.
- Formal targets may include only facts that BIM JSON 2.0 can validate and the
  IFC2X3 compiler can generate.
- Unsupported source facts must remain in Draft/loss sidecars.
- Full BIMNet source-equivalent generation is not ready because mapped,
  BRep, tessellated, boolean, and surface-model geometry are still reported as
  losses instead of reconstructed.

## What Phase 4 Added

### Generated IFC correctness gate

Wave 0 added deterministic generated-IFC quality checks for:

- parse validity
- BIM JSON 2.0 validity
- IFC compile and reopen
- project/site/building/storey/space structure
- wall count, orientation, thickness, and room enclosure
- opening host fit
- door and window dimensions
- selected attributes and relationships
- artifact secret scanning

The known disconnected simple-room output is rejected with stable diagnostics.
The corrected `simple-room-fixed` and `two-room-suite` demos pass the gate.

### Prompt and experiment control

Prompt v3 records the wall-layout rules learned from the live Mimo failure:

- rectangle profiles are center-origin profiles in local representation space
- product `ObjectPlacement` and representation `position` are separate
- east/west walls must be rotated or otherwise oriented correctly
- provider output remains BIM JSON 2.0 only

The generated demo artifacts now preserve prompt, input, raw response,
candidate JSON, diagnostics, markdown report, metrics, and IFC output.

### All-25 BIMNet fidelity inventory

Wave 1 created a phase-specific inventory for all 25 authorized IFC2X3 files,
preserving scene-family split metadata and SHA-256 verification.

The current extraction audit covers all 25 files and reports balanced
represented-plus-reported accounting.

## Quantitative Results

Current all-25 extraction audit:

| Category | Source | Represented | Reported | Represented rate |
|---|---:|---:|---:|---:|
| Entities | 5308 | 4444 | 864 | 83.72% |
| Relationships | 16926 | 15046 | 1880 | 88.89% |
| Properties | 18758 | 17607 | 1151 | 93.86% |
| Representations | 6382 | 4509 | 1873 | 70.65% |
| Materials | 2554 | 1533 | 1021 | 60.02% |
| Types | 1012 | 154 | 858 | 15.22% |
| Connections | 2263 | 2263 | 0 | 100.00% |

Current loss counts:

| Loss kind | Count |
|---|---:|
| MAPPED_GEOMETRY | 1031 |
| MATERIAL_ASSOCIATION | 1021 |
| CLASS_CAPABILITY | 864 |
| TYPE_RELATIONSHIP | 858 |
| UNSUPPORTED_GEOMETRY | 505 |
| UNSUPPORTED_PROPERTY_VALUE | 485 |
| FACETED_BREP_GEOMETRY | 314 |
| MISSING_REPRESENTATION | 102 |
| BOOLEAN_GEOMETRY | 20 |
| SURFACE_GEOMETRY | 3 |
| UNSUPPORTED_RELATIONSHIP | 1 |

## Supported Fidelity Boundary

Supported in Formal BIM JSON 2.0 and IFC2X3 generation:

- project/site/building/storey/product semantic graph
- parent-relative placement
- `IfcSpace`
- `IfcOpeningElement`
- `IfcRelVoidsElement`
- `IfcRelFillsElement`
- selected rectangle and closed-polygon extrusions
- representation-local `position`
- selected scalar properties
- selected wall material layer-set usage
- `IfcWallType`
- `IfcRelDefinesByType` for selected wall type reuse
- `IfcRelConnectsPathElements`
- broad generated product classes already marked `generate`, including common
  Beam, Column, Slab, Covering, Member, Plate, CurtainWall, Railing, Stair,
  StairFlight, Wall, Door, Window, Space, Opening, Site, Building, and Storey
  classes

Reported as explicit Draft/loss content:

- extract-only product classes such as `IfcBuildingElementProxy` and
  `IfcFurnishingElement`
- unsupported type/style relationships
- unsupported material association shapes
- mapped geometry
- faceted BRep and broader BRep-like geometry
- tessellated and face/surface model geometry
- boolean clipping/result geometry
- non-scalar property values
- missing supported Body representation

Wave 5 and Wave 6 make no-substitution explicit: unsupported complex geometry
and extract-only product classes are not replaced with fabricated boxes or
proxies.

## Phase 6 Readiness

Phase 6 can start for:

- supported-scope text-to-BIM-JSON training and evaluation
- clarification-Agent repair loops using BIM JSON 2.0 validation and generated
  IFC quality gates
- baseline versus fine-tune comparison on supported-scope targets
- deployable service packaging for the supported generation profile

Phase 6 must not claim:

- full BIMNet source IFC reconstruction
- exact mapped/BRep/tessellated geometry recovery
- complete material/type/style fidelity
- hidden default filling for missing user facts

Recommended Phase 6 entry condition:

1. Train/evaluate only against formal supported-scope targets.
2. Keep source-loss sidecars linked to every target.
3. Report fidelity and geometry-gate metrics separately.
4. Treat Draft records as clarification/evaluation data, not Formal gold.
5. Use generated IFC quality gates as blocking deployment checks.

## Final Verification

Final Phase 4 gates passed on 2026-06-16:

- Full repository regression: 337 passed.
- Focused IFC quality, Agent, and compiler regression: 89 passed.
- Phase 4 acceptance, complex geometry, and extractor regression: 12 passed.
- `simple-room-fixed` generated IFC gate passed.
- `two-room-suite` generated IFC gate passed.
- Direct generated IFC checks for both geometry-gate artifacts passed with no
  issues.
- `python -m compileall src scripts -q` passed.
- Geometry-gate artifact secret scan reported 0 findings across 16 files.
- All-25 extraction audit accounting passed.
- Phase 4 fidelity inventory check reported 25 records and no issues.

## Residual Risks

- Complex geometry remains the largest fidelity gap.
- Type reuse is currently narrow and wall-focused.
- Material support preserves selected wall layer-set usage but still reports
  many unsupported material association forms.
- Broad product class generation is bounded by the current extrusion profile;
  non-extrusion geometry remains loss-explicit.
- Full regression can be slow on Windows because IFC extraction repeatedly
  opens 25 source files.
