# BIMNet IFC数据管线方法论

## 1. 研究背景与目标

### 1.1 问题定义

Text2BIM的核心任务是将自然语言建筑描述自动转换为标准BIM模型（IFC格式）。这是一个跨模态生成问题，涉及：

- **语义理解层**：从文本中提取建筑意图（楼层、结构类型、空间布局、构件参数）
- **结构化映射层**：将建筑意图转化为IFC实体参数（构件类型、几何尺寸、拓扑关系）
- **物理生成层**：用IFC SDK程序化创建符合标准的BIM模型

### 1.2 技术路线选择

我们采用**分层管线**而非端到端方案，理由：

| 方案 | 优势 | 劣势 |
|------|------|------|
| 端到端（文本直接生成IFC STEP） | 简洁 | IFC语法复杂，生成正确率低 |
| 分层管线（文本→结构化参数→IFC） | 可调试、可验证、可扩展 | 需要定义中间表示 |

分层方案的每一层都可以独立验证，错误可定位到具体层级。

### 1.3 数据基础

使用Scan-to-BIM 2025挑战赛数据集：

- 来源：Tianjin University校园13栋真实建筑
- 规模：23个场景（train 18 / test 5）
- 格式：IFC2X3 coordination view
- 构件类型：结构（墙/柱/梁/板）+ 围护（门/窗）+ MEP（本数据集为空）
- 点云：24亿点（TLS扫描，待下载）

---

## 2. IFC解析方法论

### 2.1 IFC数据模型理解

IFC采用EXPRESS语言定义的面向对象数据模型，核心层级为：

```
IfcProject
  └─ IfcSite
       └─ IfcBuilding
            └─ IfcBuildingStorey
                 ├─ IfcWall / IfcWallStandardCase
                 ├─ IfcColumn
                 ├─ IfcBeam
                 ├─ IfcSlab
                 ├─ IfcDoor
                 ├─ IfcWindow
                 └─ IfcStair / IfcStairFlight
```

每个实体通过以下机制关联：

- **IfcRelContainedInSpatialStructure**：构件→楼层的空间归属
- **IfcRelAssociatesMaterial**：构件→材料的关联
- **IfcRelVoidsElement**：墙→洞口的开洞关系
- **IfcRelAggregates**：父级→子级的聚合关系

### 2.2 多层级信息提取策略

我们设计了三个层级的信息提取：

#### Level 1：完整实体导出（Full Dump）

对IFC文件中的每个实体，导出其全部属性、属性集、几何表达、材料关联和空间关系。输出为结构化文本，保留IFC的全部语义信息。

```python
# 核心提取逻辑
def dump_entity_detail(ifc, entity, lines):
    # 1. 基本属性（Name, GlobalId, ObjectType, Tag）
    info = entity.get_info(include_identifier=False)

    # 2. 属性集（Pset_WallCommon, Pset_QuantityTakeOff等）
    psets = ifcopenshell.util.element.get_psets(entity)

    # 3. 材料关联（IfcMaterial, IfcMaterialLayerSet, IfcMaterialList）
    for rel in entity.HasAssociations:
        if rel.is_a('IfcRelAssociatesMaterial'):
            # 提取材料层、厚度、名称

    # 4. 几何表达（IfcExtrudedAreaSolid, IfcRectangleProfileDef等）
    if entity.Representation:
        for rep in entity.Representation.Representations:
            for item in rep.Items:
                # 提取截面类型、尺寸、拉伸深度

    # 5. 空间归属（所在楼层）
    for rel in entity.ContainedInStructure:
        # 提取楼层名称
```

**设计决策**：保留IFC实体ID（如`#366`）以便溯源验证。

#### Level 2：结构化JSON（Parsed Data）

从完整dump中提取建筑语义关键信息，组织为JSON格式：

```json
{
  "schema": "IFC2X3",
  "storeys": [{"name": "Level 1", "elevation": 0.0}],
  "walls": [{
    "name": "基本墙:Generic - 240mm:206341",
    "storey": "Level 1",
    "is_external": true,
    "load_bearing": false,
    "thickness": 240.0,
    "profile": {"type": "rectangle", "x_dim": 5000, "y_dim": 240, "depth": 3000}
  }],
  "columns": [...],
  "materials": ["Default Wall", "Glass", ...]
}
```

**信息保留策略**：
- 保留：构件名称、类型、空间归属、几何参数、属性值、材料
- 丢弃：IFC内部ID、OwnerHistory、几何表达上下文、样式信息

#### Level 3：自然语言描述（Description）

将结构化JSON转化为人类可读的建筑描述：

```markdown
# IFC模型描述: vt2_1.ifc

## 1. 建筑概况
本模型包含3个楼层：Level 1（标高0.00m）、Level 1.8（标高2.41m）、
Level 1.9（标高2.52m）。所有楼层均为地上楼层。

## 2. 结构体系
推断结构类型：**无法确定**
推断依据：所有墙体LoadBearing=False，柱子数量不足以判断框架体系

**数据质量说明：** 所有30面墙均标记为IsExternal=True，
这可能是源模型的建模约定或错误，而非实际建筑状况。
```

