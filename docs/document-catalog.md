# 文档分类、归档与保留目录

更新：2026-09-23。覆盖 `docs/` 下 212 份 Markdown 文件（不含本目录自身）。
按功能和用途整理导航；逐文件分类依据路径、标题及各分区索引，不表示已逐句审计全部历史正文。
本次事实核对集中于 Repair、材料／Type／外观、R1 和 presentation 案例。
`.planning/`、源数据、Prompt／Schema、accepted Proof 与运行产物保留原有权威位置，未纳入删除。

## 日常只从这些入口开始

| 工作 | 必要入口 |
|---|---|
| Repair 论文和老师汇报 | [技术正文](architecture/ifc-repair-pipeline-status-and-roadmap.md)、[Claim／实验](reports/repair-demo/claims-and-experiments.md)、[文献矩阵](reports/repair-demo/repair-literature-matrix-20260921.md) |
| Generation 研究 | [三份主稿导航](reports/generation-demo/README.md) |
| IFC2Text 与往返重建 | [研究与实现](architecture/bim2text-bidirectional-bridge-research.md)、[进展与限制](reports/ifc2text-stepwise-fixes-2026-09-22.md) |
| 开发、验证及历史证据 | [接管指南](how-to/agent-takeover.md)、[验证索引](validation/README.md)、[Proof](../dataset/processed/proof/README.md) |

“当前正文”与“必要证据”分开保存：前者简明、持续更新；后者即使年代较早，也可能是论文结果、失败和来源的唯一依据。

## 已完成的归档与纠偏

- Repair 的旧草案先归档并推送 Git；用户批准后删除 D1–D4，相关评测要点并入现行 Claims。历史原文见下方固定提交链接。
- 继续核查 Generation 早期研究稿，列出第二批 10 份待删除审核项；周报、旧 handoff 和独立证据另行判断，不再一律标为永久保留。
- 将全局和报告索引增加为按功能阅读，改正架构索引仍只写 Phase 7–10.1、验证索引仍写 R1 待执行等过时描述。
- Repair 技术主文档补齐 Type／材料／外观，并将运行 PASS、人工待审、离线回归分别报告。没有重写任何冻结 Proof 或实验结果。

## 第一批删除已完成：D1–D4

2026-09-23 用户明确批准后，以下 **4 份已从工作目录删除**。内容先保存在已推送提交 `d6a9d4c4`，下表阅读入口指向该提交中的历史原文；现行内容由三份主文档承接。

