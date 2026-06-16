# Plan 04-05 Summary: Complex and Mapped Geometry Fidelity

**Date:** 2026-06-16
**Status:** Complete

## What Changed

- Added tests proving unsupported complex geometry losses explicitly record
  that no substitution occurred.
- Extended Draft loss records with optional:
  - `source_item_class`
  - `substitution`
- Updated extraction so unsupported geometry losses include:
  - the source IFC representation item class, such as `IfcMappedItem` or
    `IfcFacetedBrep`
  - `substitution: "none"`

## Capability Decision

No mapped, BRep, tessellated, boolean, or surface-model geometry was promoted
to Formal BIM JSON in this wave.

Reason:

- Phase 4 requires exact-enough fidelity, not box substitution.
- Current compiler support is still bounded to rectangle and closed-polygon
  extrusions.
- The 04-01 inventory shows complex geometry is common, but this wave did not
  establish a safe minimal representation that can round-trip without
  misleading geometry claims.

Therefore unsupported complex geometry remains Draft/loss content.

## Supported Boundary

Supported now:

- Auditable unsupported-geometry loss records with no-substitution metadata.

Still unsupported:

- `IfcMappedItem`
- `IfcFacetedBrep`
- `IfcFaceBasedSurfaceModel`
- tessellated geometry
- boolean clipping/result geometry
- arbitrary BRep or mesh-like geometry

## TDD Evidence

- RED `05517ed`: unsupported complex geometry losses lacked
  `substitution` and `source_item_class`.
- GREEN `ea832d2`: extractor and Draft schema record no-substitution metadata.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_complex_geometry.py -q
python -m pytest tests\fidelity\test_complex_geometry.py tests\extractor -q
python scripts\bim_json_v2\generate_reference.py --check
python scripts\ifc_pipeline_v2\audit_bimnet.py --write
python scripts\ifc_pipeline_v2\audit_bimnet.py --check-accounting
python -m compileall src scripts -q
```

Observed results:

- Complex geometry focused tests: 1 passed.
- Complex geometry + extractor regression: 11 passed.
- BIM JSON 2.0 references are current.
- BIMNet audit check passed for all 25 files.
- compileall passed.

## Remaining Work

- If future metrics justify it, add exact support for a narrow mapped or BRep
  subset with reopened IFC verification.
- Continue to Wave 6 broader classes, all-25 audit, and Phase 6 readiness.