### 2.3 审查驱动的质量保障

采用**生成→审查→修复**的迭代流程：

1. **自动生成**：用脚本从IFC提取信息生成描述
2. **专业审查**：启动建筑/IFC专业agent交叉验证描述与原始数据
3. **问题分类**：按严重度分级（Critical/Medium/Low）
4. **定向修复**：针对系统性问题修改解析逻辑

审查发现的6类问题及修复方案：

| 问题 | 根因 | 修复方案 |
|------|------|----------|
| 楼板类型混算 | 未读取IfcSlab.PredefinedType | 按FLOOR/LANDING/ROOF分类统计 |
| 材料分类错误 | 关键词匹配缺少领域知识 | 建立材料分类规则（钢筋混凝土→混凝土，钢化玻璃→玻璃） |
| 结构类型武断推断 | 仅基于构件数量的简单规则 | 加入LoadBearing属性分析，无法判断时明确标注"无法确定" |
| 楼层计数失真 | 将所有IfcBuildingStorey视为真实楼层 | 分析标高间距，区分真实楼层和参考标高 |
| 外墙标记异常 | 直接呈现IsExternal值 | 添加数据质量声明 |
| 墙厚提取不全 | 仅从名称提取 | 从几何截面和材料层集双路径提取 |

---

## 3. IFC重建方法论

### 3.1 IfcOpenShell API能力评估

通过实验验证IfcOpenShell API支持程序化IFC生成：

```python
# 验证实验：从零创建包含所有构件类型的IFC
ifc = ifcopenshell.file(schema='IFC2X3')

# 创建层级结构
project = ifcopenshell.api.run('root.create_entity', ifc, ifc_class='IfcProject')
site = ifcopenshell.api.run('aggregate.assign_object', ifc, products=[...], relating_object=project)
building = ...
storey = ...

# 创建构件并添加几何
wall = ifcopenshell.api.run('root.create_entity', ifc, ifc_class='IfcWall')
ifcopenshell.api.run('geometry.add_wall_representation', ifc, context=context,
    length=5000, height=3000, thickness=240)

# 材料和属性
ifcopenshell.api.run('material.assign_material', ifc, products=[wall], material=mat)
ifcopenshell.api.run('pset.add_pset', ifc, product=wall, name='Pset_WallCommon')
```

**结论**：IfcOpenShell API覆盖了IFC创建所需的全部操作，包括：
- 项目层级结构（`aggregate.assign_object`）
- 构件创建（`root.create_entity`）
- 空间归属（`spatial.assign_container`）
- 几何表达（`geometry.add_wall_representation`等）
- 材料关联（`material.assign_material`）
- 属性集（`pset.add_pset`）

### 3.2 JSON→IFC重建流程

```python
def create_ifc_from_json(model, output_path):
    # 1. 初始化IFC文件和Owner信息
    ifc = ifcopenshell.file(schema=model['schema'])

    # 2. 创建项目层级（Project → Site → Building → Storey）
    for st_data in model['storeys']:
        storey = ifcopenshell.api.run('root.create_entity', ...)
        storey_map[st_data['name']] = storey

    # 3. 创建材料定义
    for mat_name in model['materials']:
        mat_map[mat_name] = ifcopenshell.api.run('material.add_material', ...)

    # 4. 创建建筑构件
    for w_data in model['walls']:
        wall = ifcopenshell.api.run('root.create_entity', ifc, ifc_class='IfcWall')
        # 添加几何（从profile参数）
        # 分配材料
        # 归属楼层

    # 5. 写入IFC文件
    ifc.write(output_path)
```

### 3.3 往返验证

对3个测试文件执行完整的IFC→JSON→IFC往返，比较构件数量：

| 文件 | 构件类型 | 原始 | 重建 | 匹配 |
|------|----------|------|------|------|
| vt2_1.ifc | Wall/Column/Slab/Door/Window | 30/1/1/6/7 | 30/1/1/6/7 | ✓ |
| i5n.ifc | Wall/Column/Slab/Door/Window | 22/0/2/6/8 | 22/0/2/6/8 | ✓ |
| hxp.ifc | Wall/Column/Slab/Door/Window | 34/0/1/7/3 | 34/0/1/7/3 | ✓ |

**往返丢失的信息**：
- 构件的精确几何位置（IFC LocalPlacement坐标）
- 构件间的连接关系（IfcRelConnectsPathElements）
- 开洞关系（IfcRelVoidsElement）
- 材料层集的详细厚度分配

**保留的信息**：
- 构件类型和数量
- 构件名称
- 楼层归属
- 材料关联
- 几何截面参数（部分）

---

## 4. Text2BIM管线架构

### 4.1 三层架构设计

