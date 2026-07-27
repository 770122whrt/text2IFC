# Phase 10.1 Window 有效属性完整复刻与 IfcDiff 报告

> 日期：2026-07-23
> 状态：真实 DeepSeek UAT 通过
> 范围：`LargeBuilding.ifc` 中单个被删除 Window 的 damage → 文本授权 →
> ChangeSet → IFC 修复 → Ground Truth 比较

## 结论

本次实验验证了下面这条路径可行：

1. 用户明确指定要复用的 Window Type；
2. Type 已经提供的属性、材料和分类继续继承，不重复写入 occurrence；
3. Type 不能提供、但 Ground Truth 中存在的 16 项有效属性由用户文本明确给值；
4. 系统把 16 项自定义属性组成一份哈希绑定的确认预览；
5. 用户一次确认后写入目标 occurrence；
6. 真实 DeepSeek Stage 1 和 Stage 2 各调用一次；
7. 修复后的 Window 与原 Window 的 **60 项有效属性完全一致**。

这里的“完整”是有效语义完整：

```text
effective properties
= Type inherited properties
+ occurrence-direct properties
```

它不等于 Revit/原作者工具级的逐实体复刻。新 Window 仍使用新的 GlobalId、
Name 和 Tag，且没有重复写入 10 项已经能从 Type 获得的 direct property。

## 测试输入

### IFC 文件

| 角色 | 文件 |
|---|---|
| Ground Truth | `dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc` |
| Damaged IFC | 从 Ground Truth 删除 Window `2cXV28XOjE6f6irgi0CO4t` 及其 Opening |
| Host Wall | `1F6umJ5H50aeL3A1As_wTm` |
| 复用 Type | `M_Fixed:0915 x 1830mm` / `2cXV28XOjE6f6irhu0CO_c` |

### 用户文本中的授权属性

用户文本逐项给出精确的 `set_name`、`property_name`、值、IFC value type、
单位和 `occurrence_direct` scope：

| Set | Property | Value | IFC type |
|---|---|---:|---|
| Constraints | Level | `Level: Level 1` | `IfcLabel` |
| Constraints | Sill Height | `305.000000000004` mm | `IfcLengthMeasure` |
| Custom_Pset | NetArea | `3.17875400000013` m² | `IfcAreaMeasure` |
| Custom_Pset | SillHeight | `305.000000000004` mm | `IfcLengthMeasure` |
| Custom_Pset | StatusConstruction | `New Construction` | `IfcLabel` |
| Custom_Pset | StoreyName | `Level: Level 1` | `IfcText` |
| Dimensions | Area | `3.17875400000013` m² | `IfcAreaMeasure` |
| Dimensions | Volume | `0.0561146700000025` m³ | `IfcVolumeMeasure` |
| Identity Data | Mark | `7` | `IfcText` |
| Other | Family | `M_Fixed: 0915 x 1830mm` | `IfcLabel` |
| Other | Family and Type | `M_Fixed: 0915 x 1830mm` | `IfcLabel` |
| Other | Head Height | `2135.0` mm | `IfcLengthMeasure` |
| Other | Host Id | `Basic Wall: Outside wall` | `IfcLabel` |
| Other | Type | `M_Fixed: 0915 x 1830mm` | `IfcLabel` |
| Other | Type Id | `M_Fixed: 0915 x 1830mm` | `IfcLabel` |
| Phasing | Phase Created | `New Construction` | `IfcLabel` |

完整文本保存在 UAT 证据目录的 `user-request.json`。

## 实际运行结果

通过证据目录：

```text
dataset/processed/ifc-repair/phase10.1-full-property-replication/
  uat-20260723T065334162570Z/
```

| 检查 | 结果 |
|---|---|
| Provider | `deepseek-openai-compatible` / `deepseek-v4-flash` |
| Stage 1 | 1 次 |
| 属性确认 | 16 项组成 1 个 `property_batch`，一次确认 |
| Stage 2 | 1 次 |
| Production L1 / L2 / L3 | passed / passed / not_required |
| Private Benchmark L1 / L2 / L3 | passed / passed / not_required |
| 有效属性 | 60/60 相同 |
| Type | 相同 |
| Materials | 2/2 相同 |
| Classification | 1/1 相同 |
| Storey container | 相同 |
| Host wall | 相同 |
| Synthetic fallback | false |

输出 Window：

```text
Ground Truth GlobalId: 2cXV28XOjE6f6irgi0CO4t
Repaired GlobalId:     1BL8jp5NDJLu_5QcT_w4dn
```

## 为什么 occurrence-direct 不是逐项相同

比较器报告 direct properties 中有 10 项只存在于原 Window：

- `Custom_Pset.Height`
- `Custom_Pset.Hyperlink`
- `Custom_Pset.Keynote`
- `Custom_Pset.TypeDescription`
- `Custom_Pset.TypeMark`
- `Custom_Pset.Width`
- `Other.Category`
- `Pset_ManufacturerTypeInformation.Manufacturer`
- `Pset_ProductRequirements.Category`
- `Pset_QuantityTakeOff.Reference`

