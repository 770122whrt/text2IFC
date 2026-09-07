# LargeBuilding 单窗完整语义复刻报告

## 1. 结论

本案例通过真实 DeepSeek Stage 1/Stage 2，从 damaged IFC 恢复一扇 Window
及其 Opening，并复用用户指定的现有 Window Type。

结果：

- Stage 1：1 次真实调用；
- Stage 2：1 次真实调用；
- synthetic fallback：`false`；
- application：passed；
- preservation：passed；
- Production：L1 passed、L2 passed、L3 not_required；
- Private Ground Truth：L1 passed、L2 passed、L3 not_required；
- `complete_repair_success = true`；
- `successful_artifact_publishable = true`。

## 2. IFC 输入与损伤

| 文件 | 实体 | Root | Wall | Opening | Window |
|---|---:|---:|---:|---:|---:|
| `01-original.ifc` | 20,735 | 3,503 | 18 | 60 | 42 |
| `02-damaged.ifc` | 20,673 | 3,474 | 18 | 59 | 41 |
| `03-repaired.ifc` | 20,750 | 3,496 | 18 | 60 | 42 |

三个文件均为 IFC2X3，并已使用 IfcOpenShell 重新打开。

Damage 删除：

| 角色 | GlobalId / 名称 |
|---|---|
| Window | `2cXV28XOjE6f6irgi0CO4t` |
| Opening | `2cXV28XOjE6f6irhW0CO4t` |
| Host Wall | `1F6umJ5H50aeL3A1As_wTm` |
| Window Type | `M_Fixed:0915 x 1830mm` / `2cXV28XOjE6f6irhu0CO_c` |

宿主墙、楼层和 Window Type 保留在 damaged IFC 中。

## 3. 用户输入

完整输入位于 [input/request.json](input/request.json)。核心要求为：

- 在指定 Wall 上恢复 Window；
- 宽 915 mm、高 1830 mm、窗台高 305 mm；
- 中心距 `wall_local_start` 3042.5 mm；
- 复用 `M_Fixed:0915 x 1830mm`；
- 显式授权 16 项 occurrence-direct `IfcPropertySingleValue`。

16 项文本属性覆盖 Constraints、Custom_Pset、Dimensions、Identity Data、
Other 和 Phasing。每项都给出精确 set/property 名、值、IFC value type、
单位和 scope，编译器不从 Ground Truth 猜测这些值。

## 4. Agent 与 ChangeSet

| Part | 输入 | 输出 | 文件 |
|---|---|---|---|
| Stage 1 | 用户文本 + operation contract | 1-operation RepairIntent | `agent/repair-intent.json` |
| Resolver | RepairIntent + damaged SQLite index | 唯一 Wall、Type 和语义事实 | Bound ChangeSet provenance |
| Stage 2 | 已解析的有界事实 | ChangeSet draft | `agent/provider-draft.json` |
| Binder/Audit | draft + source fingerprint + policy | Bound ChangeSet 0.2 | `changeset/bound-changeset.json` |
| Applicator | damaged IFC + Bound ChangeSet | repaired IFC | `03-repaired.ifc` |

Provider 为 `deepseek-openai-compatible / deepseek-v4-flash`。Stage 2
transport attempt 为 1，元数据位于
`agent/provider-metadata-stage2.json`。

## 5. 验证结果

### Production

`validation/production-evaluation.json` 记录：

| Gate | 结果 |
|---|---|
| application | passed |
| global preservation | passed |
| operation `op-001` | passed |
| L1 | passed |
| L2 | passed |
| L3 | not_required |
| publishable | true |

L1 验证 repaired IFC 可读、IFC2X3 schema、授权 scope、Window/Opening/Wall
关系、位置、尺寸、朝向、宿主墙体积和非目标 preservation。

### Ground Truth

跨 GUID 比较结果：

- effective properties：60/60 一致；
- Window Type：一致；
- materials：`Glass`、`Sash` 一致；
- classification：一致；
- storey 与 host wall：一致；
- Width/Height/Area、IsExternal、Reference 等 L2 事实一致。

原 Window 的 10 项 occurrence-direct 属性在 repaired Window 上可从同一
Type 获得相同有效值，因此系统没有重复 author。由此：

```text
direct_properties.complete_match    = false
effective_properties.complete_match = true
```

这是精简 Type 复用策略，不是属性丢失。详细差异位于
`validation/window-comparison.json`。

## 6. 为什么文件不与 Ground Truth 完全相同

新建 Window 使用新 GlobalId：

```text
Original: 2cXV28XOjE6f6irgi0CO4t
Repaired: 1BL8jp5NDJLu_5QcT_w4dn
```

Name、Tag、关系实体身份和 STEP 排序也可能不同。IfcDiff 因此报告 1 added、
1 deleted 和 126 changed；部分 relationship 身份变化会传播为 container 或
aggregate 差异。这不等价于 126 个业务构件被错误修改。

当前成功状态要求 L1/L2 等价和非目标 preservation，不要求 L3 作者工具级
复刻。

## 7. 文件说明

| 路径 | 作用 |
|---|---|
| `01-original.ifc` | evaluator-only Ground Truth |
| `02-damaged.ifc` | Agent repair 的实际 IFC 输入 |
| `03-repaired.ifc` | 通过 Production gate 的发布产物 |
| `input/request.json` | 完整用户输入 |
| `agent/repair-intent.json` | Stage 1 结构化语义 |
| `agent/provider-draft.json` | Stage 2 原始 ChangeSet draft |
| `changeset/bound-changeset.json` | 确定性绑定后的执行合同 |
| `validation/mutation-manifest.private.json` | 被删除对象的 private Ground Truth |
| `validation/production-evaluation.json` | 发布依据 |
| `validation/private-ground-truth-evaluation.json` | evaluator-only L1/L2 |
| `validation/ifc-comparison.json` | 全模型 IfcDiff |
| `validation/window-comparison.json` | original/repaired Window 跨 GUID 比较 |
| `FILES.json` | 文件来源、大小与 SHA-256 |

## 8. 当前边界

本案例证明了 Type 复用和用户文本补齐 occurrence 属性可以恢复完整有效语义。
它不承诺原 GlobalId、Name、Tag、OwnerHistory 或 direct/inherited authoring
位置完全相同。
