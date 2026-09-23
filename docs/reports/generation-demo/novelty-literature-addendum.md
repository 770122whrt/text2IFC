# 方法创新扩展调研：论文矩阵与决策记录

> **历史材料，2026-09-16已整合。** 当前方向与实验统一见[研究方案](research-plan.md)，文献统一见[简版](literature-review-short.md)和[完整版](literature-review-full.md)。下文保留调查时的结论与编号，不再作为当前优先级。

核查截止：2026-09-15。目的：寻找现有模型与 text2IFC 基础上可尝试的方法创新，范围覆盖知识利用、技能学习、程序综合、空间规划、澄清与几何一致性。

本轮为**有针对性的广泛探索**：检索原始论文并追查最近机制和经典先例，不是宣称穷尽的系统综述。没有只凭摘要判定新颖性，也不把别人的评测缺陷当成其方法不存在。论文全文可读不等于代码/数据可复现。

## 1. 范围、证据与计数

| 材料 | 正文证据卡 F | 说明 |
|---|---:|---|
| [知识利用](literature-evidence/frontier-knowledge.md) | 9 | FK01–FK09 |
| [技能与程序学习](literature-evidence/frontier-skills.md) | 15 | SK01–SK15；另回查原矩阵 Cobbie，不计新卡 |
| [空间规划与生成](literature-evidence/frontier-spatial.md) | 9 | FSP01–FSP09 |
| [规格、关系与一致性](literature-evidence/frontier-reasoning.md) | 8 | FR01–FR08 |
| **本轮合计** | **41 张卡 / 40 篇不同论文** | ExpeL 在两个专题读了不同版本，合并计一篇 |

另保留 **1 条 P 线索**：DepthBenchCAD，见文末。CoLLAs 2023 关系状态抽象已完成补核，新增 SK15，并据此下调 N02 的宽泛表述。AIDL 正式版未取得全文，但其 v1 正文已读；这是同一论文的版本缺口，不另加一篇 P。原 [63 条矩阵](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/paper-matrix.md) 的 49 F / 14 P 保持原范围，不用这次新材料偷偷补齐旧的全文缺口。

**F 的定义：** 取得指定原始正文，读到方法、实验及有关限制，不表示读完每个附录或完成复现。各卡给出原始链接、读取节号/版本、作者报告的分母和限制；没有披露的数字明确留空或标未知。表格短行只是索引。

## 2. 知识如何被使用，而不只是被检索

