# text2IFC 参数化门窗部件扩展计划 v1.0

日期：2026-09-24。状态：**Goal 开发中；S0／S1 编译验证通过；S2 已接通公开部件说明、Brief、生成和人工澄清恢复，单门／单窗的离线公开链路通过。真实模型阶段准入与整栋重建尚未完成。**

首阶段有 226 项定向回归及两个真实来源的单构件原生几何诊断；后续 S2 的测试和公开说明准备结果也见[结果与证据范围](../validation/ifc2text/component-v26/README.md)。目前没有真实 LLM 完整 loop 或整栋重建结果。

本文合并原部件计划、窗结构问答和 IFC 表示调查，是本次扩展的唯一计划。合并前内容保存在 Git 提交 `e8a926b0`，不再保留独立旧稿；原始调查 JSON 保留为证据附件。文档版本与产品 schema 版本分开管理。

## 1. 具体要做什么

让 text2IFC 根据自然语言描述，创建由**框、门板、百叶、把手等部件**组成的门窗。整体仍是一个 `IfcDoor`／`IfcWindow`，部件分别描述、编号和定位。

1. 扩展 Brief 和 BIM JSON，完整传递部件的几何、位置和引用。
2. 扩展编译器，把参数化部件生成真实 IFC 几何。
3. 扩展 IFC2Text，把支持的源构造写成可读、可重建的说明。
4. 不支持时返回具体内容，与 human 交互后再继续。
5. 分别测试单门和单窗，再测宿主安装，最后测完整建筑。

不为每种窗型增加模板，不以覆盖任意 BRep／网格为目标。旧模板保留为明确选择的简单建模路径。已获授权进入 Goal 开发；真实模型调用仍须完成对应阶段的离线准入。

## 2. 已确认的范围

| 内容 | 首版决定 |
|---|---|
| 构件与部件 | 一个门窗内包含多个几何项，部件不是独立建筑构件 |
| 几何 | 矩形、圆形、含孔多边形截面；直线挤出；平移、旋转放置；有限等距重复 |
| 材料与显示 | 保留已有整体材料；支持逐项颜色／透明度；部件物理材料后续单独验证接入 |
| Type | 按明确需求创建，与模板、几何分开；满足 IFC2X3 导出的实际合法性要求 |
| 输入不足 | 缺尺寸等信息时请求补充，不猜测细节 |
| 不支持 | 逐项列出对象、原因与影响，再由 human 选择“排除列明内容后继续”或“暂停”；前者产出其余部分并附拒绝清单，后者不生成；未明确选择时等待 |
| 精度 | 线性几何差 ≤1 mm 接受；数量、拓扑和材料错误单独判断 |
| 验证 | 门和窗都做；无视图输入，以 IfcOpenShell 读取和检查 |
| 暂不做 | 一般扫掠、旋转体、自由曲面、任意布尔、逐面 BRep／网格生成、外部构件库、IFC4 输出迁移 |

**自然语言可表达、参数化优先。** “带孔窗框＋十四片等距斜板”适合本路线；“精致的弯曲把手”只有名称，没有足够构造信息。支持必须同时满足：输入足以确定几何、合同能够表达、编译和独立检查能够验证。

旋转现有部件的放置，与绕轴生成旋转体不同，首版只有前者。简单 BRep 经已有且受验证的识别路径能恢复为允许的参数构造时，可以转换；不能证明等价则报告不支持，不开展任意 BRep 逆向工程。很多面不证明来自 GLB，工程软件导出的文件也可能不保留原建模参数。

## 3. 总体流程

```mermaid
flowchart TB
    S["源 IFC"] --> P["读取几何、单位、映射、材料与关系"]
    P --> T["公开说明：主体 + 部件目录 + 尺寸与放置"]
    T --> B["新版 Brief"]
    B --> J["LLM 按合同输出新版 BIM JSON"]
    J --> V["检查引用、几何与输入覆盖"]
    V --> C["确定性编译：一个门窗 + 多个几何项"]
    C --> R["重开 IFC，核查实际几何与关系"]
    R --> A["Audit：是否满足公开说明"]
    R --> Q["Compare：是否复现源 IFC"]
    S --> Q
    P -->|不支持| H["返回具体问题，与 human 交互"]
    V -->|缺参或不支持| H
    H -->|明确回答后重新检查| B
```

