# Repair 与 Generation 的 Type、材质、属性和外观计划

更新：2026-09-08。状态：范围已定稿；S0—S4 离线实施已落地，S5 离线展示完成、人工视觉审查待进行。纳入小型内置参数化模板和 Generation 基础门窗细节，Repair 保留原几何。

最新决定：用户选择“采用建议：小型模板＋Generation 基础门窗细节”。它取代此前 Generation 全程保持现有几何的范围限制；默认配色、性能属性缺省不写入、不实现跨 IFC 参照的决定继续有效。实施顺序为先补齐语义链路，再完善配色与门窗细节。第 10 节保留工程探测、模板边界和独立审查依据。

本计划的目标是让 IFC 在当前支持的建筑范围内同时满足请求、具有合理语义，并呈现协调的颜色。它接续已有 presentation 实现，不改变既有 Phase 或 Proof 的验收状态。当前实现基线为 `362f5b49`，历史实现与验证记录见 [第一阶段边界](../validation/ifc2x3-changeset/ifc-presentation-development-boundary-2026-09-03.md)。

## 1. 已确定的范围

1. 优先完成这条产品线；外部 IFC 来源扩展不作为前置任务。
2. 维护少量内置参数化构造/样式模板，初版为单面板窗、双竖面板窗、左/右单开门。不维护外部 IFC Type 资产库，不实现参照另一份 IFC、跨 IFC 检索、资产导入或跨 IFC 类型复用。
3. Generation 的新 Type 在本次生成的项目中建立。只有用户表达类型、同规格共享或同类型要求时，才进入对应的类型组织分支；不按颜色相同或尺寸碰巧相同自动强行合并。
4. 没有 Type 需求时，不强求新建或复用 Type，不询问用户必须选择哪一个 Type。既有 IFC/编译合同要求的最小合法类型附件仍由代码处理，并与用户的设计意图区分。
5. Repair 可按请求使用当前待修 IFC 中仍存在的 Type；这不引入第二份参照 IFC。未请求的类型、属性、材质与样式保持不变。
6. 材质、property 和颜色质量不以存在 Type 为前提。没有 Type 关系的构件也可以有合理材料、合法属性和协调样式。
7. Generation 在新版本表示合同下增加基础门窗细节，直接呈现窗框、玻璃面板、门框和门扇等适用部件。Repair 不升级或替换已有几何；其他 Generation 构件与旧版本几何行为保持不变。任意分格、推拉/折叠、复杂五金和外伸装饰不在本轮范围。
8. 用户未指定外观时采用默认风格。未提供强度、耐火、热工等性能值时，不创建相应 property；不写零值、占位值或“未知”。
9. 保持 IFC2X3、现有构件支持范围及现行默认生成策略；不同时扩展 IFC4、复杂曲面、完整建筑系统或大型建筑生成能力。

“相同类型”与“完全相同实例”不等价：类型表达共同定义，位置、编号、实例属性和按合同可变的尺寸仍属于实例。类型关系不能代替材料、属性和几何的实际验证。

## 2. 基线与真正缺口

| 部分 | 当前已具备 | 本计划补齐 |
|---|---|---|
| Repair | Type 绑定与保真、属性解析/写入、显式材质和外观合同、多色映射 Type 保留 | 同一请求中 Type/材质/属性/颜色的一致性、冲突说明、无 Type 需求的兼容路径及组合回归 |
| Generation Type/property | BIM JSON 2.0、类型关系写入、property set 写入 | 从需求确定作用域、按需创建/共享项目内 Type、属性依据与有效值检查，完整接入公共流程 |
| Generation 材质 | 部分材料层表达；编译器已有 WallStandardCase 材料层路径 | 对实际支持构件逐类核对材料写入，缺失/不支持内容不能只停留在 JSON 或静默丢弃 |
| Generation 外观 | 可选 compiler profile/seed、有限 palette、共享样式工具 | 请求与主题传递、材料/部件角色协调、绑定优先级、最终 IFC 外观检查 |
| Generation 门窗细节 | 单拉伸表示；基础门窗 API 的隔离探测已完成 | 受限参数化模板、新版本表示合同、开口/墙厚/坐标适配、分部件几何与样式，接入完整公共生成路径 |
| 验证 | 编译/reopen、几何、Repair L0/L1/L2/preservation、离线 presentation 示例 | 请求到最终 IFC 的语义与视觉双重结果，以及失败/澄清/恢复与发布边界 |

现有 `apply_generation_profile()` 主要按构件类别和身份选择样式并写到表示项；这不能证明材料合理，也不能证明自然语言已经选择了合适主题。公共 `live_pipeline.py` 与编译 CLI 的调用尚未传入这些外观选项。

## 3. 信息依据与缺失处理

每项待写入事实区分四种来源：用户明确要求、当前模型既有事实、可验证的确定性推导、允许的生成设计选择。缺失值保持未提供，并在结果中说明；不向标准布尔/数值 property 写入字符串“未知”。

| 信息 | Generation 规则 | Repair 规则 |
|---|---|---|
| Type | 用户要求时在当前项目内创建/共享；不依赖外部库 | 按请求解析当前 IFC 中的类型；无法唯一解析则澄清 |
| 材料/构造层 | 有明确请求或可用类型定义时处理；未指定时沿用既有最小合法附件，不因默认配色额外推断物理材料或构造层 | 保留已有事实，只写入本次请求授权且适用的材料 |
| 普通属性 | 处理用户值及既有合同允许、具有明确前提的推导；不新增自动补齐普通属性的默认策略 | 按合法属性合同与作用域写入，不自动补全整个模型 |
| 性能值 | 用户未提供则不创建相应 property；不写入 null、零值或“未知”占位，不因其缺失触发澄清 | 不从外观猜测性能，不使用 private Gold 补值 |
| 外观 | 用户颜色/风格优先；未指定时自动采用默认协调风格 | 已有权威与修改范围优先，不自动美化源 IFC |
| 模板参数 | 显式输入优先；模板可提供已冻结、可校验的局部构造参数和样式默认值，记录模板 ID/版本与参数来源；不能据此补写材料、性能值或更改宿主/开口尺寸 | 不用 Generation 模板替换源 IFC 的几何或 Type 权威 |

用户提出性能指标时，区分“设计要求/用户声明”与“实测或认证值”；即使属性可写入，也不宣称已经验证实际性能。设计选择记录在现有 provenance/报告链路中，不伪装成外部来源事实。

丰富语义以请求相关信息是否正确、可解释为标准；不追求 property 个数或 Type 覆盖率。

## 4. 两条流程与冲突策略

Generation：

```text
需求 / Design Brief / 必要澄清
→ 构件规格、材料、属性与整体风格决策
→ 有 Type 需求时：当前项目内创建/共享类型；否则沿用无强制复用路径
→ 对支持的新建门窗选择内置模板，绑定用户参数和允许的构造默认值
→ Formal BIM JSON 及必要的版本化控制信息
→ 确定性构件、关系、材料、属性与样式写入
→ reopen、语义和几何检查、外观检查
→ 发布 IFC 与可读报告
```

Repair：

```text
当前待修 IFC + 请求
→ 解析目标及请求涉及的 Type/材料/属性/外观
→ 检查证据、作用域与冲突
→ 有界 ChangeSet / 确定性绑定 / 原子应用
→ reopen、L0/L1/L2、preservation 与有效语义检查
→ 发布 repaired IFC 或明确 no-output
```

- 复用/共享 Type 时，不能通过修改它的定义影响请求之外的实例；实例覆盖和类型级修改必须区分。
- 用户要求 exact Type，同时要求与该 Type 不兼容的材质/属性/颜色时，进入澄清，不静默覆盖 Type，也不无声丢弃用户要求。已有版本行为作为历史事实保留；新路由经版本化合同与回归后生效。
- 本轮不新增“复制现有 Type 并任意变体化”的通用 Repair 操作；Generation 中用户明确要求不同规格时，可分别新建项目内类型。
- 梁柱长度、轴线、位置等按当前请求和几何合同生成；不因为共享 Type 而覆盖实例尺寸。Repair 门窗沿用已有几何权威分类；Generation 新门窗按新版本参数合同构建，不能改变旧表示的含义。
- 同名不能证明同一 Type/材料。目标模型内使用稳定身份和完整定义判定，不用名称或 RGB 做语义去重键。
- 没有兼容材料表达、属性不适用、类型关系冲突或事实不足时，保留 Draft/澄清/不支持结果；不能丢字段后发布为成功。

## 5. 配色与材料表达

未指定颜色/风格时自动采用默认协调风格。初始主题建议低饱和度、有限强调色；已有明确材料时保持相应视觉倾向，没有材料依据时只表达颜色，不据此声称物理材质。具体色板可通过首批效果审查调整。

1. 一次生成采用一个协调主题；颜色按材料、类型和建筑角色组织，而非逐实例随机着色。
2. 用户明确颜色优先。木饰面、玻璃、金属框等在符合请求时采用可辨认的表达；颜色不能反向创造材料语义。
3. 材料级样式用于共有表达；构件或部件的明确差异使用受控样式覆盖。不能把全局 style override 当成默认材质实现。
4. 同一材料可有经明确区分的表面处理；不同外观不自动意味着不同物理材料。共享材料样式的修改范围必须可控。
5. Generation 基础门窗通过确定性模板建立适用的框、扇和玻璃面板表示，并按部件角色分色；玻璃面板的透明样式不等于已经写入或验证物理玻璃材料。Repair 保留已有分部件样式和几何，不为美化重建表示。只改主题时，任何构件的几何签名均不得变化。
6. 稳定性检查比较语义与样式签名，不要求包含时间等元数据的整个 IFC 字节相同。“颜色更多”不作为视觉质量指标。

## 6. 实施顺序与提交边界

下列 S0—S5 是本任务的交付步骤，不是新的正式 Phase 编号。每步先确定可观察失败与预期结果，再修改最小相关模块。

| 步骤 | 工作与主要路径 | 可审查交付 / 完成条件 |
|---|---|---|
| S0：冻结输入与适用合同 | `src/text2ifc_agent/design_brief.py`、`semantic_capabilities.py`；`src/text2ifc_contract/`；现有 schemas | 形成逐项语义预期、材料支持矩阵与作用域/冲突矩阵；加入 Type 家族配对、实例有效 Type 唯一性。冻结模板默认参数白名单、来源和边界；区分 Repair/纯配色几何保全与 Generation 新门窗几何验收。先冻结公共入口纵向案例，并按最窄边界保留能复现审核问题的失败测试；已注册版本不重写 |
| S1：Repair 收尾 | `src/text2ifc_ifc_repair/{repair_intent,resolution_flow,semantic_authoring,type_templates}.py`、`operations/`、相关 request/provider 路由 | 指定/未指定 Type、材质和属性作用域、冲突澄清、多实例保全都有聚焦与公共离线回归。已有成功结果不被提升为新版本 live 证据 |
| S2：Generation 语义闭环 | `src/text2ifc_compiler/{bootstrap,relationships,properties,compiler}.py`；必要时新增独立 `materials.py`；Agent Brief/semantic coverage | 先明确单材料/材料层的构件支持矩阵及版本合同；按需创建和共享项目内 Type。独立读回 reopened IFC 的有效 Type、材料、直接/继承 property 和缺省性能属性，逐项核对预期；一个纵向案例通过后再扩构件范围 |
| S3a：协调外观 | `src/text2ifc_presentation/`、compiler 外观绑定处 | 在 S2 语义纵向案例通过后接入主题；按已有材料/角色绑定，显式颜色可追溯；只改样式时几何、尺寸、开口与位置不变 |
| S3b：模板与基础门窗细节 | `src/text2ifc_contract/geometry_v2.py` 对应的新版本合同、`schemas/bim-json/` 新版本、`src/text2ifc_compiler/geometry.py` 及独立模板模块、presentation 部件绑定 | 单/双竖面板窗、左/右单开门的受限参数表示；模板 ID/版本、有效参数和来源可追溯；毫米/米、旋转放置、宿主墙厚、开口、部件角色与分色全部验证。新模板不依赖 Type 共享，不改 Repair 或旧版本几何行为 |
| S4：公共入口覆盖补齐 | `src/text2ifc_agent/{live_pipeline,interactive_cli_flow,staged_generation,generation_packages}.py`、`scripts/bim_json/compile_ifc.py` | 在 S2 已打通的纵向入口基础上补齐其余入口；语义、主题、模板版本和参数从请求传至最终编译，澄清/恢复后不丢失；保留 `legacy_full` 默认与 `staged` 显式选择；两条策略的新版本相关路径与旧版本兼容路径均验证 |
| S5：结果审查与 Proof | `scripts/presentation/validate_offline.py`、聚焦 tests、现有 human Proof 工具 | 每案可找到 request、BIM JSON/输入 IFC、最终 IFC 或 no-output、逐项语义表及视觉视图；来源和验收等级明确，人工审查后才提升相应状态 |

预计按 Repair、Generation 语义、Generation 外观、模板/门窗几何、公共接入/验证形成独立实现提交；每个行为提交附带相关测试。共享代码只共享机械写入/检查能力，Repair 与 Generation 的决策优先级分别保留。

本轮为受限门窗参数表示增加适用的 Formal 合同版本，并同步版本注册、编译入口与聚焦测试。具体版本号在 S0 核对当前 registry 后确定，不重写已注册 Prompt/Schema，也不将新参数塞入旧 `extruded_profile` 含义中。超出本轮支持的 geometry 仍进入 Draft/澄清/明确不支持，不能静默退回简单盒子后称为完成细节请求。

## 7. 首批案例与验证

### S0 冻结合同（2026-09-08）

新 Formal 版本为 `bim-json/2.1`，2.0 Schema 字节不变。新版本添加单材料、Type 材料层集合、外观控制和独立 `basic_filling` 表示；不改变 `extruded_profile`。同一对象最多一个材料附件，材料身份按对象/附件创建，不按名字合并。普通实例允许直接材料/property 覆盖继承值；共享 Type 定义不随实例覆盖改变。

| 对象/作用域 | 单材料 | 层材料 | 缺省 |
|---|---|---|---|
| Wall / WallStandardCase 实例 | Wall 支持；StandardCase 使用单层 usage 表达 | AXIS2，厚度合计等于矩形墙厚 | 仅 StandardCase 保留既有最小合法层附件 |
| Slab / Roof / Plate / Covering 实例 | 支持 | AXIS3，厚度合计等于竖向拉伸深度 | 无 |
| Beam / Column / Door / Window / Member / Railing / Stair / StairFlight / CurtainWall 实例 | 支持 | 不支持，阻断且说明 | 无 |
| 上述构件适用的项目内 Type / DoorStyle / WindowStyle | 支持 | 仅 WallType / SlabType / PlateType / CoveringType 支持 layer set（无 usage） | 无 |
| Project / Site / Building / Storey / Space / Opening | 不纳入本轮材料 authoring | 不支持 | 无 |

Type 配对显式按 IFC2X3 家族验证，Door→DoorStyle、Window→WindowStyle、Wall/WallStandardCase→WallType，其余按对应 Type；每实例最多一个定义关系，重复同 Type 关系亦拒绝。2.1 扩展只开放已支持构件的适用 Type，不扩展新构件族。属性需通过当前 PSD 的身份、值类型及适用家族检查；Type 上标准属性按对应 occurrence 家族检查。报告区分直接值、继承值及用户声明，未请求性能值不写入。

模板版本 `text2ifc/basic-filling/1.0`：`window-single`、`window-double-vertical`、`door-left`、`door-right`。长度在 Formal 中为毫米；模板仅允许 `frame_width`（默认 50，合法 10–100）、`frame_depth`（默认 60，合法 20–200）、`panel_thickness`（窗默认 6，合法 3–30；门默认 40，合法 10–100）、`split_ratio`（双窗默认 0.5，合法 0.2–0.8）。框深/面板厚不得超出开口深度，框宽不得消灭净开口；默认不适配时阻断，不自动缩放。总体宽高、深度、宿主、开口和 placement 是输入约束，不是模板默认。门套/门槛外伸关闭；使用关闭状态门扇，开启侧通过新类型/模板合同表达。每个有效参数记录 `user` 或模板 ID/版本来源；不从模板写材料或性能属性。

失败边界与排序假设：① 通用 Type 父类检查放过错误家族/多重关系；② 材料 first-item/仅墙分支静默丢值；③ coverage 支持标签不等于 IFC 有效值；④ Type 继承/覆盖与样式写入可能污染另一组。先以 contract/compiler 公共入口建立正负、重复/边界及跨家族测试，再接入从冻结 Brief 到 reopened IFC 的独立逐项检查。此案例族用于 Bug 修复与离线回归，不是盲测能力提升数据集。

初始展示范围建议为小型住宅与小型办公组合场景，覆盖现有可生成的墙、板、梁、柱、门、窗。此范围是首批检查载体，不声称复杂整栋建筑能力，也不为了覆盖表新增 Repair operation。

| 案例族 | 核心预期 |
|---|---|
| G1：未提 Type、材料或性能属性，只描述建筑 | 不强制寻找/共享 Type；默认风格正常生效；未提供的性能 property 在 IFC 中不存在；没有相关缺参澄清，不推断物理材料 |
| G2：要求多扇同类型门 | 当前项目中新建共同 Type，实例位置/编号独立，类型材料/property 关系正确 |
| G3：相同尺寸但指定不同材料或类型 | 不错误合并；样式变化不污染另一组 |
| G4：指定材料、颜色和合法 property | 最终 IFC 中逐项可查；用户要求不被主题覆盖 |
| G5：材质层厚度冲突或明确请求的属性不适用/不完整 | 按合同澄清、Draft 或明确不支持；与 G1 的“用户未请求性能属性”区分，后者直接不写属性 |
| G6：同一几何更换主题 | 固定 viewer 配置和视角检查配色、部件样式与适用透明度；只改主题时几何签名不变 |
| G7：澄清后恢复、同 seed 再编译 | 语义/风格决策不丢失，样式签名稳定；不要求 IFC 整体哈希相同 |
| G8：malformed/truncated 输出或发布失败 | 不发布被遗漏语义的候选，不留下伪成功状态 |
| G9：四种基础门窗模板 | 单面板窗、双竖面板窗、左/右单开门均有适用的框/面板/扇部件，可重读、网格化和分色；无 Type 共享需求也可构建 |
| G10：模板单位、尺寸与开口边界 | 覆盖毫米/米、旋转放置、墙厚变化、小尺寸及非法参数；区分外轮廓、净开口和深度，部件不能越过冻结的几何边界；不得通过移动开口或放宽旧阈值使检查通过 |
| G11：模板与用户值冲突 | 用户参数优先，模板默认值不覆盖显式尺寸、材料、颜色和属性；不合法或不能满足时阻断；模板 ID/版本及来源可查，不新增缺省材料/性能属性 |
| G12：新旧版本与恢复 | 旧表示编译行为保持；新模板参数经澄清/恢复和两种生成策略后不漂移；Repair 不受 Generation 模板影响 |
| R1：明确选择当前 IFC 的 Type | Type 权威保真；相关材料/属性/样式有效值可追溯 |
| R2：没有 Type 请求，仅修改已有支持的语义 | 不强制换 Type，不补写未授权信息 |
| R3：exact Type 与显式要求冲突 | 新合同下进入澄清，源文件无 mutation/no publish |
| R4：共享 Type 与多色部件 | 未请求实例与 Type 定义不被改动；框/玻璃原样式不扁平覆盖 |
| R5：不适用 property 或原子多操作失败 | 拒绝不合法写入，完整回滚，repaired/no-output 互斥 |
| R6：合法无输出、澄清恢复和来源保全 | 最终状态、调用边界和证据正确；private Gold 不进入生产 |

