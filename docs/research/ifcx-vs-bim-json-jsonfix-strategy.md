# IFCx 与 BIM JSON 对照及 jsonfix 合并方案

本文用于比较 `buildingSMART/IFC5-development` 中 IFCx alpha JSON 思路与
text2IFC 当前 BIM JSON 2.0 的差异，并提出 jsonfix 阶段可以吸收的结构方向。

它不是最终 BIM JSON 3.0 规范，也不是 IFC5 到 IFC2X3 的转换规范。本文的目的
是帮助决策：在最终仍输出 IFC2X3 的前提下，哪些 IFCx 思想值得引入
text2IFC 的 JSON 表达。

## 结论

jsonfix 阶段不应把 text2IFC 直接改成 IFCx，也不应把 IFC5 alpha schema 当成
IFC2X3 的替代品。更合理的路线是：

```text
保留 BIM JSON 的语义实体清晰度
+ 吸收 IFCx 的 layer / patch / inherits / namespace 思想
+ 继续用 IFC2X3 registry、validator、compiler 作为真实输出边界
```

换句话说，IFCx 适合启发“怎么组织可增量修复的 JSON”，而 BIM JSON 继续承担
“让自然语言模型输出可验证、可编译 IFC2X3 语义”的任务。

## 当前 BIM JSON 2.0 的定位

text2IFC 当前 BIM JSON 2.0 是 IFC2X3 语义输入和训练标签合同。它的顶层结构是：

```json
{
  "schema_version": "bim-json/2.0",
  "ifc_schema": "IFC2X3",
  "units": {},
  "entities": [],
  "relationships": [],
  "provenance": {}
}
```

它的核心特点：

- `entities[]` 保存用户可理解的 IFC 对象，例如 `IfcWall`、`IfcSpace`。
- `relationships[]` 保存显式 IFC 关系，例如 `IfcRelVoidsElement`。
- `ifc_class` 是每个语义实体的明确字段。
- `ObjectPlacement` 使用 parent-relative placement。
- `Representation` 使用语义几何，例如 `extruded_profile`。
- 低层 IFC 对象由 compiler 生成，例如 `IfcCartesianPoint`、`IfcDirection`、
  `IfcLocalPlacement`、`IfcOwnerHistory`。
- Formal BIM JSON 必须完整、验证通过，Draft Envelope 用于保存不完整或不支持内容。

这个设计对自然语言生成友好：模型只需要输出墙、门、窗、空间、位置、尺寸、
属性、关系，不需要输出 STEP 行号、mesh 面索引或低层 IFC helper 对象。

## IFCx alpha 的定位

IFCx alpha 文件的顶层结构是：

```json
{
  "header": {},
  "imports": [],
  "schemas": {},
  "data": []
}
```

核心内容在 `data[]`。每个数据片段是一个节点：

```json
{
  "path": "node-id-or-path",
  "children": {},
  "inherits": {},
  "attributes": {}
}
```

IFCx 的核心特点：

- 节点本身不固定为墙、门、窗，IFC 类通过 `attributes["bsi::ifc::class"]` 表达。
- 同一个 `path` 可以出现多次，每次补充一部分事实。
- `imports` 引入外部 schema layer。
- `schemas` 可以定义本文件新增的属性类型。
- `children` 表达树结构或组成关系。
- `inherits` 表达类型复用或模板复用。
- `attributes` 可以挂 IFC、OpenUSD、材料、分类、空间边界等不同命名空间下的事实。
- `Federate -> Flatten -> Compose` 把多个 layer 合成为最终 tree。

## 关键差异

| 对比点 | BIM JSON 2.0 | IFCx alpha |
|---|---|---|
| 主要目标 | 自然语言到 IFC2X3 的语义输入和训练标签 | IFC5 alpha 示例、组合场景、layer/federation |
| 顶层组织 | `entities[]` + `relationships[]` | `data[]` 节点片段 |
| 对象类型 | `ifc_class` 是固定字段 | IFC class 是 `attributes` 中的命名空间属性 |
| 增量修改 | 目前主要依赖 Draft 或完整文档替换 | 原生支持多 layer、同 path 叠加 |
| 类型复用 | Phase 4 已支持部分 type reuse，但表达仍偏显式关系 | `inherits` 是基础机制 |
| 几何表达 | 语义 extrusion、profile、placement | 示例中大量使用 OpenUSD mesh 和 transform |
| 适合 LLM 输出 | 较适合 | 不完全适合，尤其 mesh 和矩阵较低层 |
| 输出边界 | IFC2X3 compiler | IFC5 alpha viewer/composer 示例 |
| 标准稳定性 | 项目内已验证、绑定 IFC2X3 | alpha，字段与覆盖范围仍会变化 |