```
┌─────────────────────────────────────────────────┐
│  Level 3: Natural Language ↔ Structured Params  │  ← 研究核心
│  "3层办公楼，框架结构" → {storeys:3, type:frame}│
├─────────────────────────────────────────────────┤
│  Level 2: Structured Params ↔ JSON              │  ← 已实现
│  {storeys:3, walls:[...]} ↔ JSON schema         │
├─────────────────────────────────────────────────┤
│  Level 1: JSON ↔ IFC                            │  ← 已验证
│  JSON ↔ IfcOpenShell API ↔ .ifc file            │
└─────────────────────────────────────────────────┘
```

### 4.2 Level 1：IFC↔JSON（已完成）

- **IFC→JSON**：`extract_ifc_to_json()` 提取全部建筑语义
- **JSON→IFC**：`create_ifc_from_json()` 重建IFC文件
- **验证状态**：往返测试通过，构件数量100%匹配

### 4.3 Level 2：JSON↔结构化参数（已完成）

- **JSON→描述**：`improved_descriptions.py` 生成自然语言描述
- **描述质量**：B-级（经审查修复后），主要构件数量准确

### 4.4 Level 3：自然语言↔结构化参数（待研究）

这是Text2BIM的核心研究问题。可能的技术路径：

#### 路径A：规则模板

```
输入: "3层办公楼，框架结构，每层4个房间"
解析:
  - 层数 → storeys: 3
  - 结构类型 → structure: frame
  - 空间布局 → rooms_per_floor: 4

生成规则:
  IF structure == frame:
    columns = rooms_per_floor * 4 (每房间4角各1柱)
    beams = columns * 2 (每柱连接2梁)
  IF storeys > 1:
    stairs = 1
```

**优势**：确定性强，可控
**劣势**：覆盖范围有限，难以处理复杂描述

#### 路径B：LLM Few-shot

```
System: 你是BIM专家。根据建筑描述生成JSON参数。

Example:
输入: "2层住宅，砖混结构，外墙240mm，内墙120mm"
输出: {
  "storeys": [{"name":"1F","elevation":0},{"name":"2F","elevation":3000}],
  "walls": [
    {"name":"外墙","is_external":true,"thickness":240,"load_bearing":true},
    ...
  ],
  "structure_type": "masonry"
}
```

**优势**：覆盖面广，能处理自然语言变体
**劣势**：输出格式不稳定，需要后处理验证

#### 路径C：混合方案（推荐）

1. LLM解析文本→粗粒度参数
2. 规则引擎细化→完整构件列表
3. 验证层→检查IFC标准合规性

### 4.5 训练数据构建策略

从现有25个IFC模型反向构建训练对：

```
IFC文件 → extract_ifc_to_json() → JSON
JSON → improved_descriptions.py → 自然语言描述
(自然语言描述, JSON) → 训练对
```

当前已有25个训练对。扩充策略：
- 对同一IFC生成多个不同粒度的描述（详细版/简洁版/指令版）
- 通过参数扰动生成变体（改层数、改墙厚、增减构件）
- 引入外部BIM数据集

---

## 5. 当前局限与下一步

### 5.1 已验证的能力

- IFC完整解析（构件、属性、几何、材料、空间关系）
- 结构化JSON中间表示
- JSON→IFC重建（构件层级和数量正确）
- 自然语言描述生成（经审查修复）

### 5.2 未解决的问题

1. **几何位置丢失**：往返过程中构件的精确位置坐标未保留
2. **拓扑关系丢失**：墙-墙连接、墙-洞口关系未重建
3. **描述→JSON映射**：Text2BIM核心问题，尚未开始
4. **评估指标**：缺乏衡量重建质量的自动化指标
5. **点云数据**：尚未下载，无法进行scan-to-BIM评估

### 5.3 下一步优先级

| 优先级 | 任务 | 理由 |
|--------|------|------|
| P0 | 下载点云数据 | 训练评估的必要输入 |
| P0 | 扩充训练对 | 25个样本不足以训练 |
| P1 | 实现规则模板baseline | 建立Text→JSON的基准线 |
| P1 | 设计评估指标 | 需要量化标准来比较方案 |
| P2 | LLM few-shot实验 | 探索更灵活的文本理解方案 |
| P2 | 几何信息保留 | 提升往返保真度 |

---

## 附录：关键文件索引

| 文件 | 用途 |
|------|------|
| `scripts/ifc_pipeline/enhanced_parser.py` | IFC→JSON解析器 |
| `scripts/ifc_pipeline/improved_descriptions.py` | JSON→自然语言描述 |
| `scripts/ifc_pipeline/roundtrip.py` | IFC↔JSON往返验证 |
| `scripts/ifc_pipeline/ifc_full_dump.py` | IFC完整信息导出 |
| `dataset/processed/ifc_parsed_enhanced.json` | 增强解析结果 |
| `dataset/processed/descriptions/REVIEW_REPORT.md` | 审查报告 |
| `dataset/processed/roundtrip_json/` | 往返中间JSON |
| `dataset/processed/roundtrip_ifc/` | 重建IFC文件 |