这 10 项在修复 Window 上仍能从复用 Type 获得相同有效值，所以：

```text
direct_properties.complete_match    = false
effective_properties.complete_match = true
```

这符合本次约定的精简策略：能可靠复用 Type 的语义不再复制到 occurrence，
避免产生重复事实和未来的 Type/occurrence 漂移。

另外两个 authoring attribute 不同：

| Attribute | Ground Truth | Repaired |
|---|---|---|
| Name | `M_Fixed:0915 x 1830mm:354395` | `Text2IFC window op-001` |
| Tag | `354395` | `op-001` |

如果以后要求作者工具级复刻，应把 Name、Tag 和“是否必须 direct-owned”作为
单独的显式授权/验证层，不能混入当前 L2 有效语义成功标准。

## 本次暴露并修复的问题

第一次真实运行目录：

```text
uat-20260723T064909300594Z/
```

它在 Stage 1 后以以下错误终止：

```text
INVALID_SEMANTIC_FACT_KEY: pset:Constraints.Sill Height
```

原因不是 IFC 不允许空格，而是内部 semantic key 错误地把合法 IFC 显示名称当成
不允许空格的稳定标识符。

修复后采用双轨表示：

- `fact_key`：归一化后的比较键，例如
  `pset:Constraints.Sill-Height`；
- `source_fact_key`：保留精确 IFC 名称，例如
  `pset:Constraints.Sill Height`。

L2 使用归一化键比较，IFC authoring 使用精确源名称写回。因此不会修改用户指定的
Pset/Property 名称，也不会因为空格而拒绝合法 IFC2X3 属性。

## IfcOpenShell 比较能力

新增两层比较：

### 1. 官方 IfcDiff 模型级比较

使用官方 `ifcdiff` Python API，支持 attributes、geometry、type、property、
container、aggregate 和 classification。

命令：

```powershell
.venv\Scripts\python scripts\ifc_repair\compare_ifc.py `
  original.ifc repaired.ifc `
  --mapping "window:OLD_GLOBAL_ID:NEW_GLOBAL_ID" `
  --output comparison.json
```

IfcDiff 按 GlobalId 识别同一对象。因此本案例会正确报告原 Window deleted、
新 Window added，但不能单独回答这两个不同 GUID 的 Window 是否语义相同。

全模型官方结果为：

| 类别 | 数量 |
|---|---:|
| added | 1 |
| deleted | 1 |
| changed | 126 |

其中 114 个 `container_changed` 和 12 个 `aggregate_changed` 主要来自共享关系
实体被重建后，IfcDiff 按关系身份传播出的变化；另有 Host Wall 的
`geometry_changed`，这是补回 Opening 后的预期变化。它们不能直接解释为
114 个构件换了楼层。

### 2. 跨 GUID 映射比较

系统通过 application result 中的角色映射
`original window GUID -> repaired window GUID`，再使用
`ifcopenshell.util.element` 比较：

- direct/effective Psets 和 Quantities；
- Type；
- Materials；
- Classification；
- Container；
- Filled opening / Host。

这一层用于回答修复实体与 Ground Truth 实体是否语义等价，也是本报告
“60 项有效属性完全相同”的来源。

官方参考：

- [IfcDiff documentation](https://docs.ifcopenshell.org/ifcdiff.html)
- [IfcDiff Python API](https://docs.ifcopenshell.org/autoapi/ifcdiff/index.html)
- [ifcopenshell.util.element](https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/element/index.html)
- [ifcopenshell.util.classification](https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/classification/index.html)

## 证据文件

| 文件 | 内容 |
|---|---|
| `result.json` | UAT 终态、Provider 次数、L1/L2 和哈希 |
| `user-request.json` | 完整用户文本 |
| `original-ground-truth.ifc` | 原始 IFC |
| `damaged.ifc` | 删除一扇 Window + Opening 后的 IFC |
| `repaired.ifc` | 真实 DeepSeek 链路修复产物 |
| `mapped-window-comparison.json` | 跨 GUID 逐类语义差异 |
| `official-ifcdiff.json` | 官方 IfcDiff 全模型结果 |
| `ifc-comparison-window-filtered.json` | Window filter + mapped comparison |
| `private-benchmark-evaluation.json` | Ground Truth L1/L2/L3 |

## 当前边界

本次证明了“Type 复用 + 用户文本补齐 occurrence 属性”可以完成 Window 的有效语义
复刻。但它尚未证明：

- 任意未知属性可以无确认写入；
- 枚举、列表、表格、复杂属性可写入；
- shared Type 可被修改；
- 原作者工具的 Name/Tag/OwnerHistory/STEP 排序可完全复刻；
- 门、梁、柱和只挖墙洞已经具备相同 handler。

这些仍应作为后续扩展，而不是把本次 Window 成功外推成全 IFC authoring 成功。
