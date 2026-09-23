# 简版选题的补查证据

> **历史材料，2026-09-16已整合。** 当前方向与实验统一见[研究方案](research-plan.md)，文献统一见[简版](literature-review-short.md)和[完整版](literature-review-full.md)。下文保留调查时的结论与编号，不再作为当前优先级。

> 后续更新：用户要求扩大选题范围。本文保留上一轮的 A/B/C 核查；当前问题池、Self-Verification 比较与 P1/P2/V1/L1 实验见 [方法方向扩展](broader-method-directions.md)。

日期：2026-09-15。本文支撑 [简洁记录](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/research-shortlist.md)，不要求先读完整 104 条矩阵。补查重点是排除已有方法，而非证明未找到就一定新颖。文献方法/实验与本项目推论分别记录；没有复现作者结果，没有运行新的产品 Provider 实验。

本轮重新核查 15 篇关键近邻的指定版本方法和实验，另核对现有工程接口；其中有沿用后再聚焦阅读的文献，15 不等于全部新增论文。并非穷尽检索，未披露或未恢复的分母仍保留缺口。工期以末尾代码核查和简版的保守估计为准。


---

# N01 聚焦复核：失败后怎样选择技能修订

2026-09-15。结论：**原 N01 降级为高风险先导问题，不能把“修程序／收窄条件／拆技能”写成创新。** 下列原始全文已有大部分组件；固定 LLM、换成 IFC 也不能补足差异。

## 五个最强近邻

