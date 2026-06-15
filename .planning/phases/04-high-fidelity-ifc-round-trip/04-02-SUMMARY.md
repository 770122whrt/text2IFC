# Plan 04-02 Summary: Material and Layer Fidelity

**Date:** 2026-06-15
**Status:** Complete

## What Changed

- Extended BIM JSON 2.0 entities with optional `materials`.
- Added support for selected `material_layer_set_usage` semantics:
  - layer set name
  - layer direction
  - direction sense
  - offset from reference line
  - one or more named layers with positive millimetre thickness
- Updated the IFC2X3 compiler to emit explicit `IfcMaterial`,
  `IfcMaterialLayer`, `IfcMaterialLayerSet`,
  `IfcMaterialLayerSetUsage`, and `IfcRelAssociatesMaterial` resources from
  semantic material input.
- Updated the extractor to preserve supported wall material layer usages and
  mark represented material relationships in accounting.
- Regenerated the BIM JSON 2.0 reference.
- Regenerated `dataset/processed/bim-json-2.0/extraction-audit.json`.

## Supported Boundary

Supported now:

- `IfcMaterialLayerSetUsage` attached through `IfcRelAssociatesMaterial`.
- Layer names and positive thickness values.
- Layer set name, direction, direction sense, and offset.

Still unsupported and loss-reported:

- `IfcMaterialList`
- material property entities
- material classification relationships
- material definition representations
- material associations whose selected material is not a layer-set usage

## Measured Effect

After regeneration across the 25 authorized BIMNet IFC2X3 files:

- material source facts: 2554
- represented material facts: 1533
- reported material losses: 1021
- aggregate loss count after Wave 2: 6747

This means Phase 4 now preserves a large supported subset of source material
facts while keeping unsupported material constructs explicit.

## TDD Evidence

- RED `eca6a97`: explicit wall material layer generation failed because
  `/entities/4/materials` was unsupported.
- GREEN `20cb5d0`: schema, compiler, and reference support for explicit wall
  material layers.
- RED `1dfeeee`: extraction failed to preserve supported wall material layers.
- GREEN `94b3189`: extractor preserves supported material layers and updates
  accounting.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_materials.py -q
python -m pytest tests\fidelity\test_materials.py tests\compiler -q
python -m pytest tests\fidelity\test_materials.py tests\extractor tests\compiler -q
python scripts\bim_json_v2\generate_reference.py --check
python scripts\ifc_pipeline_v2\audit_bimnet.py --write
python scripts\ifc_pipeline_v2\audit_bimnet.py --check-accounting
python -m compileall src scripts -q
```

Observed results:

- Material focused tests: 2 passed.
- Material + compiler regression: 47 passed.
- Material + extractor + compiler regression: 58 passed.
- BIM JSON 2.0 references are current.
- BIMNet audit check passed for all 25 files.
- compileall passed.

## Remaining Work

- Add support or explicit typed losses for `IfcMaterialList`,
  material properties, classifications, and material representations in later
  fidelity work if metrics justify it.
- Re-run Phase 4 fidelity inventory after additional support waves to track
  represented vs reported source facts.
