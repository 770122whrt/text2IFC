# IFCx Hello Wall 结构解析报告

本文用于帮助读者读懂 `buildingSMART/IFC5-development` 仓库中
`examples/Hello Wall/hello-wall.ifcx` 的 JSON 结构和编排方式。它不是
text2IFC 的实现规范，也不把 IFC5 alpha 示例等同于稳定标准。

## 结论

`hello-wall.ifcx` 不是“一个对象完整描述一个 IFC 实体”的格式。它更像一组
可叠加的节点片段：每个片段用 `path` 指向同一个语义对象或几何对象，再通过
`children`、`inherits` 和 `attributes` 拼成最终场景。

这个文件最值得关注的思想是：

- 模型内容可以分层增添，不必每次重写整份 JSON。
- 同一个 `path` 可以多次出现，后出现的属性会覆盖或补充前面的属性。
- `inherits` 用来复用类型或模板，适合表达窗类型、材料模板、构件组合。
- IFC 类、属性、材料、分类、几何都挂在 `attributes` 上，并使用命名空间。

## 证据来源与边界

本报告基于以下已读取内容：

- `buildingSMART/IFC5-development/README.md`
- `buildingSMART/IFC5-development/Examples_FAQ.md`
- `buildingSMART/IFC5-development/schema/ifcx.tsp`
- `buildingSMART/IFC5-development/examples/Hello Wall/hello-wall.ifcx`
- `buildingSMART/IFC5-development/examples/Hello Wall/hello-wall-add-fire-rating-30.ifcx`
- `buildingSMART/IFC5-development/examples/Hello Wall/hello-wall-add-fire-rating-60.ifcx`
- `buildingSMART/IFC5-development/src/ifcx-core/composition/compose.ts`
- `buildingSMART/IFC5-development/src/ifcx-core/workflows.ts`
- `buildingSMART/IFC5-development/src/ifcx-core/layers/layer-stack.ts`

需要注意：

- IFC5-development 仓库声明这些示例处于 alpha 阶段，仍会变化。
- `schema/ifcx.tsp` 自身注释说明它只覆盖当前示例模型，不覆盖完整 IFC5。
- `Examples_FAQ.md` 说明 units 后续才会文档化，因此本报告不推断完整单位规则。
- `originalStepInstance` 只用于示例中展示与 SPFF/STEP 的关系，不代表 IFC5 会保留 STEP 语法。

## 顶层结构

`hello-wall.ifcx` 顶层由四块组成：

```json
{
  "header": {},
  "imports": [],
  "schemas": {},
  "data": []
}
```

这四块的作用如下。

| 字段 | 作用 | Hello Wall 中的内容 |
|---|---|---|
| `header` | 文件身份和版本元信息 | `id`、`ifcxVersion`、`dataVersion`、`author`、`timestamp` |
| `imports` | 引入外部 schema layer | IFC core、IFC prop、IFC material、OpenUSD、NLSfB |
| `schemas` | 本文件自定义属性 schema | 只定义了 `customdata.originalStepInstance` |
| `data` | 实际模型节点片段 | 62 个节点片段 |

这里的 `imports` 很关键。Hello Wall 本身没有把所有 IFC 属性定义塞进文件里，
而是引用外部层，例如：

- `https://ifcx.dev/@standards.buildingsmart.org/ifc/core/ifc@v5a.ifcx`
- `https://ifcx.dev/@standards.buildingsmart.org/ifc/core/prop@v5a.ifcx`
- `https://ifcx.dev/@standards.buildingsmart.org/ifc/ifc-mat/ifc-mat@v1.0.0.ifcx`
- `https://ifcx.dev/@openusd.org/usd@v1.ifcx`
- `https://ifcx.dev/@nlsfb/nlsfb@v1.ifcx`

这说明 IFCx 的属性系统倾向于“命名空间 + schema layer”，而不是把所有字段写成
固定顶层结构。

## 节点结构

`schema/ifcx.tsp` 中的核心节点模型是：

```typespec
model IfcxNode {
    path: path;
    children?: Record<string | null>;
    inherits?: Record<string | null>;
    attributes?: Record<unknown>;
}
```

对应到实际 JSON，节点通常长这样：

```json
{
  "path": "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b",
  "attributes": {
    "bsi::ifc::class": {
      "code": "IfcWall",
      "uri": "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/IfcWall"
    }
  }
}
```

三个可选字段的含义：

