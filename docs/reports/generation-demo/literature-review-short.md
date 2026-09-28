# text2IFC 文献综述·简版

更新：2026-09-16。用途：讨论选题和撰写Demo相关工作。逐篇方法、实验分母、限制、版本和来源见[完整版](literature-review-full.md)；研究选择见[研究方案](research-plan.md)。本页只摘最影响选题的工作，不代替完整矩阵，也不宣称穷尽文献。

**结论：已有研究覆盖自然语言建模、自验证、知识检索、可编辑表示和多样化设计。text2IFC可以展示受控生成与修改的系统价值；新的AI方法仍需落到D1设计模式覆盖或D2编辑交互学习，并通过强基线实验成立。**

## 1. BIM / IFC：生成、编辑与自验证

| Paper / 来源 | 贡献与实验 | 与text2IFC的冲突或启发 |
|---|---|---|
| [Text2BIM](https://arxiv.org/abs/2408.08054) | 多角色把文本变成建模程序，执行与规则检查后修订。10提示/391 IFC与25提示/534 IFC属于不同版本，不合并分母 | “多Agent＋建模工具＋检查循环”已存在；生成份数不是独立任务数 |
| [Text2MBL](https://arxiv.org/html/2509.23713v1) | 用建模语言承接自然语言、高层构造与执行；详细任务及限制见完整记录D01 | 中间语言、少写底层代码不是新思想；应作共享底层能力的表示对照 |
| [BIM-Edit](https://arxiv.org/html/2606.20146v3) | 将自然语言驱动IFC编辑作为可评任务；此处沿用v3正文卡，不混后续工具版本 | 不能只同one-shot生成比较；要比较已有模型上的修改与保全 |
| [Self-Verification](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf) | 请求转IDS及非IDS规格，创建/修改IFC，执行检查并反馈。一个两层住宅、GPT-5.2、五轮；空间—楼层关系仍未解决 | 直接覆盖需求→规格→检查→修订；小样本不抹去方法先例；规格遗漏也是我们的风险 |
| [MCP4IFC](https://arxiv.org/html/2511.05533v1) / [IFC-Copilot项目](https://show2instruct.github.io/ifc-copilot/) | IFC工具访问与建模交互；项目延续和论文证据分开 | MCP、工具化和领域知识接入不是新方法；项目网页不能算一篇新全文证据 |

BIM-Edit、BIBIMBAP、Self-Verification和MCP4IFC存在作者重合；Self-Verification明确依赖MCP4IFC相关工具。它们不是可以随意相加的独立团队复制。完整综述保留谱系与版本限制。

**对当前系统的启示：**重点测原始要求、几何、关系和非目标保持是否同时成立。文件可解析、规则通过和视觉合理应分开；我们的受限ChangeSet与运行记录可描述为系统机制，不能仅据这些机制宣称AI首创。

## 2. CAD / 空间生成：从单个结果到有效方案集合

| Paper / 来源 | 贡献与实验 | 对D1/D2的影响 |
|---|---|---|
| [TileGPT：Generative Design through Quality-Diversity Data Synthesis and Language Models](https://arxiv.org/html/2405.09997v1) | MAP-Elites生成数据、DistilGPT2输出粗布局、WFC细化。两组各50k训练设计；243提示各100次；有效性与各属性匹配分开测 | **多样性＋语言模型＋约束已有直接建筑先例**；D1必须超越多次采样和QD封装 |
| [SceneCraft](https://proceedings.mlr.press/v235/hu24g.html) | 空间分解、关系约束、求解、视觉修订、技能库；40查询中20学习/20评测 | “程序＋求解器＋知识库”已有；样本小不表示机制不存在 |
| [SceneMotifCoder](https://arxiv.org/html/2408.02211v2) | 从1–3例抽可复用空间程序；202描述，数量/布局/物理性分别评测 | 参数化程序与组合复用已有；分别通过不等于联合通过 |
| [PSDL](https://arxiv.org/html/2510.16147v1) | 相对坐标、共享参数和数值搜索；70自建＋66 Holodeck提示；布局修正阶段不需LLM | D1必须与便宜的数值搜索比较，证明何时需要换结构 |
| [Graph-CAD](https://proceedings.iclr.cc/paper_files/paper/2026/file/90e06fe49254204248cb12562528b952-Paper-Conference.pdf) | 图→动作→代码及能力课程；12k训练来源，CADBench700；几何约束指标只测280例 | 结构分解、动作规划和能力课程不能重新命名；冻结模型也有两示例基线 |
| [TraceCAD](https://arxiv.org/html/2608.03062v1) | 需求/步骤/失败关联，局部回溯与条件技能；200消融、1000比较，在线记忆需注意评测顺序 | D2必须超过局部反馈与技能记忆；不能只胜过无反馈Agent |

**对多解评价的启示：**通过硬约束的不同布局都可正确，但不同GUID、镜头或序列化不算新设计。小型受限任务可枚举真实模式；大场景只测预定义模式覆盖，不声称完整解空间覆盖。固定模型和总预算，同时统计无效尝试。

## 3. 通用AI：知识、规划与验证

| Paper / 来源 | 已有贡献与实验边界 | 对我们的限制 |
|---|---|---|
| [EvoR](https://aclanthology.org/2024.findings-emnlp.143.pdf)、[PURPLE](https://arxiv.org/html/2601.12078v1)、[DearICL](https://arxiv.org/html/2609.06670v1) | 分别覆盖执行驱动检索演化、集合感知上下文选择、组合收益代理；任务与监督不同 | “知识有协同、按执行效果选知识”不够新；D2压缩需要决策保全证据 |
| [DST](https://arxiv.org/html/2603.12712v1) | 多粒度设计说明覆盖与示例选择；900测试、三模型 | CAD中互补知识检索已有；文本覆盖保证不是执行正确保证 |
| [ChopChop](https://arxiv.org/html/2509.00360v1) | 程序空间上的语义约束解码；10等价任务、74个可表达的TypeScript任务，三个模型；类型任务按编译成功计 | JSON格式约束弱于语义约束；闭源API未必能接token级机制；编译不等于意图正确 |
| [SCOPE](https://aclanthology.org/2026.acl-long.2028.pdf) | 查询转结构参数，复用Combination/Filter/Deliver函数；五模型、旅行/行程/会议规划 | “LLM只决定参数、执行器承担细节、减少token”已有；仍依赖约束被正确表达 |
| WorldCoder、[Contract2Tool](https://arxiv.org/html/2606.07904v1) | 程序化转移模型、操作前提/效果学习；具体正文与实验见完整记录 | 世界模型或合同本身不新；D2需证明多操作几何交互、探测与迁移的增量 |
| [VeriAct / Spec-Harness v1](https://arxiv.org/html/2604.00280v1)、[Prompt Coverage Adequacy](https://arxiv.org/html/2607.02057v1) | 规格检查、输出变异和提示需求覆盖已有研究；有限测试与覆盖代理都不是完整证明 | 自验证检查器不能默认正确；须测错误放行和合法多解误拒 |
| [CWM](https://arxiv.org/html/2510.02387v1)、[Absolute Zero](https://arxiv.org/html/2505.03335v1)、[SWE-smith](https://arxiv.org/html/2504.21798v1)、[Hybrid-Gym](https://arxiv.org/html/2602.16819v1) | 执行状态建模、可验证自博弈、造题与跨任务训练；训练成本和监督来源差异大 | Repair轨迹→Generation提升只能作为待测迁移，不能只因有执行器就宣布新学习范式 |

**保留的两个问题：**D1问怎样在预算内覆盖更多有效设计模式；D2问怎样学会编辑相互作用、减少多步试错。可审计/回滚支撑两者，知识效率是实验轴。若标准QD、约束求解或转移模型同样有效，应据实收缩贡献，而不是以IFC应用域替代方法差异。
