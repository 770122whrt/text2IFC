# IFC2X3 Restoration Validation Boundary — 2026-09-04

Status: **FROZEN FOR THIS VALIDATION**

## Goal

Validate a real restoration chain, not an additive-only repair:

```text
original.ifc
  -> deterministic damage mutation (remove an existing Beam + occurrence-owned relations)
  -> damaged.ifc
  -> RepairAPI public chain
  -> repaired.ifc
  -> independent reopen + original/damaged/repaired comparison
```

The canonical original IFC is never mutated in place. Damage is created only from a copied/opened model and is source-hash bound.

## Fixed Case 1 — exact Type reuse restoration

Status: **PASS after correcting the public center-axis input.**

The first request incorrectly copied the source Beam's diagnostic `IfcShapeRepresentation.Axis` Z as if it were the Body centroid line. For this VVO Beam that Axis lies on the top face of the 570 mm-high solid. The repair input was therefore corrected only at the request layer from Storey-local center-axis `Z=0` to `Z=-285 mm`; Beam authoring code was not changed.

Final Case 1 gates:

1. `original.ifc -> damaged.ifc` removes one real Beam and its occurrence-owned relations while preserving the shared Type, Storey and source IFC.
2. The corrected user request restores the Beam with the same XY endpoints, length, 455 x 570 mm section and exact existing `IfcBeamType` `17tPjyQtf2L9JnbXXmcTTd`.
3. Original and repaired world-space Body bounding boxes match within `0.01 mm`; observed maximum bbox error is approximately `2.63e-7 mm`.
4. Repository system comparator `text2ifc_ifc_repair.compare.compare_ifc_models` reports `unexpected_changed_ids=[]` and `complete_preservation_success=true` for the authorized restoration scope.
5. Future restoration requests must derive the requested center axis from Body restoration geometry; an IFC `Axis` representation is diagnostic unless independently proven to coincide with the Body centroid line.

## Fixed Case 2 — explicit user colour restoration

Status: **PASS — appearance and occurrence Material restoration both verified in genuine live RepairAPI.**

The user confirmed that full restoration must also restore the deleted Beam's occurrence-level `IfcRelAssociatesMaterial` to the existing `IfcMaterial` named `C_钢筋砼C30`, while keeping the restored occurrence surface RGB at `(0.92, 0.12, 0.18)`. Material identity and presentation colour remain separate authorities. The first live appearance run is retained only as appearance evidence because it omitted the occurrence material relation.

The minimal repair path is public-input authorization, not new inference policy: the Case 2 request must explicitly require reuse of the existing `IfcMaterial` `C_钢筋砼C30`. Existing RepairIntent material intent, semantic `material:*` evidence, `reuse_material` authoring, and `IfcRelAssociatesMaterial` support are reused. Do not add Beam same-Type material cohort inference unless this explicit-input path proves insufficient.

The first explicit-material live retry proved that the complete material contract is already generated correctly, but exposed a provenance canonicalization defect: Stage 1 may emit a public provenance reference such as `public_request`, while executable Material authoring intentionally requires a canonical `request:/...` authority locator. The fix is limited to production-evidence projection: retain the Provider/public provenance reference in the provenance trail, but canonicalize explicit Material `source_ref` to `request:/text` before semantic authoring. This does not change material meaning, Prompt behavior, or Beam capability/version.

This case validates explicit user appearance authority. It does **not** introduce a Repair default palette.

Frozen authority priority remains:

```text
exact Type-owned appearance
  > explicit user appearance
  > authorized existing/reference appearance
  > none
```

Material identity and presentation appearance are separate authorities. A user RGB request may override only a lower-priority reference appearance; it must not replace material identity and must not override exact Type-owned appearance.

To make explicit user colour observable, the selected Type must have no authoritative Type-owned appearance. If same-Type occurrence/reference appearance exists, explicit user appearance must override that reference layer.

### Minimal versioning rule

