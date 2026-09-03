# LargeBuilding 真实修复 Window 属性对比

**执行日期：** 2026-07-23
**Provider / Model：** `deepseek-openai-compatible / deepseek-v4-flash`
**真实证据目录：**
`dataset/processed/ifc-repair/phase10.1-live-uat/uat-20260723T061215087384Z/`

## 1. 结论

本次真实 damage → DeepSeek → ChangeSet → IFC repair 链路成功：

- Stage 1：1 次真实调用；
- Stage 2：1 次真实调用；
- `synthetic_fallback=false`；
- Production：L1 passed、L2 passed、L3 not_required；
- Private Ground Truth：L1 passed、L2 passed、L3 not_required；
- repaired IFC 可重新打开并发布。

修复后的 Window 在几何、宿主关系、楼层、Window Type、材料、分类和当前
Production L2 要求上正确。但它不是原始 Window 全部 authoring metadata 的
完整复制：

- occurrence-direct：原始 32 个值，修复后 7 个值；
- 其中 6 个值完全相同，新增用户要求的 `FireRating=EI30`；
- 原始 26 个 occurrence-direct 值没有按原 authoring 位置重建；
- 考虑同一 Type 的继承后，原始 60 个有效值中有 44 个保持一致，仍有
  16 个有效值缺失；
- 没有发现同名属性值冲突。

因此，若目标是“按照文本恢复可用 Window”，本次通过；若目标是“复刻原始
作者模型的全部 occurrence 属性”，本次尚未完成。

## 2. 输入、损伤和输出

### 原始对象

| 角色 | GlobalId | 名称 |
|---|---|---|
| Wall | `1F6umJ5H50aeL3A1As_wTm` | `Basic Wall:Outside wall:346660` |
| Opening | `2cXV28XOjE6f6irhW0CO4t` | 原始 Window Opening |
| Window | `2cXV28XOjE6f6irgi0CO4t` | `M_Fixed:0915 x 1830mm:354395` |
| Window Type | `2cXV28XOjE6f6irhu0CO_c` | `M_Fixed:0915 x 1830mm` |

damage 操作删除上述原始 Window、Opening 及其 filling/voiding 链，但保留宿主
Wall、楼层和可复用 Window Type。

### 用户输入

```text
On IfcWall GlobalId 1F6umJ5H50aeL3A1As_wTm, restore the missing window.
Create a 915 mm wide and 1830 mm high window, with a 305 mm sill.
Its center offset is 3042.5 mm from wall_local_start.
Reuse the existing Window Type named 'M_Fixed:0915 x 1830mm'.
Set the occurrence property Pset_WindowCommon.FireRating to EI30.
```

