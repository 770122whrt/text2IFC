# IFC-SemRepair Literature：文献矩阵与重点近邻

> 文献实质核查：2026-09-21｜版本：v0.4｜维护说明更新：2026-09-23。
> 用途：记录近邻论文的任务、方法、验证与证据边界；本轮重点核对 RAMC 和 Self-Verification，不扩大实验计划。
> 本矩阵独立于 Generation 选题矩阵；同一论文可因共享机制被交叉引用，但不重复计算为独立证据。

当前方法与 Demo 见 [展示版 Method](../../architecture/ifc-repair-pipeline-status-and-roadmap.md)，贡献措辞和实验登记见 [Claim 与实验](claims-and-experiments.md)。文件名中的日期保留为首次建立标记，后续更新版本与修改记录，不另立平行“最新矩阵”。

本对话持续在本文件维护 Repair 文献调研，记录贡献／观点、实验设置、来源阅读程度及与本研究的关系；技术与 Claims 分别回写另两份主文档。2026-09-23 仅确认维护分工与原技术稿来源，未新增文献条目、重新核查论文或改变下表结论。

### 1. 研究边界与读法

**目标任务**： 对可读取的已有 IFC2X3，根据用户请求进行受支持的属性修正或构件补全。不是任意损坏文件恢复、无条件推断被删除内容、自动结构验算或从零生成整栋建筑。

需要区分四种常被混称为 repair 的任务：已知问题的修正；已有模型的普通编辑；从合规问题搜索替代设计；只输出诊断与建议。只有明确存在当前状态与期望状态的不一致时，才适合把一个普通属性更新叫“修复”。

证据标签表示本轮读取程度，不评价论文质量：

- **正文核查**：读到与本条主张相关的连续方法/实验/限制段落；不表示复现或逐页审计全部附录。
- **局部/摘要**：只取得指定片段或官方摘要；未知内容不填“没有”。
- **项目/工具**：作者项目页或官方文档，不伪装成论文全文。
- **用户全文**：用户上传 PDF，正文与相关图示已核对。

当前 **22 条记录：18 条论文记录、1 个后续项目、3 项工具基础**。本轮新增 T3 是 IfcOpenShell 官方事务 API，不是新增论文。不以重复阅读增加条目数量，也不与旧 134 条综述直接相加。

v0.3 曾补核 IFC-Agent、BIM-Edit v3、BIBIMBAP、Query2Property 等。v0.4 重点核查 RAMC 的 §III–IV、Self-Verification 的两页方法和图示，并补查 IFC-Agent §6.3、Wu 作者摘要和 IfcOpenShell 事务文档。其余条目继承各版阅读记录，不表示本轮重新读完全部文献。表内“本轮／本版”若来自历史条目，读取时间以本段及原始来源记录为准。

### 2. 总体判定

| 候选主张 | 关键先例 | 当前可以保留 | 当前不能宣称 |
|---|---|---|---|
| 自然语言 → IFC 标准属性 | SGSS、Query2Property | 面向实际写入的语义落地能力 | 新检索算法；首次属性语义对齐 |
| 当前实例 + Schema 联合定位 | IFC-Agent、MCP4IFC、CADIR | IFC occurrence/Type/关系语义的具体实现 | 只要有 GUID 与 Pset 就是新的 grounding 方法 |
| 显式 Model-Bound ChangeSet | RAMC、CADIR、γμS | 领域化变更合同与操作实现 | 首次把编辑变成独立中间表示 |
| 同一规范驱动写入和检查 | ATLAS、Self-Verification | 减少写入/检查定义漂移 | 完整自然语言正确性保证；新的 round-trip 理论 |
| 执行后检查语义与保持 | CADIR、TraceCAD、BIM 编辑评测 | IFC 特定字段、来源、关系与非目标检查 | 首次以实际产物验证修复 |
| 自动改正既有 BIM | Design Healing、Wu 2026、RL conflict resolution | 请求驱动、受支持语义范围的系统展示 | 首个 BIM/IFC 自动修复系统 |

