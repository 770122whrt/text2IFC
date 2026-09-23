# text2IFC 论文矩阵与证据索引

> **历史材料，2026-09-16已整合。** 当前方向与实验统一见[研究方案](research-plan.md)，文献统一见[简版](literature-review-short.md)和[完整版](literature-review-full.md)。下文保留调查时的结论与编号，不再作为当前优先级。

核查日期：2026-09-15。本页保留前轮 63 条记录范围；后续方法研究见 [扩展论文矩阵](novelty-literature-addendum.md)、[当前方法候选](novelty-directions.md) 与 [对应实验](novelty-experiments.md)。此前综合草案保留在 [研究草案](research-proposal.md)。

本矩阵覆盖用户 v2.1 调查稿 2A.1、2A.2、2A.4、2A.5、2A.6 中的 **51 条文献/项目记录**，并新增 12 条与当前 Coding Agent、知识效率方向直接相关的记录：IFC-Bench v1 原论文、Cobbie、Tell2Design 原论文、ATLAS、CodeAct、RepoCoder、Repoformer、RepoGraph、SWE-agent、LLMLingua、LongLLMLingua、MAS4SysML。共 **63 条**，不是 63 个互相独立的系统。

**49 条完成指定版本的正文核查；14 条尚未完成全文核查。** 后者仍逐项保留，不拿摘要、前作、项目网页或综述填补结果。

## 怎样使用这张矩阵

- **F：** 已实际取得原始正文，阅读方法、实验设置/结果及讨论/局限的相关部分；不表示审计全部补充材料或复现。
- **P：** 全文核查未完成。可取得材料进一步标成摘要/片段/项目；底层证据卡中的 PARTIAL 与 UNAVAILABLE 在本表统归 P，区别仍保留。
- **每个论文名称链接到独立证据卡**：包含完整书目、原始全文/出版商/作者链接、已读节号或页码、方法、结果分母、局限及对本项目的推论。下面的短行只是索引，不能替代这些卡片。
- F/P 是本轮读取状态，不是对论文质量的等级。预印本、正式论文、综述和项目材料分别注明；没有把不同版本结果合并。
- 本轮没有复现任何论文、运行作者实现或调用 Provider。表中数字是作者报告，少数表格复算已单独说明。

| 分组 | 条目数 | F | P | 详细材料 |
|---|---:|---:|---:|---|
| A：BIM 创作与领域综述 | 14 | 9 | 5 | [逐篇证据](literature-evidence/bim-authoring.md) |
| B：IFC、评价与知识使用 | 12 | 9 | 3 | [逐篇证据及作者谱系](literature-evidence/ifc-evaluation.md) |
| C：CAD、空间生成与 MDE | 16 | 12 | 4 | [逐篇证据](literature-evidence/structured-generation.md) |
| D：Coding、知识、压缩与控制 | 21 | 19 | 2 | [逐篇证据](literature-evidence/coding-knowledge-and-control.md) |
| **合计** | **63** | **49** | **14** | |

## A. BIM 创作、布局与领域综述