这些是待冻结的案例族，不是已通过的案例数量。实施前加入正向、负向、边界和不同场景 sibling，保持解释维度独立，避免一次修改多个因素后无法定位原因。

验证分两层：

- **语义/执行硬门**：请求相关字段必须正确表达或明确报告未满足；类型和实例作用域正确，材料不丢失，属性适用且有依据；几何、reopen、原子发布及适用的 Repair L0/L1/L2/preservation 全部通过。核心阻断错误不得通过视觉评分抵消。
- **人工视觉门**：配色比较固定几何、viewer 配置、光照、背景和视角；门窗细节比较固定宿主、开口、名义尺寸及 viewer 条件，允许新合同内的分部件几何变化。检查协调性、框/扇层次、部件分色、适用透明度和穿插/异常覆盖。每项记录通过/需调整与原因；视觉审查不能代替语义验收。

人工视觉门适用于首批主题和代表性展示/Proof 的审查，不把每次普通生成都挂起等待人工。普通运行经自动语义、执行和样式有效性检查后可交付 IFC；运行发布状态与主题/Proof 人工审查状态分别记录。最终 IFC 检查不得仅复用 Agent 自报的 represented 标签。

Generation 没有 repair 三元组；IFCCompare 的 original/damaged/repaired 角色为 N/A。Repair 仅在已有合法、预先冻结的私有评估合同下使用相应比较。只改报告或导航时不重跑 curator。

迭代先跑相关 tests；第一次进入新的 Agent/公共执行阶段，按 [Agent 准入协议](../validation/agent-capability-evaluation.md) 完成该阶段 seam 和完整离线 API/CLI 路径。Full Preflight 仍须另说明范围并获得明确批准。当前计划不授权新 Provider 调用；离线完成后再单独讨论 live 验证。

## 8. 交付与阅读方式

每个新展示案例应包括中文 `REPORT.md`、`request.txt`、最终 BIM JSON（Generation）或输入 IFC（Repair）、最终 IFC/明确 no-output、`evidence/` 和必要视图。报告给出 Type、材料、属性、颜色的请求值/有效结果/依据/结论；使用模板时同时列出模板 ID/版本、有效参数及默认值来源。门窗展示提供整体视图与部件近景，不要求读者理解 runtime。

沿用 [Proof 工作流目录](../../dataset/processed/proof/README.md) 与现有机器合同。正式 Phase 归属待与当前规划对齐后确定；不挤入历史 accepted 集合，也不为讨论先创建空 Proof 目录。模型表现只有在适用验收实际完成后才可宣称。

## 9. 已确认的讨论结论

| 决策 | 用户答复 | 本计划的落实方式 |
|---|---|---|
| Q1：未指定的语义与颜色 | 未处理时按默认风格处理颜色；强度、耐火等没有提供则直接没有该属性 | 默认颜色与语义补全分开：性能 property 缺省时不创建、不占位、不因此澄清；不新增自动补齐材料或普通属性的默认策略，既有合法编译附件和有依据的请求处理继续保留 |
| Q2：门窗分部件几何（早期决定，Generation 范围已由 Q3 更新） | 先保留现有几何，只完善语义与外观 | Repair 和纯样式修改仍需几何保全；Generation 基础门窗细节按 Q3 纳入 |
| Q3：审核后的最终范围 | 采用建议：小型模板＋Generation 基础门窗细节 | 少量内置参数化模板；单/双竖面板窗、左/右单开门；先完成语义再实施；Repair 保留原几何，模板不默认补写材料或性能属性 |

Q3 是当前模板与门窗几何范围的决定；第 1—8 节已同步。性能属性缺省不写、跨 IFC 参照不实现等决定不重复询问。实施时不将缺省性能属性或未要求 Type 当作阻塞。

## 10. 已选模板方案、工程评估与独立审查

### 10.1 小型模板与请求驱动可以并存

已选择“严格满足显式输入＋小组内置参数化模板”。模板是版本化的构造/样式规则；实际 IFC Type 仍在本次项目中建立，不读取第二份 IFC，也不引入外部资产库。

- 初版采用单面板窗、双竖面板窗、左/右单开门四种受限变体；梁柱沿用已有参数化规则，不囤积大量固定尺寸 Type 文件。
- 用户尺寸、材料、类型、合法 property 和显式颜色优先；模板只填允许的空缺。适配不了时澄清或明确不支持，不能悄悄替换要求。
- 模板只提供构造/样式，不额外补物理材料、普通属性和性能属性；有依据的用户请求及既有合法事实按第 3 节处理，不从外观反推材料。
- 使用模板不意味着必须让所有实例共享一个 IFC Type。仍按用户类型需求和现有合法附件规则组织 Type/实例。
- 同一模板可由不同尺寸参数生成不同项目内定义；模板默认值与用户输入分别记录。不能将模板中的任意性能值继承进未请求的生成结果。

模板默认参数限定为局部框宽、框深、面板厚度、分格比例及样式等受限构造选择；在 S0 逐项确定合法区间、尺寸适配规则和版本，不预先猜定统一数值。宿主、开口尺寸、位置等继续遵守当前需求合同；缺失会影响意图或几何正确性的事实时澄清。面板数量和门开启方向从明确请求或已授权的设计选择解析并记录，不能由模板暗中改变。默认值不合法时阻断，不能通过缩放用户尺寸或更换所需材料来适配模板。

### 10.2 门窗工程难度：局部成型较低，接入中等，Repair 扩展较高

已核对本机 IfcOpenShell `0.8.5` 和官方 [window API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_window_representation/index.html)、[door API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_door_representation/index.html)。它们提供 lining、frame/panel、glass 等参数，能够借助 ShapeAspect 标记部件角色；不需要 LLM 生成顶点或自行从零实现全部实体算法。

本次仅做隔离的内存 API 探测，结果保存在本地临时记录 `.tmp/semantic-appearance-api-assessment.json`，不是 accepted Proof：

| 探测 | 观察结果 |
|---|---|
| 单面板窗、双竖面板窗，各用毫米/米单位 | 4 组均可 IFC2X3 序列化重读、网格化，宽高符合输入；可区分 Lining/Framing/Glazing |
| 左/右单开门，各用毫米/米，API 默认参数 | 4 组可重读和网格化，但输入 900×2100 mm 的外包围盒约为 950×2125 mm；默认门套等装饰不能直接套用当前开口宽高断言 |
| 同一组门关闭 casing/threshold 参数 | 4 组可重读、网格化并保持 900×2100 mm 宽高，仍有门框/门扇相关部件；几何深度约 115 mm，尚需真实墙厚/开口位置适配验证 |
| 双竖面板窗省略第二项 panel 参数 | 初始探测产生 IndexError；显式传两个 panel 定义后通过。生产前需要自己的数量/尺寸参数校验 |

本次没有运行完整 IFC Schema/项目验证、公共生成链路、viewer 视觉审查、真实 Provider 或 Proof curator。API 能创建几何只证明局部实现可行，不证明整体接入完成。

| 实现范围 | 难度判断 / 当前决定 | 主要工作 |
|---|---|---|
| Generation 单/双竖面板窗＋左/右单开门的基础细节 | 中等，已纳入 | 新的受限表示合同；局部坐标/毫米单位、开口与墙厚适配；部件分色；完整 IFC 语义/几何读回和公共路径回归 |
| 任意分格、推拉/折叠、复杂门套/五金 | 较高，当前不建议 | 参数组合与形状边界增长，开启行为、净开口与实体包围盒需各自定义 |
| 把现有 Repair 门窗统一升级为丰富几何 | 较高，当前不建议 | 现有 exact Type/maps 保真、source/preservation、旧比较器及坐标/尺寸合同同时受影响 |

本轮仅扩 Generation 新建门窗；Repair 的已有 exact Type 几何继续保留。初版去掉超出当前开口表达的外伸装饰，但仍需分别验证总宽高、净开口、深度和位置，不能只看包围盒，也不能放宽旧验收阈值来容纳新几何。

Generation 当前 `geometry_v2.py` 限定 `extruded_profile`，compiler 对应单个拉伸体；因此门窗细节不能静默替换同一冻结 representation 的含义。应先定义受限、版本化的门窗参数表示，再实现确定性编译。几何配置与 Type 复用是独立问题，可以分别推进。

### 10.3 用户要求的独立 subagent 审核

本次独立只读审核发现 5 项；主线不重复执行审核探针：

| 优先级 | 发现与证据 | 对计划的处理 |
|---|---|---|
| P1 | `src/text2ifc_agent/semantic_coverage.py:641` 的局部覆盖检查不能证明值在候选/最终 IFC 中存在；内存探针中空候选仍将材料/耐火事实标 represented | S0/S2 明确独立 reopened IFC 读回及逐项比较，先做纵向公共入口案例 |
| P1 | `schemas/bim-json/2.0/schema.json:138` 当前只有材料层 usage；`bootstrap.py:283` 取首项，`:366` 写入路径局限于 WallStandardCase | 先冻结按构件/作用域划分的单材料和层材料支持矩阵，不能仅改 Prompt/配色 |
| P1 | `src/text2ifc_contract/relationships_v2.py:23` 局部 Type 检查缺家族配对/唯一性；探针中 Beam 同时指向 WindowStyle/DoorStyle 未报错 | 加入兼容类别、唯一有效 Type、继承/覆盖与跨组保全硬门 |
| P2 | 审核时内置模板默认内容尚未决定 | 用户已选定模板与基础门窗范围；本节限定构造/样式默认值，禁止默认补写材料和性能属性；S0 冻结具体参数及边界 |
| P2 | 计划原先未区分普通生成交付与人工视觉验收 | 已明确普通运行自动检查后交付，首批主题和代表性 Proof 单独人工审查 |

两个内存探针只证明相应局部门禁存在缺口，不证明完整发布链路必然放行错误结果。修复前需形成能命中真实边界的 red-capable 用例；本次未修改任何生产行为。


## 11. 2026-09-08 实施与离线验证

当前事实来自工作树和测试，不沿用会话显示推断。接管时 HEAD 为 `362f5b49`、暂存区为空，新计划及三个导航尚未提交；新行为此前未实施。其他任务的 ifc-bench、历史运行和权限异常 Proof 路径保持原状。

| 步骤 | 实施状态与实际结果 |
|---|---|
| S0 | 已冻结本页支持矩阵、IFC2X3 Type 家族/唯一性、单材料/层材料作用域和模板参数。保留缺值、错值、畸形 Type、重复关系、错家族及边界案例的先红后绿记录。 |
| S1 | Repair Intent/Body 0.10、Prompt 0.13 为公共 API 新默认。exact Type 与材料、颜色、继承属性冲突在 Stage2 前澄清；明确实例属性覆盖走既有合法流程。旧版本合同继续可用。 |
| S2 | 新 Formal 2.1、Brief 2.1、Draft 1.1。请求期冻结 semantic_expectations；候选和最终验收都独立重读 IFC 比较 Type、材料、属性、显式颜色及模板。represented 标签不再作为这些值存在的证据。无请求材料/普通属性被阻断。 |
| S3a | neutral-architectural / warm-residential 协调主题、角色及部件样式；显式值优先，默认色实际值也经独立读回。共享材料实体只绑定一次样式，实例配色不污染共享材料。纯主题变化保持网格。 |
| S3b | 四模板的受限拉伸实体构造、ShapeAspect 部件、门向 Style、参数来源已实现。选择独立矩形实体以避免 API 隐含门套/门槛外伸。重读校验名义尺寸、局部部件占用体积、世界放置、净开口、宿主边界和门向。 |
| S4 | legacy_full 默认不变；staged 显式选择，新增末尾 semantic_types 包。四模板覆盖两策略，公共 CLI 编译、完整 Brief→最终验收、澄清持久化、新旧版本兼容已离线验证。冻结请求不允许降版或丢弃主题/seed。 |
| S5 | 新离线展示具有中文逐项表、IFC、BIM JSON、请求、evidence 和网格整体/近景。普通自动交付与主题/Proof 人工审查分开；后者待进行，不安装到 accepted Proof。 |

`depth` 表示宿主与开口共同允许的对称安装深度预算，实际框深和面板厚分别由白名单参数表达。开口切割体可以比墙厚，但不能把切割体深度直接当作门窗可用深度。旧 `extruded_profile` 含义不变；Repair 不采用 Generation 模板升级几何。

运行与查看：

- [四模板中文展示入口](../../dataset/processed/ifc-presentation-validation/semantic-appearance-20260908-final/REPORT.md)。图像来自实际重读 IFC 三角网格的固定正交投影，不能代替真实 viewer 人工审查。
- 离线重建：`.venv\Scripts\python.exe scripts/presentation/validate_semantic_appearance.py --output-dir <新的目录>`；已存在目录拒绝覆盖。
- 公共离线编译：`.venv\Scripts\python.exe scripts/bim_json/compile_ifc.py <candidate.json> <output.ifc>`。
- 现有交互入口 `scripts/agent/run_phase6_2_cli.py` 使用新 Brief/Generator 合同；本任务未调用其真实 Provider。Repair 通过既有 `RepairAPI.start` / `continue_with_answer` 接入。
- 公共运行目录生成 `request-semantics.json`、`semantic-verification.json` 和中文 `semantic-report.md`；最终发布前再校验。请求期错误在恢复后仍阻断，不能因 Brief 变更丢失冻结预期。

验证等级：全部为确定性离线测试或本机 IFC 编译/序列化/网格检查。不是真实 Provider、盲测能力提升或 accepted Proof。未运行真实 Provider、Full Preflight、全库 pytest、accepted curator 或人工视觉审查。初次离线渲染失败及中间成功目录保留，正式查看入口另建 fresh 目录。


### 实际验证记录与限制

- 第一组阶段范围回归：406 passed / 1 failed；畸形 Type 引用的材料继承异常修复后，相关 91 项通过。
- 扩大的阶段范围回归：451 passed / 1 failed；在编辑新 Prompt/hash 时读到短暂不一致，冻结文件后相关 47 项通过。失败记录保留，不将该整轮标成全绿。
- 首轮 Brief 降版防护与新旧公共调用兼容的最终复验：75 passed / 0 failed。旧版回放显式选择 `design_brief_schema_version="text2ifc/design-brief/2.0"`；新调用默认 2.1 并拒绝降版响应。
- 四个展示 IFC、8 个 SVG XML/本地链接检查通过。机器记录与完整 pytest XML 见[离线验证 evidence](../../dataset/processed/ifc-presentation-validation/semantic-appearance-20260908-final/evidence/README.md)。各组有重叠，不合并为独立案例总数或能力分数。

本轮 Code HEAD 为 `82476b5b`。框/面板为受限、关闭状态的矩形实体，左右门向以 IFC2X3 DoorStyle 表达；不提供开门动画或复杂五金。仅支持本页定义的竖直矩形墙/开口及合法参数，超出范围阻断。人工 viewer/主题审查、真实 Provider 验证和正式 accepted Proof 安装均未进行，不能由这些离线结果替代。

## 12. 2026-09-08 真实运行与通用边界调试

用户后续明确授权 DeepSeek 真实调用及两条链路的人工检查材料。上节“未调用真实 Provider”是此前离线检查点；当前待验收入口为 [真实运行报告](../../dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/REPORT.md)。它位于展示验证目录，尚未安装 accepted Proof。

- Repair：dataset `vvo.ifc` 在执行前冻结为 private_ground_truth，仅删除一个实例属性关系。公共 API 实际只接收 damaged 与公开请求；成功 live-04 有 2 次真实调用，完整 IFC 发布并通过独立四项有类型属性核对。原有 STEP 实体均未改动，三份文件各 152 个构件的网格和样式一致。此前真实失败 attempt-02 及离线回归分别保留。公共 conditional L2 的 not_required 标签不用于证明请求值，报告链接独立重读结果。
- Generation：真实 Brief 澄清／恢复及两次 Generator 均保留。第二次真实候选纠正局部坐标重复旋转；未经手改候选，修复确定性代码后编译、重读、候选和几何检查通过，45 项独立用户预期核对通过。整体、门窗近景已由 Agent 查看；人工审查待确认。用户明确授权具体载荷后，真实 Audit 接受且最终发布验收通过；最终 IFC 再独立核对 45 项通过。该结果经历开发纠错及同例复验，不是完整真实 CLI 首次成功或盲测能力提升，accepted Proof 仍待人工确认。
- 通用修复：冻结 Brief／canonical 身份在语义、空间几何、门窗宿主检查中一致绑定；多候选、类别不符和跨楼层错误继续阻断。IfcWallStandardCase 计入墙家族。Name／Description 在开洞、填充、聚合、Type 和连接路径均按文本处理。澄清恢复保存既有调用；请求／响应先落盘，失败尝试和重复编号不得被覆盖。既有 Prompt、Schema 和 profile 版本未重写。
- 最终聚焦回归：82 passed（通用身份、关系、Type、调用证据与恢复），34 passed（公共完整入口、旧／canonical ID、简化／详细门窗、staged 与恢复）。此前 84 项身份／几何和 77 项关系／模板检查也通过，各组有重叠。stage 初始失败及 Repair 广泛测试超时保留，不能称为全库通过。未运行 Full Preflight、全库 pytest 或 accepted curator。

