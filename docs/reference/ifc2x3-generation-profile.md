<!-- Generated from IFC2X3 registries and capability overlay. Do not edit. -->
<!-- Regenerate with: python scripts/bim_json_v2/generate_reference.py -->

# IFC2X3 Generation Profile

Deterministic Phase 2.5 capability boundary for text2IFC.

## Knowledge Sources

- Official IFC2X3 EXPRESS registry: 980
  declarations and 653 entities.
- Official PSD registry: 317 property sets,
  6 complex properties, and
  1850 simple properties.
- Project capability overlay: one explicit state for every IFC2X3 entity.

EXPRESS is the structural authority and PSD XML is the standard property
authority. The project capability overlay describes implemented behavior; it
does not rewrite official schema facts.

## Capability Counts

| State | Count | Meaning |
| --- | ---: | --- |
| `generate` | 26 | Accepted in Formal BIM JSON and emitted exactly |
| `extract-only` | 2 | Preserved during extraction but cannot compile formally |
| `compiler-only` | 24 | Generated from semantic input, never model-authored |
| `unsupported` | 601 | Reported as Draft/loss content |

## Generate Classes

### Semantic Entities

`IfcBeam`, `IfcBuilding`, `IfcBuildingStorey`, `IfcColumn`, `IfcCovering`, `IfcCurtainWall`, `IfcDoor`, `IfcMember`, `IfcOpeningElement`, `IfcPlate`, `IfcProject`, `IfcRailing`, `IfcRoof`, `IfcSite`, `IfcSlab`, `IfcSpace`, `IfcStair`, `IfcStairFlight`, `IfcWall`, `IfcWallStandardCase`, `IfcWallType`, `IfcWindow`

### Explicit Semantic Relationships

`IfcRelConnectsPathElements`, `IfcRelDefinesByType`, `IfcRelFillsElement`, `IfcRelVoidsElement`

`IfcWallStandardCase` remains exact and is not downgraded to `IfcWall`.
`IfcSpace`, `IfcOpeningElement`, and explicit void/fill endpoints are part of
the initial profile.

## Extract-only Classes

`IfcBuildingElementProxy`, `IfcFurnishingElement`

These classes remain visible in extraction losses and Draft partial documents.
They are never replaced by `IfcBuildingElementProxy` or another generated
class.

## Compiler-only Classes

`IfcApplication`, `IfcArbitraryClosedProfileDef`, `IfcAxis2Placement2D`, `IfcAxis2Placement3D`, `IfcCartesianPoint`, `IfcDirection`, `IfcExtrudedAreaSolid`, `IfcGeometricRepresentationContext`, `IfcLocalPlacement`, `IfcOrganization`, `IfcOwnerHistory`, `IfcPerson`, `IfcPersonAndOrganization`, `IfcPolyline`, `IfcProductDefinitionShape`, `IfcPropertySet`, `IfcPropertySingleValue`, `IfcRectangleProfileDef`, `IfcRelAggregates`, `IfcRelContainedInSpatialStructure`, `IfcRelDefinesByProperties`, `IfcSIUnit`, `IfcShapeRepresentation`, `IfcUnitAssignment`

These are low-level IFC implementation resources. Natural-language or model
output must not author `IfcCartesianPoint`, `IfcDirection`,
`IfcOwnerHistory`, placement resources, representation resources, or
bookkeeping relationships directly.

## Unsupported Boundary

The remaining 601 IFC2X3 entities are explicit
`unsupported` capabilities. Unknown class strings are invalid. A known
non-generate class cannot pass Formal validation and cannot be silently
dropped.

Mapped geometry, arbitrary BRep/tessellation, source materials and layer
composition, reusable types, broad connection topology, furnishing, and MEP
generation remain outside Phase 2.5. Their source facts stay in Draft losses
for later fidelity work.

## Verification Commands

```powershell
python scripts/ifc_knowledge/check_registry.py
python scripts/bim_json_v2/generate_reference.py --check
python scripts/ifc_pipeline_v2/audit_bimnet.py --check-accounting
python -m pytest tests/contract_v2 tests/extractor tests/compiler -q
```
