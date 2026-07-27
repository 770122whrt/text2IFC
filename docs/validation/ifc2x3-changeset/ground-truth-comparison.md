# LargeBuilding Window Repair：Pipeline 与 Ground Truth 对比

> 状态：2026-07-18 真实 DeepSeek UAT 后的直接对比记录
> 成功证据：`large-building-window-repair-001-deepseek-live-20260718-v2`
> 结论：当前达到几何—关系修复，不等于原始 IFC 的全量 BIM 语义或字节级复原。

## 1. Pipeline

```text
原始 LargeBuilding.ifc（只读、冻结 SHA-256）
  -> 单点 mutation
     -> damaged.ifc
     -> mutation_report.json
     -> mutation_manifest.private.json（禁止进入 Provider）
  -> allowlist public projection
     -> repair_request.txt
     -> public-repair-spec.json
  -> operation-aware context builder(damaged.ifc)
     -> public-context.json
  -> Prompt renderer
     -> renderer-input.json
     -> rendered-prompt.md
  -> DeepSeek Provider
     -> raw-response.txt
     -> live-request.json / live-response.json / live-events.jsonl
     -> provider-metadata.json
  -> JSON parse + Schema/binding validation
     -> diagnostics.json
     -> predicted-changeset.json
  -> deterministic Audit
     -> audit-report.json
  -> transactional IFC Applicator（语义 ChangeSet -> IFC2X3 实体/关系/几何）
     -> repaired.ifc
     -> application-report.json
  -> damaged-vs-repaired preservation comparator
     -> evaluation_report.json
     -> report.md
  -> evidence packager
     -> artifact-manifest.json
```

## 2. Provider 实际输入

Provider 不接收原始 IFC、damaged IFC、private manifest、原窗/洞口 GlobalId、STEP ID
或 gold ChangeSet。它接收一个渲染后的文本 Prompt，内容由以下公开输入组成：

1. `REPAIR_REQUEST`：用户可读的修复要求；
2. `PUBLIC_REPAIR_SPEC`：楼层、墙描述、局部坐标语义、洞口尺寸和保持要求；
3. `PUBLIC_CONTEXT`：8 个候选墙、裸 `ifc_global_id`、墙轴、尺寸、已有洞口摘要和模型约束；
4. `SOURCE_REQUEST_HASH`；
5. `SUPPORTED_OPERATIONS`：operation type、`target_schema`、`parameter_schema`、允许的
   pre/postcondition names 和 capability constraints；
6. `CHANGESET_SCHEMA`；
7. 固定 Prompt 规则和一个不可复制数值的完整 Window ChangeSet 示例。

本次证据中的大小与实际 Provider usage：

| 项目 | 结果 |
|---|---:|
| `repair_request.txt` | 434 bytes |
| `public-repair-spec.json` | 814 bytes |
| `public-context.json`（pretty JSON） | 14,193 bytes |
| Context canonical payload | 7,427 bytes / 估算 1,857 tokens |
| `rendered-prompt.md` | 17,706 bytes |
| DeepSeek 实际 prompt usage | 6,381 tokens |

## 3. Provider 输出与确定性编译输入

DeepSeek 返回一个语义 ChangeSet，不返回 STEP 或底层 IFC placement/representation：

- operation：`add_window_with_opening_to_wall`；
- host：`target.wall_global_id = 1F6umJ5H50aeL3A1As_wTm`；
- opening：`915 x 1830 mm`，窗台高 `305 mm`；
- position：从 `wall_local_start` 起算，中心 `3042.5 mm`；
- window：`fit_opening = true`；
- evidence：`spec:/...` 与 `context:/...`；
- preconditions / postconditions：仅使用 Registry 声明的名称。

Provider 输出为 `1,162 completion tokens`。解析后的
`predicted-changeset.json` 是确定性 Applicator 的直接输入。

## 4. 确定性 Applicator 产物

Applicator 在 damaged IFC 的内存副本中创建：

| Role | IFC class | 新 GlobalId |
|---|---|---|
| opening | `IfcOpeningElement` | `2j2TckM0bJ2vV4g4idDAKa` |
| window | `IfcWindow` | `3rdpSQx1HJlu3wqnKkosXf` |
| voids | `IfcRelVoidsElement` | `05VylE791KYvHNhmYJYdky` |
| fills | `IfcRelFillsElement` | `1iPt8BshzSIxeBvMiyXy$M` |

