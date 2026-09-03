# Phase 12 Structural Type Visual Fidelity 修复计划

状态：**调研完成，待实现**

日期：2026-09-03

范围：Beam / Column 新增操作中的 `reuse_exact_existing` Type 复用；不启动 Phase 13，不改变既有 R1 Proof 历史结论。

## 1. 问题现象

当前新增 Beam/Column 并“精确复用现有 Type”时：

- Type GlobalId 能正确绑定；
- 位置、尺寸、Storey、L0/L1/L2 可以通过；
- 但新构件在 IFC Viewer 中可能显示为默认灰色，和原同 Type 构件的材质/颜色外观不一致。

R1 A1 是可复现入口：请求明确复用 `IfcBeamType` `12jWe1_Rb2cR0ot5ICgwf_`，当前 Proof 能证明几何和 Type binding，但没有验证 visual fidelity。

## 2. 调研结论

### 2.1 IFC 中 Type、Material、Appearance 是不同层

当前需要区分：

1. `IfcRelDefinesByType`：Occurrence 与 Type 的类型关系；
2. `IfcRepresentationMap` / `IfcMappedItem`：Type-owned geometry 的复用；
3. `IfcRelAssociatesMaterial` / `IfcMaterial`：材料语义；
4. `IfcStyledItem` / `IfcSurfaceStyle` / `IfcMaterialDefinitionRepresentation`：颜色和显示外观。

因此“Material/Type 正确”并不自动等于“Viewer 颜色正确”。buildingSMART IFC2X3 明确将 `IfcStyledItem` 定义为几何或 Material 的 presentation style 载体，并由 `IfcMaterialDefinitionRepresentation` 保存 Material 的 presentation information。

### 2.2 IfcOpenShell 已提供正确的 Type 映射语义

IfcOpenShell 0.8.5 的 `ifcopenshell.api.type.assign_type(..., should_map_representations=True)` 默认会在 Type 有 `RepresentationMaps` 时把 Type representation 映射到 occurrence；官方文档同时说明 Type 有 representation 时 occurrence 应使用相同 representation。

Style API 也区分：

- `ifcopenshell.api.style.assign_item_style(...)`：给新的 representation item 直接赋样式；
- `ifcopenshell.api.style.assign_material_style(...)`：给 Material 赋样式，官方推荐优先采用 Material style。

参考：

- https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/type/assign_type/index.html
- https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/style/assign_item_style/index.html
- https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/style/assign_material_style/index.html
- https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcpresentationappearanceresource/lexical/ifcstyleditem.htm
- https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcmaterialdefinitionrepresentation.htm

## 3. 历史实现、当前实现与回归来源

### 3.1 历史实现：Window 的 Type Representation 复用

Git 历史中，提交 `56037c5b`（`feat(08-02): implement operation-owned L2 evaluation policy`，2026-07-19）已经包含一条实际可工作的 Window Type representation 复用路径。其核心代码是：

```python
window_type = _find_compatible_window_type(model, width=width, height=height)
window = model.create_entity("IfcWindow", ...)

if window_type is not None and window_type.RepresentationMaps:
    mapped_representations = [
        ifcopenshell.api.geometry.map_representation(
            model,
            representation=representation_map.MappedRepresentation,
        )
        for representation_map in window_type.RepresentationMaps
    ]
    window.Representation = model.create_entity(
        "IfcProductDefinitionShape",
        Representations=mapped_representations,
    )
else:
    window_representation = ifcopenshell.api.geometry.add_wall_representation(...)
    window.Representation = model.create_entity(
        "IfcProductDefinitionShape",
        Representations=[window_representation],
    )
```

之后再通过 `IfcRelDefinesByType` 把新 Window 绑定回选中的 Type。

这段旧实现中真正重要的不是单独的 Type relationship，而是：

```text
existing Type
  -> RepresentationMaps
  -> map_representation()
  -> new occurrence representation
  -> IfcRelDefinesByType
```

当 Type 的 mapped representation 内已经包含 geometry item 及其 presentation/style 引用时，新 occurrence 复用的是同一 representation authority，因此在 Viewer 中更容易保持与原 Type 实例一致的外观。这与用户此前观察到“复用 Type 后看起来和原来基本一致”是吻合的。