#### 2.1 单项机制重合与完整修复系统重合，必须分开

上表用于限制“首次检索／首次变更 IR／首次验证循环”等宽泛说法，不据此推出本项目的全部系统贡献已被占领。RAMC 是跨领域变更表示和模型补全近邻；Self-Verification 是实际 IFC 验证与迭代近邻。两篇拼在一起，不等于已有一套与本项目输入、事务粒度、语义追溯和产物检查均相同的系统。

| 关键问题 | RAMC 原文支持 | Self-Verification 原文支持 | 对整体 Claim 的影响 |
|---|---|---|---|
| 是否以原生已有 IFC 修复为主要任务 | 软件模型差异及历史驱动的补全，不是 IFC2X3 修复服务 | 生成并修改真实 IFC，但展示主任务是 Text-to-BIM 迭代生成 | 两篇都不能直接等同本项目完整任务；Self-Verification 不能被说成不修改 IFC |
| 是否强调局部或上下文效率 | §IV.B 已通过变更图与模型切片减少上下文 | 所读短文没有给同条件的 token／耗时比较 | 局部表示的效率动机有先例；本项目速度优势仍需测量 |
| 是否明确请求级原子回滚 | 所读正文未建立这种 IFC 事务合同 | 两页论文未定义或验证同一用户请求全操作的原子回滚合同 | 记“未建立该项证据”，不填“确定不支持” |
| 是否有追溯信息 | 明确依赖历史变更，不能称没有历史 | 有规格、检查反馈和迭代过程 | 要比较事实来源→操作→实际实体→检查证据的关联范围，而不是只比较有没有日志 |
| 能否否定完整贡献 | 可否定显式变更表示本身首次 | 可否定验证驱动 IFC 修改本身首次 | 不能仅由单项先例否定面向当前 IFC 的事务化、可追溯语义修复设计 |

完整组合仍需与 IFC-Agent、MCP4IFC／IFC-Copilot、Wu 等直接近邻核对；本文不把未取得全文的部分写成对方没有。具体保留主张及三项关联贡献统一在 Claim 主文档维护。

### 3. 直接 IFC/BIM 编辑、修复与语义修补

