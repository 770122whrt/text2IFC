# Repair Milestone R1 当前能力声明

## 1. 判定口径

本声明从当前工作树的生产注册与实现抽取，不用旧 PLAN 代替实现事实：

- 默认注册入口：`src/text2ifc_ifc_repair/operations/__init__.py:18`
- 操作合同：`src/text2ifc_ifc_repair/registry.py:40`
- target resolver：`src/text2ifc_ifc_repair/target_query.py:112`
- property runtime：`src/text2ifc_knowledge/property_runtime.py:99`
- Stage 1.5：`src/text2ifc_ifc_repair/property_resolution_stage.py:43`
- deterministic admissibility：`src/text2ifc_ifc_repair/property_admissibility.py:358`
- `ExactPropertyIntent`：`src/text2ifc_ifc_repair/property_intent.py:32`
- ChangeSet Binder：`src/text2ifc_ifc_repair/changesets.py:142`
- atomic orchestration：`src/text2ifc_ifc_repair/orchestrator.py:165`
- reopen/publish：`src/text2ifc_ifc_repair/apply.py:264`
- L1/L2 evaluator：`src/text2ifc_ifc_repair/evaluation.py:803`
- fail-closed release：`src/text2ifc_ifc_repair/release_decision.py:1`

状态含义：

- `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE`：当前生产合同和离线 seams 支持，并被本冻结
  案例覆盖，可进入后续 genuine acceptance；尚不等于已通过。
- `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE`：实现存在，但本 R1 集没有覆盖或
  当前证据不足，不纳入最终 R1 声明。
- `NOT_SUPPORTED`：当前注册合同明确拒绝或没有注册生产操作。

## 2. Component capability table