Version only contracts that actually change. Do **not** bump `beam.add` or its prompt profile merely because the downstream Repair pipeline gains appearance authoring. Reuse the existing Beam operation/profile unless a concrete Stage-1 capability-validation constraint proves that a profile change is required.

Current expected minimum version surface is:

- RepairIntent/body: new version only if an explicit appearance field is added to the public Stage-1 contract;
- RepairIntent prompt: new immutable prompt entry only if the extraction instructions/schema actually change;
- ChangeSet draft/bound schema: new version only if `appearance` becomes a first-class ChangeSet field;
- ChangeSet prompt: reuse the current prompt if it already instructs the Provider to copy the complete resolved operation projection exactly and the supplied schema is authoritative; bump only if prompt text itself must change;
- `beam.add` operation definition/profile: no version bump by default.

Any new prompt asset must be registered in `prompts/agent/registry.json` with its immutable path/hash/inputs, and any new schema version must be registered in its existing loader/version map. Existing released versions remain unchanged. User-request provenance remains attached to `appearance_intent` in RepairIntent; the executable resolved/ChangeSet `appearance` projection contains only `intent_kind` and the numeric RGB components, so Provider Stage 2 copies executable authority rather than duplicating provenance fields.

PASS requires:
- user request -> explicit appearance intent -> resolved authority -> bound ChangeSet appearance -> structural applicator -> IFC presentation assignment;
- exact requested RGB survives IFC2X3 write/reopen;
- geometry, Storey and exact Type relation remain correct;
- material identity remains unchanged unless independently requested;
- no shared Type appearance is mutated merely to colour one restored occurrence.

## Next stage after Repair closure — Generation appearance chain

Generation appearance remains a required follow-on validation and must start only after Case 2 Repair is closed. The Generation stage is **not** part of the current Repair acceptance and must not be mixed into Case 2 evidence.

Frozen next-stage chain:

```text
BIM JSON / generation request
  -> Generation appearance authority selection
  -> compiler / deterministic IFC authoring
  -> IfcSurfaceStyle / material presentation assignment
  -> generated.ifc
  -> independent reopen + appearance/profile/geometry validation
```

The follow-on Generation validation must cover at least: explicit user appearance winning over generated profile selection; explicit `AppearanceProfile`; controlled LLM/profile choice without arbitrary RGB invention; deterministic seeded fallback; coordinated one-run theme behavior; and IFC2X3 reopen verification. It must reuse the shared presentation primitives without changing the frozen Repair authority priority or Repair schemas merely for Generation needs.

No Generation implementation changes are authorized by this document yet; this section fixes ordering and acceptance scope only. A dedicated Generation validation document/report must be synchronized before Generation-specific code changes begin.

## Explicit non-goals

- No Window/Door geometry changes.
- No Agent main-loop redesign.
- No default Repair palette in this validation.
- No mutation of canonical source IFC.
- No rewriting historical accepted R1 Proof.
- No hidden/private mutation facts injected into Provider prompts beyond the explicitly frozen user request.
- No broad `git add .`, reset, clean, or commit/push of unrelated dirty worktree changes.

## Evidence package

Each final case directory must contain at minimum:

```text
REPORT.md
original.ifc
damaged.ifc
repaired.ifc
```

Additional machine evidence may be retained in a bounded `evidence/` subdirectory, but pytest tmp/cache and transient retry directories must be removed after closure.

## Git isolation

This repository is under multi-threaded development. All edits for this validation must be path-scoped. Before any commit, staged content must be reviewed and contain only this validation's paths. Push must not include unrelated local commits or another thread's work.

2026-09-07 交付入口：[集中 Proof](../../../dataset/processed/proof/repair/phase12/presentation-cases/REPORT.md)；[当前代码与回归边界](ifc-presentation-development-boundary-2026-09-03.md#10-2026-09-07-git-接续状态)。上述历史运行结论不改写。