| ID / 工作 / 证据 | 输入、机制与输出 | 评价与边界 | 对候选 Claim 的攻击与剩余区别 |
|---|---|---|---|
| **R1 IFC-Agent**；AIC 186 (2026), 106888；正文核查 | 自然语言和已有 IFC；schema-guided 工具遍历、记忆及混合执行；支持字段修改与导出 | §6.3 明确缺少修改后模型一致性验证；不把查询成绩当修复成功率 | 直接覆盖 schema+实际模型交互。我们可强调已实现的修改后核验，但不是整个领域验证首创 |
| **R2 MCP4IFC**；arXiv 2511.05533v1；正文核查 | 自然语言调用 IFC 查询/创建/修改工具；另有 RAG 与动态 IfcOpenShell 代码 | 编辑、生成、QA 是不同任务，不合并分母；工具运行成功不自动等于所有用户要求满足 | “不直接写 STEP、调用确定性工具、编辑原生 IFC”都不是新点。比较需使用有合理工具与上下文的强 Agent |
| **R3 IFC-Copilot**；MCP4IFC 后续项目；项目 | 作者页介绍工具化 IFC 生成/修改、代码执行与多轮工作流 | 本轮项目页可读，但 Paper 链接未取得正文；页面自报性能不当全文实验 | 保留为必须补核的直接系统近邻；与 MCP4IFC 不是两次独立复制，未知功能不填叉 |
| **R4 Automated building component alterations driven by LLM-formalized human strategies to achieve code compliance**；Wu 等，AIC 190 (2026), 107148；摘要 | ACC 问题+设计人员策略；LLM 形式化构件操作，基于拓扑关联实例化修改，重新评价方案 | 本轮作者机构摘要可读；期刊卷期标为 2026-10，不能据此猜首发日；完整执行与验证合同待核 | 覆盖“人类策略→结构化操作→实际 BIM 修改”。不能仅凭输入是自然语言就把我们与它分开 |
| **R5 Design Healing framework for automated code compliance**；Wu、Nousias、Borrmann，AIC 171 (2025), 106004；摘要/局部 | 从设计与 ACC 结果定位相关构件，以拓扑传播、敏感性分析和设计空间探索产生相近的合规方案 | 以合规改正与改动距离为核心；本轮不重算实验结果，不宣称任意原生 IFC 写回 | “修已有模型而非从零生成”“局部修正且维持设计”已有明确先例；区别在请求级语义修复目标 |
| **R6 Intelligent Identification and Repair of Design Defects in BIM via Domain-Specific Large Language Models**；Lin 等；书目待全文 | 核实 SSRN 5894611 同题记录；2025-12-13 已发布记录，另有 arXiv 2608.28629 线索 | 本轮未取得可连续审读的原始方法/实验；不沿用上轮代理/聚合页的 85%/94% 数字，也不据此断言完整执行链缺失 | 保留高相关待查项；“只生成修复建议而不写 IFC”目前不能升级为本轮全文确认的差异 |
| **R7 Shape encoding for semantic healing of design models and knowledge transfer to scan-to-BIM**；Collins 等，2022；局部正文 | 几何表示与学习用于语义分类/错误识别及 scan-to-BIM 知识迁移 | 本轮核对出版商的语义 healing 定位与方法背景；未完成逐项原生 IFC 修补回写审查 | “BIM semantic healing”不是 LLM 出现后才有；但分类研究也不等同语言驱动变更系统 |
| **R8 Towards Automated BIM Conflict Resolution Using Reinforcement Learning**；Jiang 等，EG-ICE 2025；正文核查 | PPO 在 IFC 环境调整构件位置/方向，Solibri 检查反馈驱动下一次调整 | 几何冲突目标；论文限制指出不同场景分别训练，不能直接当跨场景通用能力 | 修改—重检闭环已有；与我们的标准属性/实例语义修复不同，不应当作同一任务直接比较总分 |

### 4. 前作、属性检索与生成内修复

| ID / 工作 / 证据 | 输入、机制与输出 | 评价与边界 | 对候选 Claim 的攻击与剩余区别 |
|---|---|---|---|
| **G1 SGSS / LLM-Powered Structurer**；WWW Companion 2026，212–215；用户全文 | Semantic Split → Schema Alignment（embedding Top-K + LLM）→ Memory Bank → IDS；ArcPath 有 Transform、Chat、Manual Editor | 两个示例要求构成 Case Study；无定量对照/消融表；自动 Validate 明确在 roadmap | 语义拆分、检索、重排和中间缓存是前作思想，不能再次独立主张；我们新增目标是已有模型的变更实现 |
| **G2 Query2Property**；Lamsal、Zlatanova，ISPRS Annals XI-4-2026，323–330；正文核查 | 从官方 IFC4.3 定义构建属性语义记录，embedding/FAISS 检索标准属性；实验阶段未使用 aliases | 55 查询的 Top-1/Top-3 是检索指标，不证明目标实例、值、作用域或实际写入正确 | 连“无手工 alias 的 IFC 属性检索”也不是独有。我们只能比较从检索到实际修改的额外能力 |
| **G3 A Self-Verification Framework Toward Reliable Text-to-BIM Generation**；EC³ 2026；v0.4 两页正文及图 1–2 复核 | Specifier 在首轮生成 IDS／非 IDS 规格；Modifier 创建并修改 IFC；IfcTester 检查 IDS，Verifier 生成并执行补充代码，随后反馈迭代 | 住宅生成示例运行五轮；部分空间—楼层问题未解决；初始规格遗漏是作者明确限制。不是只让 LLM 口头自评 | 规格—修改—验证闭环已有，不能以“只生成不修改”排除。IDS／非 IDS 是检查类型，与 L0／L1／L2 不是同一分层轴，不能数层数论证创新 |
| **G4 Text2BIM**；arXiv 2408.08054v2；正文核查 | 多代理和高层 Vectorworks API；执行错误与导出 IFC 的 Solibri 问题反馈修订 | 本条固定作者 v2；不将正式期刊版或早期版的样本相加；商业 authoring 工具条件不同 | 多代理与审核反馈不是新点；已有 IFC 请求级编辑仍需单列，不能因它主要生成就排除其修复机制 |