重建端只收到公开文本，包括部件目录、尺寸表和重复规则；不得暗中读取源 IFC、`source-facts.json` 或私有几何附件。保存源→事实→文本→Brief→BIM JSON→IFC→Compare，区分解析、描述、传播和编译问题。

人工完整描述→text2IFC 与源 IFC→IFC2Text→text2IFC 都要测试。前者检查生成与编译，后者检查描述链是否丢失信息。

## 4. 数据合同与 IFC 输出

### 4.1 主体、部件、几何项

| 层级 | 示例 | 作用 |
|---|---|---|
| 构件 ID | `N001` | 一个 IfcWindow，负责楼层、宿主、类型与名义尺寸 |
| 部件 ID | `N001/frame`、`N001/slat-07` | 描述与局部修改对象，需跨 IFC 重开可识别 |
| 几何项 ID | `N001/frame/solid-01` | 描述／BIM JSON 内引用，一个部件可有多个实体 |
| 几何定义 ID | `slat-definition-01` | 复用截面和长度，各实例仍有独立位置及部件 ID |

父门窗不额外生成一套完整几何，避免重复叠加。“主体”若指门板，应作为部件。角色不充当唯一 ID，两个部件均可为把手。STEP 行号如 `#2380` 只定位源文件，不作为稳定编号。

首版稳定引用到部件层，不承诺几何项 ID 在 IFC 中逐一恢复；部件内部按真实几何集合验证。错误跨门窗引用、循环、重复 ID、孤立几何项、重复所有权都要报错。重复先限数量、起点与等距平移向量，编译前确定性展开；修改 slat-07 不得改变全部叶片。规模上限在合同冻结前通过离线试验确定，不能按单例随意设置。

拟议结构（尚非已发布 schema）：

```text
N001 : IfcWindow
  placement / nominal_dimensions / opening_ref
  geometry.mode = component_geometry
  parts:
    N001/frame -> 带孔截面 + 挤出方向与长度
    N001/slat-01 ... N001/slat-14
      -> 共用叶片定义 + 各自局部放置
```

`template` 与 `component_geometry` 互斥，`type_id` 独立。部件模式缺参不能自动转成普通窗模板。LLM 输出受支持参数，RepresentationMaps 和 IFC 实体创建由编译器管理。

### 4.2 坐标、截面与安装

部件相对父门窗、几何项相对部件，轮廓在二维局部平面内；明确挤出方向和长度。统一毫米、声明角度单位，变换只组合一次。检查有限正尺寸、合法正交坐标、轮廓闭合、孔位于外环内、孔不相交和轮廓不自交；圆保留解析半径，不默认改成低边数多边形。

处理映射原点、映射目标、产品及几何项放置。缩放／反射仅在可证明等价时归一化，不能通过正交化丢失镜像手性；无法处理则明确报告。

名义宽高、安装洞口和实际外廓分开。把手和门套可外伸，不能扩大洞口或改名义尺寸来通过旧模板检查。安装参考包括 opening_ref、安装坐标系和公开说明中的偏移／参考轮廓；检查实际 Fills／Voids 关系和各部件位置。不能从实体并集重新推导名义尺寸，也不能以“小部件与墙相交”认定正确安装。

### 4.3 几何、身份和显示

输出一个门窗及其 ProductDefinitionShape，Body/SweptSolid 包含多个挤出实体。拟用真实 IfcShapeAspect 将部件关联到 Body items：Name 存部件 ID，Description 存版本化角色说明。旧模板原约定不变，新 reader 显式区分。重开按产品→ShapeAspect→实际几何核查，不能只检查自写属性 JSON。

ShapeAspect 没有独立放置字段。编译时把部件和几何项变换合入实体 Position；重开验证等价位置，不承诺恢复原参数变换树。可编辑参数层级由保存的 BIM JSON 维护。

首版不输出共享 RepresentationMap，复用定义先展开为实例几何。IFC2X3 ShapeAspect 关联 ProductDefinitionShape，不能照搬 IFC4 挂到 RepresentationMap。以后增加表示时，RepresentationType 必须匹配 Items，并核查交换视图兼容性，不能将 BRep 标为 SweptSolid。