## IFCx 的优势

### 增量层适合补全缺失内容

IFCx 的 FireRating 示例说明，一个增量文件可以只写：

```json
{
  "path": "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b",
  "attributes": {
    "bsi::ifc::prop::FireRating": "R30"
  }
}
```

这对 text2IFC 很有价值。如果未来出现“已有 IFC 文件被拿掉一块，希望用自然
语言补全”的场景，我们不应该直接覆盖原始 IFC 提取结果，而应该新增补全层：

```text
source IFC2X3 extraction layer
+ user natural-language patch layer
+ agent clarification patch layer
+ validation repair layer
= composed semantic model
```

这样可以保留原始事实、用户补充、Agent 推断、验证修复之间的来源边界。

### 多作者和多阶段事实更容易审计

IFCx 的 layer 模型天然适合记录“谁在什么时候补了什么”。这对 text2IFC 的多轮
Agent 也有意义：

- 原始 IFC 提取器提供 base layer。
- 用户自然语言提供 intent layer。
- 专家 Agent 提供 interpretation layer。
- Validator 提供 diagnostics layer。
- 用户确认提供 confirmation layer。

每一层都可以保留 provenance，而不是只保存最终结果。

### inherits 更适合类型复用

在 Hello Wall 中，两个窗实例通过 `inherits` 复用同一个窗类型。这个设计比重复
粘贴窗框、玻璃、洞口结构更干净。

对 BIM JSON 来说，后续可以吸收这种思想，用更清晰的方式表达：

```json
{
  "types": [
    {
      "id": "window-type-1",
      "ifc_class": "IfcWindowType",
      "template": {}
    }
  ],
  "entities": [
    {
      "id": "window-1",
      "ifc_class": "IfcWindow",
      "type_ref": "window-type-1"
    }
  ]
}
```

具体字段名待确认，但方向是让类型复用成为 JSON 的一等概念，而不是只靠普通
关系隐藏表达。

### namespace 属性更统一

IFCx 使用类似下面的命名空间：

```text
bsi::ifc::class
bsi::ifc::prop::Height
bsi::ifc::material
usd::usdgeom::mesh
usd::xformop
nlsfb::class
```

它的优势是不同来源的事实可以在同一个 `attributes` 下共存，同时仍能看出来源。

BIM JSON 2.0 目前把内容分散在 `attributes`、`property_sets`、`materials`、
`relationships`。这对编译器清晰，但对增量 patch 和外部知识层可能略分散。

## BIM JSON 2.0 的优势

### 更适合自然语言模型输出

BIM JSON 2.0 的字段更接近用户语言：

```json
{
  "id": "wall-1",
  "ifc_class": "IfcWall",
  "attributes": {
    "ObjectPlacement": {},
    "Representation": {}
  }
}
```

模型可以直接理解“墙、位置、尺寸、属性、空间关系”。相比之下，IFCx 示例中的
mesh points、face indices、transform matrix 对模型来说太底层。

### 绑定 IFC2X3 数据集和验证器

当前项目的数据集是 IFC2X3。BIM JSON 2.0 已经绑定：

- IFC2X3 EXPRESS registry
- IFC2X3 property registry
- capability gate
- `validate_v2_document`
- IFC2X3 compiler
- reopened IFC verification

这保证它能落回当前项目最重要的目标：生成真实可打开、可验证的 IFC2X3。

### Formal / Draft 边界更安全

BIM JSON 2.0 已经明确：

- Formal 是完整、可验证、可编译文档。
- Draft Envelope 保存缺失事实、unsupported losses、clarification targets。
- Draft 不能直接进入 IFC compiler。

这比直接让模型输出任意 IFCx 节点更安全，也更适合训练和评估。

## 合并方案：不改目标，改组织方式

推荐的 jsonfix 方向是：**BIM JSON 继续作为 IFC2X3 semantic model，新增 IFCx
启发的增量层。**

可以先探索一个独立 patch envelope，而不是马上推翻 BIM JSON 2.0：

```json
{
  "patch_version": "bim-json-patch/1.0",
  "target_schema_version": "bim-json/2.0",
  "target_document_id": "source-model-id",
  "layers": [
    {
      "id": "user-repair-001",
      "kind": "semantic_patch",
      "provenance": {
        "source": "user-natural-language"
      },
      "operations": []
    }
  ]
}
```

这种方式有几个好处：

