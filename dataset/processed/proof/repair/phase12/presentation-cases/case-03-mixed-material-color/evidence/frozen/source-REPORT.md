# Repair Success Case 03 — Mixed Material + RGB

Status: **PASS**

## Purpose

This proof case is the final appearance-strengthened mixed Repair validation. One IFC2X3 transaction restores six elements across four operation families while preserving structural authority and applying two explicit material/appearance groups to Window/Door occurrences.

## Live authority

- Run ID: `repair-9c96869574ac414bb8af8d857055e0bb`
- Run status: `succeeded`
- Public evaluation: `passed`
- `complete_repair_success = true`
- `successful_artifact_publishable = true`
- Operations: 2 × Window, 2 × Door, 1 × Beam, 1 × Column
- Provider path: genuine live Stage 1 -> target resolution -> genuine live Stage 2 -> Bound ChangeSet 0.6 -> atomic application -> independent evaluation -> publication

## IFC triplet

- `01-original.ifc` — canonical VVO source
- `02-damaged.ifc` — six-target mixed damaged fixture
- `03-repaired.ifc` — successful all-genuine RepairAPI artifact

SHA256 values are frozen in `evidence/frozen/authority.json`. The packaged `03-repaired.ifc` is byte-identical to the authoritative terminal `successful/repaired.ifc`.

## Reopened appearance/material proof

- Window 1 + Door 1: Material `深灰铝合金`, RGB `(0.18, 0.20, 0.22)`
- Window 2 + Door 2: Material `浅橡木`, RGB `(0.72, 0.45, 0.24)`
- Door 1 operation: `SINGLE_SWING_LEFT`
- Door 2 operation: `SINGLE_SWING_RIGHT`
- Beam: exact surviving Beam Type reuse + C30 material authority, without unrelated explicit recolouring
- Column: exact surviving Column Type reuse, without additional material/appearance request
- IFC2X3 preserved
- All 6 public operation evaluations passed
- Common scope / relationship preservation gates passed

## Evidence layout

- `evidence/provider-evidence/` — only this successful all-genuine Stage 1 / Stage 2 Provider evidence
- `evidence/runtime/` — run state, RepairIntent, resolution, Bound ChangeSet, semantic-manifest bundle, terminal evidence, artifact manifest
- `evidence/validation/` — public evaluation, independent reopened validation, intent completeness, and package proof checks
- `evidence/frozen/` — immutable authority/run/hash manifest for this packaged proof

Historical not-publishable runs, retries, cached-completion runs, target indexes, staging candidate, validation caches, and failure evidence are intentionally excluded from this success-case package; they remain in the original working validation directory.