已准备 `generation/request.txt` 与最终完整 `generated.ifc`，以及 Repair 的 `01-original.ifc`／`02-damaged.ifc`／`03-repaired.ifc`。交互 HTML 从重读 IFC 提取实际网格、样式、直接及有效属性，可打开后审查；普通属性与内部溯源属性在报告中区分。下一步等待用户对两条链路分别确认，再按适用检查整理 Proof。真实尝试清单记录 9 次调用（Generation 5、Repair 4，包含此前失败尝试）。单例修复和真实可行性记录不能宣称类级或系统级能力提升。

交付位置说明：本批真实运行及待人工检查材料仍保存在上述本地展示目录，尚未纳入 Git 或发布为 Proof；本轮只提交通用代码、测试和离线查看器。查看器可用 `.venv\Scripts\python.exe scripts/presentation/render_ifc_review.py <input.ifc> <新的输出.html>` 生成，已有输出拒绝覆盖。

### 人工检查收纳更新

用户随后要求按既有 Proof 格式先收纳、检查通过后再登记。已新增本地待检查视图：[Generation](../../dataset/processed/proof/generation/phase6.6/semantic-appearance-20260908/README.md) 与 [Repair](../../dataset/processed/proof/repair/phase12.1/semantic-appearance-20260908/README.md)。两者仅使用独立 `review-manifest.json`，标记 `pending_human_review`／`unregistered`，没有主 `manifest.json`，未改 Proof 总索引或 accepted 名单。源运行保持不动，真实成功与失败材料按既有 package schema 逐字节复制并记录旧路径映射。

原 request.txt 是 UTF-8，旧 HTTP 服务缺少 charset 导致浏览器误解码。新增中文阅读页并保持原始请求字节；`.venv\Scripts\python.exe scripts/presentation/serve_review.py --root dataset/processed/proof --port 8768` 可启动本地 UTF-8 查看服务。文本 HTTP 回归 3 项通过；两包既有人读检查通过，重读 4 份 IFC，122 个展示链接正常。此次仅收纳待检查视图，未运行 accepted curator，未登记或提交这些本地 Proof 材料。

### 双层案例与自然语言定位反馈

用户要求保留单层案例，新增更完整的双层 Generation，并尽量使用工程师语言定位 Repair 目标。单层案例仍待人工检查、未登记。Repair 的待检查报告已补充平面定位图及属性前后中文解释，原始技术请求和三份 IFC 字节未改；18 个报告链接及四份核心文件绑定检查通过。当前无 GUID 的“标高0层、长约2.22米、厚240毫米”查询确实返回两个候选，未强行选中；`direction` 描述轴线朝向，不能冒充外立面方位。任意“北侧／从西数第二个／距转角若干米”的组合定位尚未实现，本次报告中的人类表达示意没有作为新 Provider 输入执行。

新增[双层开发记录](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/REPORT.md)：运行前冻结输入和预期，设计包含上下两层活动厅、直跑楼梯与实际楼板洞口、10 窗／3 门和协调主题。累计 5 次真实响应（2 Brief、3 Generator）均保留。首次 Brief 因文本末尾换行回显差异被拒绝；随后公共 CLI 候选存在 IFC2X3 楼梯属性名、DoorStyle 与局部坐标轴错误。既有反馈接口纠正一次返回空正文，有限重试返回完整 JSON，但十个 WindowStyle 使用非法 ConstructionType=`WINDOW`，离线原样重放确认阻断。当前没有可交付双层 IFC，本轮真实调用已停止；未运行新 Audit、最终验收或双层视觉检查，未收纳为成功 Proof。

两组新增聚焦回归为 54 passed 与 59 passed（离线、存在重叠），复用并核对既有同阶段准入源哈希；没有修改生产代码或已注册 Prompt／Schema／profile，没有运行 Full Preflight。下一步先冻结枚举约束、无 Type 请求最小附件与公共纠错案例族，再评估通用修复；若继续真实调用须基于适用的离线复验，保留这些失败。新成功案例只需既有 Proof 格式与实际 IFC 静态图，不另建网页；仍须等用户人工确认后登记。

## 13. 2026-09-08 Pipeline 稳定性排查与批准实施

用户进一步要求解释 LLM 修好一处又破坏另一处的原因，并检查 pipeline 的稳定性改进点。本节记录当前源码、实际载荷和离线探针得到的发现，不改变已批准产品范围，也不是新的实施完成声明。基线 HEAD `3626133d`，生产代码／Prompt／Schema 未改；既有待审 Proof、原始响应和其他任务修改保留。本轮没有真实 Provider、Full Preflight 或 accepted 安装。

### 13.1 已核实的缺口与可复用机制

| 优先级／环节 | 当前证据 | 建议及边界 |
|---|---|---|
| P0：生成合同与验证合同 | Formal 2.1 的 attributes 只显式约束放置和表示；实际 Generator 的 Schema／capability／few-shot／反馈均未给出 ConstructionType 及其枚举。IFC2X3 校验在输出后才拒绝 WINDOW。 | 从现有 IFC schema 与支持矩阵派生按类别选择的字段、枚举和约束上下文，带版本／哈希；生成和校验共用权威，避免手抄第二份枚举。无用户 Type 请求时约束多余样式生成，必要合法附件由现有确定性代码负责，不推断材料或性能。 |
| P0：早期失败与局部修复接入 | `failure_routing.py` 可修集合包含 INVALID_ENUM，却没有实际产生的 INVALID_IFC_ATTRIBUTE_TYPE；BASIC_FILLING_CONSTRAINT_CONFLICT 也阻断。`interactive_cli_flow.py` 对 invalid Formal 提前返回，已有 scoped ChangeSet 路径主要在后续几何／Audit 纠错阶段。 | 按错误子因和证据生成恢复动作，打通可恢复的早期错误；真实用户冲突、缺事实、unsupported 保持澄清／阻断，不能仅把整类冲突加入白名单。 |
| P0：合法修改范围 | 实际楼梯旧字段 NumberOfRisers 的报错仅授权旧路径；只做正确字段改名也因新增 NumberOfRiser 被 fact-delta 拒绝。同路径权限正例通过、无关改名反例被拒。 | 由 schema 和冻结请求生成成对字段操作与精确授权；以稳定实体 ID 绑定，减少数组下标和顺序引起的虚假变化。保留无关对象保护，不扩大到整份文档。 |
| P0：语义依赖范围 | 对实际门的 Representation 问题派生的范围有 7 个实体、6 条关系，但不包含冲突的 DoorStyle；当前自动遍历关系不含 IfcRelDefinesByType。 | 补 Type／样式／材料／属性的语义依赖；区分只读上下文、可写字段和受影响但应保全的实例。不能遍历到共享 Type 就自动授权修改整个共享组。 |
| P0：早期候选的修复进度 | `apply_changeset` 在提升 revision 前要求整个 Formal 校验通过。内存中只纠正十个错误窗样式之一后仍有 9 个错误，因此不能直接套用现有“合法 revision”应用器逐个积累这类修复。 | 优先构造能一次修完的有界依赖组；若仍需分步修 invalid candidate，必须明确未验收工作区与可发布 revision 的区别，验证未修错误集合和已通过不变量，不放宽最终发布。 |
| P1：缩小生成与反馈上下文 | legacy_full 输出整份模型；纠正载荷约 99 KB。已有 staged 按包生成、冻结既有构件哈希；但 ChangeSet stage 仍固定加载八个 few-shot，并传完整 Brief／Expected Facts。 | 复用现有分包和 scoped component 机制；按包／错误选择例子与只读依赖，保留相关约束。legacy_full 默认不变、staged 显式选择，需同预算对照才能声称后者更稳定或更省。 |
| P1：输出约束与 Provider 故障 | `OpenAICompatibleLiveProvider.generate_live` 的 schema 参数未进入 API 约束，实际用 json_object；temperature=0 已设置，DeepSeek thinking 的元数据标记其不生效。空正文已有真实证据。 | 先补有效的类别合同，再评估严格输出适配；仅 JSON 合法不能保证 IFC 合法。空正文／截断／连接错误走各自有上限的恢复，不混同语义修复；不要把继续降温当成主要方案。 |
| P1：进度、回滚与预算 | 已有 revision／component hash、事务式 ChangeSet、最终全局 gates 和 bounded attempts。旧修复按问题数量下降判断 improved，feedback loop 允许问题签名变化后继续；staged 和 scoped 各有自己的重试上限。 | 保留最后可信候选，比较已修／残留／新增根因及强制 gate 状态，识别 A→B→A 和重复候选；增加贯穿同一任务的调用／token／时间预算。检查阶段推进后才新暴露的问题，避免把“数量没降”一概判成无进展。 |

主要实现：[Provider](../../src/text2ifc_agent/openai_compat.py)、[旧生成修复与权限](../../src/text2ifc_agent/live_pipeline.py)、[失败路由](../../src/text2ifc_agent/failure_routing.py)、[公共链路](../../src/text2ifc_agent/interactive_cli_flow.py)、[局部修订](../../src/text2ifc_agent/scoped_loop.py)、[依赖范围](../../src/text2ifc_agent/change_scope.py)、[事务应用](../../src/text2ifc_agent/changeset_apply.py)、[分包生成](../../src/text2ifc_agent/staged_generation.py)、[反馈轮次](../../src/text2ifc_agent/feedback_loop.py)。这些机制已有部分实现，建议优先接通和补齐，不重复建设第二套编排。

### 13.2 验证与方法依据

本轮聚焦运行 `test_repair_fact_delta.py`、`test_generator_failure_routing.py`、`test_phase6_5_changeset_apply.py`、`test_phase6_5_scoped_loop.py`、`test_phase6_5_staged_generation.py`、`test_phase6_4_feedback_loop.py`：**57 passed**。测试为离线 seam／fake，不代表真实恢复成功。额外只读／内存探针证明枚举路由阻断、合法字段改名被权限拦截、只修一个样式仍剩九错、门的 Type 未进入自动 scope；没有保存修改后的候选或编译 IFC。

- [测试 XML](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/scoped-offline-evidence/pipeline-stability-inspection-01.xml)
- [合同／权限／早期恢复探针](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/scoped-offline-evidence/pipeline-stability-inspection-01.json)
- [Type 依赖探针](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/scoped-offline-evidence/pipeline-stability-type-scope-01.json)