| Family | Operation | Supported target | Geometry / operation capability | Important constraints | Type support | Property support | Unsupported boundary | R1 status |
|---|---|---|---|---|---|---|---|---|
| Beam | `add_beam` | `IfcBuildingStorey` | Storey-local straight horizontal centre axis；unrotated rectangular section | IFC2X3；no grid/curve/section rotation/analysis node；same-axis overlap fail-closed | deterministic generated `IfcBeamType`；exact existing Type；unspecified selection path exists | new Beam occurrence may carry explicit scalar intents；existing Beam through occurrence edit | I/H/round/arbitrary/variable sections、grid、curve、structural analysis | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |
| Column | `add_column` | `IfcBuildingStorey` | Storey-local straight vertical centre axis；rectangular section；non-square requires explicit width direction | IFC2X3；base-Storey containment；no automatic Storey split/grid/curve/analysis | deterministic generated `IfcColumnType`；exact existing Type；unspecified selection path exists | new Column occurrence may carry explicit scalar intents；existing Column through occurrence edit | sloped/curved、multi-Storey auto split、structural analysis | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |
| Window add | `add_window_with_opening_to_wall` | straight `IfcWall` | create Opening + Window + void/fill topology | bounded opening interval；millimetre intent；no curved wall | generated `IfcWindowStyle` or exact `IfcWindowStyle`/`IfcWindowType` | explicit Window occurrence scalar intents | curved/unsupported host；shared Type mutation | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` |
| Window edit | `set_occurrence_properties` | existing `IfcWindow` | no geometry mutation | occurrence-direct `IfcPropertySingleValue` only | Type graph must remain unchanged | authoritative scalar PSD properties | Type-owned mutation、quantities、complex/list/table properties | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |
| Door add | `add_door_with_opening_to_wall` | straight `IfcWall` | create Opening + Door + void/fill + Storey containment | supported formal operation: single swing left/right or `NOTDEFINED` | generated/exact `IfcDoorStyle` | explicit Door occurrence scalar intents | other formal operation enums are intent-visible but production policy rejects them | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` |
| Door fill | `fill_existing_opening_with_door` | unfilled `IfcOpeningElement` | preserve Opening and add Door/fill relation | Opening must void one straight Wall and have no filling | generated/exact `IfcDoorStyle` | explicit Door occurrence scalar intents | replace an existing filling；unsupported host geometry | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` |
| Door edit | `set_occurrence_properties` | existing `IfcDoor` | no geometry mutation | occurrence-direct single values | shared Type unchanged | `Pset_DoorCommon` and other class-applicable authoritative scalar records | Type mutation/non-scalar | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |
| Wall edit | `set_occurrence_properties` | existing `IfcWall` / `IfcWallStandardCase` | property-only；no Wall add/geometry edit | occurrence-direct single values | shared Type unchanged | `Pset_WallCommon` scalar records | add/move/resize Wall；type-level edit | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |
| Opening | `add_opening_to_wall` | straight `IfcWall` | create unfilled Opening + void relation | bounded interval；explicit position/width/height/sill | N/A | no Opening property intent claim in R1 | filling element、curved Wall | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` |
| Generic occurrence property | `set_occurrence_properties` | Beam/Column/Door/Wall/WallStandardCase/Window | deterministic direct Pset write; copy-on-write where needed; preserves non-property state | `IfcPropertySingleValue`、explicit request、occurrence scope | never mutates shared Type | alias-free authority + Stage 1.5 + admissibility | other IFC classes/scopes/templates | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` |

## 3. System-level capability declaration

| Capability | Classification | Concrete reason / path | Frozen coverage |
|---|---|---|---|
| deterministic target resolution | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | hard class/Storey/GlobalId constraints and deterministic score/margin in `target_query.py:112-151` | all cases; H3 exercises ambiguity |
| exact target identity | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | reliable public `IfcRoot.GlobalId` is a hard constraint | E1–E4, M1, H1, H2 |
| generated Type | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | `generated_type_authority` and versioned templates; handler creates and binds one Type | M2, M3, H1 |
| exact existing Type reuse | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | `_explicit_prototype` resolves reliable Type identity; `ensure_bound_type` rejects missing/wrong class and leaves Type graph unchanged | A1 |
| unspecified Type reuse with clarification | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` | `selection_required` and `_type_candidates` exist, but no R1 genuine case is frozen; some public Type records lack requested dimension facts | none |
| property semantic retrieval | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | alias-free class/scope/authorable filtering then BGE-M3/Qdrant Top-K | E1–E4, M1–M3, H1–H3 |
| Stage 1.5 candidate selection | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | Provider may select only offered candidate or clarify/unsupported; canonical executable identity stays program-owned | same property cases |
| clarification | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | target ambiguity and value incompatibility produce explicit fail-closed checkpoints | M1, H3 |
| clarification/resume | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | API persists lineage and validates answer against current offered candidates | M1 correction, H3 stable GlobalId answer |
| unsupported-operation rejection | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | structural intent capability rejects analysis/nodes before ChangeSet mutation | H4 |
| unsupported-property handling | `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` | empty/non-authoritative resolution fails closed, but no separate R1 unsupported-property case is added | none |
| invalid/incompatible property value handling | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | value/type/unit checks occur after canonical property resolution (`property_admissibility.py:271-297`) | M1 |
| `ExactPropertyIntent` construction | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | code binds authority-owned Pset/property/value type and request-owned value/scope/provenance | all property cases |
| multi-operation ChangeSet | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | binder accepts an ordered operation set and reconstructs executable authority | H1, H2 |
| cross-family multi-operation ChangeSet | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | registry definitions share one transaction while preserving per-operation profiles/authority | H1, H2 |
| atomic execution | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | orchestrator applies once to candidate, reopens/evaluates, then promotes | H1, H2, H4 guard |
| fail-closed rollback / zero mutation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | no final artifact on apply/evaluation/unsupported failure; source hash is rechecked | M1 pre-correction, H4 |
| Binder deterministic-authority equality | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | Stage 2 Draft is bound against resolved target/parameters/semantic assignments and cannot override them | M2, M3, H1, H2 |
| IFC2X3 reopen | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | temporary output must reopen as IFC2X3 before `os.replace` | every success/resume success |
| L0 evaluation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | Audit and independent collection validation check artifact/source/declared mutation scope | all success; zero-mutation terminals |
| L1 evaluation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | reopened IFC structural/topology/property and source-immutability checks | every success/resume success |
| L2 evaluation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | operation evaluation policies measure semantic facts from reopened IFC | every success/resume success |
| preservation / unintended-mutation evaluation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | global comparator plus per-operation authorization and occurrence identity signatures | all cases |
| private-evidence isolation | `SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` | prompt forbidden outputs, production-boundary redaction and live evidence scans exclude pristine/Gold/mutation truth | all future attempts |

## 4. Property authority

