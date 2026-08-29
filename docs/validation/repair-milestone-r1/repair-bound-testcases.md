# Repair Milestone R1 冻结案例规格

## 1. 冻结规则

本文件冻结未来 genuine execution 的用户请求、公开模型、稳定 IFC identity、预期
语义路径和证据义务。`expected` 只供执行后的 evaluator/curator 使用，不得进入
Provider、retrieval、target resolution、Stage 1、Stage 1.5 或 Stage 2 输入。

- 模型 identity、路径和 SHA-256 以
  [模型选择文档](repair-acceptance-model-selection.md) 为准。
- 坐标均为 Storey-local millimetres；source IFC 永不原位修改。
- property case 必须先解析权威 property identity，再做 deterministic
  value/type/unit admissibility；不能用错误值把正确 property 提前过滤掉。
- clarification resume 使用稳定 semantic/authoritative identity；运行时必须重新验证
  identity 仍属于当前 offered set。
- multi-operation case 必须保持单一原子事务；不允许部分发布。
- 下列 request text 是冻结输入。未来若改字，必须形成新的、明确区分的 acceptance run。

## 2. Case inventory

| ID | Difficulty | Model | Shape | Frozen outcome | Primary capability |
|---|---|---|---|---|---|
| E1 | Easy | R1-DPX-ARC | single | success | Window `IsExternal` Boolean |
| E2 | Easy | R1-WRH-ARC | single | success | Door `FireRating` Label |
| E3 | Easy | R1-S65-STR | single | success | Beam `Reference` Identifier |
| E4 | Easy | R1-BW-TALL | single | success | Wall `AcousticRating` Label |
| M1 | Medium | R1-WRH-ARC | single + resume | value correction, then success | property-first resolution + value admissibility |
| M2 | Medium | R1-BW-TALL | single | success | Beam add + generated Type + property |
| M3 | Medium | R1-S65-STR | single | success | Column add + generated Type + orientation + property |
| H1 | Hard | R1-DPX-ARC | multi | atomic success | Beam add + Window property |
| H2 | Hard | R1-WRH-ARC | multi | atomic success | Door + Wall properties |
| H3 | Hard | R1-DPX-ARC | single + resume | target clarification, then success | stable target identity + offered-set validation |
| H4 | Hard | R1-BW-TALL | multi | unsupported, zero mutation | mixed supported/unsupported transaction guard |
| A1 | Capability-driven | R1-S65-STR | single | success | exact existing Beam Type reuse |

## 3. Easy cases

### E1 — Window Boolean property

**Frozen request**

> 将 Level 1 中 GlobalId 为 1hOSvn6df7F8_7GcBWlRRL、Tag 为 147051 的窗设置为外窗。

- Model: `R1-DPX-ARC`
- Target: `IfcWindow` / `1hOSvn6df7F8_7GcBWlRRL` / Tag `147051`
- Exact property: `Pset_WindowCommon.IsExternal`, `IfcBoolean`, value `true`
- Required path: Stage 1 → exact target → retrieval/Top-K → Stage 1.5 → admissibility
  → Stage 2 → Binder → atomic apply → reopen → L0/L1/L2/preservation
- PASS: occurrence property exists with canonical Boolean true; no unintended mutation.

### E2 — Door Label property

**Frozen request**

> 将 Level 4 中 GlobalId 为 3JlX9$$_PCKBNpDob64$5M、Tag 为 439207 的门的防火等级设置为 EI60。

- Model: `R1-WRH-ARC`
- Target: `IfcDoor` / `3JlX9$$_PCKBNpDob64$5M` / Tag `439207`
- Exact property: `Pset_DoorCommon.FireRating`, `IfcLabel`, value `EI60`
- Required path: complete property path through reopen and L0/L1/L2/preservation.
- PASS: exact occurrence property/value is authored; no Type-level or unrelated occurrence mutation.

### E3 — Beam Identifier property

**Frozen request**

> 将 00 begane grond 中 GlobalId 为 1BpQ2K66f13Pyv1xzN7BBN、Tag 为 738548 的梁的构件编号设置为 B-204。

- Model: `R1-S65-STR`
- Target: `IfcBeam` / `1BpQ2K66f13Pyv1xzN7BBN` / Tag `738548`
- Exact property: `Pset_BeamCommon.Reference`, `IfcIdentifier`, value `B-204`
- Required path: complete property path through reopen and L0/L1/L2/preservation.
- PASS: exact occurrence property/value is authored without altering the reused Type.

### E4 — Wall acoustic Label property

**Frozen request**

> 将 Level 1 中 GlobalId 为 0ZBert7zf3GhThdO12NKAr、Tag 为 358471 的墙的隔声等级设置为 Rw 50。

