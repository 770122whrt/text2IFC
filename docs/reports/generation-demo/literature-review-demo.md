# text2IFC Generation 文献综述：论文正文短版

> **历史材料，2026-09-16已整合。** 当前方向与实验统一见[研究方案](research-plan.md)，文献统一见[简版](literature-review-short.md)和[完整版](literature-review-full.md)。下文保留调查时的结论与编号，不再作为当前优先级。

更新：2026-09-15。本文用于论文初稿；论文事实、我们的判断和待验证主张分开表述。

本页是供短篇论文使用的早期压缩稿，不承担完整选题调研。最新方法、实验和边界见 [论文矩阵及逐篇证据](paper-matrix.md)，选题见 [研究主线草案](research-proposal.md)。当前选题仍在讨论，以下自我定位段落须随最终方法修改。

## 1. 文献综述正文

自然语言生成 BIM 已有多条路线。Text2BIM 通过多个 Agent 生成建模代码，并结合规则检查反复改善模型；Text2MBL 将模块化建筑布局表示为分层建模动作，生成可执行的 BIM 代码。因此，自然语言输入、多 Agent、分层表示与反馈循环都已有先例。[Text2BIM](https://doi.org/10.1061/JCCEE5.CPENG-6386)、[Text2MBL](https://proceedings.neurips.cc/paper_files/paper/2025/hash/61a3e68eb9059ccacdde0bb84870b80e-Abstract-Conference.html)

面向 IFC，MCP4IFC / IFC-Copilot 提供参数化工具、动态代码和执行反馈，支持查询、创建与修改。Self-Verification 则在生成前提取 IDS 与非 IDS 要求，再根据验证结果修订 IFC。这些工作已经覆盖“先明确要求，再生成、检查和纠错”的基本流程。[IFC-Copilot](https://show2instruct.github.io/ifc-copilot/)、[Self-Verification](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)

验证也需要超出文件能否打开。BIM-Edit 分别评价编辑后的几何、语义和拓扑；BIBIMBAP 用原子 CRUD 任务检查具体操作。这两类基准可帮助设计局部能力评估，但不能直接当作完整建筑生成的测试集。[BIM-Edit](https://arxiv.org/html/2606.20146v3)、[BIBIMBAP](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)

本文据此将 text2IFC 的重点放在生成过程的状态管理：明确每一步允许创建或修改的内容，保留可追踪的版本，并检查最终 IFC。需要进一步回答的是：这些约束能否减少后续生成或修订对已有正确结果的破坏，同时保持任务完成能力。这是待验证的研究问题，不是本次综述已经证明的性能优势。

## 2. 英文 Related Work 初稿

以下三段可作为短篇 Demo paper 的起点；不包含未完成的实验结果。

Natural-language BIM authoring has been explored through multi-agent code generation and structured modeling actions. Text2BIM combines BIM authoring APIs with rule-based checking and iterative refinement, while Text2MBL generates executable code for hierarchical modular layouts. MCP4IFC, continued as IFC-Copilot, provides tools and dynamic code execution for IFC querying, creation, and editing. These studies establish language-driven BIM authoring and feedback loops as existing capabilities. [Text2BIM](https://doi.org/10.1061/JCCEE5.CPENG-6386), [Text2MBL](https://proceedings.neurips.cc/paper_files/paper/2025/hash/61a3e68eb9059ccacdde0bb84870b80e-Abstract-Conference.html), [IFC-Copilot](https://show2instruct.github.io/ifc-copilot/)

Verification is also an established component of this workflow. The Self-Verification framework derives task-specific specifications before IFC generation and combines IDS checks with programmatic verification. BIM-Edit and BIBIMBAP provide complementary evaluations of IFC editing and atomic modeling operations, emphasizing correctness beyond visual plausibility. [Self-Verification](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf), [BIM-Edit](https://arxiv.org/html/2606.20146v3), [BIBIMBAP](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)

Our demonstration focuses on how these capabilities are organized in text2IFC. The system combines requirement-derived expectations, ownership-bounded staged generation, revision-bound correction, and checks on compiled IFC artifacts. It exposes the permitted changes and resulting model versions for inspection. Whether these controls improve completion and preservation over alternative loops remains an empirical question; the demonstration does not claim to introduce verification loops or access-control primitives.

## 3. 最相关的工作与区别

| 工作 | 已经做到什么 | 我们应怎样对待它 |
| --- | --- | --- |
| Text2BIM | 建模代码、多 Agent、规则检查与迭代优化 | 直接基线；不能写“已有工作没有整栋生成或反馈循环” |
| Text2MBL | 模块化布局的分层动作、文本与代码配对数据 | 表示和数据设计近邻；Revit 模块化任务与当前 IFC 流程需做适配 |
| MCP4IFC → IFC-Copilot | 直接操作 IFC 的工具与代码路线 | 按同一项目演进线引用；复现时固定版本 |
| Self-Verification | 生成前规范、双路验证与修订 | 直接覆盖“需求派生验证契约”的宽泛 Claim |
| BIM-Edit / BIBIMBAP | IFC 编辑和原子操作的可执行评估 | 借鉴任务与指标；不把编辑或 CRUD 成绩写成整栋生成成绩 |
| Trestle-Bridge | 栈桥领域的参数规划、依赖组织与自纠错 | 说明受领域规则约束的分阶段建模已有先例；不等同一般建筑生成 |

Trestle-Bridge 的原始论文报告 200 个测试案例，并分析触发后的纠错表现；其研究对象是栈桥参数化建模。本 Demo 不需要复述全部实验数字，但应避免将其描述成没有评估的简单工具演示。[原文](https://link.springer.com/article/10.1186/s44147-026-01130-3)

## 4. 为什么不把 ownership / freeze 当成独立创新

模型工程已有对象、引用和属性级访问控制，也有事务及不可变的历史版本。CodeMEM 研究了迭代代码生成中的遗忘与错误重现。PRISM 进一步提出验证证据驱动的局部修补。因此，权限、版本、回退现象与局部修补本身，都不足以证明本项目新颖。[细粒度模型访问控制](https://doi.org/10.1007/s10270-017-0631-8)、[ChronoSphere](https://doi.org/10.1007/s10270-019-00725-0)、[CodeMEM](https://aclanthology.org/2026.findings-acl.834/)、[PRISM](https://arxiv.org/html/2510.25890v1)

可保留的候选方向是它们在完整 IFC 构造中的具体组合与效果：后续步骤允许改哪里、如何处理关系依赖、何时接受新版本。没有找到完全相同的系统，不等于已经证明这套组合新颖。

## 5. 本次核对及版本勘误

| 调查稿中的内容 | 原始材料核查 | 本组文档采用方式 |
| --- | --- | --- |
| Text2BIM 的“25 prompts / 534 IFC”是不准确说法 | [arXiv v1 §5](https://arxiv.org/html/2408.08054v1) 是 10 prompts × 3 LLMs × 5 次，391 份含中间结果的 IFC；[v2 §6](https://arxiv.org/html/2408.08054v2) 明确是 25 × 3 × 3，534 份 | 两组数均有版本依据；不能互相替换或当作独立建筑数。正式发表信息引用 ASCE，若使用数量则注明对应 arXiv 版本 |
| Text2MBL 已正式发表且有配对数据 | NeurIPS 2025 Main Conference 官方页可核实；[arXiv 方法与实验](https://arxiv.org/html/2509.23713v1) 记载 198 个设计、396 对文本与代码，按设计划分 138/20/40 | 可作为分层生成与配对数据的近邻；代码公开不自动说明数据使用许可已明确 |
| BIM-Edit 数据集页面的行数可以当场景数 | [IFC 页面](https://huggingface.co/datasets/BIM-Edit/BIM-Edit) 的 viewer 只有一条元数据记录；[任务页](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks) 明确有 324 条任务 | 分开记录任务数、文件数与基础场景；不把输入/参考模型的变体当新建筑 |
| 当前 text2IFC 有严格读写/引用隔离 | 当前 `package_gates.py` 允许解析全部已存在 workspace ID；2026-09-14 审核已定位这一边界，本次关键代码仍一致 | 只写已实现的写入所有权、追加阶段保全及局部修订，不写完整引用白名单 |

本轮对新调查的重点补充项核查了正式页面、原文关键章节和公开数据入口；没有复现外部系统的实验，也没有证明所有后端均不存在某种机制。基础机制的详细代码依据见 [仓库审核](../Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md)。

## 6. 引用与代码入口

| 简称 | 论文 | 作者代码 / 项目 |
| --- | --- | --- |
| Text2BIM | [JCCE 40(2), 2026](https://doi.org/10.1061/JCCEE5.CPENG-6386) | [dcy0577/Text2BIM](https://github.com/dcy0577/Text2BIM) |
| Text2MBL | [NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/61a3e68eb9059ccacdde0bb84870b80e-Abstract-Conference.html) | [CI3LAB/Text2MBL](https://github.com/CI3LAB/Text2MBL) |
| MCP4IFC / IFC-Copilot | [MCP4IFC 预印本](https://arxiv.org/abs/2511.05533) | [当前项目](https://show2instruct.github.io/ifc-copilot/)、[新版 bonsai-mcp](https://github.com/Show2Instruct/bonsai-mcp) |
| Self-Verification | [EC3 2026](https://ec-3.org/publication/ec32026_444/) | [Text2BIM-Self-Verification](https://github.com/Tsesterh/Text2BIM-Self-Verification) |
| BIM-Edit | [2026 预印本](https://arxiv.org/abs/2606.20146) | [IFC 数据](https://huggingface.co/datasets/BIM-Edit/BIM-Edit)、[任务](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks) |
| BIBIMBAP | [EC3 2026](https://ec-3.org/publication/ec32026_271/) | 数据获取边界见 [数据说明](../../../dataset/external/GENERATION_DATASETS.md) |

投稿前按目标模板生成正式参考文献；当前页面中出现的 2026 预印本不默认视为某个会议的正式论文。