方法参考：[Self-Debugging](https://arxiv.org/abs/2304.05128) 在代码任务中使用执行反馈与失败预测复用；[自纠错边界研究](https://arxiv.org/abs/2310.01798) 说明无外部反馈的自我修正并不可靠，不能将其标题概括成所有模型均不能纠错。这些研究支持优先验证反馈质量，但不证明 text2IFC 上的改进幅度。[DeepSeek JSON Output](https://api-docs.deepseek.com/guides/json_mode/) 明确说明 JSON 模式可能返回空正文；[strict Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) 是另一个具有 schema 子集和 Beta 端点要求的能力，当前仓库未接入，本轮没有测试其真实效果。严格输出也不能替代关系、几何、用户语义和 IFC 重读校验，且适配不能迫使缺省普通属性填 null。

建议实施顺序为 P0 合同一致性与最小附件 → 早期路由／依赖授权／有界修复组 → P1 上下文选择与全任务预算 → 可选 strict Provider 适配及 staged 同预算对照。修改前冻结跨构件、跨楼层、旋转宿主、Type 共享冲突、空响应和恢复失败案例族；同例只能证明修复可行。实际成功率须另外以固定 evaluator、包含失败的完整分母、隔离场景的配对测试报告 first-attempt／bounded-retry 严格成功率、无关变更率、误发布率、调用数、token 和延迟。

### 13.3 已批准的执行合同与进度

用户已批准更新本计划并逐点修复。第 13.1 节从调查建议转为本次实施依据，按下列顺序推进；本表只凭代码／测试／提交证据更新，不将计划写成完成状态。

| 步骤 | 实施及验收边界 | 当前状态 |
|---|---|---|
| T1 合同一致性 | IFC registry 派生字段／枚举／可编写范围，Generator、Repair、ChangeSet 共用；新增 Prompt 版本与 registry，旧版本字节不变；覆盖有／无 Type、不同构件及未知类拒绝 | implemented：Generator／Repair 2.2、ChangeSet 1.2；9 项先红后绿。两策略公共语义／ChangeSet 回归另有 32 项通过（扩展轮共 40 passed／1 failed，唯一失败为测试读取 fake 未记录的 prompt；修正实际载荷捕获后 9 项通过）。仅离线证据。 |
| T2 有界早期恢复 | 新错误子因路由、稳定 ID 的字段授权和 Type 依赖；一次完成可授权的错误组，禁止未合法候选晋升；明确冲突／缺失事实仍阻断；覆盖公共 CLI 与 staged 相关路径、源与未请求内容保全 | implemented：新 Formal 的枚举／唯一末尾 s 字段改名错误组；独立重现 validator 后才授权，ChangeSet 事务逐叶检查、值保全、禁止增删，Type 及共享实例只读。45 项聚焦回归通过；T5 新增四个完整公共恢复案例通过，两策略相关分包路径通过。几何／门向冲突仍不扩大白名单。 |
| T3 生成及反馈上下文 | 按任务／包／错误选择必要示例与 schema 资料；依赖上下文不自动成为写权限；保留完整原始 traces 和冻结请求，legacy_full 默认不变 | implemented：ChangeSet 1.4 按字段／局部／楼层包选择示例和 registry；独立只读依赖含宿主、放置父节点及跨关系共享 Type 用户。包缺少完整类别声明时保留全 registry。冻结 Brief／Expected Facts 不裁剪。4 项先红后绿，两策略公共语义／分包／旧 Prompt／早期恢复共 58 项通过。 |
| T4 进度与总预算 | 保留可信基线、区分新暴露与回归错误、重复候选／循环停止，统一任务内调用及 token 上限；预算耗尽不发布部分结果，恢复后不得重置已用预算 | implemented：公共 Generation 的 Brief／Generator／Repair／ChangeSet／Audit 共用落盘预算，恢复冻结额度；原子候选保留，重复失败 patch 与同阶段 A→B→A 停止，跨校验阶段推进不误判。预算耗尽返回 budget_blocked、无交付指针；33 项预算／循环／分包回归及此前 32 项公共／恢复回归通过，存在重叠。 |
| T5 公共接入与验证 | 逐项聚焦回归后，运行变更相关公共 API／CLI 离线全链路与恢复、安全、版本兼容检查；记录新 stage admission 判断；再决定是否进入真实双层验收 | scoped complete：新字段恢复经公共入口到最终 IFC，含旧／canonical ID、简化／详细门窗四种组合；最终重读语义检查通过。Prompt／版本／Provider seam 轮为 67 passed／2 failed，既有 attempt 冲突检查顺序修复后，相关最后一轮 36 passed。compileall 与 diff check 通过。live admission：not_admitted；旧准入不覆盖本次入口／事务变化，需要单独 Generation Stage Preflight，未自动升级 Full Preflight 或启动真实调用。 |

新增严格 Provider 输出适配属于 T5 后的可选受控实验，先做离线兼容性评估；不自动切换 Beta 端点、Provider、生成默认策略或扩大真实调用预算。Repair 自然语言空间定位是已记录的后续能力缺口，不把本次 Generation 纠错改动冒充该能力已完成。本轮真实 Provider 暂停，Full Preflight 仍需单独明确批准；Proof 登记继续等待用户人工检查。

修复前冻结失败案例族：字段名／枚举／值类型（正例、非法值、相邻合法类、无 Type）；门向／开口局部轴（旋转宿主、跨楼层、显式冲突）；Type 共享依赖（单实例、多实例、未请求范围）；原子恢复（多错误组、合法字段对、无关变化、空／截断输出）；上下文／预算（small/multi-storey、stage/resume、重复输出、失败消耗）。现有双层真实候选仅作为已揭示开发复现，禁止混入盲测成功率。

预算合同：公共 Generation 新任务默认最多 32 次调用、累计 2,000,000 token、3,600 秒已测 Provider 活动时间；这是拒绝继续调用的工程上限，不是新真实调用授权。每次调用先预留 UTF-8 输入字节数＋既有 Provider 输出上限，不下调输出长度来绕过预算；已返回且有合法 usage 的调用按实际消耗结算，空／失败／中断用量不明时保留预留量。旧会话逐文件收纳既有 response/request 的预算占用，记录来源哈希；无法判断的副本保守重复计数，历史未测耗时明确标记未知。恢复不能静默扩大额度，锁冲突或损坏状态阻断。活动时间门禁不会中断正在执行的 transport；最终发布前再次检查。直接调用内部 stage helper 不构成完整任务预算入口。

本轮收尾证据：[本地离线记录](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/scoped-offline-evidence/pipeline-stability-implementation-20260908/verification.json)。各轮测试存在重叠，失败 XML 同样保留，不合并为独立案例成功率。新增错误组测试只使用测试场景；此前双层真实候选没有被手改、重编译或登记为成功 Proof。

下一步明确为 **Generation Stage Preflight／新准入**，随后才能恢复真实双层开发验收；该阶段尚未执行。当前改动证明确定性约束、恢复及预算机制的离线行为，不能声称真实修复成功率已提高。仍未实现任意字段别名推断、自动解决真实用户门向／材料／exact Type 冲突、跨 IFC Type 复用、Repair 工程师语言空间定位或 strict Provider 适配。已有 Proof 的人工确认与登记要求不变。

### 13.4 2026-09-09 阶段准入与真实双层复验

本节更新上一检查点。用户已明确要求完成修复并调用 Provider，原双层请求及独立 IFC 预期保持冻结；复验属于已揭示开发案例，不是盲测。

- Generation Stage Preflight：`tests/agent tests/compiler tests/contract_v2 tests/ifc_quality` 首轮 **905 passed／3 failed／0 skipped**，原 XML 与日志保留。三项失败均来自旧 REPL 离线夹具只写响应 ID、缺少模拟 token usage，被新历史预算门禁正确阻断；补齐夹具用量后，REPL／预算相关 **19 passed**，含三项新增未知历史用量拒绝案例的预算复验 **13 passed**。这两组存在重叠，不合并为独立总数。
- `compileall src tests scripts` 与相关路径 `git diff --check` 通过。三层代表性离线模型经真实公共 ready-session 代码、编译和最终 gates 发布 IFC，约 9.3 秒，主进程峰值工作集约 164 MiB；生成／Audit 上下文分别 45,780／45,331 UTF-8 字节。未测子进程内存，不宣称大型建筑性能。测量脚本的缺失 sidecar、非法空 provenance、统计字段错误均保留，不能计作产品或真实 Provider 失败。
- [当前 Stage Admission](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/admission.json) 已记录环节矩阵、初轮失败、聚焦修正、依赖和源哈希。准入仅覆盖 Generation，Repair source／private Gold 在纯文本 Generation 输入中不适用；没有执行 Full Preflight。
- 已基于该准入启动 `api.deepseek.com / deepseek-v4-flash` 的真实公共 CLI，默认 `legacy_full`。调用运行目录独立于旧尝试，全部原始响应、失败和预算记录保留。完成状态、独立 IFC 逐项核对和视觉检查以后续实际运行报告为准；未通过前不称为可交付双层 IFC。

本次只修正离线夹具及增补预算反例，没有削弱未知用量阻断或扩大任务预算。待人工 Proof 仍不得登记或晋升 accepted。

真实运行更新：Brief `cbd4a500-48aa-4d1e-9909-f2fb74d5ebc4` ready，Generator `b48255e4-349d-43e9-816b-8600b6fd6450` 返回完整 JSON，但九项基础门窗约束阻断，无 IFC／Audit。两次响应共 117,920 reported token，原始尝试保留。候选普遍把矩形截面中心误作角点，旋转宿主的子级还重复设置世界轴；不能仅改报错的门窗或放宽门禁。

新增只读 `generation-authoring-contract/1.1`：明确矩形中心／底标高、父子坐标逆变换、楼层标高只应用一次，以及 slab void、开口和填充的编码规则。支持显式选择 1.0，旧投影哈希不变；已注册 Prompt／Schema 未改。八项朝向／尺寸组合独立编译并检查 IFC 网格包围盒；相关公共链路／两策略／早期恢复回归 67 passed，上下文／预算／版本 25 passed，旧哈希 1 passed。初始 10 failed／8 passed 的红测试及一次命令路径错误保留。[补充准入](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/geometry-admission.json)复用同阶段基础证据并覆盖变更上下游；不扩大 BASIC_FILLING_CONSTRAINT_CONFLICT 自动修复白名单。

第二次真实生成准备复用原 Brief、继承累计预算并保存到 fresh 目录，但 transport 前被自动审批拒绝：要求明确授权向 `api.deepseek.com` 发送本次完整新载荷。已生成[本地载荷预览](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/geometry-payload-preview/prompt-rendered.md)，待用户确认该具体范围。此审批拒绝不是一次 Provider 失败，也没有新增真实调用。当前详细入口为[本轮报告](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/REPORT.md)；尚无可交付双层 IFC，未进行双层视觉检查或 Proof 登记。

## 14. 渐进重构：工程意图到确定性几何

用户已批准将“LLM表达工程意图，确定性代码完成坐标换算与IFC组装”作为后续重要方向，要求逐渐重构，不一次完成。每次只接入一个有明确输入、失败复现和保全检查的构件路径；不能把新辅助函数当作完整Generation链路已迁移。

### 第一小步：矩形边界与 scaffold 屋面（2026-09-09）

已实现 `geometry_authoring.rectangular_prism_attributes`：输入明确父级及父坐标系中的三维最小／最大边界，确定性计算XY中心、底标高和截面／拉伸尺寸，输出既有BIM JSON的放置与表示属性。拒绝缺少父级、非数值、NaN／Infinity、退化或反向边界；不猜测角点含义、不隐式转换单位、不修改输入、不添加材料或普通属性。旋转及平移由父级已有放置继承一次。

本次只接入 `complex_scaffold` 的矩形屋面，修复其将 `(0,0)` 角点误用为截面中心、屋面偏移半个宽度／进深的确定性缺陷。hypotheses：若是原点错位，XY应恰好偏移半尺寸且旋转后偏移随父级旋转；若是单位错误，跨度也会变化；若是层高重复，Z边界会错。重读IFC的两层／三层及旋转父级案例确认第一项，未修改尺寸或Z语义。该路径不是默认LLM候选的自动校正器，也不能修复此前双层真实候选。

验证：新增20项先红后绿（其中4项直接复现屋面实际IFC包围盒错误）；连同scaffold、公共入口相关集成与多层矩阵，共 **30 passed**。与基线 `33ecbfc0` 的确定性比较证明两层／三层仅屋面XY中心改变，其他实体和全部关系相同；compileall及相关diff检查通过。证据位于本地 `.tmp/roof-refactor-red-20260909.xml`、`.tmp/roof-refactor-green-20260909.xml`、`.tmp/roof-refactor-preservation-20260909.json`。这些是聚焦离线回归，不是系统能力提升或真实Provider结果。

### 后续顺序（尚未实施）

1. 明确墙／楼板的边界和锚点输入后，逐个接入同类确定性转换；先修正实际旧路径，再扩大使用范围。
2. 为一个门窗入口增加显式“楼层＋宿主＋尺寸＋位置”到局部放置的转换，冻结缺事实、旋转宿主、跨层和共享依赖边界；不得自动移动宿主来适配错误候选。
3. 需要LLM提供新的工程意图结构时，新增版本合同并接入一条公共纵向链路，再逐步扩构件与两种策略。每一步仍须独立重读IFC、约束修改范围并保留失败证据。

本轮未新增真实Provider调用、未运行Full Preflight、未修改Prompt／Schema或accepted Proof；legacy_full默认与staged显式选择不变。scaffold源码已变化，旧live准入哈希不能直接复用，后续调用前需评估并补充受影响路径验证。本轮请求只完成这个小范围重构，不继续扩大到完整几何重写；真实双层交付及人工Proof仍未完成。

### 后续真实运行与完成情况复核（2026-09-09）

用户随后授权继续真实调用；基于原 Stage Admission 增补屋面改动的 30 项聚焦回归、保全比较及源码哈希，形成 `roof-admission.json`。此前 transport 审批阻断已解除，继承原 Brief 和累计预算，在新运行 `5cd2006f0891913f` 执行真实 Generator／Audit，未手改模型。此段为最新状态，取代上文“等待授权／尚无双层候选”的历史检查点，但不表示完成发布。

已有真实 Generator 生成的 IFC2X3 候选：2 层、4 空间、10 墙、3 板、10 窗、3 门和楼梯／实际楼板洞口；冻结请求独立重读检查首次及本次复核均为 167 项通过。27 个实体构件网格化成功；整体、剖看及门窗近景观感协调，图片来源哈希与 IFC 一致。然而正式 geometry gate 仍有三项阻断，真实 Audit 返回 blocking／revise；不能由独立检查或外观判断覆盖它。

最新[完成情况核验报告](../../dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/completion-recheck/REPORT.md)记录：楼板洞口无显式 ID 时派生的预期身份未与候选绑定；Brief 的隔墙只保留邻接和厚度，净空间留墙厚、二层平台仅局部接邻，无法可靠推导原请求的完整隔墙边界；门禁争议被送往候选 ChangeSet 后，missing_facts 引用不可寻址的预期／Brief 路径，两次返回均被拒。后续优先建立这三个边界的通用失败族，区分意图事实缺失、身份绑定失败和真正候选几何错误，再逐步修复；不靠放宽门禁或修改正确几何过关。

同任务预算保存了 6 次完成响应（Brief 1、Generator 2、Audit 1、ChangeSet 2），reported token 为 331,538；第 7 次 ChangeSet 保留 172,003 token 预留，响应与用量未知。核验时无 Python 运行进程，旧 execution.json 仍为 running，终端发布未完成，中断原因未知；没有将它重写为成功或清除预留。此前“通过自动门禁”的进度表述已更正为仅部分检查通过。

此次完成情况核验没有新增 Provider 调用或行为修改；报告 14 个本地链接及源文件哈希保全检查通过。候选与失败尝试留在开发运行目录，没有新建待人工验收的成功 Proof、没有登记／accepted 安装，未运行 Full Preflight。当前阶段为 **工程阻断，待上述离线修复与完整终端验收后再收纳 Proof**；原有 Proof 人工确认要求不变。

## 15. 人工验收收纳与工程修复待审方案（2026-09-09）

用户随后明确“我验收过了没什么问题”，授权将本次有效模型、报告和图片收纳到 Proof，并记录人工已验收。最新[人读集合](../../dataset/processed/proof/generation/phase6.6/two-storey-community-20260909/README.md)使用既有 package 格式及独立 review-manifest：`status=human_accepted`，`machine_acceptance_status=blocked`，`accepted_proof_installed=false`。人工结论绑定本次 IFC／request 哈希；源运行、失败响应、未知预算和旧报告字节保持不动，不覆盖第 14 节描述的机器结果。该集合可用于展示已由用户检查的模型，不能作为严格端到端成功或稳定性提升证据。

用户先要求审核方案，随后明确批准按内容和 pipeline 修复并提高循环解决能力。下表为 **已批准的小步实施范围**；具体完成情况见本节后的执行记录，不把范围批准写成实现完成，也不一次重写 Generation。

| 顺序 | 问题与建议 | 必须证明的边界 |
|---|---|---|
| R1 事实完整性 | 将请求中明确的墙端点／边界和楼板洞口位置带入版本化 Brief 与 Expected Facts；显式范围优先，空间邻接仅作为具有唯一几何结论时的推导。已提供事实不能被摘要丢弃后重新问用户。先用跨场景离线复现判断问题在哪一层，再选择是否确需新 Brief 版本。 | 净空间之间有墙厚、局部平台只接邻一段墙、旋转／跨层、显式与推导冲突、确实缺值；显式事实来源保留，禁止根据当前候选反向补预期。 |
| R2 身份一致 | 无显式 ID 的楼板洞口在 Expected Facts 中一次生成稳定身份，Generator／Gate／ChangeSet 共用；旧候选兼容只能在明确宿主及冻结几何约束下唯一绑定并记录依据。 | 同板多个洞口、等尺寸不同位置、错误宿主、跨层、零／多候选、显式 ID 冲突必须阻断；不能使用模糊别名或仅按尺寸碰巧一致认定同一对象。 |
| R3 纠错归属 | 分开候选错误、Brief 事实缺失、Evaluator／gate dispute。后两类没有合法候选写范围时，应返回工程诊断或针对真正缺失事实澄清；在 transport 前验证问题路径能映射到合法候选写范围。修复 missing_facts 的寻址合同若影响已发布版本则新增版本。 | 含混合问题的请求不能把门禁争议一并送往改几何；不重复花调用修不可写对象；合法局部修复、只读依赖、原子回滚及未请求内容保全仍通过。 |
| R4 中断收尾 | 任务预算／调用日志与会话恢复核对，区分已完成、失败、仍在执行和中断未知；未知调用保留预留，恢复不能重置预算或把遗留 running 当成功。先检验现有恢复机制缺口，再做最小修改。 | 注入进程在 transport 前、响应保存后、预算结算前、最终发布前中断；防重复请求、证据追加、无部分发布、终端幂等。不能凭本地无进程断言远端未收费。 |

验收顺序：冻结真实失败与相邻正／反／边界案例 → 每个 R 步骤先红后绿及直接上下游聚焦回归 → 同一旧候选用固定的新评分器重算并保留前后结果 → 复验两策略相关公共路径与澄清／恢复 → 判断同阶段准入是否仍有效 → 才进行有界真实验收。旧 IFC 不修改，旧 Audit 不重写，后续成功另立运行记录。Full Preflight 不自动升级；这组修复不以单例成功宣称系统稳定性提高。

### 第一批执行：R3 路由与回退边界

优先闭合已命中真实调用浪费的 R3 边界，再扩展 R1／R2 的事实合同。旧流程存在两层问题：normalizer 将 GEOMETRY_EXPECTATION_INCOMPLETE／Audit gate_dispute 当作候选错误；修正主路由后，公共路径测试又揭示其返回 None 会让旧 Repair fallback 重新调用 Provider。该发现说明只修改分类 helper 不足以修好整个 loop。

已实现：结构化 gate_dispute 分类和预期不完整进入既有 gate_issue 工程诊断；混合候选问题不能覆盖该停止决定；信息级历史提示不阻断合法模型；旧 Repair fallback 在创建 Provider／预留预算前遵守已落盘的路由及 retry_allowed。既有 issues／route schema、Prompt 版本和 IFC 文件未重写。这里的旧 gate_false_positive 枚举仅沿用“门禁适用性争议”的现有路由语义，不宣称已证明所有门禁为误报，也不自动放行模型。

验证：修正新测试夹具的缺参数／staged revision 后，冻结有效红结果 **9 failed／4 passed**；首次实现得到 **63 passed／2 failed**，两项失败暴露真实公共路径的 fallback 绕行；补齐该路径后，两策略聚焦 **2 passed**，最后完整相关回归 **72 passed**。范围包括分类、混合顺序、正反例、停止决定、公共生成／正常局部纠错／两策略共享链路；staged 初始生成使用明确 fake seam，后续编译、门禁、Audit 路由和终端检查使用实际代码。首次夹具失败日志保留，不能当作产品失败计数。

对已揭示双层运行的原样确定性重放，决策从 regenerate_json／retry=true 变为 gate_issue／retry=false；六份源文件哈希不变，未新增 Provider 调用。证据位于 [R3 离线记录](../../dataset/processed/ifc-presentation-validation/pipeline-gate-routing-20260909/verification.json)。相关 compileall 与 diff 检查通过；未运行 Full Preflight 或新 live admission，当前代码变化后不能直接复用旧 Provider 准入。

本批只证明路由／回退缺陷已修复，不证明实际生成成功率提高。R1 明确事实完整性、R2 洞口身份、R3 其他合法 missing_facts 地址转换和 R4 中断状态收尾仍未完成；已批准后续继续，无需再次讨论既定产品选择。人工已验收 Proof 的机器阻断状态和原始证据保持不变。

### 第二批小步修复：洞口身份与显式墙界合同（2026-09-09）

R2 已接入新的 `design-geometry-expectation/1.1`：冻结事实中已有的洞口 ID 严格匹配；只有系统派生 ID 不存在时，才允许独立重读 IFC，根据唯一 IfcSlab 宿主、唯一 Voids 关系及精确世界坐标包围盒建立一对一绑定。位置匹配上限为 1 微米，不沿用普通几何检查的 5 厘米容差来猜身份。错误宿主、重复身份、多个匹配、一个洞口承担多项预期、不可读几何均阻断。投影中的重复洞口 ID 和缺少边界不再静默覆盖／丢弃。保留显式选择 1.0 的旧行为；已揭示旧例的 1.0 投影与冻结文件完全一致。

验证：首组红测试 9 failed／7 passed，第一轮绿测试 16 passed；追加边界红测试 2 failed／19 passed，最终相关回归 **80 passed**，包括编译后重读、毫米级位置偏差、旋转、唯一性、公共 Generation 和两策略相关路径。原样重读旧双层 IFC 后，阻断从三项减少为两项墙预期缺失；八份原始文件哈希不变，没有改模型或重新宣告旧 Audit 成功。详见 [R2 离线复验](../../dataset/processed/ifc-presentation-validation/pipeline-opening-binding-20260909/frozen-case-replay.json)。

R1 本批为 partial：新增 Brief 2.3 与 ChangeSet 1.5，两个公共 Brief 入口及新语义 ChangeSet 路径使用新版本；已有 Prompt 字节不变。合同明确完整墙界／中心线优先于 connects，净房间之间允许已确认墙厚，局部平台不缩短显式墙体，真实冲突仍澄清。四项跨轴／局部平台测试验证已有事实投影保留完整墙界且缺失事实不猜测；版本接入先红后绿，公共调用、澄清恢复、registry 和 ChangeSet 相关首轮 44 passed，补新旧 ChangeSet 真实代码载荷／版本绑定后 **46 passed**。这是合同及确定性传递验证，不能证明真实 LLM 已不再漏提取事实。

尚未完成：R1 的原文事实完整性独立核验、R2 在 Expected Facts／Generator／ChangeSet 间统一派生身份、R3 其余 missing_facts 地址转换、R4 中断运行状态收尾，以及新一例建筑的公共链路与真实 Provider 验收。当前准入需按变化范围更新；本批未执行 Full Preflight 或真实 IFC Provider 调用。人工已验收模型、机器阻断结论和旧尝试均保留。

## 16. 下一例 Generation 与论文图：已批准设计方向

后续设计决策权限以第 18 节为准：本节早期允许 Agent 自行补齐尺寸、布局和设计取舍的授权已收紧；未确认且影响布局、尺寸、通行或使用合理性的选择应集中澄清。光庭方向本身保留，实施仍后置。

用户希望下一例尽可能惊艳、美观且稳定，作为高水平论文配图。建议目标是 **“两层光庭阅读馆”**：围绕一处矩形采光庭组织阅读空间，立面使用有节奏的竖向窗组，浅暖灰主体配深色细框和有限木色强调，让层次来自实际空间、比例及光影。当前只提出设计目标，不将其写成已经验证可生成的能力，也不立即启动 Provider。

### 当前能力和需要补充的内容

- 已有实例证据：矩形两层建筑、直跑楼梯及楼板洞口、基本单／双面板窗、单开门、部件分色与协调主题。多边形拉伸在合同和 scaffold 中有实现，但这不证明光庭／回廊复杂组合已通过公共链路验收。
- 当前实际查看器与 PNG 脚本主要是网格、颜色和简单明暗展示，缺少成熟的投影阴影、环境遮蔽、出版尺寸控制和多图一致相机；仅增加模型数量不能解决画面扁平的问题。
- 建议先完成 R1—R4，随后用 **一个矩形光庭、正交墙板、无悬挑回廊** 建立有界公开请求→几何／开口→IFC 的案例族。若当前合同无法完整保留空洞／边界，新增窄版本支持；缺少必要的栏杆／防护表达时明确提出小范围扩展，不能渲染出模型里不存在的构件。
- 出图作为独立改进：只读取最终 IFC 网格，增加固定相机、可复现光照和阴影、抗锯齿、透明面排序以及高分辨率导出；相机、剖切及显示隐藏可改变，IFC 几何、材料语义与实际颜色不能在图中偷偷替换。环境和背景若仅为展示需在图注标明；不以生成式补画冒充真实 IFC。

### 推荐的图与验证

主图为克制背景下的三分之四整体视图；配一张光庭／楼梯剖轴测，门窗部件近景，以及自然语言输入到可核验 IFC 的小型过程图。统一尺度、字体、视角和有限颜色，导出无文字高分辨率底图及可编辑矢量标注，具体尺寸按目标期刊栏宽确定。美观不能代替论文的科学贡献；成功示例作为可追溯案例图，稳定性主张仍需包含失败的冻结多场景评测。

首次设计输入应采用人类工程师语言，例如：“请设计一座明亮、安静的两层社区阅读馆，围绕一个矩形采光庭布置阅读空间，入口清楚，窗户排列有秩序，浅暖灰墙面搭配深色细窗框和少量木色。两层之间用直跑楼梯连接，真实保留庭院和楼梯洞口。”下一步将按已授权工程判断补充必要尺寸、明确物理材料和视觉要求，冻结完整输入及验证预期；这段草案尚未发送 Provider。

执行顺序：继续完成 R1—R4 的小步修复，再以光庭阅读馆验证必要的有界建筑表达及出图改进。默认采用建筑整体主图加光庭剖轴测组合。已有方向不再等待审核；真实 Provider 仍需当前阶段的适用准入。

后续决定更新：用户已批准 pipeline 修复，并在查看 [光庭阅读馆概念图](../../dataset/processed/ifc-presentation-validation/courtyard-library-concept-20260909/README.md)后，明确授权朝该图的建筑方向实施，由工程判断把握还原程度，**排除花草景观**。本决定取代上文待审措辞，不再次询问既定方向。该图仍是 AI 概念示意，非 IFC，未收入 Proof。

已授权优先目标：两层正交围合与矩形光庭、可连续通行的回廊、明确入口与楼梯洞口、有节奏的基本门窗和适用防护；浅暖灰主体、深灰框、透明玻璃及有限木色／木材强调。下次请求须明确实际材料与仅视觉颜色的区别，由已授权设计选择形成可读输入并冻结预期；不由材质名称补写强度、耐火或热工值。先在现有表达内实现，再按失败证据增加必要的小范围能力；不追求未支持的复杂曲面、装饰五金或凭渲染补出不存在的建筑。图中的家具和景观不作为本轮还原目标。

出图以实际最终 IFC 为唯一建筑来源，先整体和光庭剖轴测，后门窗／材料近景。下一例具体尺寸和设计取舍由已授权范围内的工程判断制定；只有真正合同冲突或新增范围才集中询问。尚无新光庭 IFC 或可投刊成图，不能把本次方向批准和离线修复写成生成验收完成。

## 17. 收尾后的三层相关案例复验（2026-09-09）

用户最新顺序为：简单收尾 → 与上一组接近难度的三层楼验证并出报告 → 再做光庭。本轮不扩展光庭能力。采用三层社区阅读活动楼，增加第二段楼梯和第二处楼板洞口，保持正交墙、基本门窗及原配色／材料边界；该例是新的相关开发案例，不是分组隔离的盲测。

当前输入、预期及独立 IFC 检查器已冻结于[三层案例目录](../../dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/request.txt)。与旧阶段准入相比，十个已登记文件变化均来自前两批有界修复；依赖、其余源文件和基础阶段证据哈希核对通过。当前路由／公共入口／澄清／版本／ChangeSet 相关 106 passed，复用上一批洞口 80 passed 和墙合同 46 passed，形成同阶段补充准入，未执行 Full Preflight。相关测试有重叠，不相加为独立成功率。

首次 transport 被自动审批要求具体载荷／目的地授权后拒绝，没有产生 Provider attempt。用户随后明确批准本案例向 `api.deepseek.com / deepseek-v4-flash` 的有界 Generation／Audit，真实公共 CLI 已启动，默认 legacy_full。Brief 首次 ready，三层完整墙界及两个洞口身份／宿主均保留；最终 IFC、Audit 和人工状态以后续实际报告为准。原双层模型、旧 attempts、未知预算及人工验收状态均未改动。

最终[三层报告](../../dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909/REPORT.md)：公共链路首次 compiled／Audit accept，共3次完成响应、183,829 reported token，无 Repair／ChangeSet。IFC 246,275字节，重读请求检查290项通过，40个实体构件网格化成功。独立表格比较器首轮两项因二进制浮点精确比较误报，原结果保留；新增v2仅修正数值比较，六个边界检查通过，同评分器重算旧双层负例仍失败。生产门禁与原模型未改。本例使用显式洞口身份，派生身份兼容和失败循环分支未在此次 live 中触发，不能据此宣称其真实成功率提高。

额外工程复核发现阻断：测试输入由 Codex 将两段反向楼梯安排在同一平面，实际网格在第一段到达端的上方间隙降至0。现有门禁及 Audit 未检查行走净空。机器接受事实保留，但单独记录 `engineering_review_status=needs_design_revision`、人工待审、未登记 Proof。建议先修订为不遮挡的楼梯布局，并用跨层梯段／楼板／梁案例补有界净空诊断；不把尺寸符合请求当成建筑可用性。本轮止于三层检查报告，光庭继续后置。

## 18. 设计澄清、忠实建模与合理性检查（2026-09-10 用户确认）

本节是最新产品边界，取代先前“未指定的设计自由度可自主优化”的建议。用户要求优先不等于设计合理性已经通过；系统不承诺完整建筑规范审查。

- 未指定且影响布局、尺寸、通行或使用合理性的设计选择，先澄清，不自行优化。已有明确事实及其唯一确定性推导无需重复问；已经批准的默认配色、受限模板参数及最小合法 IFC 附件继续适用。不追问未请求的 Type、材料或性能值，不补造属性。
- 明确要求之间的冲突同样进入澄清。保留原要求，说明楼层、方位、具体位置、原因及候选方案的影响，由用户选择；GUID 只作内部证据。问题尽量分组集中提出，建议不等于用户已授权改变设计。
- 用户确认忠实建模已知有缺陷的设计时，可按要求交付技术上有效的 IFC。Audit 和交付文档必须指出已知问题、影响、证据及未检查范围；请求符合性和使用合理性分别记录。用户确认不能让已知问题变成“合理性通过”，也不能覆盖技术有效性、范围保全等硬门。此行为尚待版本化接入，不能据此绕过当前发布门禁。
- 技术有效性、请求符合性、基本使用合理性及特定规范符合性分开报告；未检查或依据不足标为未覆盖／待确认。规范阈值须绑定适用规则、版本、建筑用途等依据，不能把经验值当作普遍规范。
- 候选违反已确认要求才进入有界局部修复；缺少设计决定或要求冲突进入澄清；检查器错误／适用性争议进入工程诊断。修复保持未请求内容，重检直接关联构件，重复且无进展时停止。等待回复、空白回复不构成设计决定。

小步实施顺序：先验证澄清等待与回答边界；再按新版本合同补充冲突原因、用户确认及 Audit／文档问题记录的公共接入；随后建立楼梯行走面与上方梯段、楼板、梁的有界净空检查，区分确定碰撞、阈值问题和无法评估。暂不扩成完整规范校核，不直接修改或重新验收三层旧 IFC，不启动新 Provider。

本批 debug 假设按优先级：① 共享控制器仅检查回答 truthiness，纯空白可触发后续模型调用；② record_model_call 未限制等待状态，可能无用户回答即替换 Brief；③ 问题未覆盖全部阻断项导致丢失——代码及 Prompt 核对表明每轮 1–3 个关键问题可分轮处理，不能据此认定缺陷，本批不更改该合同。

修复前冻结测试族：空串／空格／制表符／换行／全角空格的回答不调用后续模型；有效回答原文字节保留，未知回答保持 Draft，部分回答仍可继续澄清；等待用户及终端状态不能直接接收新 Brief；公共澄清入口和数据库恢复后仍遵守以上限制。该族是离线回归，不是盲测能力评估；本批不声称已能识别任意设计冲突或已完成合理性 Audit。

第一批已实现：`ClarificationController.record_model_call` 只允许 `awaiting_model` 接收结果；等待用户及终端状态不得直接被新 Brief 覆盖。`answer_and_rerun` 在调用 invoker 前拒绝纯空白回答，仅用于判断的 strip 不修改有效回答原文。终端 REPL 已有空白处理，此次补齐共享控制器及可程序调用／恢复的公共入口边界。

验证：首轮夹具缺少必要 evidence_refs，13 failed／4 passed 不能作为产品基线；修正夹具后有效红结果为 **12 failed／5 passed**，最小实现后 **17 passed**。直接相关回归 **60 passed**（包含这17项，不相加），覆盖 `test_clarification_answer_boundary`、`test_live_clarification`、`test_clarification_resume_preservation`、`test_clarification_demo`、`test_interactive_cli_flow`、`test_phase6_2_fix_repl_cli`、`test_interactive_cli_generation`、`test_design_brief_attempt_preservation`；公共路径使用 fake Provider，实际会话恢复及相关 IFC 编译检查，不是 live 能力证据。聚焦 compileall 和本任务路径 diff 检查通过；本地红／绿／回归 XML 保留在 `.tmp/clarification-boundary-{red-valid,green,regression}-20260910.xml`。测试与政策冻结提交 `a6ea9fbc`。

本批仅证明空白回答和非法状态跃迁缺陷已修复。并未验证模型能正确理解所有有效文字回答，也未实施新的 Audit 合理性字段或净空算法。未运行 Full Preflight、Stage Preflight 或真实 Provider；再次 live 前需对上述共享澄清路径变化复核准入。旧三层 IFC、机器 Audit、报告及 Proof 状态未改。

### 双分支 Proof：原文件作为参考，追加澄清形成新约束

用户已确认“原文件不变”指旧请求／IFC／运行证据保留作为参考，不禁止 A 分支通过追加澄清修改对应约束。A 分支展示用户确认调整方案后的生成；B 分支展示用户知悉问题后仍坚持原要求的忠实建模，Audit 和文档持续记录已知问题。两者分别形成运行及待人工检查的人读材料，不能改写旧 Audit 或把脚本回答伪称真人对话，也不能把 B 的忠实表达验收写成合理性通过。具体交付仍需前述新合同、公共链路与适用验证完成。

A 的布局决定：用户允许采用上轮具体建议或向外扩建，并授权本次二选一；选择内部调整以保留外轮廓及立面。保持建筑外轮廓、标高、墙厚、梯段宽1200毫米、18×175毫米踢面与18×300毫米踏面；三层分隔墙整体西移300毫米至 X=7300～7500，大厅净宽改为7300毫米，楼梯间净宽2500毫米。首层到二层的北向梯段为 X=7500～8700、Y=1500～6900；二层到三层的南向梯段为 X=8800～10000、Y=1500～6900，两梯段平面错开，中间100毫米间隔。二层楼板只切第一梯段对应洞口，三层只切第二梯段对应洞口；南／北平台随楼梯间改为 X=7500～10000，三樘分隔墙门随墙西移而保持原南北位置与尺寸。其余原要求保持。每层大厅面积减少2.52平方米；本决定仅消除两梯段相互覆盖的布局原因，不构成完整净空、通行或规范验收。原请求排除栏杆的事实保留，不能将无防护展示模型描述为可施工设计。追加澄清按用户授权的测试分支脚本记录，不伪称由 Provider 提问或逐字现场人工回答。

第二批小步接入先冻结 Audit 问题保留合同：假设① 旧 Audit 没有已知问题和用户决定的独立记录，可能忽略上下文；② 无来源绑定可将模型建议误当用户确认；③ 只有 accept/revise 结论会让已知设计缺陷被抹掉或重复改写。新增测试以缺少记录、版本降级、问题丢失／重复／未知、错误证据路径、虚构引文、assistant 轮次、过期对话哈希、修改过的证据和未决选择为负例，A 修订／B 保留为正例。先建立公共 Audit stage 红复现，再新增版本而不重写旧 Prompt；本批不声称独立发现所有合理性问题或验证任意用户自然语言决策。

第二批已接入：新增显式启用的 `design-brief.v2.4` 与条件选择的 `audit.v3`，旧 Prompt、Schema 和普通入口默认版本保留。调用方在 `design-review-context.json`（`text2ifc/design-review-context/1.0`）提供已授权的 revise／retain 决定、完整用户原句／轮次及参考证据哈希；这不是 Agent 可自行编写的放行依据。对话和证据必须匹配当前运行，assistant 轮次、未知决定、重复问题、虚构引文与过期文件在 transport 前拒绝。引用匹配只能证明出处，不能单独证明任意自然语言同意的语义，调用方仍负责合法授权。

Audit 3.0 必须逐项保留已知问题和局限，不能降级、遗漏、重复或声称用户接受即问题已解决。保留分支为 `retained_known_issue`；修订分支只允许 `not_verified` 或阻断的 `unresolved`，本版本不接受 Agent 自报 `resolved` 作为独立工程证据。普通技术门及请求符合性仍检查，Audit/最终会话报告单独呈现合理性问题。最终发布重核上下文哈希；使用新 Brief 却没有已绑定上下文时，在 Generator 前停止，避免落回旧 Audit。后续仍需接入普通交互入口的决定收集、独立当前 IFC 复核绑定与通用净空检查。

验证记录：公共 Audit 定向红结果14 failed，首轮14 passed；最终发布和版本选择追加红结果3 failed／14 passed，修复后24 passed（含相关墙合同测试）。首轮相关回归102 passed／1条旧默认版本断言失败，更新接入检查后104 passed，补充76 passed；随后收紧为显式启用，新选择边界先2 failed再46 passed，缺少确认上下文先1 failed再22 passed。这些范围互有重叠，不累计成案例成功率；A/B 新输出尚未实际产生。测试使用离线 Provider，相关公共入口执行真实 IFC 编译和重读；没有新 Provider 调用或 Full Preflight。

最终普通生成、staged 相关公共路径及 REPL 回归 **19 passed**（`.tmp/design-review-public-final-20260910.xml`），验证显式启用与缺失上下文检查后的兼容性；测试与上述范围重叠，不相加为成功率。离线 A/B 公共链路的实际编译／重读仅验证接入，不代表三层新布局已经生成或通过工程检查。

分支输入、预算及运行前检查准备位于 `dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/`。两份 request.txt 与原文逐字节一致，追加脚本分别冻结到 conversation.json 并绑定独立检查器。原 IFC 对 A 新预期出现19项差异，对 B 原预期290项通过；同一原 IFC 的108个轴向净空采样最小为0、3个采样为0。此采样只覆盖本案南北直跑楼梯上方梯段／楼板／屋面／梁，非规范阈值判断或完整通行审查。每分支最多6次调用、80万 token、1800秒 Provider 活动时间；本次具体载荷授权待用户回复，尚未执行，不登记 Proof。

### A 首次真实尝试与共用缺陷暂停（2026-09-10）

用户随后明确回复“支持授权真实运行”。再次核对现有文件／依赖及两个分支 dry run 后，A 会话 `48dcf264b1a6df16` 完成 Brief、Generator、Audit、ChangeSet 共4次真实响应，288,462 reported token、446.750秒 Provider 活动时间。Brief ready 并提取修订布局；首个候选 JSON 合同通过，但18个 Type 的材料作用域被门禁拒绝，另有2个跨层楼梯名称误报。Audit 3.0 保留修订决定并标记 `not_verified`，没有越过技术硬门；ChangeSet 因授权字段不匹配返回 Draft，最终 `audit_blocked`，无新 IFC。详见[本次真实运行报告](../../dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/REPORT.md)。

离线原样复现确认 `_targeted_issues` 将具体 `/materials` 字段压成 `#/attributes`，Change Scope 因而不允许修正门禁所指材料；模型提出的范围澄清不能作为需要用户再次批准建筑设计的理由。另一个问题是名称检查将合法起止层描述中的到达层误作归属冲突；两段楼梯到达层均与冻结 Expected Facts 相符。4个合成字段探针中3个不满足精确路径目标、1个未知目标保全通过；没有修改生产行为或旧运行证据，不是修复成功证据。

下一步保持小步：① 建立正／反／边界及跨场景测试，再保留确定性报错的精确实体字段路径，不扩大到整实体或未经证据绑定的关系；② 使跨层名称检查依据已确认起止层判断适用性，保留无关层名及真实归属错误的阻断；③ 验证公共 ChangeSet、原子应用／回滚与范围外保全，以及两策略相关共用路径；④ 更新适用准入后再继续剩余授权预算。B 尚未启动，0次调用；A 预算已用4次，不得重置后假称新的完整6次额度。当前操作层准入暂停记录为 `RUN-HOLD.json`，不能仅凭旧 admission 文件哈希仍匹配就继续调用。两份新 IFC、图片、Proof及人工验收仍未完成；旧请求／IFC哈希保持不变。

### 本次获准的小步范围：语义字段路径与请求级 Type 检查

用户批准先修精确权限映射与请求级 Type 门禁，并强调限定范围。本轮只传递材料、属性、外观和模板等已有语义字段的精确路径，沿用稳定 ID 解析；保留几何修复现有依赖合同。不重构 Schema／Prompt、不改楼梯名称检查、不自动删除 Type／关联、不增加新 Provider 调用。新 Type 规则仅作用于 BIM JSON 2.1 Generation 候选：允许冻结请求的 Type 身份及关联实例，不允许候选凭 provenance 自报为编译器附件；合法最小 DoorStyle 仍由确定性编译器生成。材料／属性授权保持独立，不因允许某个 Type 就允许给它补值。

修复前假设：① 语义字段在 normalizer 被压成 attributes，精确传递可恢复原有 ChangeSet 操作；② 无请求 Type 缺少确定性检查，空材料 Type 也会通过候选门；③ 仅允许 Type ID 仍可能把其他实例悄悄加入共享组，须同时约束关联实例；④ 新检查若误施于最终编译器附件会破坏基本门，需保留公共编译重读正例。冻结19项案例族包含材料／属性／外观／模板、转义路径、未知／冲突目标、几何兼容、多 Type 家族、显式共享／独立类型、关联越界、值授权及基本门重读。首次夹具导入错误修正后，有效红结果13 failed／6 passed；这是离线回归基线，不是能力评测。

本小步已实施：`issue_normalizers.py` 保留上述语义字段原始 JSON Pointer，经现有解析器绑定稳定 ID；冲突／未知目标不获得修改权限。`semantic_requirements.py` 使用 IFC2X3 registry 的 Type 家族信息检查显式 Type／Style 和请求允许的实例—Type 配对，在公共候选门及最终验收复查路径生效；不影响 BIM JSON 2.0，也不靠候选自报 provenance 豁免。编译器最小门样式通过实际编译／重读正例验证。

公共应用验证进一步暴露同一范围内的问题：纯语义目标会沿原有依赖遍历开放门洞关系字段。补充四种语义字段的失败用例后，`change_scope.py` 仅从非局部语义目标及已有显式依赖提示启动遍历；混合问题仍保留有独立几何问题依据的依赖流程。最终案例族扩到27项，另含公共 Gate → Issue → ChangeSet → 原子应用／拒绝 → IFC 编译重读、整 Type 报错不授予删除权限，以及混合语义／几何兼容用例。关系夹具和集合排序断言修正后，依赖收紧前有效红结果4 failed／23 passed；实现后相关聚焦39 passed（含原有范围／回合测试）。测试先独立提交为 `8e8ef326`，生产实现另提交。

本轮离线验证记录：初步相关回归92 passed（`.tmp/type-scope-regression-20260910.xml`）；最终聚焦39 passed（`.tmp/type-scope-integration-green-20260910.xml`）；依赖边界收紧后的两策略公共路径、分段生成、CLI／澄清恢复及 Audit 回归69 passed（`.tmp/type-scope-public-regression-20260910.xml`）。范围有重叠，不累加为案例成功率。以上为离线测试，部分公共路径执行真实 IFC 编译／重读；没有新 Provider 调用、Full Preflight 或阶段发布验收。

旧 A 候选只读复查：现有38条材料预期不授权 Type；新检查识别37个未请求 Type、37条未请求关联及18处材料问题。原有两类 gate 视图合计36条材料诊断对应18个唯一目标，全部保持 `#/materials`。7份关键冻结输入哈希与旧诊断记录一致，没有改写历史运行；复查输出位于 `.tmp/type-scope-offline-check-20260910.json`。这证明本轮门禁与字段映射命中已暴露问题，不证明旧候选修复完成或普遍成功率提高。

继续边界：本轮不自动删除额外 Type／关联，不改楼梯名称检查，不迁移 Type 上的材料或属性，不改变原 IFC、既有 Prompt／Schema 或 Proof 状态。后续处理 Type 清理前须限定受影响关系和继承值保全，不能直接开放整实体或整图修改。A/B 真实运行仍遵循 `RUN-HOLD.json`；准入暂停未解除，A 已用4次调用、B 为0次，两份新 IFC 和人工检查仍待完成。

### A/B 真实续跑准备（2026-09-10）

用户随后要求继续 A/B 真实运行，遇到问题沟通。首先处理暂停记录中尚未解决的跨层名称误报。定位假设：名称检查只比较归属层导致合法到达层误报；豁免所有楼梯会放过其他楼层标签；只有唯一冻结起止层、正确出发层归属和名称同时含两个端点，才能缩小豁免范围。冻结14项中英文及不同楼层标签／构件族正反例，红结果6 failed／8 passed（测试提交 `268a114b`）。最小实现仅允许上述有依据的端点标签；无关层、仅写到达层、缺失／重复冻结记录、错误归属、墙体及候选自报端点继续阻断。聚焦和现有 Gate 回归52 passed，旧 A 四个动态 Gate 只读复查通过；不是旧 A 整体验收或完整名称语义理解能力证明。

续跑新增 `continue_branches.py`，保留原 runner、RUN-HOLD 和已提交运行证据。新目录 `continuation-20260910/` 单独保存当前准入和产物。A 复用首次真实 Brief 的原始文件，创建有来源关联的新 Generation 会话，原4次预算完整继承，至多再2次调用；不是原候选的局部 Type 删除，也不把复用 Brief 记为新调用。B 从冻结脚本开始，至多6次调用。两案同样保留80万 token、1800秒 Provider 活动时间上限，任何额外调用需另行授权。离线 runner 公共链路3 passed，涵盖两案实际编译／重读、原目录不变、累计预算、耗尽不调用和重复输出路径拒绝。继续使用 legacy_full；不改原请求、布局选择、Prompt／Schema、几何模板、Type 清理合同及 Proof 状态。

最终受影响公共路径回归31 passed（`.tmp/branch-continuation-public-20260910.xml`），覆盖两种策略的语义公共路径、Gate/Audit bundle、几何修复循环与 scoped loop；与前述范围重叠，不累加为成功率。原准入555个文件绑定只发生4个预期生产文件变化，其余551个保持一致；据本次52／3／31项及上一小步39／69项有效结果续接同一 Stage Admission，不运行 Full Preflight。新准入通过前暂停仍有效；旧暂停文件保留，由新准入明确绑定并说明解除依据，不改写旧失败记录。

### A/B 续跑结果与再次暂停（2026-09-10）

准入和具体授权冻结后真实执行8次新增调用，详见[续跑报告](../../dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/continuation-20260910/REPORT.md)。A 新会话 `60b27145d6d8d3a3` 复用真实 Brief，Generator／Audit 共2次；新候选再次增加39个 Type／Style、39条关联及34项普通属性，语义门拒绝。累计6次达到上限，最终 budget_blocked，无 IFC。新增144,164 reported token、202.063秒；含首次累计432,626 token、648.813秒。准确拦截不是自动修复成功，本轮仍未扩展 Type 删除或继承值迁移。

B 会话 `51592773914118fb` 执行 Brief、Generator、Audit、ChangeSet、Audit、ChangeSet 共6次。最终留下的候选 IFC 可编译重读，独立请求检查290项通过，40个可见实体网格成功；但生产几何门仍有2项 MISSING_STAIR_OPENING、2项 MISSING_STAIR_FLIGHT。第1轮补丁修正两处梯段名称，身份问题保留；第2轮响应 finish_reason=length，抛出 OpenAICompatError，流程未完成发布。前5次 reported token 合计320,167；第6次实际用量没有保存，按208,955预留 token 保守计账后预算为529,122，不是真实总用量。Provider 活动时间651.532秒。

只读定位新增共用缺口：Brief／预期中的楼梯与梯段身份同候选不一致（stair-1-flight → 派生 stair-flight-1-flight，而候选为 stair-1／stair-flight-1）；洞口实际 ID 多出 opening- 前缀。独立几何符合不能覆盖严格身份合同，下一步先冻结身份来源、父子角色及合法绑定的失败案例族，不临时加字符串别名或放宽门禁。楼梯名称的最小修复依赖唯一匹配的冻结记录，尚未解决此父子身份投影问题。

另有证据保存缺陷：OpenAI-compatible 解析器收到截断响应后携带 evidence 抛错，ChangeSet 调用路径未持久化该异常证据；本次第6次响应正文、响应 ID 和实际用量未落盘。已有输入、异常类型、预算和终端观察保留，不能补造丢失响应。下一小步优先公共截断／畸形响应证据落盘，再统一身份合同；修复进展按各阻断项分别记录，保留名称修复的局部进展事实，避免把任意变更误称整体修复。Type 图处理仍另行限定范围。

B Audit 持续记录 retained_known_issue；独立108点净空采样最小0米、3点为0，已知缺陷保留。图片来自实际候选 IFC，Codex 已做整体／剖开／门窗检查，配色协调但造型基础，无人工验收或合理性通过结论。候选只供诊断，未登记 Proof。新 [RUN-HOLD.json](../../dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/continuation-20260910/RUN-HOLD.json) 暂停后续调用，原准入／旧暂停／174份历史冻结文件及参考 IFC 不改写；两案均耗尽6次预算。继续前需先离线修复、适用复核及新的调用预算，不追加重试，不运行 Full Preflight。本次未推送 GitHub。

### A 起点澄清与 B 有界根因修复（2026-09-10）

用户要求先查原因、解释与旧修复的区别，再小改。A 实际复用首次 ready 的真实 Brief，从 Generator 重新调用，不复用旧失败候选；ready 是当时合同检查结果，不是任意语义无缺陷的保证。此前 Type 工作只补拒绝及修改权限，未修模型生成收敛或 Type 图清理，故不能将 A 重试解释为已修好该问题后的成功起点。

编辑前假设按优先级冻结：① Generator 的 entity_id_contract 只有墙／空间／门窗，缺少楼梯父子和楼板洞口，导致 authoring 和几何身份要求脱节；② v2.2 语义 Prompt 未保留 v2 的逐字使用技术 ID 指令，需新增版本补回而不重写旧版；③ 楼梯名称豁免仅匹配父项自身 ID，漏掉合法聚合的梯段子项，须以唯一冻结父子身份及实际关系验证，不能泛化豁免；④ 截断 parser 抛出证据后，ChangeSet 未落盘，预算也只记预留值，需在异常边界保留已收到响应与有效用量并停止，不自动重试。

冻结测试族覆盖不同 ID 命名／语言、显式与派生子项／洞口、重复或跨角色身份、错误父项／聚合／归属、公共 Generator 合同传递，以及公共 ChangeSet 的截断／无 choice／禁止输出／非 JSON／正常响应／缺失用量／耗尽预算。范围限于身份合同传递、名称适用性和失败证据，不删除 Type、不改用户布局或尺寸、不重写旧 IFC／运行／Prompt／Schema，不调用 Provider 或 Full Preflight。

根因已核实：B 实际发送的技术身份表只有 doors／spaces／walls／windows 四组；楼梯父子和楼板洞口未列入，而下游按 Brief ID 和确定性派生 ID 严格查找。旧 v2 Prompt 有逐字使用技术 ID 的规则，语义 v2.2 仅保留技术身份输入而未保留完整指令。新增 `bim-json-generator.v2.3` 补回规则，旧版本字节及 registry 旧条目不改；不是通过取消身份检查来接受旧 B。

已实施：`cross_storey_identity.py` 统一梯段及楼板洞口 ID 投影，补充到现有 entity_id_contract 的 slabs／floor_openings／stairs／stair_flights／roof；父项、子项和宿主单独列明，显式 ID 不改前后缀。沿用既有正常派生 ID；父项不含原前缀时，原代码会派生出同名子项，现改为独立子项 ID。跨角色和重复技术身份在投影时阻断，候选不能靠自己改名重新定义冻结身份。分包与几何预期调用同一派生函数；维持 explicit／derived 洞口绑定边界，未修改 IFC 检查器。

名称修复补齐之前遗漏的父子路径：只有冻结记录提供的梯段身份、唯一实际 IfcRelAggregates、正确 IfcStair 父项和起始层归属同时成立，子梯段名称才允许包含目的层。错误父项／无聚合／重复聚合／未提供子项／错误归属继续拒绝。之前只测父项 ID 的名称豁免属于覆盖不足，本次补的是这个缺口，不声称此前已完整解决。

异常边界已补：OpenAI-compatible adapter 在截断、无 choice 或禁止输出等解析拒绝时保留已收到的脱敏响应；ChangeSet 保存 provider-error、实际收到的 response 和可用文本／用量，再以 provider_failed 停止 scoped／staged 循环。携带完整 LiveProviderResult 的另一异常接口也覆盖。连接失败没有 response 时不造 response 文件；预算耗尽仍在 transport 前抛出原预算停止。异常中有效用量用于结算，缺失时仍保守计入原预留值，原 A/B 预算不回填、不重置。

验证：首次导入名称拼写错误不计产品基线；修正后有效红结果21 failed／8 passed（`763e749e`）。随后更正夹具 bounds 字段为现有 x／y 合同，追加 scoped／staged 停止、连接失败和携带响应异常；后者先1 failed／12 passed，再修复。补充测试提交 `f73b7ed2`。聚焦29 passed；身份／分包／原门禁回归147 passed；Provider／预算／循环回归91 passed；最终受影响聚焦60 passed；公共 Generator、两策略、续跑、Gate/Audit 和 CLI／恢复回归67 passed。以上互有重叠，不累计为独立案例成功率，全部使用 fake／注入 Provider；涉及的实际 IFC 编译重读仍是离线验证。XML 为 `.tmp/ab-{boundary-green,identity-regression,failure-regression,boundary-final,public-final}-20260910.xml`；聚焦 compileall、新 Prompt registry 哈希及 diff 检查通过。未运行 Stage／Full Preflight 或新真实调用，旧 RUN-HOLD 继续生效。

A 来源对照确认 Brief 逐字节复用、候选未复用、新调用只有 generate／audit，重启时只余2次预算。该安排验证了新门禁能拒绝另一候选，不是 Type 生成／自动改正已经修好的验证；下一次 A 真实尝试前仍需另行闭合这项行为和预算。B 首次只读探针漏调既有 wall／space binder，额外 missing-wall／space 诊断属于探针接入错误，原探针保留；按实际绑定步骤复查的 v2 记录确认旧 IFC 仍仅有2项 MISSING_STAIR_OPENING、2项 MISSING_STAIR_FLIGHT，没有被放行（`.tmp/ab-identity-readonly-diagnosis-v2-20260910.json`）。174份首次记录及335份续跑冻结文件无变化。

B 四张实际 IFC 图片本轮重新查看：浅暖墙、深色框与蓝灰玻璃协调，门窗部件清楚，体量仍基础；原零净空缺陷按保留决定存在，不做美化性几何修改。原候选、人工验收及 Proof 状态不变。已知限制仍是：模型是否遵守新身份合同未经新 live 验证；多余 Type 图清理未实施；已丢失的第6次响应无法回填；这批离线修复不构成系统成功率提升。

### A/B 通用修复闭环与整次运行预算（2026-09-10 用户确认）

当前基线为 `06230aa9`。B 身份合同及失败响应保存已有离线修复，继续回归，不重做或改写旧候选；A 剩余确定性缺口是：门禁能发现多余 Type／关联及材料／属性，但局部 scope 尚不能完整表达受控删除，模型可能只能改字段而无法完成正确的图变更。不能把这个缺口归结为预算不足或仅靠增加 Prompt 禁令。

预算以一次完整输出运行共用，覆盖 Brief、Generator、Audit、ChangeSet 和合法恢复。产品现有默认上限为32次调用、200万 token、3600秒活动时间，属于可配置兜底，不要求按阶段各分一小份。旧 A/B 的累计6次是历史演示配置，不能沿用为以后完整修复验收的永久上限；也不修改历史账本或抹掉失败花费。重试仍依靠有限修复轮数、重复候选／无进展、无法确定范围、缺少用户事实、Provider 失败等退出机制；预算放宽不等于无限循环。下一次真实运行需针对完整链路冻结新的配置及适用准入，本次先完成离线工程修复。

修改前冻结假设及可证伪预测：① Type 全记录问题被降为属性路径，导致合法 remove 被 scope 拒绝；精确操作授权应使同一补丁可应用。② 关联删除与成员缩减没有从冻结请求计算，可能留下悬挂关系或越权删除合法成员；按请求授权计算的图规则应同时接受清理、拒绝扩大范围。③ Type 携带材料／属性时，直接删除可能丢失请求值；仅以冻结实例请求重建所需字段并独立重读 IFC，可验证保留与未请求值移除，不能从候选反向授权继承值迁移。④ 只依赖模型自报 source Issue 或完成标签可能绕过保全；执行器必须验证实际图差异及显式请求，不允许隐式级联或几何改动。

实施边界：限于新 Generation 语义合同中的受控 ChangeSet 修正，不对 Repair 源 IFC 应用模板或自动 Type 清理，不重写旧 Prompt／Schema。优先复用已有显式 remove/update 操作；只开放确定性门禁证实的未请求 Type、未授权关联或成员及明确语义字段，合法 Type、跨组成员、几何和其它实体继续保全。未知引用、无法唯一绑定、需要猜测值或作用域的情形停止并给出诊断。用户已确认 B 保留的净空缺陷不改。

先冻结失败案例族再改代码：无 Type 请求／合法 Type 保留、混合共享成员、不同构件族及无规律 ID、实例直接值与 Type 附带值、未知引用／重复身份、部分删除／原子回滚、越权几何／跨组修改；公共路径使用 fake Provider 完成 Gate→Issue→Scope→ChangeSet→编译重读，并回归两策略、恢复及循环退出。现有 B 身份与异常证据测试纳入相关回归。结论仅限离线 Bug fixed，不把揭示案例称盲测或系统成功率提升；不启动新真实 Provider、Full Preflight、Proof 安装或 GitHub 推送。

本轮已完成的通用代码修复：

- `semantic_correction.py` 从冻结 Brief／expected facts 重新绑定请求、独立重算未授权语义问题，再生成受限操作合同。只有命中真实问题的 scope 才扩展；明确列出删除 Type、删除关联或缩减成员，以及需要保留的请求值和依赖。未请求 Type 不再停留于不可执行的整记录 Issue。
- 同一合同进入模型上下文、scope 和原子应用检查。继续使用 ChangeSet 1.0 的显式 remove／update，不自动应用或级联删除。新增 `bim-json-changeset.v1.6`，原 Prompt 与 registry 旧条目保持不变。字段权限不再意味着可以删除合法 Type、类型关联或只有语义字段权限的实例；部分清理、越权修改和不正确的请求值不生成新 revision。
- 属性清理使用精确的最终容器值保留其它属性，支持带 `/`、`~` 的合法自定义键。Type 删除影响实例时，仅从冻结请求写回必要的直接值；不复制 Type 中猜测的材料／性能。已有正确继承值保持继承，合法共享成员及其它构件保持不变；未知引用、身份不唯一、直接／有效值冲突或需要猜测覆盖的情况在 transport 前停止。布尔与数值不能被 Python 的相等比较混同。重复候选身份返回结构化阻断，不再抛出未处理异常。
- 预算实现原本就是整次 Generation 共享，不需新增分阶段配额。确认公共循环有3轮反馈上限、无进展停止、A→B→A 循环检测、同一基底重复失败补丁停止、Draft／unsupported／范围不明和 Provider 失败停止，以及持久化共享预算兜底。历史账本不变；新完整真实运行不得套用旧 A 只剩2次调用的安排。

验证记录：`3374b975` 先提交问题记录及首批失败族，红结果10 failed／5 passed。公共补测发现属性路径转义缺口；另两项初始失败来自测试夹具洞口挖空整面墙及误用 ready-only API 重入完成会话，修正测试前提，未为此修改产品几何或恢复行为。之后补充空引用、重复身份、类型化值冲突、合法继承保全及 direct／effective 冲突的红测试（`da44a3db`、`3dcadd7d`、`efd1c97c`）。最终新增案例族27 passed，相关公共／身份／两策略／恢复回归135 passed；最后固定代码状态的 Changed-scope 复核126 passed（包括新增27项、已有语义 scope／原子应用／失败证据／预算和公共语义链路）。这些集合重叠，不累加为独立案例数或成功率。XML 分别为 `.tmp/semantic-correction-final-20260910.xml`、`.tmp/semantic-correction-public-regression-v2-20260910.xml`、`.tmp/semantic-correction-closeout-20260910.xml`；最初公共回归命令含不存在的测试文件、没有执行测试，其同名无 v2 XML 保留，不计通过。聚焦 compileall、Prompt registry 哈希及 diff 检查通过。

原 A 冻结候选的离线诊断重放保存在 `.tmp/semantic-correction-frozen-a-replay-20260910/`，未修改原运行。第一轮确定性构造78个显式操作，移除39个未请求 Type 和39条关联；其中附带的34项未请求属性随其所属 Type 删除。120个其它实体／关系的 hash 全保留，材料／属性请求由 reopened IFC 独立检查通过。此时才暴露旧候选原有的一项 `STAIR_RISE_DIRECTION_MISMATCH`：楼梯放置已相对二层，却再次加入3150毫米层标高，世界 Z 为6.3–9.45米而冻结请求为3.15–6.3米；不是语义清理移动了几何。

第二轮按既有父子坐标合同，从请求起点标高减去父层标高构造局部补丁，通过现有公共 `run_scoped_changeset_round` 接续 revision-01→revision-02，语义值及其余几何保持，最终 candidate gate、编译重读及语义检查通过。`two-round-replay-result.json` 记录该结果。第一轮为确定性策略重放，第二轮为 fake Provider；没有真实 Audit、完整终端验收或人工验收，因此该 IFC 仅为离线诊断，不进入 Proof，也不把原 A 的 budget_blocked 改成成功。

本轮代码闭环完成，允许结论为 **Bug fixed（离线）**。原始174份与续跑335份冻结文件、参考 IFC 及 B 诊断 IFC 的哈希均不变。B 已有身份和失败证据修复保持通过，其用户确认保留的净空缺陷不改。下一步真实 A/B 必须使用当前 Prompt／应用合同、覆盖完整 loop 的新预算及适用 Stage Admission；新操作权限改变了执行边界，旧准入与 RUN-HOLD 不能直接转为放行。仍未执行新的 Stage／Full Preflight、真实 Provider、人工验收、Proof 安装或 push；不声明模型收敛率或系统能力已经提高。

2026-09-10 后续全新 A/B 运行准备：用户已要求真实重新运行，新增 append-only `three-storey-clarification-branches-20260910/rerun-20260910/`。两分支均从新的 Brief 开始，不接续旧候选、Brief 或6次账本；新运行器离线 A/B 公共编译测试2 passed。针对操作权限合同刷新 Stage Admission：环节243、公共完整链路124、IFC重读120项，共487 passed，零失败/错误/跳过，compileall和diff检查通过；绑定619份文件。不是 Full Preflight，未改变产品行为或既有 Prompt。旧509份冻结文件哈希保持。首次真实启动在创建进程前被自动审批层拒绝，要求对本次具体载荷再次发送到 `api.deepseek.com` 明确确认；已向用户集中请求 A/B 两条完整 loop 的授权确认。此时实际 Provider 调用为0，没有新 IFC、视觉审查或 Proof；不能把此审批阻断记为 Provider 失败。新[运行报告](../../dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/rerun-20260910/REPORT.md)与载荷预览保存当前状态。

随后用户明确批准该载荷和目的地，外部审批阻断已解决。新 A 会话 `026823cac75af845` 从真实 Brief 开始完成 Brief/Generator/Audit 3次调用，共172,308 reported token、259.907秒 Provider活动时间，最终 `audit_blocked` / `scope_unresolved`，无 IFC；B 暂未启动。真正根因不是初步怀疑的 seed：Brief 的 `appearance.style_notes` 被整个复制到硬性请求投影，比较器逐键要求候选包含该说明，而 BIM JSON 2.1 顶层 appearance 仅允许 profile/seed 且禁止额外字段。相同冻结说明被 Brief/expected facts 重复投影，生成两条误报；编译前置门阻断后，`/appearance` 又无法定位局部实体/关系 scope。新候选75实体、0额外 Type/Style、4项动态门通过，但没有 IFC，因此不声明几何/材料/外观通过。只读原案复现证实去 seed 仍失败，内存中仅排除 style_notes 的机器比较后该项误报消失；跨主题/中英文说明/seed边界14例中4例合法说明误报，红结果保存在新包 diagnostics。下一步先作受支持外观字段的类型化投影，保留说明及来源供 Audit/报告使用，并覆盖真正值冲突和恢复保全；不直接扩大全文 ChangeSet 权限，不改旧 Schema/Prompt。真实失败与新 RUN-HOLD 保留，先离线修复和适用准入复核再继续 A/B。当前未作此产品修复、B调用、视觉审查、Proof安装或push。

2026-09-10 继续 goal 后完成外观投影小步修复：机器约束从当前 BIM JSON 2.1 的 appearance Schema 派生，仅识别 `style_notes` 为文字说明并保留原文和来源；其余未知字段、非字符串说明、非法主题/seed类型仍明确阻断，不能任意忽略附加要求。Brief 与 frozen expected facts 的结构化约束同时保留，恢复时任何一方改变主题或显式seed仍不能放行；相同外观不一致诊断去重。说明进入 `request-semantics.json` 的 `appearance_notes` 及中文语义报告，保持 Audit 可见，不当作逐字 IFC 属性或视觉合格证明。本轮未修改任何注册 Schema/Prompt，也未扩大 ChangeSet 文档编辑权限。

修改前扩展失败族并命中两种策略与 ready-session 完整公共链路：36 failed /14 passed，红 XML 为 `.tmp/appearance-projection-red-20260910.xml`。修复后31项投影/类型/冲突/恢复保全测试通过，相关公共链路/Type清理/身份/早期恢复/门禁回归108 passed；XML 为 `.tmp/appearance-projection-unit-green-20260910.xml` 与 `.tmp/appearance-projection-public-green-20260910.xml`。原 A 候选在 `.tmp/appearance-projection-original-a-20260910/` 只读复制后重检，候选字节未变，公共 candidate gates、编译重读和冻结290项IFC检查全部通过；108点楼梯净空采样最小约3米、零间隙0处。这仅为已揭示案例的离线诊断，未重写原失败运行，未补造真实Audit或注册Proof。后续应复核本阶段受影响路径并记录准入更新，再继续已授权A/B任务；前次A真实3次消费仍计入同一分支任务总预算，B本任务尚未消费，不能因重启把失败花费清零。

收尾补测发现新说明来源最初固定写成根目录 Brief 路径，虽文本正确，但在存在 canonical final Brief 时可能指向旧副本。新增 red 测试后改为记录实际选中文件的相对路径，最终投影族32 passed（`.tmp/appearance-projection-unit-final-20260910.xml`）。仅修正本次新增来源记录，未改变既有 final Brief 选择规则。

2026-09-10 下一次 A 真运行 `25a7dcb4706b8bf4`（`projection-retry-20260910/`）生产状态 compiled、Audit accepted，但独立重读290项中34项失败：19扇门窗部件统一着色，15扇窗的窗框也被设为透明。新3次调用加前次3次共计6次；B仍0次。原IFC、原始响应与生产状态保留，独立QA失败单独记录并新增 RUN-HOLD，不能登记为验收Proof。

定位顺序：① 检查器对映射样式误读；② 候选整件覆盖抹平模板分部件样式；③ 编译器默认模板分色错误。实际IFC直接Body样式均为explicit-user、窗透明度均0.7，原网格近景也显示透明框；候选19扇门窗和15面墙有实体appearance，而冻结Brief无任何实体appearance要求。证据支持②，编译器忠实执行已有整件覆盖合同；production检查只核对候选值，缺少覆盖授权门禁。不得通过改变旧appearance含义或放宽独立检查掩盖。

本次小步修复限Generation请求授权：默认配色仍由主题/模板确定；实体或Type的整件appearance须有冻结语义要求，候选自报来源不能授权。显式整件同色/透明请求仍照常表达。为使loop可真正撤销未经授权的可选字段，新增ChangeSet 1.1的受限remove_paths（初版只支持/appearance），只在新鲜诊断和精确语义修复计划共同授权时可用；保持1.0字节及行为，禁止null/空对象替代缺省、禁止删除几何/身份或整个构件。Generator和相关ChangeSet提示新增版本，旧版本保留。先冻结 `tests/agent/test_unrequested_appearance.py` 的四模板、明确覆盖、伪造来源、跨家族、原子越权和纯外观几何保全案例族；修复后补当前阶段相关公共链路与版本/事务准入，未获授权Full Preflight。A/B后续只作为同案例重试证据，不作盲测能力提升。

外观修复于 `6dd98ae4` 完成；旧失败包与预算继承测试于 `d01cf0ef` 保留。新 Generation 阶段准入为 `appearance-guard-rerun-20260910/admission.json`：331项seam、129项完整公共链路、120项IFC重读，共580 passed，0失败/错误/跳过，Full Preflight未运行。旧A的离线受限撤销重放删除34个未授权整件覆盖，冻结290项IFC检查通过；这是离线诊断，不是新真实运行。

随后A新运行 `4927c3df4028e515` 从原输入/已批准对话新建Brief与候选，真实5次调用（Brief、Generator、Audit、ChangeSet、Audit），本任务A累计11次、698521 token、962.282秒；B仍0次。生产compiled/Audit accepted，但独立IFC检查为288/290：门窗分色、玻璃、尺寸/位置通过，墙体/板屋面材料两组失败。108点楼梯间隙最小约3米、零间隙0处。近景确认不透明深框、独立玻璃与分色门扇恢复，仍不能靠外观证明物理材料。

新增阻断已记录于该包 RUN-HOLD：Brief在 `material_and_attribute_policy` 自由文字中正确保留砖和混凝土要求，却完全没有 `semantic_requirements`；投影把缺失字段折成空预期，授权19项材料清空，后续Audit也未阻止发布。原始候选其实含这些材料。机制问题是“未完成结构化提取”被当成“明确无请求”，而非本次RGB修复倒退或编译器丢字段。20项跨Wall/Beam/Door/Slab、不同自由文字位置的离线复现中12项仍错误授权删除；8项明确空清单/明确要求对照符合预期。脚本和结果见该包 semantic-authority-reproduction.py/json，尚未作此新缺陷的产品修复，不得将580项准入复用为继续transport的依据。

下一步严格限语义权威完整性：区分“明确无要求”“已结构化要求”“提取未完成/来源不合约”，未知状态不得授权删除；按新版本合同把缺少规范清单的Brief退回Agent校正，冻结几何/用户决策不变，不把这类Agent返工变成无谓用户澄清。不为本例增加 `material_and_attribute_policy` 别名，不从任意自由文字/颜色反推材料，也不通过放宽检查保留虚构材料。先冻结缺失、显式空、部分遗漏、合法语义、多构件、澄清恢复与原子保全失败族，验证后再继续同一A/B预算。当前按用户“遇问题停下”暂停真实调用并给出报告，B尚未执行、A/B尚未待验收Proof、没有push。

2026-09-10 继续实施上述边界：新增 Design Brief 2.2，明确要求 canonical semantic_requirements 和材料、属性、Type、构件外观、模板五类 semantic_review（specified / not_specified / unresolved，引用真实用户轮次）。缺失不是空值，声明与清单矛盾或 ready 仍 unresolved 均阻断。旧版本文件保持不变；2.1 缺失清单不再授予删除权限，显式空清单保持旧合法含义。新合同先显式用于 A/B，并覆盖普通/设计合理性审查两个 Prompt 入口；默认生成策略不变。

Brief 语义校正限定一次 Agent 调用，计入同一任务预算，只能修改 known_facts.semantic_requirements / semantic_review；初次响应、校正响应与反馈分别保留。尺寸、位置、楼层、稳定身份、已批准决定和 original_request 一律保持；拒绝校正越界、伪造用户轮次、截断、仍未完成提取以及借校正绕过真实用户歧义。类别检查与来源绑定可证明结构化合同成立，不能证明任意自然语言被完整理解；最终仍须由冻结原请求预期独立重读 IFC。当前仅进行离线实现与验证，不复用已被 RUN-HOLD 否定的准入，不启动真实调用。

2026-09-10 后续：上述修复提交 `2231c06b`；阶段与补充复验有效覆盖658项，冻结20项旧失败族通过。A新运行 `135976189dc358f9` 收到4次真实Provider响应（Brief、语义校正、Generation、Audit），一次ChangeSet因本地输入门控在发送前拒绝，终态audit_blocked，无IFC；B未调用。初次Brief保留19材料+19模板要求，但 appearance 分类声明与清单矛盾。校正新增34个含 frame_color 等文字部件字段的对象，过宽的Brief2.2 appearance Schema放行，后续Audit阻断。不是已解决的缺失材料授权再次复发，而是源头字段格式及部件/整件作用域仍缺约束。详细证据保留于 `semantic-authority-rerun-20260910/REPORT.md` 与RUN-HOLD。A预算累计16槽位（15个真实响应、1个发送前拒绝）、1265772已用或预留token、1277.047秒；不篡改失败预留。下一步只做通用外观字段格式校验及新版本Prompt约束，从实际BIM JSON Schema派生，保持主题与部件风格说明，不擅自改写为整件覆盖。先失败族和公共链路离线验证，随后才可在新目录继续已授权A/B任务。Full Preflight、push和人工Proof验收均未执行。

该次失败证据提交 `f0a03620`，198个冻结文件、14个报告链接核对通过，声明文本后缀扫描0发现。后续窄范围实现新增 Brief2.3 / Prompt2.7、2.8 / 语义校正Prompt1.1：构件外观约束从现有BIM JSON2.1的entity.appearance派生，拒绝空对象、非法字段和非数值RGB/透明度；不更改旧Schema/Prompt版本。语义投影同样拒绝无法编译的外观对象，不把它们冻结为候选修改权威。主题与匹配默认模板的部件风格留在profile/style_notes，合法整件数值覆盖仍支持；不新增任意部件配色能力，不把模糊风格擅自量化。已完成99项入口/校正/预算/恢复、116项公共生成/Audit/修复、69项原有外观回归，均通过；旧真实Brief的离线机制重放拒绝34个非法外观对象并保留19项材料要求。新调用仍须绑定此次修复及原阶段证据；上述结果不证明任意自然语言被完整理解，也不代替最终IFC独立验收。

- 2026-09-10 typed-appearance 真实 A `411166603facdde6`：Brief 外观已正确，但门模板记录附带 `material:{}`；源头投影仅检查 Mapping，错误冻结空要求。reopen 拒绝该要求，下游概括为编译失败导致错误修复方向，Audit02 本地输入超限异常退出；5次真实响应、1次本地拒绝，无终态 IFC，B未启动。A累计22槽位/1925775含预留token，准入已暂停。下一小步先建立材料源值格式失败族并复用实际材料Schema，保持合法要求与几何；不手动退回预算，不把本案例当盲测能力证据。
- 2026-09-10 该材料源值修复已完成离线验证：从实际 BIM JSON 2.1 materialAssignment 及其引用定义校验，非法值不冻结，合法单材料/分层及作用域保持。新失败族先27失败/14通过，修复后116项源头/外观/保全检查、87项公共生成/语义闭环检查通过（共203项）；实际失败 Brief 重放拒绝1项空材料并保留19项合法要求。未改变已注册 Prompt/Schema。typed-appearance 包219份文件已冻结，1326份旧机器证据与参考IFC哈希未变。**仍 pending：重读语义失败的具体原因需传递到修复路由；再生成后 Audit 的 ProviderOutputError 需正常收尾；此后重新准入，A额外预算需获批才可真实重跑。B未运行，A/B交付及人工审查均未完成。**
- 2026-09-10 后续两个通用流程缺口已完成离线修复：未完成编译/重读时，几何检查明确记为未执行，真正的上游失败继续阻断；Audit接收原始 input_issues/ifc_issues，Brief源值错误归属Brief，原生重读失败归属编译器，实际几何问题仍走原局部修复。仅当真实上游失败存在时才允许几何检查记为skipped。Audit首轮或修复后轮次抛出ProviderOutputError时，公共流程持久化provider_failed与路由、停止后续调用并返回无发布结果；失败轮次输入/响应单独保存，重复失败不覆盖旧尝试。本轮所有注册版本保持不变。错误归属失败族先12失败/2通过，Audit失败族先8失败；修复后62项聚焦、2项跳过保护、84项公共生成/修复/Audit回归通过（148项），仍为离线回归证据。准备failure-recovery-rerun新目录与阶段准入；A既有22槽位与1925775含预留token继续计费，不自动扩大200万上限，预算追加预览只是提案。B仍0次，本轮尚未恢复真实调用；A/B完整交付仍pending。
- 2026-09-10 上述流程修复提交 `d12ed931`，阶段准入绑定789项有效检查。用户随后明确批准A追加100万token，累计上限改为300万，32槽位/3600秒保持，22槽位与1925775已用或预留token全量保留；B仍按原200万上限。授权作用于新运行账本，原账本字节不改；不允许未批准、历史哈希不符、调用数/活动时间变更或未结算账本扩容。新增9项预算边界先失败，修复后连同原重试检查14项通过，另1项完整离线新Brief→生成→Audit→IFC检查通过。等待更新此局部准入绑定后，使用同一冻结输入恢复真实A/B；不把离线预算验证称为真实交付。
- 2026-09-10 A/B本轮真实重跑已完成，当前审查入口为 [failure-recovery-rerun报告](../../dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/REPORT.md)。A `6b4c8ce023e02a07` 从新Brief开始，3次真实响应，无修复轮次；独立原生IFC检查290/290，108点最小垂直净空约3米、零净空0点。A累计25槽位、2092740已用/失败预留token、1929.642秒，批准的300万上限内。B `8b3add702299a50f` 5次真实响应、324504 token、327.827秒；首候选两处楼板洞口局部Z多下移150毫米，被几何gate捕获，一轮受限ChangeSet仅修正两个origin.z，再次Audit通过。稳定ID逐项比较确认其余候选值未改变；B独立290/290，108点中仍3个零净空点，Audit为retained_known_issue。两者各补充6项Type检查通过，仅4个必需门Style，无额外Type材料/属性；共8张原生视图已由助手查看。有效准入799项，Full Preflight未运行。1545份历史冻结证据、原参考IFC、833项运行时准入绑定及39个报告链接已核实。**A/B均为待人工审查，未验收、未登记Proof、未push。** 这是同案例重试与一次实际loop收敛证据，不是盲测或普遍成功率提升。此次调用已结束；原准入作为运行时快照保留，后续真实调用须重新确认适用绑定，不能把本条收尾记录当新调用授权。

### 2026-09-10：A/B人工验收与下一组稳定性观察

用户确认generated-A.ifc / generated-B.ifc内容无误，已按现有package 0.1格式收纳到 `dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910`，人工状态accepted。源运行及报告字节冻结，用户重命名在manifest中映射；新human-review记录当前验收，不回写旧pending。两案完整Generation Final Acceptance确定性重验通过（无Provider），人读validator通过2案/27份绑定/2次IFC重开；根索引增加2案，共50个直接展示案例。B accepted只表示忠实保留并披露已知问题，不等于工程合理或规范合规。

当前合理性边界：Brief可提出缺失/歧义/冲突澄清；几何gate检查已实现的构件包围盒、标高、开口绑定/尺寸、踏步和楼梯-墙相交等合同；Audit结合请求、候选及检查反馈给出有限判断。`design_review.py`由调用者提供并绑定已知concern及用户原话，retain必须保持retained_known_issue，revise只允许not_verified/unresolved，不能把用户确认写成已解决。A/B的楼梯零净空先由外部独立测量发现并显式注入，不是当前通用pipeline自主发现能力的证明；measure_clearance也仍是独立案例审查工具。尚无全面净空、疏散、结构或建筑规范审查器。

下一组限定为三层C型教学活动楼（向东敞开，13.2×16.8米外包络，6教学室、3交通空间，21窗、7门），沿用现有构件/模板/材料合同和legacy_full，不扩展新产品能力。`c-shaped-teaching-building-20260910/request.txt`为助手编写的人类工程语言测试请求；运行前冻结独立预期和评价器，包含C形真实缺口/体积，不能只检查矩形包围盒。本轮不预置已知concern或复用A/B参考IFC，分开记录模型自主提出的问题、确定性规则检出和事后独立检出；信息不足或冲突时暂停等真实用户回答，不脚本化代答。它是新场景前瞻可行性/稳定性观察，单次结果不支持成功率估计或系统能力提升。新Provider载荷仍需具体授权，旧A/B授权不能直接挪用。

2026-09-10 用户已批准本次C型教学楼独立载荷、api.deepseek.com/deepseek-v4-flash及32次/200万token/3600秒共用预算。运行前复用未变生产路径的799项阶段证据，新增11项凹形几何检查、精确新runner的完整fake公共链路及485项独立IFC检查、5类评价器负对照；Full Preflight未运行。真实run `41edcb4296d1b826` 首次Design Brief返回finish_reason=length，预算记录1次失败调用、83996 token、282.296秒，未进入Generation/Audit，无最终IFC。发现初始公共 `run_design_brief_stage` 未在Provider抛异常时保存异常内的原始响应，进程结束后该响应缺失；只能确认截断，不能推断Prompt/Schema或模型推理的深层原因。CLI Brief、Audit、ChangeSet既有留痕不能证明这个入口已覆盖。三类异常与空内容对照的离线复现支持该缺口，尚未修复。按约暂停真实调用，原准入失效但快照保留；详见 [C型报告](../../dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910/REPORT.md)。下一小步只补公共Brief异常留痕、attempt保全及公共调用方的失败/恢复验证，再更新局部准入；任何重试继承原预算，不补造缺失响应、不用offline IFC代替交付。C未验收/未入Proof，A/B accepted保持。

2026-09-10 用户随后明确要求直接尝试一个阶段定位截断。公共Brief异常留痕与attempt目录保全已修复（75f70f5d），失败族先14失败/3通过；相关公共入口/澄清/语义/生成路径220项有效检查通过，旧成功夹具缺少显式空语义清单的问题经修改前代码复核后仅修正夹具。新单响应诊断runner离线验证ready/截断、账本继承及Prompt不变，随后只增加一次真实Brief响应：返回ready，结构校验0问题，response_id=d15e96ef-6636-476f-bfd0-fa291afb2ebb；输入18460、输出45174（其中reasoning33759）、总63634 token，165.359秒。相同渲染Prompt，仍用65536单次上限；旧总83996减新输入18460恰为65536，强支持旧失败命中单次输出额度，但旧原始响应缺失，不能确认截断位置或更深原因。本次没复现截断，不代表稳定性问题消失。新C累计2次调用/147630 token/447.655秒，后续必须继承 `c-shaped-brief-debug-20260910/live-attempt/generation-budget.json`，旧1次账本不可继续当最新值。

同时发现普通Prompt v2.7最终输出检查仍写2.0而正文/Schema为2.3；审查v2.8已正确。新增普通v2.9只纠正这一句，保留全部旧版本及Schema；普通/审查对照先1失败/1通过，修正后158项相关验证通过。此修正在真实成功之后，v2.9仅有离线验证，不能归因为真实成功的原因。详见 [单阶段报告](../../dataset/processed/ifc-presentation-validation/c-shaped-brief-debug-20260910/REPORT.md)。本轮未继续Generation/Audit/IFC，未Full Preflight或push；C仍非待验收Proof，A/B accepted不变。下一步可在适用准入更新后将合法Brief接回公共Generation，独立冻结预期保持，不为C型增加特判或盲目扩大输出额度。

### 2026-09-10：单次额度配对实验与获准运行目录退役

用户要求先推送，再实验并给出节省token建议。既有提交已普通推送到codex/workflow-dataset-links；双层人工review包原来仅存在于本地，核对533份源文件副本后另以9dfd91b4保全并推送，保持人工accepted、机器blocked。用户随后明确批准清单12目录；等待实验结束后，核验9,378份源文件及831份规范Proof副本，删除约112.18 MiB重复runtime与本对话合成测试目录。A/B运行脚本、原输入、早期失败、全部Proof和C型证据均保留；A/B与双层人读检查/3次IFC重开及保留脚本10项回归通过。旧admission/FILES保持历史快照，原runtime路径已退役，后续准入必须重新绑定规范Proof，不能直接重用旧快照。详见[清理记录](../reports/run-cleanup-review-20260910/REPORT.md)。

实验仅改变单次输出额度，使用当前普通Prompt v2.9与Brief2.3，按预先冻结的96K→64K顺序各执行一次真实Brief，不进入Generation/Audit。38项实验runner与受影响公共路径离线检查通过，沿用同阶段证据，没有Full Preflight。两组请求逐字段比较仅max_tokens不同；均finish_reason=stop、Schema/严格合同校验通过，但均needs_clarification，不能写成ready。96K输出68,621（推理54,461），64K输出47,369（推理36,911）；新增总152,910token。C任务最新累计4次/300,540token/886.717秒，原32次/200万token/3600秒不变，最新账本位于c-shaped-brief-budget-experiment-20260910/live/generation-budget.json。旧失败和账本不改写。

结论与下一步：96K这次使用超过旧上限的空间，但64K这次也成功；单次配对受随机性、缓存和顺序影响，不证明提高额度改善稳定性或节省成本。先建议新版本输入去重、重复规则/相关上下文精简，再比较实际用量与语义保全；若仍长推理，再独立评估阶段设置及按全局布局/构件语义拆分、稳定ID合并和共享预算。此轮没有实施这些生产改动。两组均按现有Prompt的STAIR_OPENING_SPACE_COLLISION规则对交通空间含楼梯井提出澄清；模型声称“确定性检查”不是本实验真实执行独立检查的证据。需复核这条规则的适用性和是否属于多余澄清，再由用户确认确有歧义的设计选择，不能代答、默认建筑不合理或直接放行。详见[额度实验报告](../../dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910/REPORT.md)。C仍无新IFC/Proof，不升级为系统能力提升。

## 19. Token 效率与质量保全：渐进实施计划（2026-09-11）

用户确认：将 input/output token 节约作为后续研究方向，按照本节逐小步实施；每一步单独报告修改、前后对比、有效原因及质量证据，再进入下一步。本节承接额度实验，不另建重复计划。当前基线为 a23301eb；本节不是新 Provider 载荷授权或阶段发布验收。

### 19.1 目标、现状与不可牺牲的质量

目标是在忠实建模和成功交付约束下减少**整次 loop 的实际输入与输出**，包括失败、澄清、语义校正、Audit 和 ChangeSet。分别报告逻辑输入、输出（含 Provider 计入的 reasoning）、缓存命中、费用和时间；缓存折扣不冒充上下文 token 减少，降低单次上限不冒充节省，失败花费不从分母移除。

现有实现已包含 Brief 相关上下文选择、staged 按楼层/跨层任务分包、ChangeSet 范围投影、Repair 目标上下文限额和无进展/重复候选/预算退出。增量工作应复用这些路径；目前多个包仍携带完整 Brief/预期，Audit 的 gate/revision 中也重复包含同一检查内容。先削减可证明重复的信息，再讨论改变模型任务分工。

计量以 **prompt-rendered.md / 实际 request 的 messages** 为权威。prompt-render-input.json 是本地渲染参数超集；例如 audit.v2/v3 未引用顶层 GATE_SUMMARY，该字段虽然落盘但未发送。不得把删除它计为节省；重复内容须在真正发送的 DETERMINISTIC_GATES / REVISION_EVIDENCE 内确认。

任何已知语义、身份、几何、材料/属性/Type、有效外观、保全或错误发布回归均阻止晋升默认。继续独立重读最终 IFC，对照冻结用户预期，不能只信 represented 标签或 Audit 自报。用户未指定的设计自由度与真实冲突按已批准澄清合同处理；不得通过省略问题、猜参数或接受较差 IFC 换 token。保留 IFC2X3、legacy_full 默认/staged 显式、Repair 源与几何不变等既有边界。

### 19.2 小步实施次序

| 步骤 | 只改变什么 | 验证与停点 | 初始状态 |
| --- | --- | --- | --- |
| T0 基线 | 从冻结真实请求重建实际发送文本，记录源文件哈希、逐阶段用量和失败；冻结本步测试族 | 区分实际 token 与字符启发式估计；A/B/C 为已见开发材料，不能作为未见能力集 | T1 的同源基线已冻结；正式研究数据集待建 |
| T1 Audit 去重 | 相同机器证据只传一份，其他位置作同一消息内引用；确定性还原校验；新增普通/设计审查 Prompt 版本，公共 Audit API 显式试验开关 | 完整候选、请求、Brief、失败、版本绑定、设计决定和证据路径不删；若含引用冲突或完整新 Prompt 不更短则回退原格式；先离线，再单独审查真实对照准入 | 离线实施/对照完成，默认仍 full；真实质量/费用对照待准入与具体授权 |
| T2 Brief 去重 | 请求与对话重复、规则重复、实际无关示例按明确来源压缩；每次只改一项 | 保留所有用户轮次与修订优先级，来源引用可还原；不同时改澄清规则/输出上限/reasoning | 待实施 |
| T3 阶段参数实验 | 分别比较 reasoning 设置、稳定前缀缓存；一次只改一个变量 | 原始响应/实际用量/首轮与 loop 终态完整保留；缓存收益与逻辑 token 分开；输出下降不得伴随遗漏或额外修复 | 待讨论、适用授权与准入 |
| T4 澄清复核 | 复核交通空间含楼梯井等规则的适用条件；区分明确要求、缺信息、真实冲突与 gate 争议 | 先冻结跨场景正反边界；明确条件不反复问，真实歧义仍停等用户；复核后才继续 C 的设计选择 | 待实施，在大规模分包重构前完成 |
| T5 依赖完整的分包输入 | 基于现有 staged/ChangeSet，传全局约束、当前范围及宿主/开口/跨层/共享 Type 的必要依赖，按需获取缺失证据 | 缺依赖不得猜测；确定性检查覆盖依赖闭包与范围外保全，必要时回退完整输入；两策略共用路径/恢复一致 | 研究候选，先单模块试验 |
| T6 紧凑输出 | 在新版本中表达已明确的重复楼层/构件参数及例外，由代码展开完整 BIM JSON、稳定身份与关系 | 展开后用相同编译与独立 IFC 检查；不隐式共享 IFC Type，不改用户尺寸位置/语义；比较输出减少是否转移成更多输入或修复 | 研究候选，先冻结合同再实施 |
| T7 增量 Audit | 在当前全局检查有效的前提下，对受影响语义与依赖增量复核 | 旧 Audit 不能证明新 revision；跨组/跨层作用和未请求变化仍全局检查；不与 T1 混为一次变更 | 后置，收益不足则不实施 |

每步只维护本计划状态及必要的测试/实验报告，不为流程另建重复规划文件。实验开关默认不启用，待相应证据成立再单独决定默认切换。新增版本并注册哈希；旧 Prompt、Schema、已验收 Proof 和所有真实失败不重写。

### 19.3 T1 修改前假设及冻结失败族

假设 H1：同一大对象在 Audit 的多个证据分支反复出现，是修复后输入膨胀的一项来源，按完整 JSON 值去重可以减少实际发送文本。H2：仅相等标签/ID 不够；不同 revision、失败状态或数值必须保留为不同值。H3：引用说明和表项也有成本，小输入可能变长，故应比较**完整渲染文本**并自动回退。H4：确定性无损只证明信息保全，引用间接性仍可能降低模型检索准确度或增加 reasoning，须用真实对照另行验证。

修改前测试族冻结在 tests/agent/test_audit_context.py：普通与设计审查、不同构件/语言/楼层、相同与近似但不相同的检查、失败与旧通过共存、空/null/零/布尔/列表顺序、已有引用标记、小输入回退、畸形/悬空/循环引用、用户请求/完整候选不变、默认版本不变、损坏还原阻止发送、公共 Audit 硬门拒绝及失败/重复尝试留痕。公共 fixture 使用 fake Provider，绝不作为真实 LLM 证据。冻结 A 首次 Audit、B 首次及修复后 Audit 用于实际消息离线对照，比较前验证输入能够逐字重建旧 Prompt。

T1 范围仅公共 Audit 输入表示，保留原始证据收集器和验证器；本轮不引入文件访问工具、增量 Audit、生成任务拆分、自动摘要或输出合同变化。公开 API 显式选择即可试验；完整 loop 默认入口继续原格式，其设置持久化和 CLI 接入留给通过单阶段试验后的接入步骤。

### 19.4 每步报告、实验设计与研究判据

每步固定报告：① 做了什么；② 同源前后输入字节/字符启发式 token 估计，若真实调用则加实际 input/output/reasoning/cache/时间及完整 loop 花费；③ 哪部分重复/计算被消除，是否把成本转移到别处；④ 测试、独立 IFC 检查、人工视觉及真实样本的实际证据级别，未运行项与是否进入下一步。没有真实输出就填未测，不以假响应 usage 代替。现有 ASCII/CJK 估算在本步三份真实请求中均低估 Provider token，不是严格上界，不用于宣称真实收益或静默放宽预算；模型 tokenizer/预算估算的校准应作为后续独立小步，不能和压缩算法效果混算。

正式质量/效率比较先冻结请求组、Prompt/模型/参数、评价器、失败分母及预算策略；按场景/请求族隔离开发集与未见集。顺序交错并重复采样，报告配对分布、失败与置信区间，不凭单次 A/B 宣称稳定。性能优化会改变回答、澄清及后续修复，应同时测阶段和端到端；“平均成功样本 token”须与全部失败花费及质量一起报告。质量非劣效界限、样本量及功效须在正式实验前确定；有限测试不能证明绝对不下降，任何已知安全/保全回归为零容忍。

建议研究主指标为“每个合格交付的总 token 成本”：固定请求集合中**所有成功和失败尝试的 input+output 总和 / 合格交付数**，同时公开分子、分母、失败率与质量分项；零交付记为不可交付，不给出有限成本。合格由冻结请求、适用发布门禁与独立 IFC 评价器判断，不能由模型自报，也不把忠实保留已知问题写成全面工程合规。只有质量/成功率约束成立才比较节省；单阶段压缩率是诊断指标，不能替代此主指标。

研究方向暂定为**依赖与证据完整性约束下的 BIM 上下文编译，以及可校验的参数化输出**：输入裁剪由任务依赖决定，输出由版本化表示展开，执行器检查完整性，再以真实 loop 成本衡量。T1 是基础工程和可行性试验，本身不声称论文创新。后续至少比较完整上下文、普通去重、按相关性选择、依赖完整投影、参数化输出及其消融；分别量化每种方法收益，评估新增调用和展开错误，不能把调低 reasoning 或缓存价格混入方法贡献。新颖性及顶刊适配还需针对这些方法做相关工作检索。

参考方法而非本项目实测结论：[DeepSeek thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/) 用于阶段参数可行性，[DeepSeek context cache](https://api-docs.deepseek.com/guides/kv_cache/) 用于区分前缀缓存与 token 减量，[Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) 与 [code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) 支持按需上下文与代码侧处理的工程思路。外部示例节省比例不可迁移为 text2IFC 收益；具体 Provider 能力在实验前按当前官方文档核对。

真实调用沿用 agent-capability-evaluation 的阶段准入/变更复验约束。C 的旧授权和累计账本不自动扩展为新的 Audit 实验载荷；不得为此次离线优化擅自运行 Full Preflight、真实 Provider 或改动 Proof 验收状态。

### 19.5 T1 本次结果（2026-09-11）

计划和28项红测试先提交为6217c3dc；红结果表示待实现模块/API尚不存在，不是28个旧生产缺陷。随后增加 audit_context 的完整 JSON 值去重与严格还原、audit.v4/v5（输出仍2.0/3.0）、公共 run_audit_report_stage 的 audit_context_mode="deduplicated" 显式入口；70份旧 Prompt 内容及其 registry 条目保持不变。请求、Brief、完整候选、审查决定、原始证据文件和门禁验证器不变。失败尝试同时保留原参数、实际发送参数、完整 Prompt 与压缩记录，不复用旧响应。

三份 A/B 冻结输入均逐字重建实际 request.messages[0].content。A首次132858→132858字节、B首次128098→128098字节：无可去除的大重复对象，自动回退。B修复后255470→195088字节，减少60382字节（23.64%）；字符估计65503→50263（23.27%），29份共享值，全部实际发送的结构和值还原一致。比例已包含引用说明/表项成本。旧 B 本轮真实输入91765、输出5464 token 属于原格式；新格式未调用 Provider，不能据此推算其实际 token 或宣称输出与质量不降。

本步聚焦28 passed后，相关默认路径/两策略/CLI/审查/失败恢复回归130 passed；追加公共编译重读、retain/revise禁止resolved及计量负对照后，本步36 passed。范围重叠，不累加为独立样本或成功率；fake Provider 输出不证明模型阅读引用后的质量。新增编译重读正例输出IFC2X3、几何检查通过、原候选字节保持。未运行真实 Provider、Stage/Full Preflight、未见能力评测或人工视觉验收；没有创建/重新验收Proof。

完整结果与复现入口见 [T1 报告](../validation/token-efficiency/20260911-audit-dedup/REPORT.md)。T1 的离线目标已完成，但真实质量/输出节约仍 pending；报告本小步后再推进，默认切换须先完成本步独立的真实对照。后续 Brief 去重、阶段参数、澄清复核与分包/参数化输出保持19.2顺序及各自单变量边界。