- Model: `R1-BW-TALL`
- Target: `IfcWallStandardCase` / `0ZBert7zf3GhThdO12NKAr` / Tag `358471`
- Exact property: `Pset_WallCommon.AcousticRating`, `IfcLabel`, value `Rw 50`
- Required path: complete property path through reopen and L0/L1/L2/preservation.
- PASS: Stage 1.5 selects the authoritative Wall property and the exact occurrence is updated.

## 4. Medium cases

### M1 — Correct property identity, incompatible raw value, correction resume

**Frozen initial request**

> 将 Level 4 中 GlobalId 为 3JlX9$$_PCKBNpDob64$4w、Tag 为 439243 的门的防火等级设置为 true。

**Frozen resume**

> 改为 EI60。

- Model: `R1-WRH-ARC`
- Target: `IfcDoor` / `3JlX9$$_PCKBNpDob64$4w` / Tag `439243`
- Exact property: `Pset_DoorCommon.FireRating`, `IfcLabel`
- Initial required path: Stage 1 → target → retrieval/Top-K → Stage 1.5 must resolve
  `FireRating` → deterministic admissibility rejects Boolean `true` for the Label contract
  → clarification/value-correction request → no Stage 2 and no mutation.
- Resume required path: same clarification lineage → corrected value `EI60` → offered/property
  identity remains authorized → Stage 2 → Binder → apply → reopen → L0/L1/L2/preservation.
- PASS: initial turn does not become `UNSUPPORTED_PROPERTY` and does not substitute another
  Boolean property; resumed turn authors `FireRating=EI60` only.

### M2 — Beam add, generated Type, Identifier property

**Frozen request**

> 在 Level 2 添加一根新的水平直线矩形梁，中心轴从 (2000, -2000, 3000) mm 到 (8000, -2000, 3000) mm，截面宽 300 mm、高 500 mm。为它创建独立的 Beam Type，并将构件编号设置为 B-NEW-01。

- Model: `R1-BW-TALL`
- Storey: `Level 2` / GlobalId `2nxdYR2RHCDBiKJuiQr1lO`
- Operations: one `add_beam` plus occurrence property
  `Pset_BeamCommon.Reference=IfcIdentifier("B-NEW-01")`
- Type policy: generated exact Beam Type; no unspecified reuse.
- Required path: geometry/unit/Storey preconditions → property retrieval/Stage 1.5 → Stage 2
  exact ChangeSet → Binder → atomic apply → reopen → L0/L1/L2/preservation.
- PASS: exactly one expected Beam occurrence and generated Type relationship; axis/section/storey
  and occurrence property equal the frozen request.

### M3 — Column add, generated Type, orientation, Boolean property

**Frozen request**

> 在 00 begane grond 添加一根新的竖直矩形柱，中心轴底点为 (25000, 60000, 0) mm，顶点为 (25000, 60000, 3000) mm，截面宽 400 mm、深 600 mm，局部宽度方向为 (1, 0)。为它创建独立的 Column Type，并将其设置为承重构件。

- Model: `R1-S65-STR`
- Storey: `00 begane grond` / GlobalId `02GkOQJZz4x9WAhoZkM67S`
- Operations: one `add_column` plus occurrence property
  `Pset_ColumnCommon.LoadBearing=IfcBoolean(true)`
- Type/orientation policy: generated exact Column Type; non-square section preserves explicit
  local width direction `(1,0)`.
- Required path: complete structural + property path through reopen and L0/L1/L2/preservation.
- PASS: one vertical Column with exact endpoints/section/orientation/Storey and property.

## 5. Hard cases

### H1 — Cross-family atomic Beam add + Window property

**Frozen request**

> 在 Level 1 添加一根新的水平矩形梁，中心轴从 (1000, -20000, 3100) mm 到 (7000, -20000, 3100) mm，截面尺寸为 300 × 500 mm，并为它创建独立 Beam Type。同时，将 GlobalId 为 1hOSvn6df7F8_7GcBWlRLx、Tag 为 146885 的窗的防火等级设置为 EI60。两项修改必须在同一个原子事务中完成，全部成功才发布。

- Model: `R1-DPX-ARC`
- Storey: `Level 1` / GlobalId `1xS3BCk291UvhgP2dvNMKI`
- Existing target: `IfcWindow` / `1hOSvn6df7F8_7GcBWlRLx` / Tag `146885`
- Exact property: `Pset_WindowCommon.FireRating`, `IfcLabel`, `EI60`
- Type policy: generated exact Beam Type.
- PASS: Beam and Window change both publish in one transaction; any failure yields neither.

### H2 — Two existing families in one atomic property transaction

**Frozen request**

