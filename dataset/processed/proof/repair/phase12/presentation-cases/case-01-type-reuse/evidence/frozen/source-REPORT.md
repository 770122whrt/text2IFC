# Repair Success Case 01 — Exact Type Reuse

Status: **PASS**

## Purpose

This proof case restores one removed Beam from the VVO IFC2X3 fixture while reusing the exact surviving `IfcBeamType`. It validates deterministic structural geometry restoration, exact Type authority, and preservation of unrelated IFC content.

## Live authority

- Run ID: `repair-a8f9a208687a4e6b92f3b2b822e469d3`
- Run status: `succeeded`
- Public evaluation: `passed`
- `complete_repair_success = true`
- `successful_artifact_publishable = true`
- Provider path: live Stage 1 -> target resolution -> live Stage 2 -> bound ChangeSet -> atomic application -> independent evaluation -> publication

## IFC triplet

- `01-original.ifc` — canonical VVO source
- `02-damaged.ifc` — source with the target Beam removed
- `03-repaired.ifc` — successful live RepairAPI artifact

SHA256 values are frozen in `evidence/frozen/authority.json`. The packaged `03-repaired.ifc` is byte-identical to the authoritative terminal `successful/repaired.ifc`.

## Restored Beam

- Original removed Beam: `17tPjyQtf2L9JnbXXmcTUF`
- Repaired Beam: `2fpFNCl9LSbwu0tCr6UKVd`
- Exact reused `IfcBeamType`: `17tPjyQtf2L9JnbXXmcTTd`
- Storey: `1vTeahUkP60PdWqwCTjUuM`
- Section: `455 x 570 mm`
- Storey-local center axis: `(-3316.629521, -3863.522838, -285)` -> `(-3316.629521, -8803.522838, -285)` mm
- Maximum reopened world Body bbox error: approximately `2.63e-7 mm`
- IFC2X3 preserved
- No unexpected out-of-scope drift in the accepted comparison

## Evidence layout

- `evidence/provider-evidence/` — only the authoritative live Stage 1 / Stage 2 Provider evidence
- `evidence/runtime/` — run state, RepairIntent, resolution, bound ChangeSet, semantic manifest, terminal evidence, artifact manifest
- `evidence/validation/` — public evaluation, intent completeness, and package proof checks
- `evidence/frozen/` — immutable authority/run/hash manifest for this packaged proof

No retry runs, failed runs, staging candidate, target index, pytest cache, or offline evidence is included in this success-case package.
