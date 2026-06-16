# Plan 04-04 Summary: Connection Topology Fidelity

**Date:** 2026-06-16
**Status:** Complete

## What Changed

- Added selected topology support for `IfcRelConnectsPathElements`.
- Extended Formal relationship validation for:
  - `RelatingElement`
  - `RelatedElement`
  - `RelatingPriorities`
  - `RelatedPriorities`
  - `RelatingConnectionType`
  - `RelatedConnectionType`
- Kept `ConnectionGeometry` unsupported in Formal BIM JSON.
- Updated the compiler to generate reopened IFC2X3
  `IfcRelConnectsPathElements` relationships.
- Updated extraction to preserve supported path-element topology and count
  represented connection relationships.
- Regenerated the IFC2X3 generation profile and BIMNet extraction audit.

## Supported Boundary

Supported now:

- `IfcRelConnectsPathElements` between represented `IfcElement` occurrences.
- Empty or integer priority lists.
- IFC2X3 `IfcConnectionTypeEnum` values: `ATPATH`, `ATSTART`, `ATEND`,
  `NOTDEFINED`.

Still unsupported:

- `ConnectionGeometry`
- other `IfcRelConnects*` specializations unless explicitly added later
- space boundary topology

## Measured Effect

After regenerating the 25-file BIMNet extraction audit:

- connection source facts: 2263
- represented connection facts: 2263
- reported connection losses: 0
- aggregate loss count after Wave 4: 5204

## TDD Evidence

- RED `42edd7b`: path element topology failed as unsupported.
- GREEN `75010ee`: compiler and validator support for
  `IfcRelConnectsPathElements`.
- RED `5d58ae2`: extractor did not preserve path topology.
- GREEN `0556563`: extractor preserves path topology and updates accounting.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_topology.py -q
python -m pytest tests\extractor -q
python -m pytest tests\fidelity\test_topology.py tests\extractor tests\compiler -q
python scripts\bim_json_v2\generate_reference.py --check
python scripts\ifc_pipeline_v2\audit_bimnet.py --write
python scripts\ifc_pipeline_v2\audit_bimnet.py --check-accounting
python -m compileall src scripts -q
```

Observed results:

- Topology focused tests: 2 passed.
- Extractor tests: 10 passed.
- Topology + extractor + compiler regression: 58 passed.
- BIM JSON 2.0 references are current.
- BIMNet audit check passed for all 25 files.
- compileall passed.

## Remaining Work

- Decide whether space boundaries or additional `IfcRelConnects*`
  specializations should be promoted later.
- Continue to Wave 5 complex and mapped geometry fidelity.