| 字段 | 可以理解为 | Hello Wall 中的例子 |
|---|---|---|
| `children` | 组成关系或树结构 | 楼层包含 `My_Space` 和 `Wall` |
| `inherits` | 类型复用或模板继承 | 两个窗实例继承同一个窗类型 |
| `attributes` | 具体事实 | IFC class、属性、材料、mesh、transform、space boundary |

## Hello Wall 的树骨架

文件前部先给出一棵场景树：

```text
ab143...                         root-like node
└── My_Project -> 14adb...        IfcProject
    └── My_Site -> e083...        IfcSite
        └── My_Building -> e84d...        IfcBuilding
            └── My_Storey -> 44af...      IfcBuildingStorey
                ├── My_Space -> e303...   IfcSpace
                └── Wall -> 9379...       IfcWall
```

这棵树只说明“谁包含谁”。这些节点到底是不是 `IfcProject`、`IfcWall`，不是在
`children` 里声明的，而是在后续 `attributes["bsi::ifc::class"]` 中补充的。

例如楼层节点先出现为：

```json
{
  "path": "44af358b-3160-4063-8a89-a868335ff3b5",
  "children": {
    "My_Space": "e3035b71-bd9f-4cdc-86fd-b56e2f4605b6",
    "Wall": "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b"
  }
}
```

后面再用同一个 `path` 补充它的 IFC 类：

```json
{
  "path": "44af358b-3160-4063-8a89-a868335ff3b5",
  "attributes": {
    "bsi::ifc::class": {
      "code": "IfcBuildingStorey",
      "uri": "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/IfcBuildingStorey"
    }
  }
}
```

## Class 是属性，不是固定字段

Hello Wall 中出现的主要 IFC 类包括：

| `path` | `bsi::ifc::class.code` |
|---|---|
| `14adb22b-d474-48a2-8e8f-6d4c067c1953` | `IfcProject` |
| `e0834921-e095-40f0-8874-3c6bd1ec699e` | `IfcSite` |
| `e84dc79e-fe9d-4781-9f4b-54dd435cca91` | `IfcBuilding` |
| `44af358b-3160-4063-8a89-a868335ff3b5` | `IfcBuildingStorey` |
| `e3035b71-bd9f-4cdc-86fd-b56e2f4605b6` | `IfcSpace` |
| `93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b` | `IfcWall` |
| `25503984-6605-43a1-8597-eae657ff5bea` | `IfcWindow` |
| `2c2d549f-f9fe-4e22-8590-562fda81a690` | `IfcWindow` |
| `592504dc-469a-44d6-9ae8-c801b591679b` | `IfcWindow` |

这体现了 IFCx 的泛化方式：节点本身不预设类型，类型通过 `attributes` 表达。

## 同一个 path 多次出现

`93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b` 这面墙在文件中多次出现：

1. 先定义 `children`：`Body`、`Axis`、`Directrix`、`Basis`、两个 `Window`。
2. 再补 `customdata.originalStepInstance`。
3. 再补 `bsi::ifc::class = IfcWall`。
4. 再补 `bsi::ifc::prop::IsExternal = true`。
5. 再通过 `inherits` 继承材料节点。
6. 再补 `nlsfb::class` 分类。
7. 再补 `bsi::ifc::prop::Volume` 和 `bsi::ifc::prop::Height`。

这种编排方式说明 IFCx 不要求一个节点一次性完整。它允许不同作者、不同文件、
不同处理阶段为同一个 `path` 逐步补充事实。

## inherits 与类型复用

文件开头定义了一个窗类型节点：

```json
{
  "path": "25503984-6605-43a1-8597-eae657ff5bea",
  "children": {
    "Void": "8fada721-cff8-590b-8d0b-9300b5fe8e18",
    "Frame": "08f06095-3f32-55b9-a353-61c9aca5cc4d",
    "Glazing": "5ad6f475-c04c-5628-8b9d-75d0bab0c0e5"
  }
}
```

两个窗实例通过 `inherits` 复用这个类型：

```json
{
  "path": "2c2d549f-f9fe-4e22-8590-562fda81a690",
  "inherits": {
    "windowType": "25503984-6605-43a1-8597-eae657ff5bea"
  }
}
```

这意味着窗实例不需要重复定义 `Void`、`Frame`、`Glazing` 的结构。组合阶段会把
类型节点中的 children 和 attributes 展开到实例上。

## 几何与位置

Hello Wall 中的几何主要以 OpenUSD 风格表达，例如：

```json
"usd::usdgeom::mesh": {
  "faceVertexIndices": [...],
  "points": [...]
}
```

位置变换使用：

```json
"usd::xformop": {
  "transform": [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [1.76767492294312, 0, 1, 1]
  ]
}
```

