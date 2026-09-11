# Repair Success Case 02 — Explicit Material + RGB

Status: **PASS**

## Purpose

This proof case restores one removed Beam while simultaneously enforcing exact surviving Type reuse, an explicitly requested existing Material, and an explicit occurrence-level RGB appearance.

## Live authority

- Run ID: `repair-510a533e43c94b7083ea8824c2221685`
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

## Restored occurrence

- Exact reused `IfcBeamType`: `17tPjyQtf2L9JnbXXmcTTd`
- Existing occurrence Material: `C_钢筋砼C30`
- Explicit RGB: `(0.92, 0.12, 0.18)`
- Reopened Body RGB: `(0.92, 0.12, 0.18)`
- Repaired Beam: `3wrIf6EXrKQu4gX$SeDa9j`
- Maximum world Body bbox error: approximately `2.63e-7 mm`
- Material identity remains separate from presentation appearance
- Shared Type / Material resources are not recoloured
- IFC2X3 preserved
- Accepted comparison reports no unexpected out-of-scope drift

## Evidence layout

- `evidence/provider-evidence/` — only the authoritative live Stage 1 / Stage 2 Provider evidence
- `evidence/runtime/` — run state, RepairIntent, resolution, bound ChangeSet, semantic manifest, terminal evidence, artifact manifest
- `evidence/validation/` — public evaluation, independent validation, intent completeness, and package proof checks
- `evidence/frozen/` — immutable authority/run/hash manifest for this packaged proof

No superseded appearance run, failed run, staging candidate, target index, pytest cache, or offline evidence is included in this success-case package.