权威来源为 IFC2X3 PSD corpus `ifc2x3-property-records/0.2`。生产 authorability
只允许 class-applicable、`TypePropertySingleValue` 且 value type 位于当前 scalar
allow-list 的记录。scope 为 `occurrence_direct`；Stage 1.5 不可覆盖 Pset、Property、
value type、unit 或 scope。

| IFC class/family | Pset | Property | Value type | Scope | Authorable now? | Suitable for R1 acceptance? |
|---|---|---|---|---|---|---|
| IfcBeam | `Pset_BeamCommon` | `Reference` | `IfcIdentifier` | occurrence-direct | yes | E3, M2 |
| IfcBeam | `Pset_BeamCommon` | `LoadBearing` | `IfcBoolean` | occurrence-direct | yes | available, not separately frozen |
| IfcBeam | `Pset_BeamCommon` | `FireRating` | `IfcLabel` | occurrence-direct | yes | available, not separately frozen |
| IfcColumn | `Pset_ColumnCommon` | `LoadBearing` | `IfcBoolean` | occurrence-direct | yes | M3 |
| IfcColumn | `Pset_ColumnCommon` | `Reference` | `IfcIdentifier` | occurrence-direct | yes | available, not separately frozen |
| IfcDoor | `Pset_DoorCommon` | `FireRating` | `IfcLabel` | occurrence-direct | yes | E2, M1, H2 |
| IfcDoor | `Pset_DoorCommon` | `IsExternal` | `IfcBoolean` | occurrence-direct | yes | available, not separately frozen |
| IfcWindow | `Pset_WindowCommon` | `IsExternal` | `IfcBoolean` | occurrence-direct | yes | E1, H3 |
| IfcWindow | `Pset_WindowCommon` | `FireRating` | `IfcLabel` | occurrence-direct | yes | H1 |
| IfcWindow | `Pset_WindowCommon` | `Reference` | `IfcIdentifier` | occurrence-direct | yes | available, not separately frozen |
| IfcWall / IfcWallStandardCase | `Pset_WallCommon` | `AcousticRating` | `IfcLabel` | occurrence-direct | yes | E4, H2 |
| IfcWall / IfcWallStandardCase | `Pset_WallCommon` | `LoadBearing` | `IfcBoolean` | occurrence-direct | yes | available, not separately frozen |
| IfcWall / IfcWallStandardCase | `Pset_WallCommon` | `Reference` | `IfcIdentifier` | occurrence-direct | yes | available, not separately frozen |

关键 authority identities：

- Window `IsExternal`: `sha256:dcb2ba5a5bdf53cb679e2c0a884d140e9dd426638d144f3b0069828fb1a6a383`
- Window `FireRating`: `sha256:1e5f4e9a3c040d312619911de885a30d9e2ee9dd68d2418da04f796bd436d2c6`
- Door `FireRating`: `sha256:18305dceef09901ee7bbdc3ba4739242e06a85ecd6409d8d2ca28462d22d202a`
- Beam `Reference`: `sha256:c34b6a67961abab027b7145bfc21d7a31a87dc5516eb8713e46f448ca1030b31`
- Column `LoadBearing`: `sha256:2923ba6268cc16843ebfdcd7c383a6a1a56776d6b02462c4c8d52fa05febcc8d`
- Wall `AcousticRating`: `sha256:c62de11554af3e5103d2331869d7d8b2003fcc2b0a8d3246d7d80ae56fb5040b`

M1 的 `true` 不改变 property identity：先解析为 `Pset_DoorCommon.FireRating`
(`IfcLabel`)，再由 deterministic admissibility 以 value type incompatible 拒绝。

## 5. 当前 capability gaps / non-claims

- 不支持新增、移动或重塑 Wall。
- 不支持 structural analysis node/member/load；H4 只声明事务级 fail-closed。
- 不支持曲梁、斜/曲柱、grid placement、自动 Storey split、非矩形结构截面。
- 不支持 property alias replay、人工新 alias 或 LLM 输出兼容层。
- 不支持 type-level/shared-Type property mutation；只写 occurrence-direct scalar Pset。
- Window add、Door add/fill、Opening-only 虽已注册，但本 R1 不升级为最终验收资格。
- unspecified Type reuse clarification 有实现，但本 R1 不声明其 genuine acceptance。
- 不声明 IFC4/IFC4X3 repair、通用 IFC editing 或跨 schema 能力。