它同时修改既有 Window type relationship 和楼层 containment relationship，将新 Window
接入既有 WindowStyle `2cXV28XOjE6f6irhu0CO_c` 和 Level 1。

## 5. Ground Truth 直接对比

### 5.1 已恢复一致的部分

| 检查 | Original | Repaired | 结果 |
|---|---:|---:|---|
| IFC schema | IFC2X3 | IFC2X3 | 一致 |
| IfcWall | 18 | 18 | 一致 |
| IfcWindow | 42 | 42 | 一致 |
| IfcDoor | 18 | 18 | 一致 |
| IfcOpeningElement | 60 | 60 | 一致 |
| IfcRelVoidsElement | 60 | 60 | 一致 |
| IfcRelFillsElement | 60 | 60 | 一致 |
| host wall GlobalId | `1F6...wTm` | `1F6...wTm` | 一致 |
| host wall root snapshot | — | — | 完全一致 |
| opening width/height/depth | 915/1830/200 mm | 915/1830/200 mm | 一致 |
| centre/sill | 3042.5/305 mm | 3042.5/305 mm | 一致 |
| wall-local geometry bounds | `[2585,3500] x [-100,100] x [305,2135]` | 相同 | 一致 |
| window type GlobalId | `2cXV...O_c` | `2cXV...O_c` | 一致 |
| storey containment | Level 1 | Level 1 | 一致 |
| void/fill host chain | 正确 | 正确 | 一致 |
| restored void volume | 0.33489 m3 | 0.33489 m3 | 一致 |

### 5.2 不一致的部分

1. 文件不是字节级复原：原始 SHA-256 为
   `102f8123...9bb725`，repaired SHA-256 为 `d4761b62...7998d0`。
2. 原 Window、Opening、Voids、Fills 的 GlobalId 没有复用；它们被 4 个确定性新 GlobalId
   替代。这符合“Provider 不接触 private gold IDs”的当前设计。
3. 原始 IFC 有 29 个 rooted entities 未出现在 repaired IFC；只新增了 4 个核心链实体，
   所以 root count 从 `3503` 变为 `3478`。除核心 4 项外，缺失项主要是随原 Window
   删除的 instance property sets、quantities、`IfcRelDefinesByProperties`、材料关联等。
4. 新 Window 复用了正确的 WindowStyle，因此继承了类型属性；但没有恢复原 Window 的
   instance-specific `BaseQuantities`、`Constraints`、`Phasing`、Mark、Host Id、Head Height、
   instance Custom_Pset 字段等。
5. `Pset_WindowCommon.IsExternal` 在原实例为 `true`，新实例解析结果为 `false`；这是一个
   真实 BIM 语义差异，不能被几何通过掩盖。
6. 原 Window 有分类和材料 association；新 Window 的 `HasAssociations` 为空。
7. Name、Tag 和原 authoring identity 没有恢复；新值使用 Text2IFC operation 标识。
8. 原/新 Window 与 Opening 的 representation hashes 不同，低层 placement 也不同。
   Window 的世界 placement 方向相差 180 度；由于该固定窗几何对称且 wall-local bounds
   相同，当前 Comparator 将其视为几何对齐，但这不是 authoring-exact 复原。
9. source 与 repaired 之间有 3 个共同 Root 的 attributes 发生变化：Window type
   relationship、楼层 containment relationship，以及未重新关联新 Window 的分类关系。

## 6. 判定

采用当前 v0.1 验收合同，本次修复完成：文本要求的指定墙、位置、洞口、窗、Voids、Fills、
楼层、类型与非目标保护均通过。

采用“恢复 original ground truth 的完整 BIM 语义”标准，本次修复未完成。当前 Comparator
主要验证 damaged-to-repaired 的授权变化与几何关系，没有把 original target 的实例属性、
材料、分类、identity 和 authoring representation 纳入成功门槛。

建议把完成度明确分层：

- L1 几何—关系修复：当前已通过；
- L2 BIM 语义保真：属性集、数量、材料、分类、IsExternal、实例 identity 等，当前未通过；
- L3 authoring/identity exactness：原 GlobalId、STEP ID、底层 placement/representation、
  文件字节一致；不应默认作为文本修复目标，除非单独定义。