- **[Empowering Large Language Model Agents through Action Learning（LearnAct）](https://arxiv.org/html/2402.15809v2)**：§4、算法1已改 Python 动作和说明，从4个更新候选中选择。§5、表7覆盖4类规划及6类 ALFWorld，每类3训练任务、3次重复；有代码／注释消融及过拟合。完整测试分母尚缺。“多种修订再测试选择”已有。
- **[Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents](https://arxiv.org/html/2606.07904v1)**：§III–IX从文档、轨迹学前提和效果，再过滤工具。100合成工具、102任务，表V成功率 .775→.980；固定谓词、主要成功路径，聚合排除一个兼容性差的模型。它覆盖合同学习，未联合改执行程序。
- **[Embodied Active Learning of Relational State Abstractions for Bilevel Planning](https://proceedings.mlr.press/v232/li23a/li23a.pdf)**：§3–5以集合熵主动探索；按控制器和对象替换后的效果分组，联合更新谓词、算子、参数采样器。3域，各50示范、1000转换、50留出任务、10种子；单次3–36小时。控制器已给定，但“主动学条件与技能结构”已有。
- **[Co-Evolving LLM Decision and Skill Bank Agents for Long-Horizon Tasks（COS-PLAY）](https://arxiv.org/html/2604.20987v1)**：§4.2已有带前提／效果契约的技能，以及 refine、merge、split、retire。§5、表1用6游戏、每游戏60教师轨迹；单人16、多人游戏每玩家10评测回合。技能主要是提示协议，系统训练5个 LoRA；没有独立证明三类修改如何选择。
- **[Bayesian-Agent: Posterior-Guided Skill Evolution for LLM Agent Harnesses](https://arxiv.org/html/2606.08348v1)**：§3.4、表1在冻结 LLM 下，用条件化失败证据选择 patch／split／compress／retire／explore，修订提示技能文本。§4.2的 GA→BA-Full（flash）：SOP 16/20→19/20，Lifelong 18/20→17/20，RealFin 18/40→21/40；无重复试验误差条。采用固定阈值，未比较竞争修订的反事实效果；增量成本只计补救，§4.4另给累计值。**它直接覆盖原 N01 的选择框架。**

## 只保留一个可否定的问题

**有限探测预算下，执行哪些对照，才能区分实现错误与适用范围错误，并选到对未见场景损害最小的修订？**

学习对象可为“修订 × 关系上下文”的效果模型。失败后提出改程序、改条件、拆分候选；在有效场景副本上执行竞争修订，依据结果更新预测。探测选择目标是降低最终修订的预期选择损失，而非仅选分歧最大处；最终兼顾任务覆盖、误放行、旧任务退化和库复杂度，证据不足则保留未知。

例如旋转墙布窗失败，轴向实现错误与宿主表示不支持可能需要不同处理。但这只是示例，必须先确认真实失败族存在。主动试验、CEGIS和贝叶斯决策本身都已有；本轮未见完整实证覆盖，也**尚未证明这是新算法**。

## 最小判别实验与投入

先用3个原语已支持的技能族、24–48个有效开发场景诊断。固定模型、候选池、检查器及全部调用预算，对照：LearnAct式候选更新＋通用生成测试；Bayesian-Agent式条件后验阈值；固定程序只学条件；每例拆一技能。交叉消融主动／随机有效探测，以及只改代码／允许联合修订。

按建筑来源隔离，再留出关系组合。测全部任务联合成功、覆盖、误接受／拒绝、负迁移及学习加执行总成本。高预算穷举只作开发诊断上界，检查少量探测选错修订的频率。若同预算通用测试一样好、收益来自更多拒绝或逐例存库，停止独立创新主张。



---

# N08 聚焦核查：暂不保留为独立 AI 主线

2026-09-15。复核四篇新近邻的原始方法、实验与局限，另沿用已读 DST；未运行实验或修改系统。

**判断：当前 N08 没有足够独立的方法新意。** “相关性不等于效用”“知识有协同/干扰”“以结果训练组合选择器”均已有直接研究。把 reward 换成 IFC 执行正确率、加两两交互项或套 contextual bandit，主要是迁移应用。它可能改善 Demo，但还不能作为 AI 方法贡献。

## 最强碰撞

| 原始来源与读取位置 | 学习对象、实验及边界 |
|---|---|
| [PURPLE：Optimizing User Profiles via Contextual Bandits for Retrieval-Augmented LLM Personalization](https://arxiv.org/html/2601.12078v1)，2026 v1，§3–5、Limitations、附录 D | 冻结 LLM，训练集合感知重排器；Transformer 建模条目依赖，Plackett–Luce 采样，每例 32 个组合，以参考回答似然作奖励。九种个性化任务，候选 20 选 5，三种生成模型；多数设置三次，GPT-5-nano 排序基线单次，各任务绝对分母未明列。**非加性、非单调效用及集合监督已直接覆盖**；但各任务分别训练，未测跨任务/域迁移，并非执行正确性实验。 |
| [DearICL：Data Efficient Sample Selection for In-Context Learning](https://arxiv.org/html/2609.06670v1)，2026-09 v1，§3–5、§8、附录 B/E | 学非线性“查询＋示例子集→收益”代理；gap-index 主动试边界组合，测试时直接排序。GSM8K 1319、AquaRAT 254；WMT19 分母含糊。主模型 Llama3.2-3B、5-shot；GSM8K 75.66% 对动态 CASE 70.00%。**学组合交互、选择新题上下文、减少试样成本均已有**。奖励是参考答案 BERTScore；理论界有代理偏差等条件，仅覆盖已访问候选池，不是全部子集保证。 |
| [CAMAB：Context Attribution with Multi-Armed Bandit Optimization](https://arxiv.org/html/2506.19977v1)，2025 v1，§3–4、Limitations | Thompson Sampling 选择上下文掩码，以原回答的归一化 token 似然归因。SST2/HotpotQA 各抽 500、两模型，比较 SHAP、ContextCite、leave-one-out 及 20/40/60 查询预算。**按干预收益选择下一次试验也已有**。此版假设加性；解释原回答不等于使回答正确，不能与后续正式版混写。 |
| [EvoR：Evolving Retrieval for Code Generation](https://aclanthology.org/2024.findings-emnlp.143.pdf)，EMNLP Findings 2024，§2–4、表 1–4、§7 | 执行结果同时更新检索查询、代码/错误知识库，不训练重排器。四集分别 142/45/107/113 题，共 407；模拟 SciPy/TensorFlow 更新及 Ring/Pony，两生成模型。表 4 已有执行反馈、代码、文档的单独/两两/三者组合消融。**执行驱动知识组合不是空白**；无异常仅作为语法正确信号，最多 30 轮，存在延迟成本。 |
| [DST：Design-Specification Tiling for ICL-based CAD Code Generation](https://arxiv.org/html/2603.12712v1)，2026 v1，§2–4、附录 B/E/F | 多粒度文本覆盖＋submodular 贪心选示例；900 测试、三模型、主表 5-shot。hard 有效率未超过各模型最强对照。它不学执行交互，但已覆盖“互补建模知识选择”；其近似保证针对文本覆盖，不能移作真实执行保证。 |

## 只保留一个小诊断

**学习对象若要改变，应是可迁移的条件化交互，而非记住哪几篇文档分数高。** 例如“坐标规则 A＋宿主绑定规则 B”在哪种接口行为下互补，何时与旧版示例 C 冲突；用公开逐项执行检查形成效果签名，验证它能否跨文案、标识符和 API 表面变化预测帮助/干扰。这是待证问题，也可能应并入 N01 的适用条件研究。

先做 A/B 四条件面板，等 token 替换缺失片段、随机顺序、多种子；加入无交互与误导案例，按操作族留出。强对照为混合检索＋普通重排、DST、相同开发反馈训练的单条效用模型，以及 PURPLE/DearICL 式集合模型。不能只胜过 BM25。测试不用隐藏答案选上下文；报告整任务成功、关系错误、所有尝试及学习成本。

**停止条件：** 若交互随换文案消失、不能预测未见操作，或标准集合模型在同等数据/预算下相当，舍弃独立 N08；小规模正结果只支持继续研究。



---

# N06 补查：空间澄清能否成为 AI 方法

核查 2026-09-15。结论：普通“执行分歧→提问”、信息增益选问题、预期损失决定是否问、CAD 澄清后生成均已有直接先例。只把问题换成空间图片不足以成为方法论文；以下剩余方向只是研究假设。

| 近邻原文与阅读位置 | 方法、实验及对候选的影响 |
|---|---|
| [ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification](https://linshi-website.github.io/paper/ClarifyGPT.pdf)，FSE 2024，§3–5、Tables 3–4 | 多程序采样、生成/变异测试、执行结果聚类，再用不同簇的程序生成问题。10 人反馈实验；正式版自动评价覆盖五个基准，与早期四基准版本不能混用。直接覆盖“执行差异发现歧义”；模型自身错误也可能产生分歧。 |
| [Active Task Disambiguation with LLMs](https://arxiv.org/html/2502.04485v1)，ICLR 2025 作者 v1，§2–5、Appendix E/F | 从候选解估计问题的信息增益，并扣提问成本。代码实验从 5 个问题选一个，最多 4 轮，按候选程序执行结果分割解空间；HumanEval 表为 48 题、APPS 表为 47 题，正文有统一写 48 的不一致。查询选择本身需更多 LLM 调用，作者将它视为相对用户反馈便宜。用户错误与“不知道”没有纳入主要模型。直接覆盖“执行候选＋信息增益”。 |
| [Clarify Before You Draw: Proactive Agents for Robust Text-to-CAD Generation](https://arxiv.org/html/2602.03045v1)，2026 预印本，§3、5.2、6.3、Table 4/7 | ProCAD 对澄清器和代码器分别 SFT，先收集一批问题，下一轮接受修订规格；§3 已写几何质量和沟通成本目标，实际训练为轨迹 SFT。Table 7 的 2,469 测试包含 1,000 清晰、1,065 缺维度、404 冲突提示，不能全称歧义测试。用 GPT-5-mini 模拟回答并以另一模型检查迁移；同代码器对照可分离部分澄清收益。固定两轮与正确回答假设限制真实交互结论。 |
| [LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation](https://arxiv.org/html/2404.10100v1)，2024 作者 v1，§IV–VII、Table III | TiCoder 按测试的区分能力提问并剪枝/排序代码；15 人、3 题的用户实验另于 MBPP 427 / HumanEval 164 自动实验。通过/失败式反馈下判断正确性较好，但时间差未显著；不同反馈形式出现不同误答。已覆盖用户认知负担、测试驱动意图与可执行反馈，不能声称此前只测代码正确率。 |
| [Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication](https://arxiv.org/html/2602.02843v1)，2026 作者 v1，Experiments、Computational Model、Discussion | 以 expected regret / 信息价值解释澄清。第一实验 125 人；第二实验招 120 人、排除 2 人，研究不确定程度与错误代价。是语言/行为实验，非 CAD 执行算法；但“预计返工损失高才问”的抽象思想已被覆盖，不能当新理论。 |

## 剩余值得诊断的具体问题

**用户能否可靠回答，比问题理论上能区分多少候选同样重要。** 在几何相似但宿主/楼层关系不同的候选中，单纯最大化分歧可能给出用户无法判断的图；文本歧义和模型编程错误也可能混在一起。

一个候选机制：先用公开确定性检查剔除实现错误，保留满足已知要求的可执行解释；在同一局部场景只改变一个有后果的绑定或参数，生成可比较的结果。由开发用户数据估计问题/视图的误答与“不确定”概率，选择预计能减少最终意图错误、而且容易回答的问题；保留“都不是”和自由补充。算法学习的是问题价值/回答噪声，不是训练基础模型会画 IFC。图形界面只提供相同的候选呈现条件。

**创新仍不确定。** 噪声下主动学习与风险决策本身不新；必须证实从可执行关系差异构造问题并估计回答可靠性，比通用熵、风险加权或语言可回答性评分有增益。未穷尽所有 noisy-oracle active learning，不能写首次。

**关键实验。** 相同候选池、模型、工具和总预算，比较通用澄清、ClarifyGPT/TiCoder 式执行分歧、ATD 信息增益、成本加权信息增益、候选策略；再做策略×呈现（文字/相同局部预览）析因，避免图形界面解释全部收益。单独报告无歧义误问、编程错误误判成歧义、意图错误、回答时间、误答与全部计算成本。模拟用户仅调试；小规模真人先导估方差，正式人数按效应量设计。

**工程依赖。** 需要多候选 Brief/局部方案、差异绑定与条件检查、并排预览和接受/拒绝/不确定回传、独立意图评价及用户数据。已有渲染与 resume 能复用，但不能视为上述策略已存在；最终估时以代码核查为准。


---

# 三候选的代码可行性核查

2026-09-15；当前 `codex/workflow-dataset-links`，工作树已有他人改动。已读 takeover、文档入口、STATE/PROJECT/ROADMAP 与 Agent evaluation 协议；仅检查相关代码/测试源文件，未运行测试、Provider 或修改实现。以下“缺少”限本次检查路径，工期为估计。

**仅按工程易做程度：N08、N06、N01。结合文献后，N08 不作为独立 AI 主线；研究选择与工程排序不同。**

| 候选 | 可复用证据与必须新增的组件 | 最小诊断／公平原型（人周） |
|---|---|---|
| **N01 技能适用性学习** | Repair 的 [OperationDefinition](<E:/code for project/bimnet/src/text2ifc_ifc_repair/registry.py:39>)已有参数、前后条件、应用/比较钩子；Generation 的 [canonical_changeset_json](<E:/code for project/bimnet/src/text2ifc_agent/changesets.py:61>)能序列化操作，[apply_changeset](<E:/code for project/bimnet/src/text2ifc_agent/changeset_apply.py:19>)支持副本执行、修订与范围保全。[SessionStore.record_payload](<E:/code for project/bimnet/src/text2ifc_agent/session_store.py:222>)持久化调用/门禁/指标；这些是固定操作和运行记录，尚非跨任务技能库。需新增参数化宏表示、ID/坐标重绑定、适用性标签、检索/选择器、版本化存储及失败反例。已有 ChangeSet 绑定不可原样跨模型复用。 | **1–2／6–9**。先选 3–5 类固定宏，用已授权 Development 中间产物离线重放，查跨布局成功/失败；公平原型保留底层权限相同的无宏对照，固定规则/相似度/学习选择共享同一宏库。风险：把答案模板记忆误认为适用性学习；训练/测试布局泄漏。 |
| **N08 知识执行价值选择** | [build_authoring_contract](<E:/code for project/bimnet/src/text2ifc_agent/authoring_contract.py:20>)已从校验 registry 投影合法字段，含局部坐标/洞口编码与源哈希；[select_changeset_context](<E:/code for project/bimnet/src/text2ifc_agent/changeset_context.py:9>)按 scope/package 选类和示例。Repair 的 [PropertyKnowledgeRuntime.retrieve](<E:/code for project/bimnet/src/text2ifc_knowledge/property_runtime.py:119>)已有适用性过滤、向量排序与版本化候选，但用途是属性身份，不能直接等同 Generation 知识。需新增知识片段目录、插拔选择策略、执行收益监督和配对实验器。 | **0.5–1／3–5**。先对 20–30 个 Development 失败做错误—知识对应及片段覆盖诊断；效果仍须配对模型实验。随后同模型比较全量、随机、规则/相关性、学习选择，匹配 token 和重试预算。风险：知识与工具能力同时改变、利用测试失败选知识、少提供知识导致少生成而虚增通过率。 |
| **N06 可执行空间澄清** | [run_design_brief_clarification_loop](<E:/code for project/bimnet/src/text2ifc_agent/interactive_cli_flow.py:396>)已有持久化问答/恢复；Repair [_clarification](<E:/code for project/bimnet/src/text2ifc_ifc_repair/api.py:934>)候选含位置/尺寸/选择 token。[render](<E:/code for project/bimnet/scripts/presentation/render_ifc_review.py:14>)能把重开 IFC 网格输出交互页面。尚未见“多个空间意图→隔离编译预览→用户选择→绑定恢复”的完整机制；需新增候选假设合同、生成/去重、只读预览与选择失效检查。 | **1–2／5–8**。先做 10–20 个方向/宿主/房间关系歧义案例，离线验证候选确实可执行且选择能恢复；公平原型比较不问、文字问、空间预览问，匹配候选信息量/交互预算并引入独立意图标签。风险：渲染能力超出实际可执行语义；视觉偏好、诱导选项与额外信息混淆效果。 |

实验接缝已具备：[run_candidate_gate_stage](<E:/code for project/bimnet/src/text2ifc_agent/live_pipeline.py:1586>)落盘编译、重开、几何和门禁结果；[GenerationBudget.reserve/settle](<E:/code for project/bimnet/src/text2ifc_agent/generation_budget.py:118>)累计调用、失败、token 与时间，未知 usage 保留预留量，不能当实测 token。读到的回归包括 [ChangeSet 副本保全](<E:/code for project/bimnet/tests/agent/test_phase6_5_changeset_apply.py:93>)、[上下文选择](<E:/code for project/bimnet/tests/agent/test_changeset_context_selection.py:12>)与[恢复](<E:/code for project/bimnet/tests/agent/test_clarification_resume_preservation.py:10>)；本次没有确认其当前通过状态。

**独立意图 oracle 尚不足。** [build_expected_facts](<E:/code for project/bimnet/src/text2ifc_agent/expected_facts.py:30>)源于 Brief；[evaluate_semantic_coverage](<E:/code for project/bimnet/src/text2ifc_agent/semantic_coverage.py:645>)按能力目录标记事实，candidate 仅用于计数，不能证明逐事实满足。其后虽有关系/几何门禁，仍可能共同漏掉 Brief 的误解。[Repair evaluate_benchmark](<E:/code for project/bimnet/src/text2ifc_ifc_repair/benchmark_evaluation.py:150>)有私有原始模型/映射边界，但不等于开放布局意图真值。三候选都需独立人工标注的请求约束或预先构造的隐藏意图，允许多个满足约束的布局，冻结评分器并分组隔离。工期按熟悉仓库的工程师估计，含小型标注与离线接入，不含大规模语料、训练算力等待或正式用户研究；真实实验另须符合[阶段准入协议](<E:/code for project/bimnet/docs/validation/agent-capability-evaluation.md:223>)。