### 5. 直接编辑评测：保全必须按实际检查范围判断

| ID / 工作 / 证据 | 评价对象 | 已确认边界 | 对我们评测的意义 |
|---|---|---|---|
| **E1 BIM-Edit**；arXiv 2606.20146v3；本版正文核查 §3.2、附录 D–E | 输入、人工参考结果和预测结果构成评测；比较参考变化与预测变化，避免未变化的大量构件主导分数 | 语义指标检查类别与任务相关属性；附录排除 Tag、Description、LongName。更新允许删除重建后评分；拓扑比较对齐后的节点/关系变化，处罚多余拓扑修改 | 三方模型比较、变化区域评价和关系核对都已有。我们应明确增加哪些 IFC 属性身份、来源及保持检查；不能称对方只有几何评价，也不能把我们的历史验收与其均分横比 |
| **E2 BIBIMBAP**；EC³ 2026；正文核查 | 100 个原子 CRUD/查询任务；基于源/结果 IFC 的确定性测试 | Limitations 明确不测 Update 的非几何属性保持；删除重建丢属性也可能计对。主分数是逐题适用检查通过比例的均值 | 新实验应补字段来源、保留语义和多轮澄清；不能称它没有关系/非目标检查，也不能把其 50.22 当完整任务成功率 |

### 6. CAD / MDE：攻击“新编辑 IR”和“新闭环”的关键机制先例

| ID / 工作 / 证据 | 可直接核实的机制 | 与 IFC 任务的区别 | 对我们的攻击 |
|---|---|---|---|
| **M1 RAMC — Software Model Evolution with Large Language Models**；ICSE 2025；v0.4 核查 §III–IV 与图 2–3 | 从模型版本差异得到 Simple Change Graph，编码增删保留和属性变化；检索历史变更作为样例，LLM 补全后解析为模型补全建议；形式化定义说明变更如何应用于模型 | 输入重点是当前编辑差异与历史模型变化，不是自然语言 IFC 修复；应区分模型变换的形式定义与论文实现的补全建议 | 不能将独立变更对象、局部表示或将图换成 JSON 作为首创。它是变更表示／模型补全的机制近邻，不据此断言已经实现本项目全部 IFC 修复能力 |
| **M2 CADIR — A Cross-Backend Editable Intermediate Representation for Agentic CAD Generation**；arXiv 2608.00891v1；正文核查 | 可编辑构造 IR、参数/依赖/实体选择与跨后端回放；编辑评价包含唯一定位、实际修改及结果状态 | 依赖 CAD 构造历史/后端，不是任意导入 IFC；字段与关系语义不同 | “Model-Bound IR + 修改后效果检查”已被同时实现，不能拆成我们的两个首创点 |
| **M3 TraceCAD — Trace-Guided Repair for Agentic CAD Generation**；arXiv 2608.03062v1；正文核查 | 连接需求、执行步骤、失败及修补结果；局部候选据执行、语义、保全和局部性决定是否提升为接受结果 | 面向生成程序；保全主要借视觉/shape-delta，不是 IFC 逐字段等价证明 | “保留意图来源并核验补丁实际效果”不是空白；可比较具体 IFC 语义核验而非泛称新闭环 |
| **M4 ATLAS — A Layered Constraint-Guided Framework for Structured Artifact Generation in LLM-Assisted MDE**；arXiv 2510.25890v3；正文核查 | ICM 统一元模型、约束、来源与依赖；编译生成期约束及生成后语义/逻辑检查，再引导修订 | AUTOSAR 等结构化工件，主要生成；约束保证限于实际编码覆盖 | 同一规范化语义模型驱动生成和验证已有；共享合同本身不是“语义 round-trip”新方法 |
| **M5 Well-Formed Executable Suggestions for Continuous Model-Driven Engineering**；MODELS 2026；官方摘要 | γμS 形式化 mutation language + MCP 规则验证 + 外部检查/反馈 + 语义 oracle；已有模型上的可执行建议 | SysML；本轮未得连续方法全文和实验表，详细保全机制未知 | 形式化可执行编辑建议已有公开先例；保留未知，不凭摘要确认全部形式保证或否定细分差异 |