需要保留的历史思想：

- 已授权 Type 的 `RepresentationMaps` 应被视为可复用 representation authority；
- 有可用 mapped representation 时，不应无条件重新裸建一套无 style 的 geometry；
- Type binding 与 representation reuse 是两个不同动作，二者都需要考虑。

但旧实现也有现在不应直接恢复的部分：它通过 `_find_compatible_window_type()` 按宽高自动寻找 compatible Type。当前 Repair Pipeline 已采用更严格的用户授权 / exact GlobalId / deterministic binding，因此不应退回到“尺寸相似即自动授权 Type”的策略。

因此本计划不是恢复整个旧实现，而是：**保留当前严格 Type authority 模型，同时重新引入旧实现中正确的 representation reuse 思路。**

### 3.2 当前 Beam / Column 实现

当前链路：

```text
create_straight_rectangular_member()
  -> 创建新的 IfcRectangleProfileDef
  -> 创建新的 IfcExtrudedAreaSolid
  -> 创建新的 IfcShapeRepresentation
  -> 创建新的 IfcBeam / IfcColumn

bind_structural_type()
  -> 仅创建或扩展 IfcRelDefinesByType
```

关键文件：

- `src/text2ifc_ifc_repair/operations/structural_member.py`
- `src/text2ifc_ifc_repair/operations/beam.py`
- `src/text2ifc_ifc_repair/operations/column.py`

`bind_structural_type()` 当前合同明确是“creates or extends only `IfcRelDefinesByType`”。因此 Type 自身的 Pset、Material、RepresentationMaps 可以保持不变，但新 occurrence 不会自动使用这些 presentation/representation authority。

当前 Beam 的顺序实际是：

```text
先创建新的参数化 SweptSolid
  -> 再解析 exact existing Type
  -> 再绑定 IfcRelDefinesByType
```

这意味着 Type identity 成功复用，但 representation/style 并没有自动进入新 geometry。

### 3.3 当前 Window / Door 对照

当前 Window / Door 仍保留了历史上正确的核心逻辑：当 Type/Style 有 `RepresentationMaps` 时，会调用 `ifcopenshell.api.geometry.map_representation(...)` 给新 occurrence 建立 mapped representation。

关键文件：

- `src/text2ifc_ifc_repair/operations/window.py`
- `src/text2ifc_ifc_repair/operations/door.py`

因此目前存在明确的不一致：

| 能力 | Window / Door | Beam / Column |
|---|---|---|
| exact / selected Type binding | 有 | 有 |
| `IfcRelDefinesByType` | 有 | 有 |
| Type `RepresentationMaps` 复用 | 有 | 当前没有 |
| 新 geometry 参数化重建 | fallback | 默认路径 |
| presentation/style 保真门禁 | 没有完整 gate | 没有 |

这说明当前 Beam/Column 的 Type reuse 语义比 Window/Door 更窄。

### 3.4 为什么不能把旧 Window 代码原样复制到 Beam / Column

旧 Window 路径的核心思路正确，但 Beam/Column 存在 variable-length 问题。例如同一个 `IfcBeamType` 可能表示 500×800 的截面和材料语义，而不同 occurrence 的长度分别为 3 m、6 m、12 m。

如果 Type 的 RepresentationMap 固定包含某个完整长度的 Beam geometry，直接 map 整个 representation 可能导致新 occurrence 的长度错误。因此结构构件需要区分：

```text
Type representation 可以完整复用
    -> map representation

Type representation 不适合完整复用 / occurrence 长度独立
    -> 保持当前参数化 geometry
    -> 只复用经过授权的 material / presentation style
```

所以正确方向不是“回滚到旧代码”，而是“旧 representation reuse + 当前 deterministic geometry/authority”的组合。

### 3.5 测试缺口

`tests/ifc_repair/test_structural_type_authoring.py` 中已有 Type preservation 测试，但其 representation fixture 使用 `Items=[]`，只证明“绑定后没有修改原 Type”，没有证明：

- 新 occurrence 使用 Type RepresentationMap；
- 新 geometry 继承/复用 SurfaceStyle；
- Viewer appearance 与授权参考构件一致。

