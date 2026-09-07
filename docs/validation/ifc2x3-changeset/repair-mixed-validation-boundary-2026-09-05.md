# Repair Mixed Validation Boundary — 2026-09-05

Status: **CLOSED — APPEARANCE-STRENGTHENED ALL-GENUINE PIPELINE PASS**

## Goal

After the two focused restoration cases pass, validate that the Repair pipeline can resolve, bind, author, evaluate, and publish heterogeneous operations together in one real IFC and one RepairAPI transaction:

```text
VVO original.ifc
  -> controlled mixed damage
  -> one damaged.ifc
  -> one user request
  -> one RepairAPI run
  -> Window + Door + Beam + Column operations
  -> one repaired.ifc
  -> independent mixed validation
```

This mixed validation is the final Repair validation stage before Generation appearance validation begins.

## Request terminology

There is only one user input/request. Documentation for this validation uses **user request** or **request text** only.

For current RepairIntent 0.9, user-request provenance is deterministic rather than Provider-named: every provenance/source object with `source_kind: user_request` must use the exact internal locator `reference: request:/text`. Provider-generated alternatives such as `public_request`, `public-request`, or `user-request-1` are invalid under the 0.9 contract. This restores the fixed convention that was present through Intent Prompt v0.7 and was accidentally dropped starting in v0.8.

Private mutation manifests and original-target snapshots are validation-only evidence. They must never be inserted into the Provider request or prompt.

## Source IFC

Canonical source:

- `dataset/external/bimnet/vvo.ifc`
- IFC schema: IFC2X3
- SHA256: `b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc`

VVO is selected because the same source already underlies the focused restoration cases and contains all four required occurrence families.

## Frozen target families

The final mixed validation reuses the already accepted Phase 12 VVO atomic fixture and contains six operations across the four required families:

1. **Window x2** — remove each existing Window together with its Opening, preserving the host Wall; restore through two `add_window_with_opening_to_wall` operations.
2. **Door x2** — remove each existing Door/fill relation while preserving its existing Opening and host Wall; restore through two `fill_existing_opening_with_door` operations.
3. **Beam x1** — remove the existing reconstructable Beam used by the focused structural restoration validation; restore through `add_beam`.
4. **Column x1** — remove the existing reconstructable Column used by the focused structural restoration validation; restore through `add_column`.

Selected existing target identities are inherited from the accepted Phase 11/12 VVO fixture. The first Window/Door pair includes Window `2dYMXn0_5AKRbD_0yUIAqJ` and Door `2IUEnGd5v4Yfg1ZlPtd0qa`; the second pair is the previously accepted second VVO Window/Door target. Structural targets remain Beam `17tPjyQtf2L9JnbXXmcTUF` and Column `1rsYNObuDC4euALdw6WUK4`.

The Window/Door request continues to use request-text geometric targeting rather than deleted object GlobalId/Name targeting. Beam and Column retain their independently verified original Storey/geometry authority.

## Damage construction

Damage may be constructed through the repository's existing official mutation helpers in a bounded sequence, but the final Provider input is exactly one `damaged.ifc` containing all six simultaneous target defects.

Required damage checks:

- both Window and both Door target occurrences plus the Beam and Column are absent;
- both preserved Door Openings remain and have no filling;
- both Window host Walls remain while the selected Windows and their Openings are absent;
- Beam/Column shared Types and target Storeys remain;
- canonical VVO source hash is unchanged;
- no unrelated mutation is introduced outside target-owned relationships.

## Mixed user request

The request must contain six clearly separable operation clauses and enough explicit authority for each registered operation. It may refer to surviving IFC facts such as Type GlobalIds, Storey name, geometry, and explicitly requested Material where required. Window/Door targeting intentionally remains geometric and does not rely on the deleted Window/Door GlobalId or Name. Geometry matching tolerance is a deterministic resolver policy rather than user-request content: when a Stage 1 geometry constraint does not explicitly carry a tolerance, `TargetQuery` supplies the code-side default `0.1 mm`; explicit tolerance values remain authoritative.

The request must not contain private mutation mappings, benchmark-gold labels, or deleted-object facts that are unavailable from the request itself or surviving IFC unless they are deliberately supplied as user input.

## Transaction requirement

PASS requires all six operations to be resolved into one transaction and published together. A partial publish or multiple separate runs does not satisfy this validation.

Expected operation multiset:

```text
add_window_with_opening_to_wall x2
fill_existing_opening_with_door x2
add_beam x1
add_column x1
```

No operation/profile version bump is authorized merely to make the mixed batch run. Any failure must first be classified as request ambiguity, cross-operation conflict, current capability constraint, or implementation defect.

## Independent PASS gates

The final reopened `repaired.ifc` must satisfy all of the following:

- IFC2X3 schema preserved;
- exactly one restored/new occurrence corresponding to each requested family;
- Window has valid Opening/void/fill/host/storey relationships and requested Type/geometry authority;
- Door fills the preserved Opening and has correct Type/operation/host/storey authority;
- Beam and Column restore their original world-space geometry/section/Storey within the existing structural tolerances;
- exact requested/reused Type relations are preserved where specified;
- any explicitly requested Material relationship is present and points to the intended existing `IfcMaterial`;
- occurrence appearance rules from focused Case B remain unchanged and are not accidentally applied to unrelated mixed operations;
- repository system IFC comparator reports no unexpected out-of-scope drift;
- source IFC remains byte-identical;
- RepairAPI status is succeeded, complete, and publishable.

## Evidence package

Final directory:

```text
dataset/processed/ifc-presentation-validation/repair-mixed-20260905/
  REPORT.md
  original.ifc
  damaged.ifc
  repaired.ifc
  request.txt
  evidence/
```

Transient pytest/cache/retry scratch is removed after closure. Private mutation evidence may be retained only under bounded `evidence/mutation/` paths and is never Provider input.

## 2026-09-06 appearance-strengthened follow-up

The mixed request was strengthened to make Door/Window material and appearance observable in the final IFC instead of relying on default grey presentation. The two semantic groups are:

- Window 1 + Door 1: material `深灰铝合金`, explicit RGB `(0.18, 0.20, 0.22)`;
- Window 2 + Door 2: material `浅橡木`, explicit RGB `(0.72, 0.45, 0.24)`.

Beam and Column retain their structural reuse responsibilities: Beam reuses the existing Beam Type and existing C30 material without a new explicit colour; Column reuses the existing Column Type without an additional material or appearance request.

This follow-up exposed three contract defects that were fixed without weakening the preservation gate:

1. **Appearance Draft 0.4 operation envelope** — `ifc-repair-changeset-draft/0.4` incorrectly enumerated only Beam/Column operations. It now uses the same generic operation envelope as the earlier mixed draft contract plus the explicit `appearance` field. Exact target/parameter/appearance authority remains enforced by the existing resolved-authority comparison rather than by benchmark-specific schema branches.
2. **Bound 0.6 legacy semantic-assignment compatibility** — the binder now applies the same legacy assignment-shape normalization to Bound ChangeSet 0.6 that 0.5 already used. This removes canonical-only `scope`/`derivation` fields when the source kind is one of the legacy source kinds, allowing the 0.6 schema's intentionally supported legacy assignment branch to validate correctly.
3. **Door L1 semantic relationship authorization** — Door semantic authoring legitimately emits scoped roles such as `semantic_door_material_relationship`, but the Door L1 comparison authorization had not registered those roles. The Door authorization contract now includes the regular scoped semantic families for psets, quantities, materials, classifications, and their numbered relationship variants. Relationship authorization remains strict: the IFC class must match and the relation must add the current operation's `door` endpoint. No wildcard `IfcRel*` allowance and no bypass of `l1.scope.relations` was added.

Observed failure before the third fix was precisely bounded: damaged-to-candidate comparison contained 24 changed IFC relationships, of which 22 were authorized and only the two newly created Door `IfcRelAssociatesMaterial` relationships failed with `Registry policy does not authorize this role/class/effect`. Re-evaluating the same candidate and the same bound ChangeSet after the Door authorization fix yields **24/24 authorized relationships** and an independent L1 status of **PASS**, with all four common scope checks passing.

The repaired candidate was independently reopened and confirms the requested occurrence presentation/material results rather than merely trusting Provider output:

```text
Window 1  深灰铝合金  RGB (0.18, 0.20, 0.22)
Door 1    深灰铝合金  RGB (0.18, 0.20, 0.22)
Window 2  浅橡木      RGB (0.72, 0.45, 0.24)
Door 2    浅橡木      RGB (0.72, 0.45, 0.24)
```

The historical live run that produced this candidate remains recorded as `not_publishable` because it was evaluated before the Door L1 authorization contract was corrected. That historical result must not be rewritten as a successful live run; the post-fix independent re-evaluation is separate evidence that the candidate itself satisfies the corrected preservation contract.

Focused regression after these fixes:

```text
96 passed
```

covering the independent L1 evaluator, evaluation policy, semantic authoring, and Repair appearance contracts.

### All-genuine closure run

After the contract fixes, the strengthened request was rerun from the public inputs with no cached Stage 1 or Stage 2 Provider output:

- Run ID: `repair-9c96869574ac414bb8af8d857055e0bb`;
- input request hash: `sha256:7af95e2e5cb9145ac697505812f53ad2b60a227e77e848e027f956f48bd708bd`;
- damaged IFC hash: `sha256:4a0116d439bcc286e501f459afb4fe31c9607d9233f18fb373921d991c436e66`;
- genuine live Stage 1 completed;
- all six targets resolved without clarification;
- genuine live Stage 2 completed and produced Bound ChangeSet 0.6;
- atomic application completed;
- public evaluation passed all six operations;
- `complete_repair_success = true`;
- `successful_artifact_publishable = true`;
- terminal run state committed as `succeeded`;
- published IFC schema is IFC2X3;
- published IFC SHA256 is `e93b222a63606f176da74f7ff869fdf860c7eda4e93c2b35d6e85807aae1c68d`.

The command wrapper reached its ten-minute observation limit while the run was finishing, but the same run directory subsequently contained the committed `succeeded` transition and the successful terminal bundle. This is one uninterrupted all-genuine RepairAPI run, not a replay using cached Provider artifacts.

Independent reopen of that published IFC again confirms both requested material/RGB pairs. Machine-readable closure evidence is `evidence/validation-material-color-all-genuine-v6.json`. The successful IFC is promoted to the case-root `repaired.ifc` with the same SHA256.

## Sequencing

```text
Focused Case A PASS
  -> Focused Case B PASS
  -> Repair mixed validation PASS
  -> Repair validation closure
  -> Generation appearance validation document sync
  -> Generation implementation / live validation
```

Do not begin Generation-specific code changes before this mixed Repair validation closes.

2026-09-07 交付入口：[集中 Proof](../../../dataset/processed/proof/repair/phase12/presentation-cases/REPORT.md)；[当前代码与回归边界](ifc-presentation-development-boundary-2026-09-03.md#10-2026-09-07-git-接续状态)。上述历史运行结论不改写。