### 7. 工具基础：不能被当成新 AI 方法

| ID / 工具 | 官方能力 | 在比较中的角色 |
|---|---|---|
| **T1 IfcPatch** | 通过具名 recipe 与参数修改 IFC | 执行工具基础、确定性对照的一部分；不是自然语言意图理解器；避免采用 IFCPatch 作为新系统名 |
| **T2 IfcDiff** | 比较 IFC 几何及可选 type、property、container、aggregate、classification 等关系变化 | 差异测量基础；“发现变化”不等于判断该变化是否满足用户；preservation 要另定义应保持的集合 |
| **T3 IfcOpenShell file transactions** | 官方 API 包含 begin_transaction、discard_transaction、end_transaction、undo、redo | 说明 IFC 基础事务／撤销不是首次；不代表任何基于该库的 Agent 已实现请求级完整修复事务，也不代表本项目已提供成功后的任意 Undo |

### 8. 评测文献的参考口径：不是当前实验计划

| 工作 | 文献使用的评价对象 | 可以借鉴 | 不能据此宣称 |
|---|---|---|---|
| BIM-Edit v3 | 输入、参考结果、预测结果的变化集合 | 三方对照；目标变化优先；不同 GUID 的结果对齐；语义与关系分开 | 我们首次使用三方 Compare；其未检查的字段也已经被验证 |
| BIBIMBAP | 输入/编辑后 IFC 与任务专属程序测试 | 检查具体对象、位置、尺寸和关系；测试经第二人复核 | 测试总分等于整任务成功；Update 非几何属性全部保持 |
| IFC-Agent | 查询、推理和修改案例；作者承认修改后验证缺口 | 作为直接系统近邻；明确补充实际修改后的语义证据 | 所有现有 IFC Agent 都不做结果验证 |
| Query2Property | 查询是否检索到参考属性 | 检索正确率单列，不能取代写回与目标恢复 | Top-K 召回高就说明修复成功 |
| Self-Verification | 模型是否满足生成出的规格及检查 | 公开检查可帮助执行；私有原始模型另用于最终评测 | 共享规格通过必然意味着没有误解原始语言 |
| RAMC | 显式模型变化和模型补全结果 | 把编辑表示与实际变化分开分析 | ChangeSet 或增量编辑表示本身是新思想 |
| IfcDiff | 按稳定 GlobalId 比较增加、删除、变化 | 保留实体的差异诊断；关系/属性差异需显式纳入 | 新 GUID 的恢复构件天然被认出是原目标；零差异就是修复完成 |

保留 G（原始参考）→D（受控损坏）→R（修复结果）的独立比较原则，不把它称为新通用比较方法。与 L0／L1／L2 的技术关系见技术主文档；具体设计、批准状态和结果统一在 [Claim 与实验](claims-and-experiments.md)维护。本轮不确定数据量、重复次数或执行预算。

BIM-Edit v3 已明确反对用全模型未变化内容主导评分。我们的恢复率同样只以被破坏的目标事实为主要分母，另行记录非目标保持，不能把 999 个没动的构件计入“修好 1 个构件”的主分数。

### 9. 历史修订与当前解释边界


**拆开任务**。 Generation、生成内自修复、已有模型编辑、合规方案搜索与诊断建议分组记录；不再按是否含 repair 关键词统一打勾。

**降低两个主张**。 Model-Bound ChangeSet 保留为领域实现对象；Semantic Round-Trip 改为修改后回读核验。新的词语不是新的机制。

**修正保全描述**。 旧 BIBIMBAP “保全 ✓”应细化为几何/关系等有限检查，并注明非几何属性未测；BIM-Edit 本版已读 v3 评测附录，检查范围更新为任务相关属性与节点/关系变化；仍不将其理解为所有 IFC 属性无损保证。