颜色／透明度写入真实几何并读回。整体“木材、钢材”清单不能冒充“木门板、钢把手”的归属；明确部件材料需求保存在公开说明与缺项记录中，首版不宣称完成该语义。部件物理材料方案另行验证，不能直接使用 IFC4 的 IfcMaterialConstituentSet。

## 5. 不支持时如何与 human 交互

返回对象／部件、失败阶段、已知与缺失内容、结果影响及处理选择：补参数、修改需求、讨论扩展、明确接受部分模型、停止或稍后继续。

> D007 的八个边界实体中，有三项目前不能可靠转换为本版支持的挤出几何。尚未省略或替换它们，因此不能完整重建这扇门。可以讨论扩展能力，明确选择标注缺失的部分模型，或者暂停。

复用既有澄清／unsupported 字段和 SessionStore 交互入口，核查问题返回、等待、回答保存与恢复。缺参数可以补充，缺算法能力不能靠回答“继续”变为支持。编译异常进入故障诊断，不让 human 猜填建筑参数。

无回答时不降级、不发布完整成功、不持续调用 Provider。回答关联具体对象范围，新问题不能沿用旧授权。部分模型须明确同意且其输出路径已有合同与验证，标明全部缺项，与完整验收分开。文件版本不支持也应返回，不能改 FILE_SCHEMA 假装兼容。

## 6. 修改模块与版本

| 层 | 入口 | 变更 |
|---|---|---|
| IFC2Text | `facts.py`、`compact.py`、`compact_pipeline.py` | 原生读取部件、展开变换、输出公开目录；未知角色中性命名 |
| Brief | `design_brief.py`、`brief_plan_constraints.py`、schema | 保留部件、几何、引用、缺失项和来源，防止投影丢失 |
| 预期／覆盖 | `semantic_requirements.py`、`semantic_coverage.py`、`expected_facts.py` | 从公开 Brief 建立预期，不用候选自报内容作为全部真值 |
| 正式／Draft 合同 | `text2ifc_contract`、BIM JSON／Draft schema | 部件模式与校验；Formal 可编译，Draft 能说明缺失 |
| Agent 路由 | `authoring_contract.py`、`generation_contract.py`、Generator／Audit／CLI | 版本、能力说明和恢复；首版用 legacy_full，不默认支持 staged／旧 changeset |
| 编译 | `geometry.py`、`basic_filling.py`、bootstrap／compiler | 多实体、圆和内孔、ShapeAspect、重开与原子输出 |
| 安装／显示 | `placement.py`、`polygon_wall.py`、presentation／part_readback | 坐标、外伸检查，按部件 ID 写入和读取显示 |
| 比较 | `precision_compare_v11.py` 及独立测量 | 新版增加内部形状、孔和部件，新旧候选统一重评分 |

候选版本为 **BIM JSON 2.6、Brief 2.9、Draft 1.6、authoring contract 1.6**；实施前再次确认占用。新增而不改写旧合同，同步 schema hash、registry、prompt/profile、消费者白名单和测试。调查脚本能打开 IFC4 不等于产品全链支持 IFC4，不顺带扩大输入版本。

两项静态发现须先复现：`presentation/generation.py` 的部件外观写入和检查只识别 2.2／2.3，而合同已接受 2.4／2.5；`compiler.py` 的 builder／异常处理位置可能使几何异常未进入预期终端路径。分别建立跨版本红灯和失败原子性测试后修复，不当作已解决问题。

## 7. 实施顺序与验收

| 阶段 | 内容 | 通过条件 |
|---|---|---|
| S0 基线与合同 | 固定当前代码／必要未提交改动、版本、案例及预期，冻结新 schema | 旧输入保持；部件身份、几何、缺参与 unsupported 可验证，先建立相关红灯 |
| S1 编译 | 不经 LLM 的部件 JSON→IFC→重开 | 单门、单窗均通过圆、孔、数量、位置、显示、身份和失败原子性检查 |
| S2 描述与传播 | IFC2Text→文本→Brief→BIM JSON，先 fake／frozen-replay | 部件均有去向；错误、澄清和人工恢复正确，源不变、无隐藏源输入 |
| S3 单构件真实实验 | 单窗、单门分别运行完整链路，保存全部尝试 | 两类均通过，不能以窗代门；真实调用前阶段准入有效 |
| S4 安装小场景 | 门、窗分别放进最小墙＋开口＋楼层 | 朝向、切洞、外伸、放置和归层正确 |
| S5 整栋 | 先处理 hxp 未支持项，再运行建筑 | 不支持项有人工决定；部分输出不算整栋完整成功 |
| S6 局部修改 | 只改某片百叶或某个部件 | 目标改变，其余部件、墙和关系保持 |