| 论文 / 证据卡 | 状态与版本 | 任务、接口与知识 | 实验及必须保留的条件 | 对当前方向的作用 |
|---|---|---|---|---|
| [A01 Interactive Design](literature-evidence/bim-authoring.md#a01) | F，2023 预印本；正式版未核 | 选择性 XML→LLM 修改→Revit | 一个模型、48 墙；分类/细化分数，不是整栋生成率 | 紧凑表示、任务属性选择及 token 动机已有先例 |
| [A02 BIM Copilot](literature-evidence/bim-authoring.md#a02) | F，EG-ICE 2024 | Vectorworks 高层工具、文档 RAG、运行反馈 | 建模示例；20 QA 的 faithfulness 不可转成建模成功率 | 工具封装工程知识已有直接论述 |
| [A03 Text2BIM](literature-evidence/bim-authoring.md#a03) | F，arXiv v1/v2；JCCE 2026 定稿未核 | 多代理＋BIM 工具＋Solibri 反馈 | v1 150 运行/391 输出；v2 225/534；含中间 IFC | 最近系统之一；有删构件使错误变少的反例 |
| [A04 BIMgent](literature-evidence/bim-authoring.md#a04) | F，2025 v2 / ICML Workshop | GUI 建模、文档、截图监督与规划 | 25 任务，8 完成；多模型混合与基线不完全同模型 | 完整任务与动作成功分开；不是主会 ICML 论文 |
| [A05 Trestle-bridge](literature-evidence/bim-authoring.md#a05) | F，JEAS 2026 | 参数合同、工程规则、Revit 函数计划、纠错 | 200 案例各三次；有工程规则消融；数据需索取 | 任务知识、几何抽象和 token 动机均已存在 |
| [A06 AutoBIM](literature-evidence/bim-authoring.md#a06) | F，Scientific Reports 2026 | 图集 RAG＋参数抽取＋Rhino/Grasshopper，含 IFC 导出 | 一个核心桥例两种指令；200+ 指参数；有 RAG/提示消融 | 不能说它不输出 IFC；参数匹配非建筑泛化 |
| [A07 Early-Stage Layout Planning](literature-evidence/bim-authoring.md#a07) | P，JCCE 2026，仅书目/摘要 | 摘要称多代理规划、气泡图和评价 | 方法/结果表均未取得 | 潜在布局近邻；机制是否覆盖保持未知 |
| [A08 AI BIM Coordinator](literature-evidence/bim-authoring.md#a08) | P，AIC 2025，片段 | Revit/AutoGen，知识技能与执行检查 | 完整设置未核；不能挪用 AHFE 前作数字 | 知识驱动非专家交互已有系统定位 |
| [A09 Worksite Trailers](literature-evidence/bim-authoring.md#a09) | F，ISARC 2026 | JSON 数据层、历史案例复用、Revit、人工迭代 | 功能原型；没有定量时间比较 | Demo 近邻；可操作系统不等于效果已证实 |
| [A10 BIMVLM](literature-evidence/bim-authoring.md#a10) | P，ESWA 2026，片段 | 多视图/文本→构件动作序列与代码 | 完整数据划分、指标与迭代准则未核 | 不能把构件 CAD 等同整栋 IFC |
| [A11 NADIA](literature-evidence/bim-authoring.md#a11) | P，AEI 2024，片段 | 外墙细化的需求、材料与参数 | 摘要数字分母未全文核实 | 不混写 GAIA、NADIA、NADIA-S |
| [A12 Generalized Framework / NADIA-S](literature-evidence/bim-authoring.md#a12) | F，CIB W78 2024 | 解释/匹配/结构化/执行/检查 | 8×30 细化；反复执行至检查通过，未给固定重试预算 | 100% 不等于首轮或预算内成功 |
| [A13 BIM–LLM Integration Review](literature-evidence/bim-authoring.md#a13) | P，AIC 2026，综述片段 | PRISMA、应用和验证分类 | 摘要称 61 篇；检索截止与编码规则未核 | 可补索引，不能替代原始系统论文 |
| [A14 Bridging BIM and NLP](literature-evidence/bim-authoring.md#a14) | F，ISARC 2026，综述 | 六库检索与分类 | 92 纳入；部分分类分母 81；截止 2025-05 | 2026 出版不代表覆盖所有 2026 系统 |

## B. IFC 任务、验证、问答与模型知识

| 论文 / 证据卡 | 状态与版本 | 任务、接口与知识 | 实验及必须保留的条件 | 对当前方向的作用 |
|---|---|---|---|---|
| [B01 BIM-Edit](literature-evidence/ifc-evaluation.md#b01) | F，arXiv 2026 v3 | 已有 IFC 编辑；几何/语义/拓扑评分 | 47 基础场景、324 变体任务；单执行工具，20 次上限 | 很强的评价先例；不是增强 Agent 的能力上限 |
| [B02 BIBIMBAP](literature-evidence/ifc-evaluation.md#b02) | F，EC³ 2026 | 小 IFC 的 CRUD 与确定性检查 | 100 题；均值是部分检查得分；更新未评非几何保全 | 原子切片有用；不能当整栋成功率 |
| [B03 Self-Verification](literature-evidence/ifc-evaluation.md#b03) | F，EC³ 2026，2 页 | IDS＋生成检查＋MCP4IFC 修订 | 一个住宅、五轮；空间/楼层关联仍失败 | 需求分解与生成内部纠错已经覆盖 |
| [B04 Capability-based Evaluation](literature-evidence/ifc-evaluation.md#b04) | P，AIC 2026，片段 | BIM 自动化能力切片、多维评价 | 31 任务见片段；完整指标和表未核 | 不声称首次多维可靠性评价 |
| [B05 Error Taxonomy](literature-evidence/ifc-evaluation.md#b05) | P，CRC 2026，摘要 | Revit 脚本错误与人工调试 | 摘要称 20 任务；人工、重试和分母未核 | 不能把最终人工调通当自主成功 |
| [B06 Qwen-BIM](literature-evidence/ifc-evaluation.md#b06) | F，arXiv 2026 v1 | BIM 文本 QA/QRA→LoRA | G-Eval 0.689→0.834；Table 7 分项与总数矛盾 | 语言得分不是 IFC 生成或修复成功率 |
| [B07 Building Descriptor](literature-evidence/ifc-evaluation.md#b07) | F，EC³ 2025 | BIM→关系 JSON→语言描述 | 四项目、139 房间；存在方向/拓扑描述错误 | 反向配对数据需检查遗漏，不天然可逆 |
| [B08 IFC-Agent](literature-evidence/ifc-evaluation.md#b08) | F，AIC 2026 | schema 工具链、缓存、抽样后批处理 | 正文/附录列 60 题，引言写 48；缺修改后一致性验证 | 领域知识指导执行已有直接先例 |
| [B09 Scan-to-BIM / Scan-to-Graph](literature-evidence/ifc-evaluation.md#b09) | F，AIC 2026 | 点云＋范围→参数布局→IFC4/图 | 房间级；部分面积指标弱于传统对照 | 参数到确定性 IFC/图的链条已有先例 |
| [B10 Dual-Layer IFC Encoding](literature-evidence/ifc-evaluation.md#b10) | P，SSRN 2026，摘要 | 摘要称双层压缩与按需重建 | 原文 41 页未取得；无损、预算和生成结果未核 | **压缩主线的高优先级全文缺口** |
| [B11 IFC-Bench v1 原论文](literature-evidence/ifc-evaluation.md#b11) | F，EC³ 2025 | CoT 预选工具＋ReAct 查询 | 99 QA；只报告最佳模型 79/99；LLM judge | 2025 已实现动态工具预选 |
| [B12 Adaptive Exploration / Cobbie](literature-evidence/ifc-evaluation.md#b12) | F，arXiv 2026 v1 | CodeAct 探索、混合文档检索、经验工具 | 514 测试题；强模型知识收益不显著；排除 crash/timeout | **知识效率的主要近邻**；需完整分母与成本比较 |

## C. 空间生成、CAD 和模型驱动工程

| 论文 / 证据卡 | 状态与版本 | 任务、接口与知识 | 实验及必须保留的条件 | 对当前方向的作用 |
|---|---|---|---|---|
| [C01 SceneCraft](literature-evidence/structured-generation.md#c01) | F，ICML 2024 | Blender 程序、空间技能库、约束求解与视觉反馈 | 20 学习/20 测试提示；有技能库消融 | “知识库＋空间代码＋求解器”强近邻 |
| [C02 Text2CAD](literature-evidence/structured-generation.md#c02) | F，NeurIPS 2024 | 文本→可编辑 sketch/extrude 序列 | 主表最详细 L3 提示；其他详略不全优 | 可执行性与语义满足应分别评价 |
| [C03 CADCodeVerify](literature-evidence/structured-generation.md#c03) | F，ICLR 2025 | CadQuery 执行修复＋需求问题＋四视图验证 | 200 对象；视觉 QA 并不全正确；GT solver 为上界 | 需求驱动自验证已有直接先例 |
| [C04 LLM4CAD](literature-evidence/structured-generation.md#c04) | F，JCISE 2025 作者稿 | 多模态 CadQuery 编码与三轮调试 | 五类零件；解析改善，条件 IoU 不必改善 | 条件评分的入选样本变化不能当同例退化 |
| [C05 Building-Diffusion](literature-evidence/structured-generation.md#c05) | F，CVPRW 2026 | 固定体素邻接、条件图、节点标签扩散 | 部分指标弱于 GAN；用 GT 选最佳采样 | 固定邻接不等于 IFC 语义关系保全 |
| [C06 MANSION](literature-evidence/structured-generation.md#c06) | F，CVPR 2026＋补充 | 多层规划、关系组、确定性求解、保持已成拓扑 | 有 GT 条件设置；难放对象可删除/缩小阵列 | **关系组交给 solver 已有实现** |
| [C07 Instance Model Code Synthesis](literature-evidence/structured-generation.md#c07) | P，MODELS 2026 议程/摘要 | 摘要称 Pydantic 元模型、验证器、代码生成 | 实验表与具体设置未取得 | 领域类型/API 驱动建模的强相关缺口 |
| [C08 Well-Formed Executable Suggestions](literature-evidence/structured-generation.md#c08) | P，MODELS 2026；有工具线索 | mutation 语言、MCP 验证、语义 oracle | 论文全文未取得；代码 MR 不能替代实验 | 编译保证与语义判断分工的近邻 |
| [C09 Software Model Slicing](literature-evidence/structured-generation.md#c09) | P，MODELS 2026 议程/摘要 | 半径、模块化、LLM 引导的图切片 | 1000 模型及效果仅摘要；算法/预算未核 | **上下文选择主线的首要全文缺口** |
| [C10 Valid SysML v2 Models](literature-evidence/structured-generation.md#c10) | P，Computers in Industry 2025 | 示例检索＋ANTLR＋生成迭代 | 大学稿下载失败；100% 仅语法摘要声称 | 不把语法通过等同工业可靠性 |
| [C11 MCeT](literature-evidence/structured-generation.md#c11) | F，MODELS 2025 | 原子需求检查、投票和交叉过滤 | 76 例；精确率提高伴随召回损失；总 token 增加 | 义务分解也应评价代价和遗漏 |
| [C12 Event-B Agent](literature-evidence/structured-generation.md#c12) | F，FSE 2026 / arXiv v1 | schema、编译器、证明义务、七类知识与原子修复 | 27 系统；含 Cursor；跨层正确性指标有近似假设 | **编译器/Agent 分工最强近邻之一** |
| [C13 Model Evolution / RaMc](literature-evidence/structured-generation.md#c13) | F，ICSE 2025＋附录 | 变更图、既有邻居、历史检索、边补全 | 三种语料；部分基线模型不同；切片外引用困难 | 关系局部表示与知识检索已有先例 |
| [C14 Tell2Design](literature-evidence/structured-generation.md#c14) | F，ACL 2023 | 语言＋边界→二维房间序列 | 80,788 图，人工描述仅 5,051；全要求满足率另测 | 数据标注及多正确答案的评价参照 |
| [C15 NextFocus](literature-evidence/structured-generation.md#c15) | F，ICSE 2026＋附录 | 共变预测 focus、两跳切片、JSON 补全 | 0.98 是排序指标；类型结构完成率远低；改版多因素变化 | 选对知识/位置不等于最终生成正确 |
| [C16 LLMs in MDE Mapping](literature-evidence/structured-generation.md#c16) | F，2026 在线 / 2027 卷期，综述 | 检索、筛选、抽取和频数综合 | 86 纳入；36 无基线、21 报成本；止早期 2026 | 用于评价规范，不能代替逐篇原文 |

## D. Coding、建模抽象、知识压缩与控制

| 论文 / 证据卡 | 状态与版本 | 任务、接口与知识 | 实验及必须保留的条件 | 对当前方向的作用 |
|---|---|---|---|---|
| [D01 Text2MBL](literature-evidence/coding-knowledge-and-control.md#d01) | F，NeurIPS 2025 / arXiv v1 | 模块/单元/房间 C# 操作与微调 | 198 设计、396 文本；138/20/40 按设计拆分；IoU 有边界 | 借鉴研究结构，不预设 text2IFC 已优于它 |
| [D02 MCP4IFC](literature-evidence/coding-knowledge-and-control.md#d02) | F，arXiv 2025 v1 | IFC 工具＋RAG＋动态代码 | 65 QA 与少量编辑/生成演示；不同分母 | 原生 IFC Agent 已存在；工具上下文成本已被讨论 |
| [D03 IFC-Copilot](literature-evidence/coding-knowledge-and-control.md#d03) | P，后续项目页面 | 52 工具、读/创建/编辑及代码 | 项目报告 100 任务；Paper 链接 404 | 不当已读论文，也不漏掉项目演进 |
| [D04 ATLAS](literature-evidence/coding-knowledge-and-control.md#d04) | F，arXiv 2026 v3 | ICM、结构约束解码、编译、SHACL/SMT | 60 组件；20 系统/284 文件；XSD 与 SMT 结果分离 | **“知识＋编译＋验证”不能整体称新** |
| [D05 Fine-grained Access Control](literature-evidence/coding-knowledge-and-control.md#d05) | F，SoSyM，2017 在线 | 过滤视图、读写依赖、双向更新 | 条件性形式性质＋风机模型伸缩实验 | 读写隔离、依赖与提交检查已有基础 |
| [D06 ChronoSphere](literature-evidence/coding-knowledge-and-control.md#d06) | F，SoSyM 2019 | 图模型、版本、事务与查询 | 20 万 EObject 合成模型；对照 OCL 路线有影响 | 冻结状态/回滚不是新原语 |
| [D07 CodeMEM](literature-evidence/coding-knowledge-and-control.md#d07) | F，Findings ACL 2026 | AST 记忆、历史指令和遗忘检测 | 40 对话/360 指令＋230 代码任务；不总省 token | 保全与知识记忆已有先例 |
| [D08 CodeAct](literature-evidence/coding-knowledge-and-control.md#d08) | F，ICML 2024 | 可执行 Python 作为 Agent 行动 | 行动格式实验＋另行微调实验；JSON 并非总弱 | 强 Coding baseline 需允许组合、执行和调试 |
| [D09 RepoCoder](literature-evidence/coding-knowledge-and-control.md#d09) | F，EMNLP 2023 | 预测辅助迭代检索、仓库补全 | 行/API 各 1600、函数 373；更多轮非单调收益 | 检索循环本身不能当创新 |
| [D10 Repoformer](literature-evidence/coding-knowledge-and-control.md#d10) | F，ICML 2024 | 学习检索时机与阈值 | 多仓库基准；最高加速点有质量条件 | 何时检索与预算取舍已有直接方法 |
| [D11 RepoGraph](literature-evidence/coding-knowledge-and-control.md#d11) | F，ICLR 2025 | 调用/包含图、k-hop 平铺或总结 | 多系统增益伴随额外 token；2-hop 可更差 | 需要超越通用邻域切片，并匹配成本 |
| [D12 SWE-agent](literature-evidence/coding-knowledge-and-control.md#d12) | F，NeurIPS 2024 | Agent 专用搜索、编辑、观察窗口和历史 | 完整 2294 / Lite 300；费用表只对成功实例平均 | 接口作为研究变量已存在；分母需对齐 |
| [D13 LLMLingua](literature-evidence/coding-knowledge-and-control.md#d13) | F，EMNLP 2023 | 预算分配、困惑度、迭代 token 压缩 | 四类任务；高压缩也掉分 | 通用压缩对照，不能假设标识/数值保全 |
| [D14 LongLLMLingua](literature-evidence/coding-knowledge-and-control.md#d14) | F，ACL 2024 | 问题相关压缩、重排、实体恢复 | 多长上下文任务；逐问题重压缩和计算开销 | 任务相关压缩已有先例，需算系统总成本 |
| [D15 Progent](literature-evidence/coding-knowledge-and-control.md#d15) | F，arXiv 2026 v3 | 工具/参数权限策略和 SMT 扩权检查 | AgentDojo/ASB；安全与正常任务效用分测 | 权限保证不等于产物语义保证 |
| [D16 MiniScope](literature-evidence/coding-knowledge-and-control.md#d16) | F，arXiv 2025 v1 | 权限层级＋ILP＋调用检查 | 10 应用合成请求；确认负担是模拟实验 | “足够而尽量少”及覆盖优化已有先例 |
| [D17 AuthBench](literature-evidence/coding-knowledge-and-control.md#d17) | F，arXiv 2026 v2 | 先充分、再收窄的权限推断 | 120 任务；参考轨迹不等于唯一最小边界 | 类似决策结构已有研究；须给出具体领域差异 |
| [D18 Agentless](literature-evidence/coding-knowledge-and-control.md#d18) | F，FSE 2025 作者正文 | 定位→多候选补丁→测试筛选 | 正文 96/300；98 对应不同测试条件 | 自主 loop 不天然胜过清晰固定流程 |
| [D19 RepairAgent](literature-evidence/coding-knowledge-and-control.md#d19) | F，arXiv 2024 v2 | 状态机、工具、动态记忆、测试修复 | 835 故障；164 正确；成本均值/中位措辞矛盾 | 修复 Agent 已存在；需 IFC 保全的具体证据 |
| [D20 PAFT](literature-evidence/coding-knowledge-and-control.md#d20) | F，arXiv 2026 v1 | 稳定片段加权监督＋课程＋QLoRA | Java 修复；修改量在通过测试子集计算 | 最小修改不等于几何/关系语义保全 |
| [D21 MAS4SysML](literature-evidence/coding-knowledge-and-control.md#d21) | P，JoVE 2026，部分正文 | 任务卡、依赖、语法/语义验证与修复 | 方法和 75 例设置可读；主要结果表受限 | 任务义务和验证分工有先例，效果待全文 |

## 目前最需要纠正的横向比较

| 容易形成的结论 | 核查后的写法 | 证据 |
|---|---|---|
| Text2BIM 用 391/534 个独立建筑验证 | 是不同版本的含中间文件输出数；对应运行设计不同 | [A03](literature-evidence/bim-authoring.md#a03) |
| AutoBIM 测了 200 多个案例且不支持 IFC | 200+ 为参数；核心实验一个桥例；明确有 IFC 导出 | [A06](literature-evidence/bim-authoring.md#a06) |
| NADIA-S 100% 说明单次可靠 | 包含执行至通过的循环，缺固定预算 | [A12](literature-evidence/bim-authoring.md#a12) |
| BIM-Edit 的低分说明现有 Agent 都不行 | 它测单一代码工具条件，未测完整检索/领域工具系统 | [B01](literature-evidence/ifc-evaluation.md#b01) |
| BIBIMBAP 均分约 50 就是半数任务完成 | 是平均部分测试得分，且更新属性保全不足 | [B02](literature-evidence/ifc-evaluation.md#b02) |
| Qwen-BIM 提升 21 个百分点的生成率 | 是问答 G-Eval 相对增益；数量表也有内部不一致 | [B06](literature-evidence/ifc-evaluation.md#b06) |
| IFC-Agent 全面验证了修改结果 | 附录实际 60 题；作者明确缺修改后一致性验证 | [B08](literature-evidence/ifc-evaluation.md#b08) |
| 知识增强总会提升强模型 | Cobbie 强模型增强收益很小；不能据此反推所有知识无效 | [B12](literature-evidence/ifc-evaluation.md#b12) |
| MANSION 的可达性说明所有要求都保留 | 难放置对象可被丢弃，需同时看对象覆盖 | [C06](literature-evidence/structured-generation.md#c06) |
| NextFocus 0.98 是模型补全成功率 | 是特定分母的排序指标；最终类型/结构正确率低得多 | [C15](literature-evidence/structured-generation.md#c15) |
| 结构合法等于语义成立 | ATLAS 文件 XSD 全通过时，系统 SMT 首轮仍可能全部失败 | [D04](literature-evidence/coding-knowledge-and-control.md#d04) |
| 图检索、记忆或更多反馈一定省 token | RepoGraph、CodeMEM、MCeT 都有成本上升或效果取舍 | [D11](literature-evidence/coding-knowledge-and-control.md#d11)、[D07](literature-evidence/coding-knowledge-and-control.md#d07)、[C11](literature-evidence/structured-generation.md#c11) |
| 摘要可代替全文；项目开源就等于实验可复现 | 还需要具体方法/分母、实现快照、数据及依赖对应关系 | 下表与全部证据卡 |

这些条件限制结论的范围，不意味着论文没有价值。窄问题做得扎实可以构成贡献；范围更大但对照不足，也不能仅凭系统复杂度得到更强论文。

## 尚未完成全文核查的 14 条

以下均已尝试原始出版商、作者/机构或公开稿路线，具体链接及结果见卡。没有自动联系作者、代付访问或把二手转述补成原文。

| 条目 | 实际取得的材料 | 还缺什么 / 对本研究的重要性 |
|---|---|---|
| [A07](literature-evidence/bim-authoring.md#a07) | 书目/摘要 | 布局规划方法、比较与实验表 |
| [A08](literature-evidence/bim-authoring.md#a08) | 出版商正文预览 | Coordinator 的完整执行/评价；不能用前作替代 |
| [A10](literature-evidence/bim-authoring.md#a10) | 方法/结果片段 | 构件动作、数据隔离、迭代和完整结果 |
| [A11](literature-evidence/bim-authoring.md#a11) | NADIA 正文预览 | 样本分母、assistant/consultant 评价 |
| [A13](literature-evidence/bim-authoring.md#a13) | 综述片段 | 检索截止、编码规则与提取表 |
| [B04](literature-evidence/ifc-evaluation.md#b04) | 能力评测章节片段 | 指标操作化、人员介入和完整分母 |
| [B05](literature-evidence/ifc-evaluation.md#b05) | ASCE 书目/摘要 | 错误分类协议、人工调试与停止条件 |
| [B10](literature-evidence/ifc-evaluation.md#b10) | SSRN 摘要和元数据 | **编码/解码、sidecar、语义可访问性及成本；高优先级** |
| [C07](literature-evidence/structured-generation.md#c07) | 官方摘要/作者列表 | Pydantic 约束、与求解器的实验；高相关 |
| [C08](literature-evidence/structured-generation.md#c08) | 官方摘要、工具说明、公开 MR | mutation 形式保证及实验，代码线索不替代论文 |
| [C09](literature-evidence/structured-generation.md#c09) | 官方摘要/作者列表 | **切片策略、依赖范围、全部成本；高优先级** |
| [C10](literature-evidence/structured-generation.md#c10) | 摘要/开放稿索引 | 大学 PDF 下载超时或受限；完整实验待取 |
| [D03](literature-evidence/coding-knowledge-and-control.md#d03) | IFC-Copilot 项目页/仓库 | 论文链接 404；实验版本与失败分母 |
| [D21](literature-evidence/coding-knowledge-and-control.md#d21) | 开放方法/实验设置 | 结果主表和讨论受限；不引用摘要高分作为核实结果 |

另外，A01/A03/C04 等明确使用作者稿，不能认定与期刊定稿逐字一致。正式投稿前若论证依赖某个版本特有结果，应固定该版引用，或再核正式定稿。

## 原调查稿中的数据资源没有丢弃

v2.1 的 2A.3 是资源清单，不能把资源页面自动算作完成了一篇论文精读。当前登记和本地状态仍见 [external 数据目录](../../../dataset/external/GENERATION_DATASETS.md)；本轮不重复下载或更改准入。Tell2Design 与 MANSION 已有原始论文证据卡，IFC-Bench 新补了两版原论文。

| 原资源项 | 在本组材料中的位置 / 可承担的用途 |
|---|---|
| ResBIM | external 登记；候选住宅模板，源模型与变体分开 |
| ResBIM-IFC | external 登记；第三方转换版本，不与源建筑重复计数 |
| IFC-bench | [B11/B12 版本核查](literature-evidence/ifc-evaluation.md#b11)；问答知识切片 |
| BIM-Edit IFC Corpus | [B01](literature-evidence/ifc-evaluation.md#b01)；输入、目标与提示变体分开 |
| buildingSMART Certification Datasets | external 登记；适用 schema/交换能力测试，不是自由文本设计集 |
| buildingSMART Community Samples | external 登记；场景候选与边界样例 |
| Schependomlaan | external 登记；真实项目输入，不能自动生成独立 NL 真值 |
| GeoBIM Benchmark | external 登记；几何/交换测试参考 |
| IFCNet | external 登记；单实体层面，不等于整栋 |
| BIMNet | external 登记；数据源名，产品名仍为 text2IFC |
| MansionWorld | [C06](literature-evidence/structured-generation.md#c06)；多层交互场景，非 IFC 生成金标准 |
| Tell2Design | [C14](literature-evidence/structured-generation.md#c14)；布局/语言与标注方式参照 |

本矩阵是有明确边界的研究记录，不宣称穷尽整个学科。正文引用可聚焦最相关的约 8–12 篇；其余证据继续保留，不能因为篇幅限制而在创新判断时忽略。