**补齐前作**。 SGSS 已有用户全文，不再保留“未获取 PDF 所以方法未知”的当前状态。自动 Validate 是未来工作，不是已实现验证闭环。

**撤回不可靠细节**。 Lin 论文的识别/建议百分比本轮不采用，旧代理网页引用不进入本版论证。只保留可核实书目及全文缺口。

**保持谱系**。 MCP4IFC/IFC-Copilot 为前后演进；Self-Verification 使用 MCP4IFC 工具。不同论文的相近结果不自动构成独立团队复制或可相加样本。

### 10. 仍开放的查重缺口

Wu 2026 与 γμS 的完整执行表示、检查边界及实验正文尚需补读；IFC-Copilot Paper 链接本轮仍未取得正文；Lin 论文需原始全文确认“建议”与“实际 IFC 写回”的边界。缺口不影响本轮对宽泛 IR/验证闭环首创的否定，但阻止我们宣称某个很窄组合是世界首次。

停止扩大通用 Agent 文献列表。后续最值得花时间的是上述直接近邻，以及同模型/同工具能力的语义落地对照，而不是再为已经成熟的事务、验证或 RAG 找数十个例子。

### 11. 原始来源与读取位置

所有外部技术结论以以下原始来源为基础；无法访问的链接只作书目定位，不作为“已读全文”的证据。

**R1** — *Multi-agent framework for schema-guided reasoning and tool-augmented interaction with IFC models*. DOI `10.1016/j.autcon.2026.106888`。[作者机构 PDF](https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf)。读取方法及 §6.2–6.3；特别核对 PDF p18 的局限。