当前 Beam/Column postcondition 也只检查 geometry、Storey、Type binding 和 structural-analysis relationship，不检查 visual fidelity。

## 4. 根因判断

当前 `reuse_exact_existing` 实际实现的是：

```text
reuse Type identity + inherited semantics
```

而用户期望的是：

```text
reuse Type identity
+ compatible representation authority
+ material semantics
+ visual appearance
```

新 Beam/Column 的 `IfcExtrudedAreaSolid` 是裸创建的，没有对应 `IfcStyledItem` / `IfcSurfaceStyle` 或 Material presentation，因此 Viewer 可以回退为默认灰色。

## 5. Solution

总体原则：**不回滚当前严格的 Type authority / deterministic binding，而是把旧实现中已经证明有效的 representation reuse 思路重新接回当前 Beam/Column authoring。**

目标链路：

```text
user-authorized exact Type
  -> deterministic resolve by GlobalId
  -> inspect representation / material / appearance authority
  -> if representation can be safely reused: map it
  -> otherwise keep parametric structural geometry and reuse only authorized appearance
  -> bind exact Type
  -> visual-fidelity validation
```

### Step 1 — 冻结一个红色回归

以 R1 A1 为主样例，增加真实非空 geometry/style fixture，明确证明当前行为：

- Type binding PASS；
- geometry PASS；
- appearance fingerprint FAIL。

测试不得只使用 `Items=[]`。

### Step 2 — 区分两种 Type reuse

**A. Type 有 `RepresentationMaps`**

优先复用 Type-owned representation。评估使用：

```python
ifcopenshell.api.type.assign_type(
    model,
    related_objects=[occurrence],
    relating_type=bound_type,
    should_map_representations=True,
)
```

或等价的受控 `map_type_representations` 路径，避免只手写 `IfcRelDefinesByType`。

**B. Type 没有 `RepresentationMaps`，但 Beam/Column 长度可变**

继续使用当前 parametric `IfcExtrudedAreaSolid` 生成长度和 placement，但从经过授权的 Type/material/reference occurrence 提取 presentation authority，并赋给新的 representation item。

优先级建议：

```text
Material-owned style
  > Type/reference representation item style
  > no style (仅当源 authority 本身无 style)
```

不要硬编码 RGB，也不要根据 Type 名称猜颜色。

### Step 3 — 增加 appearance fingerprint / gate

增加只读的 visual fingerprint，至少覆盖：

- representation item class；
- mapped vs generated representation；
- `IfcStyledItem`；
- `IfcSurfaceStyle` / surface colour；
- transparency（存在时）；
- Material presentation reference。

`reuse_exact_existing` 的验收应增加 visual-fidelity predicate。若源 Type/reference 没有 visual authority，则记录 `not_applicable`，不能伪造 style。

### Step 4 — 最小验证

至少验证：

1. Beam exact existing Type + Type RepresentationMap；
2. Beam variable length + Material/SurfaceStyle；
3. Column 同类路径；
4. 源 Type 无 style 时保持无 style，不新增猜测颜色；
5. Window / Door 既有 mapped representation 行为不回归；
6. R1 A1 重新生成后人工 Viewer 检查与机器 visual fingerprint 同时通过。

## 6. 完成标准

只有同时满足以下条件，才可以把该问题标记为修复：

- exact Type GlobalId 仍正确；
- geometry / placement / Storey 既有门禁保持通过；
- Type authority fingerprint 不被非法修改；
- 新 occurrence 的 appearance 与授权的 Type/material/reference authority 一致；
- 无 source appearance 时不凭空创建颜色；
- 至少一个真实 IFC 在 Viewer 中不再以错误默认灰色显示；
- 新 visual-fidelity regression 在 reopen 后可独立重算。

## 7. 推荐实现顺序

```text
1. A1 / fixture 红色回归
2. appearance inspection + fingerprint
3. Type RepresentationMap 映射
4. variable-length geometry 的 style/material 复用
5. Beam + Column focused tests
6. A1 reopen + Viewer 人工检查
7. 再决定是否纳入更强的 R1/后续 Proof gate
```

本计划只解决“Type 精确复用时视觉外观丢失”的确定性缺口，不扩展新的结构构件几何能力，也不修改历史 accepted Proof。