| 卡 / 论文 | 方法已做到什么 | 实验证据及应保留的边界 | 对候选的约束 |
|---|---|---|---|
| [FK01 HippoRAG 2](literature-evidence/frontier-knowledge.md#fk01) | 三元组、段落节点与图传播检索 | 多套 QA；语料分批增长仍有干扰退化 | N08 不能只做关系图 RAG |
| [FK02 ACE](literature-evidence/frontier-knowledge.md#fk02) | 经验条目增量更新、反思与去重 | 在线/离线适配；无可靠反馈时可负迁移 | N01/N03 不能仅加错误本 |
| [FK03 CRAFT](literature-evidence/frontier-knowledge.md#fk03) | 生成、抽象、验证、检索工具 | 三任务域；建库/执行模型不同，部分简单检索更好 | N02 需超过成功代码工具化 |
| [FK04 ExpeL](literature-evidence/frontier-knowledge.md#fk04) | 成败对比提炼经验，跨任务复用 | 正式版四折；所读位置未明确全部绝对分母 | N03 的直接先例；与 SK02 合并计数 |
| [FK05 SePer](literature-evidence/frontier-knowledge.md#fk05) | 用正确答案信念变化评价检索效用 | 依赖参考答案；不是可直接部署的无标签策略 | N08 不能把测试 Gold 当效用反馈 |
| [FK06 CF-RAG](literature-evidence/frontier-knowledge.md#fk06) | 反事实查询、对照证据与候选评分 | 多候选/多查询；Smart EM 与标准 EM 有区别 | N05 不因“反事实”一词获得新意 |
| [FK07 ToolChoiceConfusion / CMTF](literature-evidence/frontier-knowledge.md#fk07) | 已知前后条件图的最短路径与逐步工具筛选 | 102 任务×6 策略×4 模型，全部 mock 执行 | “最小必要工具/知识”已有直接先例 |
| [FK08 LLM-Wiki](literature-evidence/frontier-knowledge.md#fk08) | 知识编译、遍历、错误本与持续修补 | 三套 QA 各 500，15 工具调用上限 | N03/N08 不能只加可组合知识库 |
| [FK09 Design-Specification Tiling / DST](literature-evidence/frontier-knowledge.md#fk09) | 多粒度设计说明覆盖与贪心示例选择 | 900 测试，5-shot；几何评价允许 GT 对齐与缩放 | N08 的强近邻；覆盖保证不等于执行保证 |

## 3. 固定模型怎样学会使用和创造技能

| 卡 / 论文 | 方法已做到什么 | 实验证据及应保留的边界 | 对候选的约束 |
|---|---|---|---|
| [SK01 Voyager](literature-evidence/frontier-skills.md#sk01) | 课程、执行反馈、可复用代码技能库 | 探索三次运行；迁移仅四任务×三次 | 冻结 LLM＋技能库已有 |
| [SK02 ExpeL](literature-evidence/frontier-skills.md#sk02) | 正负经验归纳、检索和迁移 | v2 补充读取任务数/划分；不与正式版数字混用 | 同 FK04，两个阅读卡而非两篇论文 |
| [SK03 LILO](literature-evidence/frontier-skills.md#sk03) | 程序库压缩、语义重写、命名和说明 | 三域、三种子；有冻结库后的独立求解 | N02 要比真正的程序抽象，而非去重 |
| [SK04 LearnAct](literature-evidence/frontier-skills.md#sk04) | 失败后选代码或说明更新 | 每类三训练任务；有代码/注释消融和过拟合 | N01 最接近的强对照之一 |
| [SK05 SkillWeaver](literature-evidence/frontier-skills.md#sk05) | 技能合成、参数测试、调试、前提过滤 | 812 WebArena＋57 真网站任务；预探索有成本 | 加合同/测试本身不足为新 |
| [SK06 PolySkill](literature-evidence/frontier-skills.md#sk06) | 抽象目标与多种实现分离 | 跨网站允许新适配；效率只统计成功轨迹 | N01/N02 不能只强调多态与迁移 |
| [SK07 Memento-Skills](literature-evidence/frontier-skills.md#sk07) | 外部技能修订、创建和重组 | GAIA/HLE 子集；路由器另有训练 | 固定基础 LLM 不等于全系统无训练 |
| [SK08 Contract2Tool](literature-evidence/frontier-skills.md#sk08) | 从文档/轨迹学习前后条件并选工具 | 100 合成工具、102 任务；成功模拟轨迹为主 | N01/N05 不能仅学条件后筛工具 |
| [SK09 SLBench](literature-evidence/frontier-skills.md#sk09) | 评价前后条件、例外、回退等技能逻辑 | 人工审计核心 86 例；11 例缓解不等于全体增益 | 逻辑关系遵循已有专门基准 |
| [SK10 DreamCoder](literature-evidence/frontier-skills.md#sk10) | 程序抽象、库学习和搜索指导 | 多域实验；部分预算较大 | N02 面对成熟程序综合路线 |
| [SK11 Epistemic Exploration](literature-evidence/frontier-skills.md#sk11) | 构造区分性探测，学习行动前提/效果 | 四规划域、多种子；固定谓词空间 | N01/N05 主动探测本身也不新 |
| [SK12 ToolMaker](literature-evidence/frontier-skills.md#sk12) | 建环境、写工具、执行调试 | 15 工具任务；成功率与成本都更高 | 按任务自动造工具已有 |
| [SK13 CREATOR](literature-evidence/frontier-skills.md#sk13) | 抽象工具和实例调用分离，执行修正 | 数学/表格的筛选子集与 Creation Challenge | 先造小工具再组合已有 |
| [SK14 AdaPlanner](literature-evidence/frontier-skills.md#sk14) | 子目标断言、反馈改计划、中途恢复、记忆 | ALFWorld 134；MiniWoB++ 有专家示例 | Agent loop 与恢复不是贡献本身 |
| [SK15 Embodied Active Learning of Relational State Abstractions](literature-evidence/frontier-skills.md#sk15) | 效果分组、对象角色、前提及参数采样器学习 | 三域；每域 50 示范/50 留出、1,000 探索转换、10 种子 | N02 的效果/角色抽象已有直接先例；仅保留新宏程序修订假设 |

原 [B12 Cobbie](literature-evidence/ifc-evaluation.md#b12) 本轮在技能证据中回查：自动工具生成/调试在 IFC 问答已有实现，且不总有收益。它不等于 IFC 生成方法，但足以反驳“多造工具自然扩展能力”的推断。

## 4. 空间表示、约束和可编辑生成

| 卡 / 论文 | 方法已做到什么 | 实验证据及应保留的边界 | 对候选的约束 |
|---|---|---|---|
| [FSP01 CIT-CAD](literature-evidence/frontier-spatial.md#fsp01) | 意图树、AST/几何检查、失败定位、保持已满足约束 | 26,783 筛选条目；CIT 同源检查、预算/分母需辨别 | 不能再把意图树＋保全修复作为新主线 |
| [FSP02 HistCAD](literature-evidence/frontier-spatial.md#fsp02) | 紧凑历史序列、显式约束、编辑保持 | 170,236 序列；参考回放与训练生成结果分开 | 压缩＋约束保持已有量化先例 |
| [FSP03 EPICCAD](literature-evidence/frontier-spatial.md#fsp03) | 平展表示、前端恢复与显式约束 | 约 129K 共同形状；编辑主要定性；资源需申请 | 与 HistCAD 不同作者，不能合并结果 |
| [FSP04 CAD-Factory](literature-evidence/frontier-spatial.md#fsp04) | AST 结构/参数分离、多角色生成与反馈 | 专门预训练/微调；文本测试精确分母未重建 | 结构先行/Agent 分工已有，训练另算 |
| [FSP05 AIDL](literature-evidence/frontier-spatial.md#fsp05) | 层级求解；先释放后代平移，再释放几何自由度 | v1：36 二维任务×10；正式版正文未取得 | N04 必须直接比逐层释放和全局求解 |
| [FSP06 WorldCoder](literature-evidence/frontier-spatial.md#fsp06) | 写动态/奖励程序、反例修订、跨任务模型复用 | Sokoban/MiniGrid/改写 ALFWorld；学习可需大量 token | N03 不能只迁移失败知识；别重复学已知 API |
| [FSP07 SayPlan](literature-evidence/frontier-spatial.md#fsp07) | 任务相关图展开、确定性路径规划、反馈重规划 | 90 任务、两个给定场景；正确/可执行分开 | 原“图切片＋工具分工”主线已有近邻 |
| [FSP08 Aligning Constraint Generation](literature-evidence/frontier-spatial.md#fsp08) | 用求解器奖励训练 CAD 约束生成 | 2.8M 来源草图非测试分母；奖励投机可出现 | 约束通过≠设计意图成立；训练是大改动 |
| [FSP09 CAD-Editor](literature-evidence/frontier-spatial.md#fsp09) | 定位后补写，复制未修改序列 | 2,000 编辑×5 输出；人工成功显著低于有效率 | 局部编辑和有效代码不能自动代表意图保持 |

## 5. 规格解释、关系综合与几何一致性

| 卡 / 论文 | 方法已做到什么 | 实验证据及应保留的边界 | 对候选的约束 |
|---|---|---|---|
| [FR01 SpecFix](literature-evidence/frontier-reasoning.md#fr01) | 采样执行行为、用公开示例筛解释、重写需求 | HumanEval+164 / MBPP+378；20 程序采样有成本 | N06 需超过基于程序分歧的澄清 |
| [FR02 Minimal-Core-Guided Repair](literature-evidence/frontier-reasoning.md#fr02) | 用冲突核与类型诊断修复形式约束 | 77 模板题，含 14 不可行；workshop poster | N03/N04 不可首创冲突核；遗漏约束仍可能通过 |
| [FR03 Formal Verification Planning](literature-evidence/frontier-reasoning.md#fr03) | LLM＋Z3 规划、不可满足反馈与用户协商 | 1,000 主测试；其他协商/OOD 分开 | N04/N06 的求解器和澄清都有先例 |
| [FR04 Know Where You're Uncertain](literature-evidence/frontier-reasoning.md#fr04) | 分开感知/决策不确定性并选择干预 | 校准、适配、主动感知与拒绝共同作用 | N05 不只是给未知量分类 |
| [FR05 Relational Decomposition](literature-evidence/frontier-reasoning.md#fr05) | 关系事实＋背景知识综合程序 | 四类任务；无噪声/封闭世界；不是每类都赢 | N02 的关系表示本身已有方法 |
| [FR06 TTL-SR](literature-evidence/frontier-reasoning.md#fr06) | 几何一致性伪标签驱动测试时 LoRA | 两开源 VLM、多基准；累计适配且有逐类退步 | N07 若固定模型，应明确区别与成本 |
| [FR07 LLMorph](literature-evidence/frontier-reasoning.md#fr07) | 多种变形关系检测输出不一致 | 561,267 次执行非独立题数；误报依关系而异 | N01/N07 的变形测试不是新方法 |
| [FR08 COMFORT](literature-evidence/frontier-reasoning.md#fr08) | 参考系歧义、空间对称和鲁棒性评价 | 9 VLM；同场景大量变体；基本方向为主 | N06/N07 不能只重新发现视角歧义 |

## 6. 从调研到方向取舍

| 原先可能采用的宽泛说法 | 现在的判断 | 仍可研究的更窄问题 |
|---|---|---|
| 高效利用知识库 | 目标合理，作为 novelty 太宽 | 知识适用条件如何从证据中辨别；真实交互价值能否被预测 |
| Agent 能不断获得新工具 | 工具创建、技能库和修订已有 | 失败应修改实现、条件还是抽象边界，以及选择是否有增益 |
| 自然语言到空间的桥梁 | 适合 motivation，不独立证明方法新颖 | 如何用可执行结果差异选择澄清，减少误理解和返工 |
| 生成后自我验证、再 repair | 有直接 CAD/规划先例 | 哪种可迁移机制使下一次生成受益，而不是仅增加重试 |
| 分层处理、只开放必要上下文 | SayPlan、AIDL、CMTF 等已覆盖一般思想 | 能否从冲突/干预选择更有效的接口调整，胜过已有策略 |
| token 压缩 | 可以是效果或工程贡献 | 同预算是否改变最终任务覆盖；是否超过 DST/图切片/程序抽象 |

补核造成的实质更正：SK15 已按对象替换下的效果等价学习角色化算子，不能再将其写成 N02 的新意。N02 只有进一步研究新宏程序本身如何根据组合表现修订，才可能留下方法空间；这仍需面对 LILO/DreamCoder 的程序抽象。N01 也不能泛称首次联合学习条件与技能，重点只能是竞争修订之间的选择机制。

建议优先诊断 [N01 联合修订](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/novelty-directions.md#n01)，把 N03 看作迁移证据；保留 N06 作为 Demo 的独立竞争路线。N02/N04 或更大的参数域构造学习是后续空间。这里排序依据可检验性、预计改动和先例压力，**不等于会议录用概率**。

## 7. 保留缺口与下一轮的停止边界

| 条目 | 已取得材料 | 仍缺什么 / 为什么相关 |
|---|---|---|
| DepthBenchCAD，2026-09-14 线索 | [arXiv 入口](https://arxiv.org/abs/2609.15122)、[作者仓库](https://github.com/HongyeYangGT/DepthBenchCAD)，P | 正文的任务、预算与参数变化评测；不能用仓库简介代替 |
| AIDL 正式 CGF 版本 | DOI/出版身份已核，v1 全文已读 | 正式版的变化未核；只引用 v1 的方法与数字 |
| 部分论文精确测试分母 | 方法/主要结果已读，缺口逐卡记录 | 如 HistCAD 编辑请求数、CAD-Factory 文本测试数、约束生成测试草图数；不反推整数 |
| 原矩阵 14 条 P | 保留原链接和尝试结果 | 仍是开放缺口，这一扩展调研不代表已读到全文 |

选定 N01/N02 时，应继续针对联合程序/条件修订、程序库拆合、谓词发明做定向检索；选定 N06 时，应追加决策理论澄清、对比示例选择与交互程序综合；选定 N04 时，应追加一般约束分解/接口细化。N07 还需要测试时表示搜索的定向查重。不能用“本轮没有找到”写成“从来没人做过”。

这些缺口不妨碍提出可证伪候选和估计投入，但会限制首创声明。更详细的决策、baseline、消融、数据划分和淘汰条件已写在 [方法方向](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/novelty-directions.md) 与 [一一对应实验](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/novelty-experiments.md)。本轮没有训练、Provider 实验、数据下载或生产代码变更。