| 编号与阅读入口 | 删除理由 | 当前替代与保留内容 | 已执行处理 |
|---|---|---|---|
| D1 [旧研究与实验草案](https://github.com/770122whrt/text2IFC/blob/d6a9d4c43e91d6e1d9e2e93c8801a006497ca969/docs/reports/repair-demo/archive/research-question-claims-experiments-20260921-v0.3.md) | 研究问题、主张和方法已合并；48 任务／288 次运行已搁置，容易被误读成当前计划 | Method 及 Claims；公平对照、分组隔离与成本解释已收拢至 Claims §9.1 | 已删除，旧规模与全文留 Git 历史 |
| D2 [旧三方比较协议](https://github.com/770122whrt/text2IFC/blob/d6a9d4c43e91d6e1d9e2e93c8801a006497ca969/docs/reports/repair-demo/archive/damage-repair-compare-protocol-20260921-v0.3.md) | 与 Claims 重复维护评测原则；独立文件不再承担执行协议职责 | G–D–R、对象匹配、容差、完整失败分母和比较器正负控制已收拢至 Claims §9.1 | 已删除，现行设计只维护 Claims |
| D3 [旧 Claim 攻击快照](https://github.com/770122whrt/text2IFC/blob/d6a9d4c43e91d6e1d9e2e93c8801a006497ca969/docs/reports/repair-demo/archive/claim-novelty-audit-20260921.md) | 近邻判断已纳入当前文献与 Claims；旧代码行号和部分当时状态会随实现漂移 | 文献矩阵保留来源与阅读范围，Claims 保留近邻差异及候选贡献；详细旧论证可查 Git | 已删除，当前入口不再绕经旧审查 |
| D4 [9 月 18 日旧 Repair 矩阵](https://github.com/770122whrt/text2IFC/blob/d6a9d4c43e91d6e1d9e2e93c8801a006497ca969/docs/reports/generation-demo/ifc-repair-literature-matrix-20260918.md) | 放在 Generation 分区，Repair 已有专属矩阵；旧保全勾选与安全／授权定位已被后续修正 | 9 月 21 日 Repair 文献矩阵及 Claims 为现行依据；旧条目与原文链接保留在 Git 历史 | 已删除，旧入口改指 Repair 矩阵 |

**阅读重点：**D1 看旧实验规模与对照，D2 看对象匹配及评分，D3 看近邻论证，D4 看旧结论；可直接与 [Claims §9.1](reports/repair-demo/claims-and-experiments.md#91-从旧稿保留的评测设计要点)、[当前矩阵](reports/repair-demo/repair-literature-matrix-20260921.md)比对。

**引用已核查：**已同步修正本目录、Repair 导航、archive 导航及 Generation 完整综述中的旧引用；四份候选相互间的引用随删除消失。引用不是无限期保留旧正文的理由。

**明确保留：**用户上传的 8 月原稿作为指定来源；SGSS 全文阅读快照作为原文阅读证据；已接受 Proof、真实运行与失败记录作为实验依据。本轮不删除这些内容，也不把未跟踪状态本身作为删除理由。

本批只审查文档内容的去留，不表示代码、数据或整个项目已完成清理。本批已删除 4 份，上传的 8 月原稿与实验依据保留。

## 第二批待审核：D5–D14，共 10 份

**状态：仅提议，尚未删除。** 这 10 份不包含已删除的 D1–D4。核查对象是 Generation 研究中反复叠加的旧稿；删除它们可减少并行版本，并非停止 Generation 研究。Repair 的三份现行正文继续维护。

现行替代入口：[研究方案](reports/generation-demo/research-plan.md)、[综述简版](reports/generation-demo/literature-review-short.md)、[综述完整版](reports/generation-demo/literature-review-full.md)。下表链接均可直接阅读待删原文。

| 编号与待审核原文 | 建议删除的具体理由 | 承接内容／审核重点 |
|---|---|---|
| D5 [旧三项 Claims](reports/generation-demo/novelty-and-claims.md) | 仍围绕可核验流程、写入所有权、版本绑定组织三项贡献；这些已经调整为系统基础，不是当前独立方法主张 | 研究方案 §2 的 RQ0／E0 承接系统定位。旧中英文贡献段落不再沿用；独立 Claims 审核报告保留 |
| D6 [A／B／C 选题讨论](reports/generation-demo/research-direction-discussion.md) | “B 优先”的关系感知修订路线已被后续研究方案取代，保留全文容易造成多个“下一步” | 研究方案 §2、§4、§5 承接受控编辑、相互作用与联合评价；旧 12 题探索建议和投稿日程不作为当前计划，历史措辞随原稿备份 |
| D7 [知识供给研究主线草案](reports/generation-demo/research-proposal.md) | 以编译器分工／知识选择作为重点方法，优先级已被现行 RQ0、D1／D2 改写；另保留一套 RQ1–RQ4、B1–B5 会造成排期歧义 | 研究方案 E0.1／E0.3、§5 承接强 Coding Agent、同接口对照与完整成本。旧“按任务义务选择知识”的具体假设只留历史备份，不宣称全文已被逐字吸收 |
| D8 [旧选题简洁记录](reports/generation-demo/research-shortlist.md) | 是 P1／P2／V1／L1 的中间摘要，既重复较长讨论，也不是当前 D1／D2 的入口 | 当前优先级看研究方案 §6；较详细的方向论证仍保留在 broader-method-directions，原始补查仍保留在 research-shortlist-evidence |
| D9 [旧 Demo 综述短稿](reports/generation-demo/literature-review-demo.md) | 与现行综述简版重复；附带的英文 Related Work 仍服务于早期状态管理定位 | 简版的三模块比较及完整版的逐篇条目承接文献事实。旧英文段落属于过期写作草稿，备份后删除，不混入 Repair Method |
| D10 [早期主题综述工作稿](reports/generation-demo/literature-review-working.md) | 已先后被论文矩阵及完整综述扩充、更正，末尾还指向旧 A／B／C 选题，继续维护会分裂比较口径 | 完整版 §1 的直接近邻、版本与实验边界，研究方案 §2／§5 的系统定位和独立评价承接；原始调查来源及独立审核保留 |
| D11 [63 条旧论文矩阵](reports/generation-demo/paper-matrix.md) | 是较小范围的旧索引；A01–A14、B01–B12、C01–C16、D01–D21 共 63 个记录编号均已进入完整综述 | 63 个编号已逐项匹配；其证据卡文件与锚点均存在并保留。旧 F／P 读取快照与数据资源表不需重复维护；资源准入仍看 external 数据目录 |
| D12 [104 条旧飞书矩阵备份](reports/generation-demo/feishu-literature-matrix.md) | 完整版已吸收整张矩阵；保留另一份独立正文只增加旧 N01–N08 定位和计数的维护负担 | 104 条正文全部对应：99 条逐字相同，另外 5 条仅新增“补充核查”链接。旧飞书页面的历史地址随备份保留；此次不删除或改写远端页面 |
| D13 [N01–N08 方法候选](reports/generation-demo/novelty-directions.md) | 同时展开八条旧假设，优先级又被多次补查推翻；与当前集中写 Repair Demo 的目的不符，也不是 Generation 当前路线 | 现行研究方案只维护 RQ0、D1／D2；文献冲突依据仍在完整版与原始证据卡。八条旧假设的具体构造未全部迁移，建议有意退出工作目录、保存在历史备份 |
| D14 [E01–E08 实验设计](reports/generation-demo/novelty-experiments.md) | 对应上一行的八条未执行假设，另有旧任务数量、人周与停止阈值，容易被误当作待执行实验清单 | 当前实验看研究方案 E0／E1／E2 和 §5；Repair 看自身 Claims。E01–E08 的专属消融和建议规模未全部迁移，随旧假设一起保留历史备份；没有删除已执行结果 |

**覆盖核查的含义：**D11 已核对记录编号及底层证据入口，不声称旧表每个摘要句都逐字进入新版。D12 已逐行比对正文，5 处差异均为新版新增的补充阅读链接。D13／D14 是建议退出当前维护的旧研究分支，不把“搁置”伪装成“内容完全重复”。

**备份状态：**这 10 份目前都未被 Git 跟踪，尚不能说“已在 Git 中可恢复”。审核期间保留原文件。若批准删除，将先把指定原稿提交并推送形成固定历史版本，验证可恢复后明确告知开始删除，再删除原件并修复引用；不会仅凭未跟踪状态删除文件。

**引用处理已定位：**除了十份候选之间互引，还涉及 Generation README、coding-agent-knowledge-direction、broader-method-directions、claims-and-novelty-synthesis、research-shortlist-evidence、novelty-literature-addendum 以及三份底层证据卡中的导航。批准后将现行入口改指研究方案／完整综述；确需引用旧论证的地方改用固定历史版本，不留下断链。

**这批明确保留的内容：**三份现行 Generation 主稿；三份现行 Repair 主稿；literature-evidence 原始阅读卡；独立 Claims 审核；包含真实成本账本的 coding-agent-knowledge-direction；仍承载详细近邻论证的 broader-method-directions／research-shortlist-evidence；用户上传的 8 月原稿、源模型、已接受 Proof 和真实失败记录。

## 逐文件分类

下表包括历史运行中附带的 Markdown，已标为运行证据，不把它们误当研究正文。
本表是一份分类快照，新增文档仍先更新所属功能的主索引，不要求每次改字都重新生成清单。

### Repair（64 份）

| 文档 | 分类／处理 |
|---|---|
| [用户指定的 8 月技术原稿](reports/repair-demo/archive/Text2IFC-Pipeline-Feishu-2026-08-29.md) | 历史来源：原字节归档保留，现行内容在技术主文档维护 |
| [text2IFC Repair：面向已有 IFC 的自然语言局部修复](architecture/ifc-repair-pipeline-status-and-roadmap.md) | 现行正文：维护 |
| [Phase 12 Plan 07 收尾与 IFC Repair 技术 Handover](handoffs/phase12-plan07-closeout-handover-2026-09-03.md) | 历史／专项：归档保留 |
| [Phase 12.1 / Repair Milestone R1 Checkpoint Handoff](handoffs/repair-milestone-r1-checkpoint-2026-09-01.md) | 历史／专项：归档保留 |
| [Repair Milestone R1 / Phase 12.1 Closure Handoff — 2026-09-03](handoffs/repair-milestone-r1-closure-2026-09-03.md) | 历史／专项：归档保留 |
| [Text2IFC Repair Milestone R1 — Final Acceptance Handoff](handoffs/repair-milestone-r1-final-acceptance.md) | 历史／专项：归档保留 |
| [Phase 11 Live Closure Design](plans/2026-07-31-phase11-live-closure-design.md) | 历史／专项：归档保留 |
| [LLM Generation / IFC Repair 下一阶段执行计划（Discussion Draft）](plans/2026-09-03-llm-generation-repair-next-step-discussion.md) | 历史／专项：归档保留 |
| [LLM Generation / IFC Repair / Demo Paper 后续方向记录](reports/llm-generation-repair-demo-next-direction-2026-09-03.md) | 日期快照／证据：保留 |
| [Repair 历史讨论归档](reports/repair-demo/archive/README.md) | 导航：保留 |
| [IFC-SemRepair：Claim、创新边界与实验登记](reports/repair-demo/claims-and-experiments.md) | 现行正文：维护 |
| [IFC-SemRepair：三份主文档导航](reports/repair-demo/README.md) | 导航：保留 |
| [IFC-SemRepair Literature：文献矩阵与重点近邻](reports/repair-demo/repair-literature-matrix-20260921.md) | 现行正文：维护 |
| [SGSS / text2IDS：全文 Overview 与 Repair 后作边界](reports/repair-demo/sgss-fulltext-review-20260921.md) | 协议／来源／验证证据：保留 |
| [IFC Repair Proof 人类可读收纳规范](validation/ifc-repair-proof-format.md) | 协议／来源／验证证据：保留 |
| [Text2IFC IFC2X3 局部 ChangeSet 评估设计](validation/ifc2x3-changeset/design.md) | 协议／来源／验证证据：保留 |
| [LargeBuilding Window Repair：Pipeline 与 Ground Truth 对比](validation/ifc2x3-changeset/ground-truth-comparison.md) | 协议／来源／验证证据：保留 |
| [IFC Presentation Development Boundary](validation/ifc2x3-changeset/ifc-presentation-development-boundary-2026-09-03.md) | 协议／来源／验证证据：保留 |
| [IFC2X3 ChangeSet implementation findings](validation/ifc2x3-changeset/implementation-findings.md) | 协议／来源／验证证据：保留 |
| [Codex Implementation Prompt：Extensible IFC2X3 Local ChangeSet Evaluation](validation/ifc2x3-changeset/implementation-prompt.md) | 协议／来源／验证证据：保留 |
| [从 damaged IFC 和文本到重新生成 IFC：单链路输入输出说明](validation/ifc2x3-changeset/phase10-single-pipeline-input-output.md) | 协议／来源／验证证据：保留 |
| [Phase 10 Window L2 语义闭环验证报告](validation/ifc2x3-changeset/phase10-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 10.1 Window 有效属性完整复刻与 IfcDiff 报告](validation/ifc2x3-changeset/phase10.1-full-window-replication-and-ifcdiff-report.md) | 协议／来源／验证证据：保留 |
| [LargeBuilding 真实修复 Window 属性对比](validation/ifc2x3-changeset/phase10.1-largebuilding-window-property-comparison.md) | 协议／来源／验证证据：保留 |
| [Phase 10.1 显式 IFC 属性写入与验证报告](validation/ifc2x3-changeset/phase10.1-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 10.2 属性知识检索与完整链路验证报告](validation/ifc2x3-changeset/phase10.2-property-knowledge-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 10.3 五窗批量修复与大型 IFC 验证报告](validation/ifc2x3-changeset/phase10.3-five-window-batch-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 10.4 Comparator 0.2 Validation Report](validation/ifc2x3-changeset/phase10.4-comparator-0.2-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 10.5 Window Occurrence Fidelity 与验证加速报告](validation/ifc2x3-changeset/phase10.5-window-fidelity-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 11 Door Storey Policy Erratum](validation/ifc2x3-changeset/phase11-door-storey-policy-erratum.md) | 协议／来源／验证证据：保留 |
| [Phase 11 Door / Opening 验证报告](validation/ifc2x3-changeset/phase11-door-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 12 / 12.1 Beam、Column 与 Property Resolution 最终验证报告](validation/ifc2x3-changeset/phase12-beam-column-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 12 Plan 07 结构恢复证据勘误与重新准入要求](validation/ifc2x3-changeset/phase12-plan07-structural-restoration-erratum-2026-09-03.md) | 协议／来源／验证证据：保留 |
| [Phase 12 Structural Type Visual Fidelity 修复计划](validation/ifc2x3-changeset/phase12-structural-type-visual-fidelity-plan-2026-09-03.md) | 协议／来源／验证证据：保留 |
| [Phase 7 Validation Report](validation/ifc2x3-changeset/phase7-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 8 L1/L2 Evaluation Contract 验证报告](validation/ifc2x3-changeset/phase8-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 9 Stage 1 合同修复与双路径 UAT 报告](validation/ifc2x3-changeset/phase9-stage1-contract-repair-report.md) | 协议／来源／验证证据：保留 |
| [Phase 9 IFC + 文本修复编排验证报告](validation/ifc2x3-changeset/phase9-validation-report.md) | 协议／来源／验证证据：保留 |
| [Phase 09.1 IFC Type 证据与 Prototype 解析验证报告](validation/ifc2x3-changeset/phase9.1-validation-report.md) | 协议／来源／验证证据：保留 |
| [IFC2X3 Local ChangeSet 验证索引](validation/ifc2x3-changeset/README.md) | 导航：保留 |
| [Repair Mixed Validation Boundary — 2026-09-05](validation/ifc2x3-changeset/repair-mixed-validation-boundary-2026-09-05.md) | 协议／来源／验证证据：保留 |
| [IFC2X3 Restoration Validation Boundary — 2026-09-04](validation/ifc2x3-changeset/restoration-validation-boundary-2026-09-04.md) | 协议／来源／验证证据：保留 |
| [IFC2X3 repair implementation reuse map](validation/ifc2x3-changeset/reuse-map.md) | 协议／来源／验证证据：保留 |
| [IFC Target Retrieval and Context Design](validation/ifc2x3-changeset/target-retrieval-design.md) | 协议／来源／验证证据：保留 |
| [Composite Bound Test Cases — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/composite-bound-testcases.md) | 协议／来源／验证证据：保留 |
| [Composite Capability Feasibility — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/composite-capability-feasibility.md) | 协议／来源／验证证据：保留 |
| [Composite Evidence Matrix — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/composite-evidence-matrix.md) | 协议／来源／验证证据：保留 |
| [COMPOSITE EVIDENCE REPORT — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/COMPOSITE-EVIDENCE-REPORT.md) | 协议／来源／验证证据：保留 |
| [Composite Independent Audit — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/composite-independent-audit.md) | 协议／来源／验证证据：保留 |
| [Composite Model Selection — Text2IFC Composite Repair Milestone](validation/repair-composite-milestone/composite-model-selection.md) | 协议／来源／验证证据：保留 |
| [C1-C5 damage-restoration completion](validation/repair-composite-milestone/damage-restoration-c1-c5-completed.md) | 协议／来源／验证证据：保留 |
| [DEFECT RECORD — Mixed-family composite defects (BOTH FIXED)](validation/repair-composite-milestone/DEFECT-RECORD.md) | 协议／来源／验证证据：保留 |
| [损伤-恢复里程碑会话总结（Session Summary）](validation/repair-composite-milestone/SESSION-SUMMARY.md) | 协议／来源／验证证据：保留 |
| [工作总结 — Composite Repair Milestone（复合修复里程碑证据包）](validation/repair-composite-milestone/WORK-SUMMARY.md) | 协议／来源／验证证据：保留 |
| [Plan 07 and Repair Milestone R1 Genuine Execution Matrix](validation/repair-milestone-r1/plan07-r1-genuine-execution-matrix-2026-09-01.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 最终验收冻结包](validation/repair-milestone-r1/README.md) | 导航：保留 |
| [Repair Milestone R1 模型选择与多样性](validation/repair-milestone-r1/repair-acceptance-model-selection.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 冻结案例规格](validation/repair-milestone-r1/repair-bound-testcases.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 能力覆盖矩阵](validation/repair-milestone-r1/repair-capability-coverage-matrix.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 当前能力声明](validation/repair-milestone-r1/repair-capability-manifest.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 Evaluation Budget Addendum](validation/repair-milestone-r1/repair-evaluation-budget-addendum.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 Final Proof Matrix](validation/repair-milestone-r1/repair-proof-matrix-2026-09-03.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 planned Proof Matrix](validation/repair-milestone-r1/repair-proof-matrix-plan.md) | 协议／来源／验证证据：保留 |
| [Repair Milestone R1 Proof Readiness Re-audit](validation/repair-milestone-r1/repair-proof-readiness-reaudit.md) | 协议／来源／验证证据：保留 |

### Generation（49 份）

| 文档 | 分类／处理 |
|---|---|
| [两层光庭阅读馆设计](architecture/courtyard-library-design.md) | 专题／参考：保留，按适用版本阅读 |
| [光庭阅读馆第二版：开敞围庭、完整真实生成](architecture/courtyard-library-open-court-design.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 2.5 Summary: BIM JSON 2.0 IFC Semantic Graph](architecture/phase-2-5-summary.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 3 Summary: Text-to-JSON Dataset and Baseline](architecture/phase-3-summary.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 4 Summary: High-fidelity IFC Round Trip](architecture/phase-4-summary.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 4 Wave 0: Generated IFC Correctness Gate](architecture/phase-4-wave-0-generated-ifc-gate.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 5 Summary: Multi-turn Clarification Agent](architecture/phase-5-summary.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 6 验收与追踪报告](architecture/phase-6-acceptance-and-trace-report.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 6 Model Decision](architecture/phase-6-model-decision.md) | 专题／参考：保留，按适用版本阅读 |
| [Phase 6 Multi-agent Design](architecture/phase-6-multiagent-design.md) | 专题／参考：保留，按适用版本阅读 |
| [IFC2X3 Generation Profile](reference/ifc2x3-generation-profile.md) | 专题／参考：保留，按适用版本阅读 |
| [光庭与本地调试目录退役清单](reports/courtyard-proof-closeout-20260912/CLEANUP.md) | 日期快照／证据：保留 |
| [光庭Proof收纳与工作目录整理](reports/courtyard-proof-closeout-20260912/REPORT.md) | 日期快照／证据：保留 |
| [text2IFC：Self-Verification 重合核查与方法方向扩展](reports/generation-demo/broader-method-directions.md) | 历史研究：归档保留 |
| [text2IFC Generation：Claims / Novelty 综合审核](reports/generation-demo/claims-and-novelty-synthesis-20260916.md) | 历史研究：归档保留 |
| [text2IFC：从 Coding Agent、领域知识到空间生成](reports/generation-demo/coding-agent-knowledge-direction.md) | 历史研究：归档保留 |
| [text2IFC 文献矩阵：分模块比较（2026-09-15）](reports/generation-demo/feishu-literature-matrix.md) | 待审核删除：D12，理由见第二批清单 |
| [BIM 创作、布局与相关综述：原文证据卡](reports/generation-demo/literature-evidence/bim-authoring.md) | 协议／来源／验证证据：保留 |
| [逐篇证据：建模抽象、Coding Agent、知识与权限](reports/generation-demo/literature-evidence/coding-knowledge-and-control.md) | 协议／来源／验证证据：保留 |
| [方法候选调研：知识利用、主动查证与跨任务迁移](reports/generation-demo/literature-evidence/frontier-knowledge.md) | 协议／来源／验证证据：保留 |
| [方法候选证据：规格、约束、关系表示与空间一致性](reports/generation-demo/literature-evidence/frontier-reasoning.md) | 协议／来源／验证证据：保留 |
| [可执行技能与能力扩展：正文证据、剩余假设与实验](reports/generation-demo/literature-evidence/frontier-skills.md) | 协议／来源／验证证据：保留 |
| [空间合成与能力扩展：正文证据与方法假设](reports/generation-demo/literature-evidence/frontier-spatial.md) | 协议／来源／验证证据：保留 |
| [IFC 生成、编辑、知识使用与评价：全文证据卡](reports/generation-demo/literature-evidence/ifc-evaluation.md) | 协议／来源／验证证据：保留 |
| [结构化生成、CAD 与模型驱动工程：逐篇正文证据](reports/generation-demo/literature-evidence/structured-generation.md) | 协议／来源／验证证据：保留 |
| [text2IFC Generation 文献综述：论文正文短版](reports/generation-demo/literature-review-demo.md) | 待审核删除：D9，理由见第二批清单 |
| [text2IFC 文献综述·完整版](reports/generation-demo/literature-review-full.md) | 现行正文：维护 |
| [text2IFC 文献综述·简版](reports/generation-demo/literature-review-short.md) | 现行正文：维护 |
| [text2IFC Generation：研究综述与选题依据](reports/generation-demo/literature-review-working.md) | 待审核删除：D10，理由见第二批清单 |
| [text2IFC Generation：Novelty 与 Claim 基础版](reports/generation-demo/novelty-and-claims.md) | 待审核删除：D5，理由见第二批清单 |
| [text2IFC：方法创新候选与方向选择](reports/generation-demo/novelty-directions.md) | 待审核删除：D13，理由见第二批清单 |
| [text2IFC：Novelties ↔ Experiments 一一对应设计](reports/generation-demo/novelty-experiments.md) | 待审核删除：D14，理由见第二批清单 |
| [方法创新扩展调研：论文矩阵与决策记录](reports/generation-demo/novelty-literature-addendum.md) | 历史研究：归档保留 |
| [text2IFC 论文矩阵与证据索引](reports/generation-demo/paper-matrix.md) | 待审核删除：D11，理由见第二批清单 |
| [text2IFC 研究与文献](reports/generation-demo/README.md) | 导航：保留 |
| [text2IFC Generation：Demo 选题与下一步讨论](reports/generation-demo/research-direction-discussion.md) | 待审核删除：D6，理由见第二批清单 |
| [text2IFC 研究方案：可接受解空间、知识效率与受控编辑](reports/generation-demo/research-plan.md) | 现行正文：维护 |
| [text2IFC：研究主线与实验草案](reports/generation-demo/research-proposal.md) | 待审核删除：D7，理由见第二批清单 |
| [简版选题的补查证据](reports/generation-demo/research-shortlist-evidence.md) | 历史研究：归档保留 |
| [简洁记录](reports/generation-demo/research-shortlist.md) | 待审核删除：D8，理由见第二批清单 |
| [text2IDS / WWW 2026 Demo：Overview 与 text2IFC 仿写参考](reports/generation-demo/text2ids-www2026-demo-overview-and-writing-reference.md) | 历史研究：归档保留 |
| [Multi-storey Prompt and Input Hardening Implementation Plan](reports/legacy-plans/2026-07-11-multistorey-prompt-input-hardening.md) | 历史／专项：归档保留 |
| [Phase 6.1 Final Acceptance Report](reports/main-integration-20260912/generation-recheck-01/A-revise/report.md) | 运行证据：保留 |
| [请求与 IFC 语义核对](reports/main-integration-20260912/generation-recheck-01/A-revise/semantic-report.md) | 运行证据：保留 |
| [Phase 6.1 Final Acceptance Report](reports/main-integration-20260912/generation-recheck-01/B-retain/report.md) | 运行证据：保留 |
| [请求与 IFC 语义核对](reports/main-integration-20260912/generation-recheck-01/B-retain/semantic-report.md) | 运行证据：保留 |
| [Phase 6.1 Final Acceptance Report](reports/main-integration-20260912/generation-recheck-01/C-teaching/report.md) | 运行证据：保留 |
| [请求与 IFC 语义核对](reports/main-integration-20260912/generation-recheck-01/C-teaching/semantic-report.md) | 运行证据：保留 |
| [text2IFC Generation Claim / Novelty Audit — 2026-09-14](reports/Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md) | 日期快照／证据：保留 |

### IFC2Text 与往返重建（21 份）

| 文档 | 分类／处理 |
|---|---|
| [IFC2Text：从建筑模型到可重建的设计说明](architecture/bim2text-bidirectional-bridge-research.md) | 现行正文：维护 |
| [IFC2Text：重新归因、真实探针与下一步指南](reports/ifc2text-attribution-and-next-steps-2026-09-21.md) | 日期快照／证据：保留 |
| [IFC2Text：显式闭合单墙真实复验与容差说明](reports/ifc2text-closed-wall-retry-result-2026-09-21.md) | 日期快照／证据：保留 |
| [IFC2Text 当前能力与往返失败证据复核](reports/ifc2text-evidence-audit-2026-09-22.md) | 日期快照／证据：保留 |
| [IFC2Text 双向链路：14 个几何差异与 Audit 续跑](reports/ifc2text-geometry-audit-2026-09-22.md) | 日期快照／证据：保留 |
| [IFC2Text 材料清单修复与整栋续跑](reports/ifc2text-material-list-rerun-2026-09-22.md) | 日期快照／证据：保留 |
| [IFC2Text 第一阶段收口](reports/ifc2text-phase1-closeout-2026-09-18/EXECUTION.md) | 日期快照／证据：保留 |
| [IFC2Text 第一阶段：决策与防复发记录](reports/ifc2text-phase1-decisions-2026-09-17.md) | 日期快照／证据：保留 |
| [IFC2Text Phase 1 实施记录（2026-09-16）](reports/ifc2text-phase1-implementation-2026-09-16.md) | 日期快照／证据：保留 |
| [IFC2Text：问题—原因—方案决策说明](reports/ifc2text-problem-solution-decision-guide-2026-09-21.md) | 日期快照／证据：保留 |
| [IFC2Text 往返链路分步修复](reports/ifc2text-stepwise-fixes-2026-09-22.md) | 日期快照／证据：保留 |
| [IFC2Text：异常墙描述与源数据归属整理](reports/ifc2text-wall-and-source-fixes-2026-09-21.md) | 日期快照／证据：保留 |
| [IFC2Text：墙体0.1 mm比较与整栋上下文检查](reports/ifc2text-wall-tolerance-and-system-context-2026-09-21.md) | 日期快照／证据：保留 |
| [IFC2Text 往返归因：冻结探针 v0.1](validation/ifc2text/attribution-probes-2026-09-21-v01.md) | 协议／来源／验证证据：保留 |
| [显式闭合单墙：两次真实复验与容差口径](validation/ifc2text/closed-wall-retry-v08-2026-09-21.md) | 协议／来源／验证证据：保留 |
| [材料清单支持后的单次续跑](validation/ifc2text/material-list-continuation-v11-2026-09-22.md) | 协议／来源／验证证据：保留 |
| [IFC2Text Phase 1 写作与公共桥 Stage Admission](validation/ifc2text/phase1-writing-admission-2026-09-17.md) | 协议／来源／验证证据：保留 |
| [IFC2Text Phase 1 写作与公共桥 Stage Admission v0.2](validation/ifc2text/phase1-writing-admission-v02-2026-09-17.md) | 协议／来源／验证证据：保留 |
| [IFC2Text Validation](validation/ifc2text/README.md) | 导航：保留 |
| [IFC2Text 两项修复：v0.7 执行边界](validation/ifc2text/wall-recovery-v07-2026-09-21.md) | 协议／来源／验证证据：保留 |
| [修复后的 hxp 整栋单次重跑](validation/ifc2text/whole-building-rerun-v10-2026-09-22.md) | 协议／来源／验证证据：保留 |

### 数据与合同参考（12 份）

| 文档 | 分类／处理 |
|---|---|
| [Dataset Reorganization / IFC Acquisition Boundary](plans/2026-09-04-dataset-reorganization-boundary.md) | 历史／专项：归档保留 |
| [BIM JSON 1.0 Contract Reference](reference/bim-json-1.0.md) | 专题／参考：保留，按适用版本阅读 |
| [BIM JSON 2.0 Contract Reference](reference/bim-json-2.0.md) | 专题／参考：保留，按适用版本阅读 |
| [BIMNet IFC数据管线方法论](reference/bimnet-ifc-data-pipeline-methodology.md) | 专题／参考：保留，按适用版本阅读 |
| [IFC2X3 Knowledge Sources](reference/ifc2x3-knowledge-sources.md) | 专题／参考：保留，按适用版本阅读 |
| [IFC2X3 Dataset Size Index](reports/ifc2x3-dataset-size-index.md) | 日期快照／证据：保留 |
| [IFC2X3 Small Candidate Meaningfulness Review](reports/ifc2x3-small-model-meaningfulness.md) | 日期快照／证据：保留 |
| [IFC2X3 Small Model Refined Shortlist](reports/ifc2x3-small-model-refined-shortlist.md) | 日期快照／证据：保留 |
| [IFC2X3 Small Model Review Batch](reports/ifc2x3-small-model-review-batch.md) | 日期快照／证据：保留 |
| [IFC2X3 Small Model Web Search](reports/ifc2x3-small-model-web-search.md) | 日期快照／证据：保留 |
| [IFC2X3 Small Source Search Follow-up](reports/ifc2x3-small-source-search-followup.md) | 日期快照／证据：保留 |
| [Kaggle IFC Examples — Strict Small IFC2X3 Scan](reports/kaggle-ifc-examples-small-ifc2x3.md) | 日期快照／证据：保留 |

### 工程维护与归档证据（25 份）

| 文档 | 分类／处理 |
|---|---|
| [text2IFC 目录清理与证据集中记录](architecture/repository-organization-refactor.md) | 专题／参考：保留，按适用版本阅读 |
| [text2IFC 仓库交接：结构、整理结果与接续边界](handoffs/repository-handoff-2026-09-13.md) | 历史／专项：归档保留 |
| [Publish the text2IFC Repository to GitHub](how-to/publish-to-github.md) | 专题／参考：保留，按适用版本阅读 |
| [根 archive 准确退役清单](reports/archive-retirement-20260913/DELETE-LIST.md) | 日期快照／证据：保留 |
| [archive 退役与 Zcode 重构参考收纳](reports/archive-retirement-20260913/REPORT.md) | 日期快照／证据：保留 |
| [已完成案例与开发工作区清理](reports/development-cleanup-20260912/REPORT.md) | 日期快照／证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-01/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-02/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-03/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-evidence-duplicate-ref/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-evidence-extra-ref/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-evidence-missing-ref/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-scope-duplicate-target/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-scope-extra-target/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [IFC Repair ChangeSet Draft Generator 0.5](reports/main-integration-20260912/baseline-runs/composite-evidence-setsem-drift-scope-missing-target/attempt-001/rendered-prompt.md) | 运行证据：保留 |
| [下一批清理清单（尚未批准／未删除）](reports/main-integration-20260912/NEXT-CLEANUP.md) | 日期快照／证据：保留 |
| [text2IFC 清理与分支整合报告](reports/main-integration-20260912/REPORT.md) | 日期快照／证据：保留 |
| [本地重复临时文件删除申请](reports/main-integration-20260912/SCRATCH-CLEANUP.md) | 日期快照／证据：保留 |
| [text2IFC 当前分支合入 main](reports/main-sync-20260912/REPORT.md) | 日期快照／证据：保留 |
| [本轮准确删除清单](reports/processed-cleanup-20260913/DELETE-LIST.md) | 日期快照／证据：保留 |
| [processed 与根目录整理](reports/processed-cleanup-20260913/REPORT.md) | 日期快照／证据：保留 |
| [本对话运行目录清理提案](reports/run-cleanup-review-20260910/REPORT.md) | 日期快照／证据：保留 |
| [terminal-session-history](reports/terminal-session-history.md) | 日期快照／证据：保留 |
| [Zcode 整合与本地恢复核查](reports/zcode-integration-20260905/REPORT.md) | 日期快照／证据：保留 |
| [Zcode 有效重构接入](reports/zcode-refactor-adoption-20260913/REPORT.md) | 日期快照／证据：保留 |

### 跨功能架构、规范与历史（41 份）

| 文档 | 分类／处理 |
|---|---|
| [text2IFC Generation 工作流与数据流（截至 Phase 6.5）](architecture/current-workflow-and-data-flow.md) | 专题／参考：保留，按适用版本阅读 |
| [Text2IFC Workflow Language Policy and Feedback Routing Design](architecture/feedback-routing/design.md) | 专题／参考：保留，按适用版本阅读 |
| [Codex Prompt: Implement Language Policy and Feedback Routing for Text2IFC](architecture/feedback-routing/implementation-prompt.md) | 专题／参考：保留，按适用版本阅读 |
| [Main Branch Workflow Code Audit](architecture/main-workflow-code-audit-2026-07-16.md) | 专题／参考：保留，按适用版本阅读 |
| [Architecture Documentation](architecture/README.md) | 导航：保留 |
| [Repair 与 Generation 的 Type、材质、属性和外观计划](architecture/semantic-appearance-plan.md) | 专题／参考：保留，按适用版本阅读 |
| [text2IFC Architecture Overview](architecture/text2ifc-overview.md) | 专题／参考：保留，按适用版本阅读 |
| [Text-to-JSON RAG, Fine-tune, and Agent Decision](architecture/text2json-rag-finetune-decision.md) | 专题／参考：保留，按适用版本阅读 |
| [Token 效率与质量保全计划](architecture/token-efficiency-plan.md) | 专题／参考：保留，按适用版本阅读 |
| [Codex 跨对话上下文维护规则](context-handoff/CONTEXT-HANDOFF-RULES.md) | 历史／专项：归档保留 |
| [Issue Context: Stage 1.5 BGE, Live Transcript, and Curator Contract Failures](context-handoff/ISSUE-CONTEXT__2026-08-24__stage15-bge-curator-contract-failures.md) | 历史／专项：归档保留 |
| [Plan 12.1-07 Stage 1.5 Post-Fix Six-Failure Evidence Dossier](context-handoff/ISSUE-EVIDENCE__2026-08-28__stage15-postfix-six-failures.md) | 历史／专项：归档保留 |
| [Project Context Pack](context-handoff/PROJECT-CONTEXT-PACK.md) | 历史／专项：归档保留 |
| [首次接管 text2IFC 项目](how-to/agent-takeover.md) | 专题／参考：保留，按适用版本阅读 |
| [How-to Guides](how-to/README.md) | 导航：保留 |
| [text2IFC 文档索引](README.md) | 导航：保留 |
| [MiMo Anthropic API Compatibility](reference/mimo-anthropic-api.md) | 专题／参考：保留，按适用版本阅读 |
| [MiMo OpenAI API Compatibility](reference/mimo-openai-api.md) | 专题／参考：保留，按适用版本阅读 |
| [Reference Documentation](reference/README.md) | 导航：保留 |
| [Phase 6.1 Final Acceptance Report](reports/c-proof-archive-20260911/post-retirement-final-acceptance/report.md) | 运行证据：保留 |
| [请求与 IFC 语义核对](reports/c-proof-archive-20260911/post-retirement-final-acceptance/semantic-report.md) | 运行证据：保留 |
| [C Proof、实验归档与原目录退役](reports/c-proof-archive-20260911/REPORT.md) | 日期快照／证据：保留 |
| [项目研究思路与 Pipeline 总结文档](reports/project-research-summary.md) | 日期快照／证据：保留 |
| [Reports](reports/README.md) | 导航：保留 |
| [text2IFC 周报 / 2026-06-11](reports/weekly/2026-06-11.md) | 历史／专项：归档保留 |
| [text2IFC 周报 / 2026-06-16](reports/weekly/2026-06-16.md) | 历史／专项：归档保留 |
| [text2IFC 周报（2026.07.10—2026.07.12）](reports/weekly/2026-07-12.md) | 历史／专项：归档保留 |
| [Text2IFC 成功案例 Proof 集设计规范](superpowers/specs/2026-07-23-text2ifc-proof-set-design.md) | 历史／专项：归档保留 |
| [Human-readable IFC Proof collections](superpowers/specs/2026-09-03-human-readable-ifc-proof-design.md) | 历史／专项：归档保留 |
| [Agent Debug、能力评测与真实 LLM 准入协议](validation/agent-capability-evaluation.md) | 协议／来源／验证证据：保留 |
| [Text2IFC — Parallel Goal Prompts Pre-Execution Audit (Charter)](validation/parallel-goal-prompts-audit-charter.md) | 协议／来源／验证证据：保留 |
| [Parallel Goal Prompts Pre-Execution Audit — Report](validation/parallel-goal-prompts-audit-inputs/audit-report.md) | 协议／来源／验证证据：保留 |
| [Text2IFC — Composite Repair Milestone Evidence Pack](validation/parallel-goal-prompts-audit-inputs/final-prompt-a.md) | 协议／来源／验证证据：保留 |
| [Text2IFC — Repository Architecture Cleanup and Full Refactored Mirror](validation/parallel-goal-prompts-audit-inputs/final-prompt-b.md) | 协议／来源／验证证据：保留 |
| [GOAL LAUNCHER — Task A (Composite Repair Milestone Evidence Pack)](validation/parallel-goal-prompts-audit-inputs/goal-launcher-a.md) | 协议／来源／验证证据：保留 |
| [GOAL LAUNCHER — Task B (Repository Architecture Cleanup and Full Refactored Mirror)](validation/parallel-goal-prompts-audit-inputs/goal-launcher-b.md) | 协议／来源／验证证据：保留 |
| [Text2IFC — Composite Repair Milestone Evidence Pack](validation/parallel-goal-prompts-audit-inputs/prompt-a.md) | 协议／来源／验证证据：保留 |
| [Text2IFC — Repository Architecture Cleanup and Full Refactored Mirror](validation/parallel-goal-prompts-audit-inputs/prompt-b.md) | 协议／来源／验证证据：保留 |
| [Validation and Evaluation Documentation](validation/README.md) | 导航：保留 |
| [T1：Audit 证据去重的第一步结果](validation/token-efficiency/20260911-audit-dedup/REPORT.md) | 协议／来源／验证证据：保留 |
| [C 首轮 Audit 去重收益为零：原因定位](validation/token-efficiency/20260911-c-scope-diagnosis/REPORT.md) | 协议／来源／验证证据：保留 |
