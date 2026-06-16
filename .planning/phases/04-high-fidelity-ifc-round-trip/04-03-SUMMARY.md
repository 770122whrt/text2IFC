# Plan 04-03 Summary: Type Reuse Fidelity

**Date:** 2026-06-16
**Status:** Complete

## What Changed

- Added Formal support for selected wall type reuse:
  - `IfcWallType`
  - `IfcRelDefinesByType`
- Extended relationship validation so `IfcRelDefinesByType` requires:
  - `RelatedObjects`: a non-empty list of occurrence entity IDs
  - `RelatingType`: an entity ID whose IFC class is an `IfcTypeObject`
- Updated the compiler to generate `IfcRelDefinesByType` with IfcOpenShell's
  type API while keeping low-level owner history and STEP IDs compiler-owned.
- Updated extraction so supported `IfcWallType` reuse is preserved as a
  semantic type entity plus an explicit `IfcRelDefinesByType` relationship.
- Kept unsupported type/style relationships as explicit `TYPE_RELATIONSHIP`
  losses.
- Regenerated the IFC2X3 generation profile and BIMNet extraction audit.

## Supported Boundary

Supported now:

- Wall occurrences sharing an `IfcWallType`.
- `IfcRelDefinesByType` where every related object is represented and the
  relating type is a supported type object.

Still unsupported and loss-reported:

- `IfcDoorStyle`
- `IfcWindowStyle`
- unsupported product type classes
- type objects with unsupported representations or unmodeled semantics

## Measured Effect

After regenerating the 25-file BIMNet extraction audit:

- type relationship source facts: 1012
- represented type relationships: 154
- reported type relationship losses: 858
- aggregate loss count after Wave 3: 7467

The loss count can rise when type objects become visible semantic entities,
because their unsupported class/property/representation facts are now accounted
for rather than hidden behind a flattened relationship loss.

## TDD Evidence

- RED `0f7cfe4`: wall type reuse failed because `IfcWallType` and
  `IfcRelDefinesByType` were unsupported.
- GREEN `adad41e`: wall type reuse compiles and reopens with
  `IfcRelDefinesByType`.
- RED `4d74825`: `RelatedObjects` endpoint shape was too permissive.
- GREEN `fe65d8d`: type relationship endpoint shape and type validation.
- RED `29c9997`: extraction did not preserve supported wall type reuse.
- GREEN `a3ade19`: extractor preserves supported wall type reuse and keeps
  unsupported type relationships loss-explicit.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_type_reuse.py -q
python -m pytest tests\fidelity\test_type_reuse.py tests\compiler -q
python -m pytest tests\extractor -q
python -m pytest tests\contract_v2 tests\fidelity\test_type_reuse.py tests\compiler -q
python scripts\bim_json_v2\generate_reference.py --check
python scripts\ifc_pipeline_v2\audit_bimnet.py --write
python scripts\ifc_pipeline_v2\audit_bimnet.py --check-accounting
```

Observed results:

- Type reuse focused tests: 4 passed.
- Type reuse + compiler regression: 50 passed.
- Extractor tests: 10 passed.
- Contract/type/compiler regression: 105 passed.
- BIM JSON 2.0 references are current.
- BIMNet audit check passed for all 25 files.

## Remaining Work

- Decide whether `IfcDoorStyle` and `IfcWindowStyle` should become supported
  in a later Phase 4 wave or remain explicit losses.
- Continue to Wave 4 connection topology fidelity.