单构件 IFC 包含合法项目所需的最小结构；未测宿主时安装项标为未评估。首批必须有 N001 百叶窗、旋转／不同规格窗、D001／D002 双扇门至少一扇、D003–D006 含圆截面门至少一扇、D007 不支持交互和四种旧模板回归。hxp 是已见诊断集，另冻结来源隔离的门、窗留出案例，同源派生文件不得跨集合。

比较同时保留两条路径：公开部件预期→输出真实部件关联；源父构件的**完整 Body**→输出完整几何。第二条不能按提取器已识别清单过滤源实体，防止解析、描述与比较一起漏项。

必须检出：外框相同但少百叶、叶片角度错、内孔填实、把手遗漏、重复实体、镜像丢失、父变换重复、单改一片却全部变化。允许等价几何分割，不要求 STEP 实体数相同；语义部件数量与重复占据另查。

线性误差 ≤1 mm。数量／拓扑不适用距离容差，面积／体积不能直接套“1 mm”。使用真实几何与独立截面／表面测量交叉检查，明确网格精度和未评估项；旧新候选使用同一评价器，不把评价器变化当作生成提升。

复用合同的 geometry／placement／type-family 测试，编译的 v2_geometry、basic_filling、polygon_wall_hosts_v24、part_appearance、coordinated_appearance、compiler_boundary、v2_compilation，以及材料清单相关测试。遵循 [Agent 能力验证协议](../validation/agent-capability-evaluation.md)：新阶段先完成适用离线全公开链路准入；普通修复做相关范围回归；Full Preflight 另行说明并获批准。真实失败回到离线定位并计入分母。Audit 通过不等于源模型保真，单例通过不等于普遍支持。

## 8. Git、版本与回退

合并前文档基线为 `e8a926b0`，计划合并提交为 `c612e8e8`。旧稿可用 `git show e8a926b0:<原路径>` 查看，不保留多个活动计划。开发开始前已备份相关未提交文件；依赖的 2.4／2.5 schema、墙体和材料修复单独保存为代码基线 `4ff01db5`。

实施前建立**可复现代码基线**：当前有历史未提交改动，不能只记 HEAD。识别依赖后按明确文件／改动块整理，必要时建立隔离分支并保留原工作区。按合同、编译、解析、Agent、比较等单元提交和推送 `codex/` 分支，不自动合入 main。

每次运行固定 Brief、BIM JSON、Draft、作者合同、prompt/profile、编译器和比较器版本。新路径显式选择、旧路径可重放；新部件请求送旧版本应明确不支持，不能降级成模板。恢复不得半新半旧，不可逆存储迁移另行讨论。

S1–S3 回退演练：新组合运行并保存→旧组合重放旧案例→验证旧行为→确认旧版不误接受新部件输入。必要时切换旧组合或回退本功能提交，不 reset 脏工作区，不删源文件、旧输出和失败证据。回退保证旧能力可用，不会让旧版获得部件能力。

## 附录 A：IFC 结构与 N001 示例

系统模板是本项目的建模规则；IFC Type 是类型对象；Representation 是形状；Material 是物理材料；SurfaceStyle 是显示外观。IFC2X3 的 IfcWindowStyle 是窗类型，不是颜色 Style。它们通过不同引用连接，不是一个单一上下级目录。

BRep 用面、边界及连接关系围出实体。长方体也可表示为简单 BRep，更一般的 BRep 可包含曲面，不等于密集三角网格。工程师通常用截面、尺寸、挤出、扫掠、切孔和阵列，软件计算边界；导出后不一定保留完整参数历史。首版借鉴参数化构造，不逐面生成。

