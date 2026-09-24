# text2IFC 文档索引

本页是 `docs/` 的稳定入口。具体文档按职责分区，避免把设计、实施 Prompt、
验证方案和历史报告混放在根目录。

## 按功能阅读（2026-09-23）

给老师汇报 Repair，先读下表第一行的技术主文档。旧交接和已完成计划是历史资料，
不按文件日期把它们当成新执行指令。完整文件分类、归档与删除建议见
[文档分类与归档目录](document-catalog.md)。

| 功能 | 当前正文入口 | 证据与补充 |
|---|---|---|
| **已有 IFC 修复（本次汇报）** | [Repair Demo Method：问题、方法和案例](architecture/ifc-repair-pipeline-status-and-roadmap.md) | [三份主文档](reports/repair-demo/README.md)、[Repair Proof](../dataset/processed/proof/repair/) |
| 从文字生成新 IFC | [Generation 研究与文献](reports/generation-demo/README.md)、[生成工作流](architecture/current-workflow-and-data-flow.md) | [语义与外观范围](architecture/semantic-appearance-plan.md)、[Generation Proof](../dataset/processed/proof/generation/) |
| IFC2Text 与往返重建 | [研究与实现入口](architecture/bim2text-bidirectional-bridge-research.md) | [门窗部件扩展计划 v1.0](architecture/text2ifc-component-plan-v1.0.md)、[验证入口](validation/ifc2text/README.md) |

数据来源、通用验证、开发接管分别使用下方相应分区；不混入 Repair 论文正文。

## 从这里开始

| 目的 | 入口 |
|---|---|
| 首次由 Agent 或开发者接管项目 | [首次接管 text2IFC 项目](how-to/agent-takeover.md) |
| 接续最近的分支整合、目录清理和文档收尾 | [仓库交接快照（2026-09-13）](handoffs/repository-handoff-2026-09-13.md)，接手时重新核实 Git |
| 了解已有/damaged IFC + 文本如何生成可验证的新 IFC，及其修复方法 | [IFC2X3 修复链路与后续路线](architecture/ifc-repair-pipeline-status-and-roadmap.md) |
| 了解 Text -> BIM JSON -> IFC generation | [Generation 工作流与数据流（截至 Phase 6.5）](architecture/current-workflow-and-data-flow.md) |
| 浏览系统架构和阶段演进 | [Architecture Index](architecture/README.md) |
| 规范 Agent Debug、能力提升声明和真实 LLM 前测试 | [Agent 能力评测与真实 LLM 准入协议](validation/agent-capability-evaluation.md) |
| 接手 Phase 12 Repair Pipeline 与 Plan 07 收尾 | [Phase 12 Plan 07 技术 handover](handoffs/repair/phase12-plan07-closeout-handover-2026-09-03.md) |
| 人工检查 Plan 07 IFC 与证据矩阵 | [Plan 07 人工 Proof 入口](../dataset/processed/proof/repair/phase12/plan07-v2/REPORT.md) |
| 查找验证、评估和 UAT 方案 | [Validation Index](validation/README.md) |
| 查找 BIM JSON、IFC2X3 和 Provider 参考 | [Reference Index](reference/README.md) |
| 查看研究总结和周报 | [Reports Index](reports/README.md) |
| 查看最新执行位置和阶段安排 | [STATE 顶部](../.planning/STATE.md)、[ROADMAP](../.planning/ROADMAP.md)、[PROJECT](../.planning/PROJECT.md) |

## 仓库整理入口

- [按工作流与 Phase 阅读 Proof](../dataset/processed/proof/README.md)
- [processed 七类目录与历史路径入口](../dataset/processed/README.md)
- [processed 与根目录整理结果（2026-09-13）](reports/processed-cleanup-20260913/REPORT.md)
- [根 archive 退役结果](reports/archive-retirement-20260913/REPORT.md)与[Zcode 轻量历史入口](../dataset/processed/experiments/zcode-history-20260913/README.md)：原始大包保留固定 Git/LFS 恢复路径，当前 Proof 不迁移
- [Zcode 有效重构接入](reports/zcode-refactor-adoption-20260913/REPORT.md)：当前评估拆分、独立 Proof 包和脚本分类的实施与验证；[脚本入口](../scripts/ifc_repair/README.md)
- [main 与 Zcode 整合后的交接快照](handoffs/repository-handoff-2026-09-13.md)
- [目录瘦身设计及历史执行记录](architecture/repository-organization-refactor.md)；当前结果以 STATE 和最新整理报告为准
- [归档的 CLI 终端记录](reports/terminal-session-history.md)
- [专项技术 handoffs](handoffs/) 与 [网页交叉讨论 context-handoff](context-handoff/CONTEXT-HANDOFF-RULES.md) 按各自职责保留。

## 专题入口与历史接续

- [Type、材质、属性和外观的接续计划](architecture/semantic-appearance-plan.md)
  - A/B/C 与光庭第二版已人工验收，实验另行收纳；项目内 Type 按需组织，基础门窗和部件配色使用适用的新版本；不补写缺省材料/性能属性，Repair 保留原几何，不实现跨 IFC 参照。
- [光庭设计与实施记录](architecture/courtyard-library-design.md)
  - [两版 Proof](../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)保留第一版参考及第二版验收，跨轮约束来源与替代管理仍有后续工作。
- [Token 效率与质量保全计划](architecture/token-efficiency-plan.md)
  - 一次真实 Audit 配对已完成并记录实际 token；[C与实验归档](../dataset/processed/experiments/README.md)已整理，后续优化按独立计划小步推进。
- [首次接管 text2IFC 项目](how-to/agent-takeover.md)
  - 先确认 Git 与当前状态，再按任务类型选择架构、Phase、验证和证据入口。