### 文件

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| Original Ground Truth | 1,292,595 | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725` |
| Damaged IFC | 1,287,030 | `ca703845ddf4a434eea0317498fb29893877f87d66047cf6c890a61cd2844933` |
| Repaired IFC | 1,289,976 | `b345a978652fa9451dae437742a41170b88f7a685850127482261ddca6ef7c9d` |

Repaired 文件比 Ground Truth 小 2,619 bytes。文件大小本身不是正确性判据；
本次差异主要对应未重建的 occurrence metadata、不同的实体标识以及重新序列化
后的 STEP 图。

## 3. 核心字段对比

| 字段 | Original Window | Repaired Window | 结论 |
|---|---|---|---|
| GlobalId | `2cXV28XOjE6f6irgi0CO4t` | `1eyD9VsMHTuukzyYdMWnBL` | 不同；新建 occurrence 的预期行为 |
| Name | `M_Fixed:0915 x 1830mm:354395` | `Text2IFC window op1` | 不同；未恢复作者命名 |
| Tag | `354395` | `op1` | 不同；未恢复作者 Tag |
| ObjectType | `M_Fixed:0915 x 1830mm` | `M_Fixed:0915 x 1830mm` | 相同 |
| OverallWidth | 915 mm | 915 mm | 相同 |
| OverallHeight | 1830 mm | 1830 mm | 相同 |
| Window Type GlobalId | `2cXV28XOjE6f6irhu0CO_c` | `2cXV28XOjE6f6irhu0CO_c` | 完全复用 |
| Storey | `Level 1` | `Level 1` | 相同 |
| Host Wall | `1F6umJ5H50aeL3A1As_wTm` | `1F6umJ5H50aeL3A1As_wTm` | 相同 |

新 Opening 的 GlobalId 为 `3Ee3G0amrOCOH30tpknxOF`。GlobalId 不同不影响
L1，因为新的 Window/Opening 关系链、位置和尺寸均重新建立并通过验证。

## 4. occurrence-direct 属性对比

原始 Window 有 11 个 direct Pset/Quantity 集合、32 个标量值。修复后有
2 个集合、7 个标量值。

### 完全相同的 6 个值

| 属性 | Original | Repaired |
|---|---:|---:|
| `BaseQuantities.Area` | 3.17875400000013 | 3.17875400000013 |
| `BaseQuantities.Height` | 1830.0 | 1830.0 |
| `BaseQuantities.Width` | 915.0 | 915.0 |
| `Pset_WindowCommon.IsExternal` | true | true |
| `Pset_WindowCommon.Reference` | `0915 x 1830mm` | `0915 x 1830mm` |
| `Pset_WindowCommon.ThermalTransmittance` | 3.6886 | 3.6886 |

### 用户新增的值

| 属性 | Original | Repaired | IFC 类型 | ownership |
|---|---|---|---|---|
| `Pset_WindowCommon.FireRating` | 不存在 | `EI30` | `IfcLabel` | occurrence-direct |

### 未按 occurrence-direct 重建的集合

| 集合 | 未重建值数量 | 内容摘要 |
|---|---:|---|
| `Pset_ManufacturerTypeInformation` | 1 | Manufacturer |
| `Pset_ProductRequirements` | 1 | Category |
| `Pset_QuantityTakeOff` | 1 | Reference |
| `Custom_Pset` | 10 | TypeMark、Keynote、StoreyName、尺寸、SillHeight 等 |
| `Constraints` | 2 | Level、Sill Height |
| `Dimensions` | 2 | Area、Volume |
| `Identity Data` | 1 | Mark |
| `Other` | 7 | Host Id、Family、Type、Head Height 等 |
| `Phasing` | 1 | Phase Created |
| **合计** | **26** |  |

这里描述的是 authoring ownership：部分值虽然不再 direct，但仍可通过复用的
Window Type 继承得到。

## 5. 包含 Type 继承后的有效属性

将 occurrence-direct 和 Type-inherited 属性合并后：

| 指标 | Original | Repaired |
|---|---:|---:|
| 有效属性总数 | 60 | 45 |
| 完全相同 | 44 | 44 |
| Repaired 新增 | — | 1 |
| Repaired 缺失 | 16 | — |
| 同名但值不同 | 0 | 0 |

仍然缺失的 16 个有效值为：

- `Constraints`：Level、Sill Height；
- `Custom_Pset`：NetArea、SillHeight、StatusConstruction、StoreyName；
- `Dimensions`：Area、Volume；
- `Identity Data`：Mark；
- `Other`：Family、Family and Type、Head Height、Host Id、Type、Type Id；
- `Phasing`：Phase Created。

这 16 个值既没有从 Type 继承，也没有由用户文本授权，因此当前编译器不会猜测
或自动补写。

## 6. 材料与分类

| 项目 | Original | Repaired | 结论 |
|---|---|---|---|
| Material 类型 | `IfcMaterialList` | `IfcMaterialList` | 相同 |
| Materials | `Glass`, `Sash` | `Glass`, `Sash` | 相同 |
| Classification | Uniformat / `Window: Assembly Code` | Uniformat / `Window: Assembly Code` | 相同 |

## 7. 为什么当前 L2 仍然通过

当前 Production/Private L2 验证的是已授权且被 Window policy 声明为 mandatory
或 conditional 的语义事实，包括 Type、宿主、楼层、尺寸、IsExternal、
BaseQuantities、材料、分类和用户显式要求的 `FireRating`。

它并不声称比较原始 Window 的全部 32 个 occurrence-direct 值。因此：

- `L2 passed` 是真实结果；
- “全部 occurrence authoring 属性已还原”不是当前 L2 的含义；
- 这次人工属性清单对比暴露了比现有 L2 更严格的 authoring-fidelity 差距。

## 8. 判断

本次修复可以判定为：

| 维度 | 结果 |
|---|---|
| geometry_relationship_success | 通过 |
| semantic_fidelity_success（当前 L2 合同） | 通过 |
| 用户新增属性 | 通过 |
| 完整 occurrence property reconstruction | 未完成 |
| authoring_exactness | 未要求；Name、Tag、GlobalId 不同 |

若下一步要提高完整度，应单独设计“occurrence metadata 重建策略”，并区分：

1. 用户显式指定的属性：继续按 Phase 10.1 精确写入；
2. 同 Type cohort 中稳定一致、可证明的属性：可以作为候选证据；
3. occurrence 特有值，如 Mark、Host Id、Phase、Sill Height：需要确定性重算
   或向用户确认；
4. 仅存在于 private Ground Truth 的值：只能用于评估，不能泄漏到生产修复。