> 将 Level 4 中 GlobalId 为 1jI3nV6Sn2LfeyEYxROCeh、Tag 为 468036 的门的防火等级设置为 EI60，同时将同层 GlobalId 为 2HaS6zNOX8xOGjmaNi_r5s、Tag 为 187497 的墙的隔声等级设置为 Rw 50。两项修改在同一个原子事务中执行。

- Model: `R1-WRH-ARC`
- Targets: `IfcDoor/1jI3nV6Sn2LfeyEYxROCeh` and
  `IfcWall/2HaS6zNOX8xOGjmaNi_r5s`
- Exact properties: `Pset_DoorCommon.FireRating=IfcLabel("EI60")` and
  `Pset_WallCommon.AcousticRating=IfcLabel("Rw 50")`
- PASS: both exact occurrence properties publish atomically; neither Type nor other occurrences
  change.

### H3 — Natural target ambiguity with stable-identity resume

**Frozen initial request**

> 将 Level 2 中 819 mm × 759 mm 类型的窗设置为外窗。

**Frozen resume**

> 选择 GlobalId 为 1hOSvn6df7F8_7GcBWlS2V、Tag 为 149537 的窗。

- Model: `R1-DPX-ARC`
- Property: `Pset_WindowCommon.IsExternal`, `IfcBoolean`, true
- Initial required path: target resolver returns ambiguous and persists offered identities;
  no property authorization, Stage 2, or mutation occurs yet.
- Resume binding: intended target `IfcWindow/1hOSvn6df7F8_7GcBWlS2V`, Tag `149537`.
  It must be resolved against the currently offered set; no frozen `candidate:N` token is accepted.
- Resume required path: stable target authorization → retrieval/Stage 1.5 → admissibility →
  Stage 2 → Binder → apply → reopen → L0/L1/L2/preservation.
- PASS: only the selected occurrence gets `IsExternal=true`.

### H4 — Mixed supported and unsupported operation guard

**Frozen request**

> 在 Level 5 添加一根受支持的水平矩形梁，中心轴从 (2000, 10000, 3000) mm 到 (8000, 10000, 3000) mm，截面宽 300 mm、高 500 mm，并同时为该梁创建一个 structural analysis node。两项必须作为同一个事务完成。

- Model: `R1-BW-TALL`
- Storey: `Level 5` / GlobalId `2nxdYR2RHCDBiKJuiQqMQj`
- Supported part: rectangular horizontal Beam add.
- Unsupported part: structural analysis node creation is outside the frozen repair registry and
  Stage 1 boundary.
- Required outcome: explicit unsupported-program guard before mutation; no partial Beam creation,
  no Stage 2/apply publication, unchanged source and terminal zero-mutation evidence.
- PASS: the whole transaction is rejected. Creating the Beam alone is a failure.

## 6. Capability-driven case

### A1 — Exact existing Beam Type reuse

**Frozen request**

> 在 00 begane grond 添加一根新的水平直线矩形梁，中心轴从 (25000, 58000, 3000) mm 到 (31000, 58000, 3000) mm，截面宽 500 mm、高 800 mm，并精确复用 GlobalId 为 12jWe1_Rb2cR0ot5ICgwf_、名称为 28_SF_AT_balk vierkant beton:balk vierkant_gen_500x800 (C35/45) 的现有 IfcBeamType。

- Model: `R1-S65-STR`
- Storey: `00 begane grond` / GlobalId `02GkOQJZz4x9WAhoZkM67S`
- Existing Type: `IfcBeamType/12jWe1_Rb2cR0ot5ICgwf_`, exact frozen name above.
- Property path: not applicable; this case exists to close the exact-Type-reuse coverage gap.
- Required path: Stage 1 → exact Type identity/compatibility → Stage 2 → Binder → atomic apply
  → reopen → L0/L1/L2/preservation.
- PASS: exactly one new Beam is related to that existing Type; no duplicate/generated Type and no
  mutation of the reused Type.

## 7. Per-case binding completeness

The detailed sections above freeze exact request, target and geometry. The following tables make the
remaining execution contract explicit for every case.