源为 `dataset/external/bimnet/hxp.ifc`，IFC2X3；SHA-256：`31f8f5a05b1965e2ab11122559385203229f316a4ea8fe15feec31c86d80d942`。N001 是 #2618，GlobalId=`1N$DqFwUP2Cfj_f4x$_L4e`，Name=`单扇百叶窗:高1100宽850:28872`，ObjectType=`单扇百叶窗:高1100宽850`，Tag=`28872`，OwnerHistory=#41，Description 为空。

```text
#2618 IfcWindow
  ObjectPlacement -> #10379
  Representation -> #2611 ProductDefinitionShape
    -> #2609 Body / MappedRepresentation
    -> #2607 IfcMappedItem (source=#2591, target=#2293)
    -> #2591 IfcRepresentationMap (origin=#2590)
    -> #2588 Body / SweptSolid
    -> #2380、#2390 ... #2510：14 个叶片挤出体
       #2536：带孔窗框挤出体
  Type：经 #10114 IfcRelDefinesByType -> #2593 IfcWindowStyle
  Material：经 #10052 IfcRelAssociatesMaterial -> #2597
  Installation：经 #10375 IfcRelFillsElement -> #10369 开口 -> #842 墙
```

类型 #2593 的 RepresentationMaps 包含 #2591，但仅有关联 Type 不够，实例必须通过 MappedItem 实际引用它。映射、比例和实例放置均影响结果；修改 OverallWidth 不会自动重画叶片。本例 #2590／#2293 为单位变换、比例 1。

类型名为“高1100宽850”，ConstructionType／OperationType=NOTDEFINED，ParameterTakesPrecedence=False，Sizeable=False，#2592 LiningProperties 几何参数为空。实例 IsExternal=True，Reference=“高1100宽850”，Manufacturer 为空；未填写不等于已知没有。

以下是拟议公开描述，尚非已实现输入格式：

> **N001 窗**：名义宽 850、高 1100。局部 X 沿宽、Y 沿深、Z 向上。局部原点的世界坐标为 (6196,3439.305336082839,−285)；X 指向世界 (0,−1,0)，Y 指向 (1,0,0)，Z 指向 (0,0,1)。填充源 #10369 开口，宿主为 #842“基本墙:墙240:7073”。
>
> **N001/frame**：在局部 XZ 平面定义外矩形 X=0…850、Z=0…1100，内孔 X=40…810、Z=40…1060；沿 +Y 挤出 240，Y=0…240，框边宽 40。
>
> **N001/slat-01…14**：每片以居中 60×20 矩形截面沿 +X 挤出 770；起始截面中心为 (40,120,zₖ)，zₖ=90+k×920/13，k=0…13。60 边单位方向为 (0,−1/√2,+1/√2)，20 边方向为 (0,−1/√2,−1/√2)。由此确定倾向、尺寸、间距与首片位置，不能只写“倾斜 45 度”。

排列规则与源解析值最大残差约 `1.38×10⁻¹¹ mm`，仅证明源规律，不是新编译器验证。

材料 #2597 为“金属漆_冷灰”，#10052 同时关联实例、类型及其他对象，不能推断底层合金、涂层厚度或逐项材料。十五项的 StyledItem 指向 #2539 SurfaceStyle／#2538 Rendering：RGB≈(0.24706,0.27843,0.30196)，Transparency=0，SpecularColour=0.5，SpecularExponent=64，ReflectanceMethod=NOTDEFINED。高光仅记录为源事实，首版只承诺颜色／透明度，不能宣称完整外观等价。

源窗在 #132“标高 3”（40 mm），宿主墙在 #126“地板标高”（−1140 mm），存在归层不一致。既有实验在副本中随宿主归层；不得修改源或把归一化结果称为原始关系。

现有 basic_filling/1.0 有 window-single、window-double-vertical、door-left、door-right 四种模板。它们内部能创建多个实体，但不等于支持任意部件输入。“单玻璃窗 850×1100、框宽 40”不能代替十四片百叶描述。

## 附录 B：数据调查与证据

2026-09-24 定向抽查八份文件，七份可读取，一份 IFC2X2 未评估；八份源 hash 前后相同。只做结构读取，未运行生成、完整 schema 校验或保真测试。按 Body 展开映射，以实例计几何项；这些数量不是唯一共享定义数或语义部件数。

