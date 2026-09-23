# 逐篇证据：建模抽象、Coding Agent、知识与权限

核查日期：2026-09-15。总入口：[论文矩阵](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/paper-matrix.md)。本文记录实际读到的版本，不把作者报告当作本项目复现结果。

**F**：已取得正文，并核对方法、实验设置/结果和局限相关部分；不表示逐行审计全部补充材料或复现。**P**：仅部分正文、出版信息或项目材料可得；不足以核实完整实验。每张卡的“对本项目”是我们的推论。

<a id="d01"></a>
## D01 — Text2MBL

- **题名/版本：** *Text-to-Code Generation for Modular Building Layouts in Building Information Modeling*；Yinyi Wei、Xiao Li；NeurIPS 2025。**F**，核查 arXiv v1 §3–5、Table 2、Appendix B/C。[正式入口](https://proceedings.neurips.cc/paper_files/paper/2025/hash/61a3e68eb9059ccacdde0bb84870b80e-Abstract-Conference.html)；[全文](https://arxiv.org/html/2509.23713v1)。简称 Text2MBL。
- **方法：** 将模块化建筑组织为 Module、Unit、Room 等 C# / Revit 操作；相对位置、邻接和连接通过接口表达，配合微调及合成训练数据。
- **实验：** 198 个设计、396 个描述；按设计分为 138/20/40，而非把两种描述当独立建筑。比较代码与坐标表示及多种 Qwen2.5 模型；报告编译、实例/参数 F1、IoU。Table 2 的 7B Coder 代码方案 IoU 为 98.43，坐标方案为 84.64。
- **边界：** IoU 基于包围盒，不覆盖全部碰撞、构件顺序和不规则几何；需求较详细、构件族受限，没有用户可用性实验。代码方案同时改变了操作抽象，不能归因为代码语法本身。
- **对本项目：** 可借鉴“任务—表示—数据—消融”的论证；高层关系 API 不能再写成空白。尚无同任务实验证明 text2IFC 更强。

<a id="d02"></a>
## D02 — MCP4IFC

- **版本：** *MCP4IFC*，Nithyanantham 等，2025 预印本。**F**，核查 v1 §3–5、Table 2、附录。[全文](https://arxiv.org/html/2511.05533v1)；[作者仓库](https://github.com/Show2Instruct/ifc-bonsai-mcp)。
- **方法：** IFC 工具、结构化场景信息、文档向量检索与动态 Python/IfcOpenShell 执行组合；已支持问答、编辑和生成。
- **实验：** IFC-bench 的 65 个 Duplex 问题中，Table 2 报告 GPT-5 mini 54/65、Sonnet 4.5 49/65；部分模糊答案按偏乐观方式处理。另有 8 个语义编辑例、6 个生成例及多轮生成展示。
- **边界：** 正文与表格的 direct-query 计数有 26/25 不一致，此处按表。生成例存在洞口、空间包含、材料或 Pset 缺失，不能外推到全部工具。作者已讨论约 40k token 工具定义和动态工具预选；后者在该版本是改进方向。
- **对本项目：** “IFC 原生＋RAG＋代码执行＋循环”已被覆盖。其问答分数不能当整栋生成成功率；也不能据少量生成失败声称所有增强式 Coding Agent 都不可靠。

<a id="d03"></a>
## D03 — IFC-Copilot

- **版本：** 同一作者团队的后续项目。**P：项目正文和仓库可查，论文全文未取得。** [原始项目页](https://show2instruct.github.io/ifc-copilot/)；[新版仓库](https://github.com/Show2Instruct/bonsai-mcp)。
- **已核实：** 项目描述 52 个工具、代码执行以及读/创建/修改任务；页面报告 100 个自定义任务及最高 86% 的项目结果。旧 MCP4IFC 仓库明确链接至新版仓库。
- **缺口：** 项目页实际 Paper 链接 `static/paper/IFC-Copilot.pdf` 在本轮返回 HTTP 404；精确题名搜索未找到替代全文。模型、评测器、失败分母和成本不能仅凭项目页确认。仓库当前版本也不能自动等同于页面实验版本。
- **对本项目：** 必须作为近邻系统保留；按共同作者和仓库演进建立谱系，不能重复算成两套互不相关方法，也不能因全文不可得而判定它没有某项机制。

<a id="d04"></a>
## D04 — ATLAS

- **题名/版本：** *ATLAS: A Layered Constraint-Guided Framework for Structured Artifact Generation in LLM-Assisted MDE*；Tong Ma 等；arXiv v3，2026-04-05。**F**，§3、§4.3–4.5、Tables 3–7。[全文](https://arxiv.org/html/2510.25890v3)。同编号早期版本题名含 PRISM，不能混用版本结果。
- **方法：** ICM 统一元模型及约束；完整结构上下文、JSON Schema/GBNF 约束解码、确定性 ARXML 投影，以及 SHACL/SMT 审核和定向修订。
- **实验：** 固定 32B 模型比较 60 个 AUTOSAR 组件、三种提示详略；多文件实验另用 20 个系统、284 个文件。Table 6 文件完整率/XSD 为 100%，但各复杂度层的系统 SMT 首轮通过率均为 0。
- **边界：** 结构可导入不等于设计逻辑成立；作者明确跨域效果未实证，结果分析也不是独立生产率实验。首轮失败不能证明后续修复永远无效。
- **对本项目：** 这是“领域约束＋编译中间表示＋语义验证”很强的直接先例。候选知识机制必须进一步证明：如何利用具体编译保证减少所需上下文，同时不丢失剩余义务；仅换成 IFC 不足以形成方法创新。

<a id="d05"></a>
## D05 — Fine-grained Access Control for Collaborative Modelling

- **题名：** *Enforcing fine-grained access control for secure collaborative modelling using bidirectional transformations*；Csaba Debreceni、Gábor Bergmann、István Ráth、Dániel Varró；SoSyM，2017 在线发表，后有勘误。**F**，§3–7。[出版商全文](https://link.springer.com/article/10.1007/s10270-017-0631-8)。
- **方法：** 对对象、属性、引用分别授予读写权限；Get 导出过滤视图，PutBack 验证更新。已明确读写依赖、反向引用和 containment 的一致性条件，并讨论/证明受条件约束的 lens 性质。
- **实验：** 风机模型的合成扩展，分别增加模型规模和协作者数量；测在线修改传播和离线提交成本，含重复测量。在线代价主要随受影响视图变化，离线需处理整个模型文件。
- **边界：** 保证的是内部结构及权限一致性，不是所有领域 well-formedness；无序集合是主要适用范围，中央完整模型和规则条件均有假设。
- **对本项目：** 局部读写边界、依赖闭包和提交检查不是 LLM 时代新原语。本文 gold model 指完整共享模型，不能与本项目私有评测 Gold 混为一谈。

<a id="d06"></a>
## D06 — ChronoSphere

- **题名：** *ChronoSphere: a graph-based EMF model repository for IT landscape models*；Martin Haeusler 等；SoSyM，2019。**F**，§3–6、§8。[全文](https://link.springer.com/article/10.1007/s10270-019-00725-0)。
- **方法：** 版本化键值存储、属性图和 EMF 模型三层映射；元模型与实例共同版本化，事务提交产生新版本，支持回滚、分支及依赖查询。
- **实验：** 约 20 万 EObject 的行业专家辅助合成模型；与 Eclipse CDO 比较插入、名称查询、根因和影响分析，预热后重复执行。图遍历较有优势，插入并非始终最快。
- **边界：** CDO 采用 OCL 路线，查询表达能力与索引实现影响差值；作者明确合成数据和运行时威胁。论文使用 snapshot isolation 的论述不应被我们升级为所有并发执行都已证明 serializable。
- **对本项目：** 冻结状态、事务和版本证据属于已有系统机制；它不研究 LLM 如何选上下文或理解建筑意图。可做修订基础的 prior art，不宜当主要生成 baseline。

<a id="d07"></a>
## D07 — CodeMEM

- **题名：** *CodeMEM: AST-Guided Adaptive Memory for Repository-Level Iterative Code Generation*；Peiding Wang 等；Findings of ACL 2026。**F**，§3–5、§7、Table 3。[全文](https://aclanthology.org/2026.findings-acl.834.pdf)。
- **方法：** AST 引导代码记忆选择，签名/轻量描述作索引、实现作内容；保存会话指令与修改，检测被遗忘的要求并触发修订。
- **实验：** CodeIF 的 40 个对话、360 条指令，以及 230 个 Python CoderEval 任务；比较完整上下文检索及多种记忆系统，报告完成质量与消融。
- **边界：** 并非所有设置更省 token。Table 3 中 CodeIF 的 CodeMEM 为 107.8k，低于 FC BM25 131.8k，却高于若干记忆对照；CoderEval 中也高于 FC BM25。长工业仓库和 LLM 选择遗漏仍是限制。
- **对本项目：** “历史保全＋结构化记忆＋按需知识”已有先例；需把成本与成功联合评价，不能只挑一种更贵 baseline 来证明压缩。

<a id="d08"></a>
## D08 — CodeAct

- **题名：** *Executable Code Actions Elicit Better LLM Agents*；Xingyao Wang 等；ICML 2024。**F**，§2–3、Tables 2–5。[正式入口](https://proceedings.mlr.press/v235/wang24h.html)；[全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/wang24h/wang24h.pdf)。
- **方法：** 用可执行 Python 统一工具调用，可组合控制流和中间结果，运行反馈用于多轮纠错；另构造 CodeActInstruct 并微调 7B 模型。
- **实验：** API-Bank 与 82 个 M3ToolEval 任务比较代码、JSON、文本行动格式；另在 MINT 等任务评价微调，区分域内/域外。代码总体有优势，但部分模型/原子调用设置 JSON 更好。
- **边界：** JSON 对照是工具行动格式，不是与高层建模代码表达能力匹配的 BIM JSON 编译器。微调混合训练和提示行动格式实验不能混为一个因果结论。
- **对本项目：** Code Agent 本身及执行反馈都不是创新；不能预设 JSON 比 Python 省 token，需匹配双方循环、复用与相对位置抽象。

<a id="d09"></a>
## D09 — RepoCoder

- **题名：** *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation*；Fengji Zhang 等；EMNLP 2023。**F**，§2–5、局限部分。[全文](https://aclanthology.org/2023.emnlp-main.151.pdf)。
- **方法：** 用未完成代码及前轮预测更新检索查询，循环提供仓库片段；主要检索实现包括滑窗和 Jaccard 相似度。
- **实验：** 正文称 RepoEval：行/API 补全各 1,600，函数补全 373 个；评价匹配和函数测试。GPT-3.5 函数 pass 从 23.32 到一次检索的 38.34、两轮的 42.63，更多轮并非单调提高。
- **边界：** 官网摘要的基准命名与 PDF 有出入，此处按 PDF；低重复仓库、停止时机和在线成本仍有限制。Oracle 上下文仅是分析条件。
- **对本项目：** “检索—生成—再检索”已有明确先例。应比较何时扩展知识有用，而非给所有案例无条件增加 Agent 轮数。

<a id="d10"></a>
## D10 — Repoformer

- **题名：** *Repoformer: Selective Retrieval for Repository-Level Code Completion*；Di Wu 等；ICML 2024。**F**，§3–7、Tables 3–5。[入口](https://proceedings.mlr.press/v235/wu24a.html)；[全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/wu24a/wu24a.pdf)。
- **方法：** 学习是否需要仓库上下文，以特殊 token 和阈值控制检索；联合选择与补全训练。
- **实验：** RepoEval、CrossCodeEval、CrossCodeLongEval，报告匹配、测试和延迟；设置涉及不同模型大小及串行/并行检索。
- **边界：** 最高约 70% 加速不是所有质量点都成立：Table 3 的 1B greedy/API 设置约 69% 加速伴随 edit similarity 下降；较保守阈值收益更小。训练过的选择器也不能当作无训练 plug-in 直接照搬。
- **对本项目：** 何时检索及预算取舍均已有方法研究。我们的候选要额外利用建模接口的保证和关系依赖，而不是只重新实现一个检索开关。

<a id="d11"></a>
## D11 — RepoGraph

- **题名：** *RepoGraph: Enhancing AI Software Engineering with Repository-Level Code Graph*；Siru Ouyang 等；ICLR 2025。**F**，§3–5、Tables 2/4/5。[全文](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf)。
- **方法：** AST 提取定义、引用及包含/调用边，以目标符号检索 k-hop 子图，平铺或总结后接入 Agentless、SWE-agent 等流程。
- **实验：** SWE-bench Lite 300 题及 Python CrossCodeEval；Table 2 的四个基础系统均有成功率增益，**token 和费用也均增加**。Table 4 的 2-hop 平铺反而弱于 1-hop，摘要也不总有利。
- **边界：** 主表 baseline 部分取自公开榜单/轨迹；结果不能证明等 token 条件下的纯算法因果收益。更多依赖信息不保证更好。
- **对本项目：** 依赖图选知识和子图压缩已有直接先例；需要测“遗漏关键关系”与“引入额外上下文”两侧代价，并设置预算匹配对照。

<a id="d12"></a>
## D12 — SWE-agent

- **题名：** *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*；John Yang 等；NeurIPS 2024。**F**，主文 §3–5、§7、Tables 1/3；未逐页审计全部长附录。[全文](https://papers.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf)。
- **方法：** 设计搜索、文件窗口、编辑/linting、历史管理接口，基于工具反馈操作真实仓库。
- **实验：** 完整 SWE-bench 2,294 题及 Lite 300 题，另有 HumanEvalFix；与 shell-only/RAG 比较并消融接口。GPT-4 Turbo 在 Lite 为 18%，shell-only 为 11%；全文件窗口、全历史均不如所选配置。
- **边界：** 主表费用按成功解决实例平均，不能直接与我们全任务成本混算；每题有美元上限，模型和接口版本均固定于当时。
- **对本项目：** “面向 Agent 的专用接口”已有很强发表先例。IFC 的贡献需用任务和实验落实；通用 Coding Agent 必须拥有合理的检索、执行和反馈能力。

<a id="d13"></a>
## D13 — LLMLingua

- **题名：** *LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models*；Huiqiang Jiang 等；EMNLP 2023。**F**，§3–5、Limitations。[全文](https://aclanthology.org/2023.emnlp-main.825.pdf)。
- **方法：** 按提示组成分配预算，以小模型困惑度筛选示例和 token，迭代更新压缩上下文；另做模型分布对齐。
- **实验：** GSM8K、BBH、ShareGPT、Arxiv-March23，分别用答案正确率或文本相似度；含预算、迭代及对齐消融。高压缩率在部分任务保持质量，在 BBH 等也出现明显下降。
- **边界：** 没有证明字段、标识符、数值及 IFC 关系被逐项保全；极高压缩率进一步损失质量。压缩器自身有计算代价。
- **对本项目：** 可作通用文本压缩对照，但应保留公平的不可压缩任务事实区；“低 token”不能替代最终 IFC 的正确性。

<a id="d14"></a>
## D14 — LongLLMLingua

- **题名：** *LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression*；Huiqiang Jiang 等；ACL 2024。**F**，§4–5、Limitation。[全文](https://aclanthology.org/2024.acl-long.91.pdf)。
- **方法：** 问题相关的粗细两级压缩、文档重排、动态预算，以及从原文恢复输出中的压缩实体。
- **实验：** NaturalQuestions、LongBench、ZeroSCROLLS、MuSiQue、LooGLE；对比检索与压缩，检查不同答案位置和组件消融。
- **边界：** 作者明确每个问题重新压缩妨碍上下文复用，相比 LLMLingua 增加压缩计算；复杂隐含依赖可能仍受影响。子串恢复不是一般语义正确性保证。
- **对本项目：** 按任务压缩和关键实体恢复均不能独立声称新颖。需要验证结构化依赖选择相对通用压缩的收益，计入压缩时间与缓存影响。

<a id="d15"></a>
## D15 — Progent

- **题名/版本：** *Progent: Securing AI Agents with Privilege Control*；Tianneng Shi 等；arXiv v3，2026。**F**，§4–5、§8–9。[全文](https://arxiv.org/html/2504.11703v3)。早期版本题名不同。
- **方法：** 对工具及参数执行确定性权限策略；SMT 判断策略是否扩大，区分收窄、扩权和不变量。
- **实验：** AgentDojo/ASB 的任务效用和注入攻击成功率；主体设置即使总是接受扩权，也报告 ASR 分别从 39.9% 到 1.0%、70.3% 到 3.9%。
- **边界：** 防护依赖策略边界和批准行为；文本输出攻击不在主要防护范围。允许操作不等于操作结果满足领域要求。
- **对本项目：** 工具权限、参数约束与受控扩权已有先例；这类证据用于反驳宽泛安全 Claim，不应被当成 IFC 语义可靠性或知识压缩证据。

<a id="d16"></a>
## D16 — MiniScope

- **题名：** *MiniScope*；Jinhao Zhu 等；arXiv v1，2025。**F**，§III–VII。[全文](https://arxiv.org/html/2512.11147v1)。
- **方法：** 从服务权限和 API 方法重建层级，由 ILP 为执行计划选择所需权限，通过会话 token 和调用检查执行。
- **实验：** 10 个真实应用的合成请求，对比 LLM 推断权限；检查配置过权及延迟。用户确认负担采用模拟用户和模拟请求，而非真实参与者实验；运行开销不含用户确认时间。
- **边界：** 最小性相对于给定计划、权限映射及代价定义；资源级参数限制主要作为更细粒度方向讨论。
- **对本项目：** 集合覆盖/优化“足够且尽量少”不是新思想，权限预算也不同于 token 预算。不能借其形式化表达替代我们的建模正确性证明。

<a id="d17"></a>
## D17 — AuthBench

- **题名/版本：** *Do Coding Agents Understand Least-Privilege Authorization?*；Zheng Yan 等；arXiv v2，2026。**F**，§3–7。[全文](https://arxiv.org/html/2605.14859v2)。
- **方法：** 评测读/写/执行权限推断；提出先确保任务充分性、再审核收窄的两阶段策略。
- **实验：** 120 个终端任务，80 常规、40 敏感；用安全参考轨迹和 strace 辅助标注，固定执行 Agent 比较不同权限生成模型。同时测权限匹配、执行成功和安全暴露；增加推理并不一致地改善两侧错误。
- **边界：** 参考权限是一个安全工作流的代理，作者明确不等同唯一最小权限；最终是否足够仍依赖执行 Agent。静态匹配不能替代任务执行。
- **对本项目：** “先覆盖义务、再压缩”已有概念近邻；我们的机制必须给出 IFC 知识和编译契约的具体不同，而不是只将权限换成上下文。

<a id="d18"></a>
## D18 — Agentless

- **正式题名：** *Demystifying LLM-Based Software Engineering Agents*；Chunqiu Steven Xia 等；FSE 2025。**F**，§3–7、Tables 1/4/6。[作者全文](https://lingming.cs.illinois.edu/publications/fse2025.pdf)。
- **方法：** 分层定位文件/代码片段，采样 Search/Replace 补丁，再用现有回归测试和生成的复现测试筛选。流程明确，但不依赖自由探索 Agent。
- **实验：** 主文 Lite 为 96/300（32%）、均费约 0.70 美元；默认每题 40 个补丁与 40 个测试候选。脚注说明直接采用 benchmark 的 PASS_TO_PASS 列表可达 98；因此不同入口的 98/32.67% 不可与正文混用。
- **边界：** 与公开榜单对比存在系统/模型差异；测试泄漏、基准范围及测试覆盖仍有限制。多候选最佳值不同于最终提交成功率。
- **对本项目：** 更复杂的 Agent loop 并非天然更优。应加入固定生成—验证流程对照，并避免让独立评分器变成生成系统可反复试探的答案接口。

<a id="d19"></a>
## D19 — RepairAgent

- **题名/版本：** *RepairAgent: An Autonomous, LLM-Based Agent for Program Repair*；Islem Bouzenia、Premkumar Devanbu、Michael Pradel；arXiv v2，2024-10-28。**F**，§III–VI。[全文](https://arxiv.org/html/2403.17134v2)。
- **方法：** 状态机指导可用工具，动态提示保存故障假设、代码信息和测试反馈；Agent 可在理解、检索和修补阶段间切换。
- **实验：** Defects4J 全部 835 个故障，另抽样 100 个较新 GitBug-Java 故障；区分测试通过补丁与人工判断正确补丁。报告正确修复 164 个；真实故障定位消融降低效果并增加成本。
- **边界：** 需要故障揭示测试，定位质量影响结论。摘要称 270k token 为 average，§V-C 称 median；本材料标记不一致，不采用为可靠均值，2024 价格也不当当前成本。
- **对本项目：** Repair＋Agent＋记忆＋执行反馈早有先例。IFC Repair 的价值要落到模型关系、几何和未受影响内容的保全，并与独立 Generation 的效果分别归因。

<a id="d20"></a>
## D20 — PAFT

- **题名/版本：** *PAFT: Preservation-Aware Fine-Tuning for Minimal-Edit Program Repair*；Boyang Yang 等；arXiv v1，2026。**F**，§3–7、Tables 7–10。[全文](https://arxiv.org/html/2604.03113v1)。
- **方法：** 对齐 buggy/fixed token，提高稳定片段训练权重，组合全序列监督和按修改难度安排的课程；使用 QLoRA。
- **实验：** 1,535 个训练对、三种微调 backbone，测试 Java 修复；同时报告测试通过率、编辑距离和复制比例，另有人评。主对照中 SFT 与 PAFT 的监督 mask 也不同，§5.4 提供拆分消融。
- **边界：** 修改量指标主要在 plausible patch 子集计算；通过测试不等于语义完全正确。作者限制于单文件 Java 场景，不能外推跨文件保全。
- **对本项目：** 最小编辑与保全已经是研究方向，不能把“少改 IFC”单独包装成新目标。几何/属性/关系保全需独立于文本 diff 评价。

<a id="d21"></a>
## D21 — MAS4SysML

- **题名：** *MAS4SysML: A Multi-Agent Framework for SysML v2 Model Generation from Natural Language*；Yuhao Liu、Junjie Hou、Haolong Zhang、Zhiang Lu；JoVE，2026-05-19，DOI 10.3791/70395。**P：方法和实验设置可读，主要结果表受限。** [原始正文页](https://www.jove.com/t/70395/mas4sysml-multi-agent-framework-for-sysml-v2-model-generation-from)。
- **已读方法：** task card 含 ID、依赖、目标、约束、参数和预期输出；自底向上生成、官方语法验证、有限修复，以及按任务卡语义验证。
- **已读实验设置：** 五类视图各 15 个，共 75 个作者建模实例；描述由 GPT-4o 起草并人工审阅；修复预算 3 次；以语法错误、语义覆盖和人工评分评价。
- **缺口：** 原始英文 Results 和 Discussion 的关键内容显示访问受限，表格与完整比较未核实，摘要 2.63/0.91 不收入已证实成绩。普通 HTML 入口内容为空，搜索可返回出版商开放段落。
- **对本项目：** 足以确认任务卡、依赖排序、语法/语义双验证已有先例；不足以确认其全部效果。原文明确不声称一次生成严格跨视图一致的完整系统，不能反过来表述为它没有结构约束。

## 本组形成的约束

“接口、检索、循环、验证、保全、权限、压缩”都存在可定位的先例。值得继续测试的窄问题是：**同一空间任务中，编译器承担了哪些义务，这会如何改变 Agent 必需的知识上下文，以及预算下的最终模型正确率？** 这是待验证问题，尚不是已排除所有先例的算法新颖性结论。