这说明 IFCx 示例更接近“可视化/组合场景图”：几何可以是 mesh，位置可以是
矩阵。它对 viewer 很直接，但对自然语言生成来说较低层。

## 空间边界的表达

Hello Wall 把空间边界表达成对象属性：

```json
{
  "path": "c8ecbf4c-e37a-4489-9133-15163b8a904e",
  "attributes": {
    "bsi::ifc::spaceBoundary": {
      "relatedelement": {
        "ref": "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b"
      },
      "relatingspace": {
        "ref": "e3035b71-bd9f-4cdc-86fd-b56e2f4605b6"
      }
    }
  }
}
```

`Examples_FAQ.md` 明确说明，Hello Wall 包含一个把 space boundary 定义为对象
而不是关系的例子，并且 IFC5 的意图是保留这种方向。

这对 text2IFC 有启发：空间关系不一定都要塞进 `IfcRel*` 风格的关系实体中，
也可以作为语义边界对象或属性层存在。

## 增添式 JSON 示例：FireRating layer

`hello-wall-add-fire-rating-30.ifcx` 只做一件事：给已有墙节点补属性。

```json
{
  "path": "93791d5d-5beb-437b-b8ec-2f1f0ba4bf3b",
  "attributes": {
    "bsi::ifc::prop::FireRating": "R30"
  }
}
```

把基础文件和增量文件按顺序组合后，可以得到：

| 组合顺序 | 最终 FireRating |
|---|---|
| `hello-wall.ifcx` | 缺失 |
| `hello-wall.ifcx` + `hello-wall-add-fire-rating-30.ifcx` | `R30` |
| `hello-wall.ifcx` + `hello-wall-add-fire-rating-30.ifcx` + `hello-wall-add-fire-rating-60.ifcx` | `R60` |

这个行为来自 `compose.ts` 和 `workflows.ts` 中的规则：后出现的同名属性覆盖前面
的同名属性。

## 组合流程

IFCx 组合流程可以概括为：

```text
多个 ifcx 文件
  -> Federation：按 layer 顺序拼成一个 data 列表
  -> Flattening：按 path 合并，后来的 children / inherits / attributes 获胜
  -> Composition：展开 inherits，再递归展开 children
  -> composed tree
```

`compose.ts` 中的注释把这个过程称为 federation、flattening、composition。

关键规则：

- 多个节点可以指向同一个 `path`。
- 同一个 `path` 的 `children`、`inherits`、`attributes` 会被折叠。
- 后来的 layer 会覆盖前面的同名键。
- `inherits` 先把类型或模板上的 children 和 attributes 带入实例。
- `children` 再把子节点挂进树。
- `attributes` 最后写入当前节点。

## 读 IFCx 文件的建议顺序

读一个 `.ifcx` 文件时，不建议从第一行逐字读到最后。更有效的顺序是：

1. 先看 `header`，确认文件身份和 alpha 版本。
2. 看 `imports`，确认它依赖哪些 schema layer。
3. 看本地 `schemas`，确认有没有自定义属性。
4. 扫描 `data[].children`，画出骨架树。
5. 扫描 `attributes["bsi::ifc::class"]`，把节点映射成 IFC 类。
6. 扫描 `inherits`，找类型复用和模板复用。
7. 扫描几何属性，例如 `usd::usdgeom::mesh` 和 `usd::xformop`。
8. 扫描关系性属性，例如 `bsi::ifc::spaceBoundary`。
9. 最后看 patch/layer 示例，理解增量文件如何覆盖或补充基础文件。

## 对后续 text2IFC 阅读的启发

IFCx 的结构不是直接可复制的 text2IFC 目标格式，但它给了一个重要方向：

- 原始模型事实可以保留为 base layer。
- 用户自然语言补全可以变成 patch layer。
- Agent 澄清结果可以继续变成新的 patch layer。
- Validator 或 reviewer 的修正也可以是可审计 patch，而不是直接覆盖原文档。
- 最终用于 IFC2X3 编译的仍应是经过组合、验证后的 formal semantic model。

## 已知限制与待确认项

- 待确认：IFC5 正式版是否会保持当前 IFCx alpha 的字段和组合行为。
- 待确认：IFCx 发布侧完整 JSON Schema 的稳定位置和版本策略。
- 待确认：`usd::xformop` 矩阵与 IFC placement 在完整 IFC5 语义中的长期映射方式。
- 已知限制：Hello Wall 只覆盖少量实体、属性和关系，不能代表完整 IFC5。
- 已知限制：units 尚未完整文档化，不应从示例数值直接推断最终标准单位规则。