- 不破坏 BIM JSON 2.0 已有 compiler 和 validator。
- 可以单独测试 patch composition。
- 可以把自然语言补全先表达成 patch，再组合成 Formal BIM JSON。
- 如果 patch 失败，原始 JSON 不会被覆盖。
- 后续如果证明有效，再考虑升级为 BIM JSON 3.0。

## 可能的 patch 操作

以下操作是候选方向，不是最终规范：

| 操作 | 作用 | 示例场景 |
|---|---|---|
| `add_entity` | 新增语义实体 | 补一面缺失墙 |
| `set_attribute` | 设置或覆盖实体属性 | 补墙高、位置、名称 |
| `set_property` | 设置 property set 或 namespace property | 补 `FireRating` |
| `add_relationship` | 新增关系 | 补 opening 和 filling |
| `set_material` | 设置材料语义 | 补墙体材料层 |
| `mark_missing` | 显式记录仍缺少事实 | 用户不知道具体尺寸 |
| `mark_unsupported_loss` | 显式记录无法安全生成的源事实 | BRep 或 mapped geometry 暂不生成 |

删除操作需要谨慎。IFCx 中可以通过 `null` 删除 children 或 inherits。text2IFC
如果需要删除，建议先用显式 tombstone 或 review-required 操作表达，避免误删源事实。

## 针对“IFC 文件被拿掉一块”的建议流程

面向用户描述的未来场景，可以设计成：

```text
1. 打开原始 IFC2X3
2. 提取为 source BIM JSON base layer，并保留 source GlobalId/provenance
3. 检测缺失区域或由用户指出缺失内容
4. 用户用自然语言描述要补的内容
5. Agent 生成 semantic patch layer
6. patch composer 把 base layer 和 patch layer 合成为 candidate BIM JSON
7. validate_v2_document 或未来 validate_v3_document 验证
8. 编译为 IFC2X3
9. 重新打开 IFC 并运行空间、属性、关系、结构审计
10. 报告哪些来自原始模型，哪些来自补全 patch
```

这个流程里，Agent 不直接输出 IFC，也不直接输出低层 STEP。Agent 输出的是可审计
的语义 patch。

## 不建议吸收的部分

以下 IFCx 内容不建议直接进入 LLM 主输出格式：

- `usd::usdgeom::mesh.faceVertexIndices`
- 大量 mesh `points`
- 通用 4x4 transform matrix 作为主要 placement 表达
- IFC5 alpha class/schema 假设
- 运行时依赖远程 schema resolution 才能完成基础验证

这些内容适合 viewer 或高级几何层，不适合作为 text2IFC 第一阶段的自然语言输出。

## 推荐的 jsonfix 探索顺序

1. 写一个只读研究阶段，确认 IFCx layer、path、inherits、attributes 的可迁移边界。
2. 设计 `bim-json-patch/1.0`，只支持少量安全操作。
3. 写 patch composer，把 BIM JSON 2.0 base document 和 patch 合成 candidate document。
4. 所有 candidate 继续走 `validate_v2_document`。
5. 做一个最小补全 demo：已有房间缺一面墙，用户自然语言补墙，patch 合成后编译 IFC2X3。
6. 记录 source facts、patch facts、compiler-generated facts 的来源差异。
7. 如果 patch 模式稳定，再讨论 BIM JSON 3.0 是否要把 layer 作为正式顶层结构。

## 待确认问题

以下问题需要在正式 specification 前确认：

- BIM JSON 3.0 是否直接采用 `layers[]` 顶层，还是先保留独立 patch envelope。
- patch 操作是否允许删除源事实，还是只允许新增和显式覆盖。
- 节点寻址使用 `id`、`global_id`、路径式 `path`，还是三者并存。
- namespace property 是否进入 Formal BIM JSON，还是只进入 patch layer。
- type reuse 是继续用 IFC relationship 表达，还是新增 `types[]` / `type_ref`。
- 空间边界是否保持 `relationships[]`，还是增加类似 IFCx 的 boundary object。
- 复杂几何是否长期保留为 loss，还是未来支持一个受限 geometry layer。

## 建议的阶段边界

jsonfix 阶段应坚持以下边界：

- 输出仍然回到 IFC2X3。
- IFC2X3 EXPRESS 和 PSD registry 仍是 schema truth。
- IFCx 只作为 JSON 组织思想来源，不作为输出标准。
- 不让模型输出 raw IFC、STEP、`IfcCartesianPoint`、`IfcDirection`、
  `IfcOwnerHistory`。
- 不让模型直接输出 mesh 点面作为常规路径。
- 原始 IFC 提取事实不得被静默覆盖。
- patch 必须带 provenance。
- patch 合成结果必须通过 Formal validation 后才能进入 compiler。