**R2** — *MCP4IFC: IFC-Based Building Design using Large Language Models*。[作者 v1](https://arxiv.org/html/2511.05533v1)。读取贡献、方法与编辑相关内容；不将其引用别人的描述当那些论文的原文证据。

**R3** — *IFC-Copilot: A Tool-Based Framework for LLM-Driven IFC Building Design*。[作者项目页](https://show2instruct.github.io/ifc-copilot/)。项目简介、功能及 Paper 入口；未取得对应论文正文。

**R4** — Wu、Fuchs、Pauwels、Borrmann，2026。DOI `10.1016/j.autcon.2026.107148`。[作者机构记录](https://portal.fis.tum.de/en/publications/automated-building-component-alterations-driven-by-llm-formalized/)；[出版商入口](https://www.sciencedirect.com/science/article/pii/S0926580526003894)。本轮依据前者摘要。

**R5** — Wu、Nousias、Borrmann，2025。DOI `10.1016/j.autcon.2025.106004`。[作者机构记录](https://portal.fis.tum.de/en/publications/design-healing-framework-for-automated-code-compliance/)。本轮以摘要为结论依据；不引用未经重算的性能。

**R6** — Lin、Cai、Ni、Pan。DOI `10.2139/ssrn.5894611`。[SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5894611)；[arXiv 线索](https://arxiv.org/abs/2608.28629)。仅核书目；两版本的正文差异未核，不合并实验。

**R7** — Collins 等，2022。DOI `10.1680/jsmic.21.00032`。[出版商正文](https://www.emerald.com/jsmic/article/175/4/160/442590/Shape-encoding-for-semantic-healing-of-design)。读取 semantic model healing 定位及 §2 方法背景，未完成全部实验表审计。

**R8** — Jiang、Du、Wu、Nousias、Borrmann，EG-ICE 2025。DOI `10.17868/strath.00093289`。[正式 PDF](https://strathprints.strath.ac.uk/93289/7/Jiang-etal-EG-ICE-2025-Towards-automated-BIM-conflict-resolution-using.pdf)。读取方法及 Generalizability 限制。

**G1** — Yang 等，WWW Companion 2026。DOI `10.1145/3774905.3793139`。用户上传四页 PDF，印刷页 212–215；阅读全文及图 1–5。出版入口：[ACM](https://doi.org/10.1145/3774905.3793139)。

**G2** — Lamsal、Zlatanova，2026。DOI `10.5194/isprs-annals-XI-4-2026-323-2026`。[正式 PDF](https://isprs-annals.copernicus.org/articles/XI-4-2026/323/2026/isprs-annals-XI-4-2026-323-2026.pdf)。读取 §3–4，核对 corpus、alias 使用范围与评价单位。

**G3** — Sesterhenn 等，EC³ 2026。[正式两页 PDF](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)。v0.4 复核 Framework、Case Study、Discussion 及图 1–2；分别记录 IfcTester 和生成后执行的补充代码，不将二者误写为仅 LLM 自评。

**G4** — *Text2BIM: Generating Building Models Using a Large Language Model-based Multi-Agent Framework*。[作者 v2](https://arxiv.org/html/2408.08054v2)。方法、修订流程及相关限制；不混用不同版本结果。

**E1** — *BIM-Edit: Benchmarking Large Language Models for IFC-Based Building Information Modeling*。[v3 正文](https://arxiv.org/html/2606.20146v3)。本版核查 §3.2、§4.1、附录 D.2 与 E.1–E.3；版本固定，不把其他版本的分数或定义混入。

**E2** — *BIBIMBAP: A Benchmark for Instructional BIM-Based Automated Programming*。[正式 PDF](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)。读取 Benchmark、Evaluation Metrics、Experiments 和 Limitations；重点 PDF p8。

**M1** — Tinnes、Welter、Apel，*Software Model Evolution with Large Language Models: Experiments on Simulated, Public, and Industrial Datasets*，ICSE 2025。[作者 PDF](https://www.se.cs.uni-saarland.de/publications/docs/TWA%2B25.pdf)。v0.4 重点复核 §III.A 的结构差异／Simple Change Graph 与 §IV.B–F 的检索、序列化和补全建议，图 2–3；旧附录核查记录保留，未复现实验。

**M2** — *CADIR: A Cross-Backend Editable Intermediate Representation for Agentic CAD Generation*。[作者 v1](https://arxiv.org/html/2608.00891v1)。方法、实体绑定、Post-reconstruction editing；不将构造回放说成已有 IFC 通用修复。

**M3** — *TraceCAD: Trace-Guided Repair for Agentic CAD Generation*。[作者 PDF](https://arxiv.org/pdf/2608.03062)。相关方法、Algorithm 1 与评估边界；本轮不重算性能表。

**M4** — *ATLAS: A Layered Constraint-Guided Framework for Structured Artifact Generation in LLM-Assisted MDE*。[作者 v3](https://arxiv.org/html/2510.25890v3)。§3.3–3.6 ICM、验证与修复；早期 PRISM 题名与版本不混算。

**M5** — *Well-Formed Executable Suggestions for Continuous Model-Driven Engineering*。[MODELS 2026 官方摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/7/Well-Formed-Executable-Suggestions-for-Continuous-Model-Driven-Engineering)。作者 Sultan、Apvrille；本轮仅按摘要评价。

**T1** — [IfcPatch 官方文档](https://docs.ifcopenshell.org/ifcpatch.html)。

**T2** — [IfcDiff 官方文档](https://docs.ifcopenshell.org/ifcdiff.html)。本版重新核对其稳定 GlobalId 假设；普通两文件差异不是语义修复成功判定。


**T3** — [IfcOpenShell file 官方 API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/file/index.html)。本轮核查 transaction/discard/undo/redo 接口；不推断下游 Agent 的实际事务策略。

### 12. 格式检查与使用

v0.3 曾修正 7 处粗体标点与相邻正文导致的 CommonMark 呈现问题；v0.4 延续标点置于粗体之外、每行一个表格条目的规则。历史 HTML 是当时的阅读快照，不作为第四份持续维护文档。

22 个条目与原始来源保持可追溯。本文只维护文献事实与对应的冲突边界；方法决定、novelty 状态、实验设计及真实结果统一见 [Claim 与实验](claims-and-experiments.md)。当前实验仍处于未批准／待讨论状态。