| 文件（相对 dataset/external） | 应用／IFC | 窗 | 门 |
|---|---|---|---|
| `bimnet/hxp.ifc` | Revit 2020／2X3 | 3 窗，45 挤出体 | 7 门，50 挤出体＋8 BRep |
| `xbim-essentials-examples/House.ifc` | Renga 2.2／2X3 | 23 个映射面模型 | 19 个映射面模型 |
| `bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc` | Revit 2021／2X3 | 21 窗，84 挤出体 | 5 门，39 BRep＋12 挤出体 |
| `gni-bim-dataset/2025_BIMfundamentals/model_0.ifc` | Revit 2024／4 | 73 窗，410 面集 | 25 门，194 面集 |
| `scan-vs-bim-quality/20260916/Test model 1.1.ifc` | SketchUp 2015／2X3 | 5 窗，各一 BRep | 3 门，各一 BRep |
| `ifc-bench/projects/fantasy_hotel_1/arc.ifc` | Revit 2024／4 | 73 窗，410 面集 | 25 门，194 面集 |
| `gni-bim-dataset/normalized-ifc4/model_80.ifc` | Revit 2026／4 | 121 窗，786 面集 | 10 门，101 面集 |
| `duraark/SGD_Munkerud/SGD_Munkerud_Arch-1.ifc` | 2X2_FINAL | 未评估 | 当前库不支持，未转换 |

原始证据：[结构统计](../reports/ifc-representation-survey-2026-09-24/source-structure-survey.json)、[实体展开与同源检查](../reports/ifc-representation-survey-2026-09-24/supplementary-inspection.json)。首次在 IFC2X2 文件读取退出的情况保留，未通过改版本字符串绕过。

House 窗 #9143 的一个面模型含 58 个面；TallBuilding 门 #10949 有 39 个 BRep、1,102 个面；GNI 窗 #6843 有五个面集、四十个面；SketchUp 窗 #3677 有一个 BRep、十四个面且无 Type。面数、几何项数和部件数不能混用。

GNI model_0 与 fantasy_hotel 的 98 个门窗 GlobalId 集合相同，文件字节及完整 Body 引用文本不同，尚未证明几何相等；评估时按同源组处理。本次可读门窗实例上未发现 ShapeAspect，不能据此推断 IFC4 类型映射也没有；Renga 门窗使用 MappedItem，但关联 Type 未携带 maps。各关系必须分别读取。

墙板也有多种表示：hxp 为挤出，House 墙含 SweptSolid／Clipping／CSG，TallBuilding 墙为 Clipping，GNI 有 SweptSolid 和 Tessellation。数据证明应区分语义组织与底层表示，不证明当前系统已支持这些形式。

已有 hxp 诊断匹配 66 个构件、无缺失或多余，修复后候选仍有 14 个几何超差，Audit 接受不代表保留源细节。仅替换三个开口的离线诊断降为 10 个门窗差异，不是新 LLM 自动成功。D007 的八个 BRep 仅五个已证明可转正棱柱，其余三项仍须返回不支持。首版不能承诺整栋 hxp 完整保真。

## 附录 C：标准与工程依据

- [IFC2X3 IfcWindow](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindow.htm)、[IfcWindowStyle](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindowstyle.htm)：实例、类型、参数与形状。
- [IFC2X3 IfcShapeRepresentation](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshaperepresentation.htm)、[IfcShapeAspect](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshapeaspect.htm)：表示约束与部件分组。
- [IfcOpenShell ShapeAspect API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_shape_aspect/index.html)、[几何创建](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)：实现基础，不等于项目能力已完成。
- [Autodesk 构造工具](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Customize/files/GUID-478961FB-DD57-445E-831F-5B83E02F0B78.htm)、[族增量测试](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-Customize/files/GUID-772026BB-2A3E-4193-A339-75E019AA8DCC.htm)、[IFC 导出选项](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-DocumentPresent/files/GUID-E029E3AD-1639-4446-A935-C9796BC34C95.htm)：参数建模与导出是不同层次。
- [IfcFacetedBrep](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcFacetedBrep.htm)、[IfcAdvancedBrep](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcAdvancedBrep.htm)、[Khronos 网格说明](https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_009_Meshes.md)：BRep 与网格的区别；实际输出仍以 IFC2X3 合同为准。