- [Phase 12 Plan 07 技术 handover](handoffs/repair/phase12-plan07-closeout-handover-2026-09-03.md)
  - 面向后续接手者说明项目分层、Repair Pipeline、关键代码、证据入口、已知风险和接续顺序。
- [Plan 07 人工 Proof 入口](../dataset/processed/proof/repair/phase12/plan07-v2/REPORT.md)
  - 直接查看 9 份 repaired IFC、1 个正确无输出 guard，以及各案例的人读报告。
- [IFC2X3 修复链路与后续路线](architecture/ifc-repair-pipeline-status-and-roadmap.md)
  - 参考成功案例文档排布，完整说明已实现 Repair Pipeline、放行证据、失败路由
    和后续 Roadmap。
- [IFC2X3 Local ChangeSet 评估设计](validation/ifc2x3-changeset/design.md)
  - 既有 IFC 局部修改、紧凑 LLM Context、可扩展 Operation Registry。
- [早期 Repair 实施与复用依据](validation/ifc2x3-changeset/design.md#18-早期实施边界与复用依据2026-09-23-整合)
  - 已并入设计正文，保留当时的实施边界和测试依据。
- [text2IFC Generation 工作流与数据流（截至 Phase 6.5）](architecture/current-workflow-and-data-flow.md)
  - 两种生成策略、多 Agent、BIM JSON、Gate、IFC 编译、ChangeSet 和报告链路。

## 文档分区

### Architecture

目录：[`docs/architecture/`](architecture/README.md)

保存系统结构、模块职责、数据流、专题设计、阶段总结和架构决策。具体 phase 的
SPEC/PLAN/VALIDATION 仍放在 `.planning/phases/`。

### Validation and Evaluation

目录：[`docs/validation/`](validation/README.md)

保存跨阶段或可复用的验证设计、评估协议、样例冻结规则、验收指标和配套实施
Prompt。一个验证主题使用一个子目录。

### Reference

目录：[`docs/reference/`](reference/README.md)

保存稳定的数据合同、生成能力边界、知识来源、兼容性说明和方法论参考。JSON
Schema、EXPRESS Schema 和数据 manifest 仍保留在其机器可读目录。

### How-to

目录：[`docs/how-to/`](how-to/README.md)

- [首次接管 text2IFC 项目](how-to/agent-takeover.md)
- [发布到 GitHub](how-to/publish-to-github.md)

保存面向具体任务的操作步骤。

### Reports

目录：[`docs/reports/`](reports/README.md)

保存项目研究总结、周报和历史汇报。报告不是架构或验收标准的权威来源。

### Handoffs

目录：[`docs/handoffs/`](handoffs/)

[当前仓库交接快照（2026-09-13）](handoffs/repository-handoff-2026-09-13.md)记录分支、整理结果、保留项和接续边界。旧 Phase／R1 handoff 保留专项历史；长期目录地图统一维护在接管指南，最新执行位置仍在 STATE。

### Project Planning

- [Project Context](../.planning/PROJECT.md)
- [Roadmap](../.planning/ROADMAP.md)
- [Current State](../.planning/STATE.md)
- [Milestones](../.planning/MILESTONES.md)
- [Retrospective](../.planning/RETROSPECTIVE.md)
- [Phase Artifacts](../.planning/phases/)

`.planning/` 保存 milestone/phase 的规格、上下文、计划、验证和执行记忆。

## 数据与机器可读合同

- [BIM JSON 1.0 Contract Reference](reference/bim-json-1.0.md)
- [Dataset Organization](../dataset/data_organization.md)
- [External Data Source Catalog](../dataset/sources/CATALOG.md)
- [外部 IFC 候选池、筛选状态与准入边界](../dataset/manifests/candidates/README.md)
- [Type／材质／属性／外观当前范围](architecture/semantic-appearance-plan.md)；[早期实现边界](validation/ifc2x3-changeset/ifc-presentation-development-boundary-2026-09-03.md#10-2026-09-07-git-接续状态)用于历史定位
- [Processed Dataset 与 Proof 分层](../dataset/processed/README.md)
- [Dataset Manifest Format](../dataset/manifests/README.md)
- [Authorized BIMNet IFC2X3 Manifest](../dataset/manifests/bimnet-ifc2x3.jsonl)
- [BIMNet Extraction Audit](../dataset/processed/derived/bim-json-2.0/extraction-audit.json)
- [IFC2X3 TC1 EXPRESS Schema](../schemas/ifc/IFC2X3_TC1.exp)
- [BIM JSON Schemas](../schemas/bim-json/)

## 文档放置规则

| 文档类型 | 位置 |
|---|---|
| 架构、数据流、模块职责、技术决策 | `docs/architecture/` |
| 验证设计、评估协议、UAT 和样例冻结 | `docs/validation/<topic>/` |
| 稳定参考、合同说明和方法论 | `docs/reference/` |
| 任务操作指南 | `docs/how-to/` |
| 研究总结、周报和人工汇报 | `docs/reports/` |
| 特定日期／阶段的交接快照 | `docs/handoffs/`；不复制长期地图或另立产品权威 |
| Phase SPEC/PLAN/VALIDATION/执行记忆 | `.planning/phases/<phase>/` |
| 数据集说明和 provenance | `dataset/` |
| 机器可读 Schema | `schemas/` |

新增持久文档时：

1. 先选择唯一权威目录；
2. 加入对应分区 README；
3. 只有当前重点或主要入口才同时加入本页；
4. Prompt 必须引用设计权威，不能复制并独立演化设计决定；
5. 移动文档后运行本地链接检查，避免 Path drift。

- [材质与外观修复：三个真实运行的中文报告](../dataset/processed/proof/repair/phase12/presentation-cases/REPORT.md)（运行 PASS，人工待审）。