| Case | Dataset/source | IFC path/schema | Operation families | Capabilities covered | Expected terminal class |
|---|---|---|---|---|---|
| E1 | IFC-Bench / Duplex | dataset/external/ifc-bench/projects/duplex/arc.ifc; IFC2X3 | Window property | exact occurrence; RAG; Stage 1.5; Boolean; preservation | SUCCESS |
| E2 | IFC-Bench / WRH | dataset/external/ifc-bench/projects/west_riverside_hospital/arc_ifc2x3.ifc; IFC2X3 | Door property | exact occurrence; RAG; Stage 1.5; Label | SUCCESS |
| E3 | IFC-Bench / Sixty5 | dataset/external/ifc-bench/projects/sixty5/str.ifc; IFC2X3 | Beam property | exact occurrence; RAG; Stage 1.5; Identifier | SUCCESS |
| E4 | BIM Whale / TallBuilding | dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc; IFC2X3 | Wall property | exact occurrence; RAG; Stage 1.5; Label | SUCCESS |
| M1 | IFC-Bench / WRH | dataset/external/ifc-bench/projects/west_riverside_hospital/arc_ifc2x3.ifc; IFC2X3 | Door property | property-first resolution; invalid value; resume | INADMISSIBLE_VALUE_OR_CLARIFICATION, then SUCCESS |
| M2 | BIM Whale / TallBuilding | dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc; IFC2X3 | Beam add + Beam property | generated Type; geometry; Identifier; atomic apply | SUCCESS |
| M3 | IFC-Bench / Sixty5 | dataset/external/ifc-bench/projects/sixty5/str.ifc; IFC2X3 | Column add + Column property | generated Type; orientation; Boolean; atomic apply | SUCCESS |
| H1 | IFC-Bench / Duplex | dataset/external/ifc-bench/projects/duplex/arc.ifc; IFC2X3 | Beam add + Window property | cross-family multi-operation; generated Type; atomicity | SUCCESS |
| H2 | IFC-Bench / WRH | dataset/external/ifc-bench/projects/west_riverside_hospital/arc_ifc2x3.ifc; IFC2X3 | Door + Wall properties | multi-target; two Label properties; atomicity | SUCCESS |
| H3 | IFC-Bench / Duplex | dataset/external/ifc-bench/projects/duplex/arc.ifc; IFC2X3 | Window property | natural target ambiguity; stable resume; Boolean | CLARIFICATION_THEN_SUCCESS |
| H4 | BIM Whale / TallBuilding | dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc; IFC2X3 | Beam add + unsupported analysis node | mixed supported/unsupported guard; rollback | UNSUPPORTED_ATOMIC_GUARD |
| A1 | IFC-Bench / Sixty5 | dataset/external/ifc-bench/projects/sixty5/str.ifc; IFC2X3 | Beam add | exact existing Type reuse; no duplicate Type | SUCCESS |

| Case | Storey / public binding | Geometry binding | Stage 1.5 | Clarification | Stage 2 | IFC mutation | L0/L1/L2 | Preservation / atomicity |
|---|---|---|:---:|---|---|---|---|---|
| E1 | Window identity; Level 1 | N/A | yes | no | yes | yes | yes | source immutable; single transaction |
| E2 | Door identity; Level 4 | N/A | yes | no | yes | yes | yes | source immutable; single transaction |
| E3 | Beam identity; ground | N/A | yes | no | yes | yes | yes | source immutable; single transaction |
| E4 | Wall identity; Level 1 | N/A | yes | no | yes | yes | yes | source immutable; single transaction |
| M1 | Door identity; Level 4 | N/A | yes | value correction | only after resume | only after resume | after resume | zero initial mutation; single transaction |
| M2 | Storey identity; Level 2 | frozen axis 2000…8000; 300×500 | yes | no | yes | yes | yes | source immutable; single transaction |
| M3 | Storey identity; ground | frozen vertical axis; 400×600; (1,0) | yes | no | yes | yes | yes | source immutable; single transaction |
| H1 | Beam + Window exact identities; Level 1 | frozen axis 1000…7000; 300×500 | yes | no | yes | yes | yes | source immutable; atomic all-or-nothing |
| H2 | Door + Wall identities; Level 4 | N/A | yes | no | yes | yes | yes | source immutable; atomic all-or-nothing |
| H3 | offered Window identities; Level 2 | N/A | after target resume | target identity | only after resume | only after resume | after resume | zero initial mutation; stable offered-set authorization |
| H4 | Storey identity; Level 5 | frozen axis 2000…8000; 300×500 | no | no | no | no | N/A | unchanged source; no partial Beam publication |
| A1 | Storey + BeamType identities; ground | frozen axis 25000…31000; 500×800 | no | no | yes | yes | yes | source immutable; reused Type unchanged |

All successful Stage 2 cases require Binder deterministic-authority equality and Audit evidence.
All property cases name their canonical identity and IFC value type in the detailed sections.
H4 uses explicit N/A downstream states rather than pretending that a rejected transaction produced
a repaired artifact.

## 8. Frozen execution order and stop rule

Future execution order is exactly:

`E1 → E2 → E3 → E4 → M1 → M2 → M3 → H1 → H2 → H3 → H4 → A1`

Before it, the original Plan 07 four-case matrix must be rerun separately on the same final code
version. During either run, a new deterministic or infrastructure defect preserves the failed
attempt and stops the run; no silent patch-and-continue is allowed.
