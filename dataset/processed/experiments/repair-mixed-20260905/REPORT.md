# Repair mixed validation — PASS

Status: **PASS**

This case validates one atomic IFC2X3 Repair transaction containing six operations on the VVO fixture:

- 2 × `add_window_with_opening_to_wall`
- 2 × `fill_existing_opening_with_door`
- 1 × `add_beam`
- 1 × `add_column`

## Final authoritative run

The current strengthened request is now closed by a new all-genuine end-to-end run:

- Run ID: `repair-9c96869574ac414bb8af8d857055e0bb`
- Evidence root: `evidence/live-material-color-all-genuine-v6/runs/repair-9c96869574ac414bb8af8d857055e0bb/`
- Provider path: genuine live Stage 1 -> target resolution -> genuine live Stage 2 -> bound ChangeSet -> atomic application -> independent evaluation -> publication
- Final status: `succeeded`
- `complete_repair_success = true`
- `successful_artifact_publishable = true`
- Public evaluation: 6 / 6 operations passed
- Published IFC SHA256: `e93b222a63606f176da74f7ff869fdf860c7eda4e93c2b35d6e85807aae1c68d`

Independent evidence: `evidence/validation-material-color-all-genuine-v6.json`.

The successful IFC from this run is copied to `repaired.ifc`. The earlier all-genuine run `repair-03976bd1ccdc4224bcc3ea77cffb550b` remains historical authority for the previous, weaker mixed request only.

## Historical baseline reopen / preservation validation

Historical evidence for the previous weaker request: `evidence/validation-genuine-final.json`

- IFC schema after reopen: `IFC2X3`
- Window 1: requested dimensions, new Opening, correct fills/voids relationships
- Window 2: requested dimensions, new Opening, correct fills/voids relationships
- Door 1: preserved existing Opening, `SINGLE_SWING_LEFT`, requested dimensions
- Door 2: preserved existing Opening, `SINGLE_SWING_RIGHT`, requested dimensions
- Beam: exact `IfcBeamType` `17tPjyQtf2L9JnbXXmcTTd`
- Beam: occurrence-level material `C_钢筋砼C30`
- Beam: no focused-case red appearance leakage
- Beam world-bbox max error: `2.634901186127081e-07 mm`
- Column: exact `IfcColumnType` `1rsYNObuDC4euALdw6WUK0`
- Column: no occurrence-level material
- Column world-bbox max error: `3.041602525399867e-07 mm`
- Comparator: `complete_preservation_success = true`
- Comparator: `unexpected_changed_ids = []`

## Fixture provenance

- `original.ifc` is the VVO source fixture.
- `damaged.ifc` is the final mixed damaged fixture with the two target Windows removed, the two target Doors removed while their retained Openings remain available for filling, and the target Beam and Column removed.
- `request.txt` is the single public six-operation Repair request.

## Intermediate diagnostic runs

Earlier directories under `evidence/live/`, `evidence/live-final/`, and `evidence/live-completion/` are retained only as diagnostic history. In particular, `live-completion` used a previously captured genuine Stage-1 result to avoid the execution-window limit while validating the downstream chain. It is **not** the final authority.

The previous request's final authority remains under `evidence/live-genuine-final/`; the current strengthened request's authority is the all-genuine v6 run listed at the top of this report.

## Appearance-strengthened follow-up — 2026-09-06

The baseline PASS above remains the authoritative result for the earlier mixed request. A strengthened follow-up request was then used to verify explicit Door/Window material and appearance instead of accepting visually grey default presentation.

Strengthened request groups:

- Window 1 + Door 1: `深灰铝合金`, RGB `(0.18, 0.20, 0.22)`;
- Window 2 + Door 2: `浅橡木`, RGB `(0.72, 0.45, 0.24)`.

The live downstream run that reached application/evaluation was:

- Run ID: `repair-b617c986a35c406ca6af40054e7f3d7e`
- Evidence root: `evidence/live-material-color-completion-v4/runs/repair-b617c986a35c406ca6af40054e7f3d7e/`
- Historical terminal status: `not_publishable`
- Historical failure gate: `l1.scope.relations`

That historical `not_publishable` result was retained rather than rewritten. Root-cause inspection showed 24 damaged-to-candidate relationship changes: 22 were already authorized, while exactly two new Door `IfcRelAssociatesMaterial` relationships were rejected because the Door L1 authorization contract did not register the applicator role `semantic_door_material_relationship`.

The implementation was corrected by aligning Door L1 relationship authorization with the generic scoped semantic-authoring roles. The fix remains fail-closed: relationship class, operation role, and Door endpoint are still checked exactly; no wildcard relationship allowance and no `l1.scope.relations` bypass were introduced.

Post-fix evidence is recorded in `evidence/validation-material-color-policy-fix.json`.

Re-evaluating the **same candidate and same bound ChangeSet** with the corrected contract gives:

- relationship authorization: `24 / 24`;
- `l1.scope.created-roots`: PASS;
- `l1.scope.modified-roots`: PASS;
- `l1.scope.removed-roots`: PASS;
- `l1.scope.relations`: PASS;
- independent L1 overall: PASS.

Independent IFC reopen also confirms the requested occurrence presentation/material values:

```text
Window 1  深灰铝合金  RGB (0.18, 0.20, 0.22)
Door 1    深灰铝合金  RGB (0.18, 0.20, 0.22)
Window 2  浅橡木      RGB (0.72, 0.45, 0.24)
Door 2    浅橡木      RGB (0.72, 0.45, 0.24)
```

The follow-up also exposed and fixed two earlier downstream contract mismatches: Draft ChangeSet 0.4 now supports the generic mixed operation envelope plus appearance, and Bound ChangeSet 0.6 now preserves the legacy semantic-assignment normalization compatibility already supported by its schema.

Focused regression after the complete set of fixes:

```text
96 passed
```

covering `test_l1_evaluator.py`, `test_evaluation_policy.py`, `test_semantic_authoring.py`, and `test_repair_appearance_contract.py`.

## Contract fixes exercised by this case

The final run uses the current RepairIntent 0.9 / Intent Prompt v0.12 contracts, including:

- canonical `user_request` provenance reference `request:/text`;
- code-side default geometry matching tolerance of `0.1 mm` when the user does not explicitly provide a tolerance;
- explicit Door formal-enum provenance for `SINGLE_SWING_LEFT` / `SINGLE_SWING_RIGHT`;
- structural Material intent contract: `intent_kind=material`, `name=Material`, non-empty string material identity in `value`;
- Repair appearance authority separation from material identity.

Repair mixed validation is therefore closed. The next validation stage is the Generation appearance chain.
