# Plan 04-01 Summary: Fidelity Inventory and Metric Harness

**Date:** 2026-06-15
**Status:** Complete

## What Changed

- Added `text2ifc_fidelity.inventory.build_fidelity_inventory`.
- Added `scripts/ifc_pipeline_v2/fidelity_inventory.py --all --check`.
- Wrote the Phase 4 inventory artifact:
  `dataset/processed/phase4/fidelity-inventory.json`.

## Inventory Scope

- Authorized BIMNet IFC2X3 files represented: 25 / 25.
- Scene-family split counts preserved:
  - train: 17 files
  - validation: 5 files
  - test: 3 files
- SHA-256 verification: all 25 records verified.

## Aggregate Findings

Across the 25 authorized source IFC files:

- material associations: 2554
- material layers: 228
- type relationships: 1012
- connection topology relationships: 4526
- mapped geometry items: 1033
- BRep-related items: 2654
- tessellation / face-based surface items: 125
- openings: 845
- spaces: 189

Top product classes:

- `IfcWallStandardCase`: 1555
- `IfcOpeningElement`: 845
- `IfcDoor`: 446
- `IfcWindow`: 288
- `IfcPlate`: 201
- `IfcSpace`: 189
- `IfcCovering`: 131
- `IfcBeam`: 90
- `IfcColumn`: 88
- `IfcCurtainWall`: 85

Top representation signals:

- `IfcExtrudedAreaSolid`: 5181
- `IfcFacetedBrep`: 1327
- `IfcMappedItem`: 1033
- `IfcFaceBasedSurfaceModel`: 125
- `IfcBooleanClippingResult`: 20

## Planning Feedback

The measured evidence supports the existing Phase 4 ordering:

- Wave 2 material/layer fidelity is high priority because material associations
  are frequent and material layers are present in source IFC.
- Wave 3 type reuse is high priority because 1012 type relationships are
  present.
- Wave 4 topology is high priority because connection relationships are the
  largest measured unsupported category.
- Wave 5 complex/mapped geometry is required because BRep and mapped geometry
  are both common.
- Wave 6 broader class work should prioritize `IfcPlate`, `IfcCovering`,
  `IfcCurtainWall`, `IfcMember`, and residual proxy-like classes after the
  core architectural profile.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_inventory.py -q
python scripts\ifc_pipeline_v2\fidelity_inventory.py --all --check
```

Observed results:

- Fidelity tests: 3 passed.
- Inventory CLI: success true, record_count 25, issues empty.

## Remaining Work

- Add richer per-fact preservation/loss classification as Waves 2-6 implement
  support.
- Recompute this inventory after each fidelity wave and compare aggregate
  unsupported counts.
