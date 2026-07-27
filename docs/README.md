# text2IFC 文档索引

本页是 `docs/` 的稳定入口。具体文档按职责分区，避免把设计、实施 Prompt、
验证方案和历史报告混放在根目录。

## 从这里开始

| 目的 | 入口 |
|---|---|
| 了解已有/damaged IFC + 文本如何生成可验证的新 IFC，以及后续 Phase 安排 | [IFC2X3 修复链路与后续路线](architecture/ifc-repair-pipeline-status-and-roadmap.md) |
| 了解当前系统如何运行 | [当前工作流与数据流](architecture/current-workflow-and-data-flow.md) |
| 浏览系统架构和阶段演进 | [Architecture Index](architecture/README.md) |
| 查找验证、评估和 UAT 方案 | [Validation Index](validation/README.md) |
| 查找 BIM JSON、IFC2X3 和 Provider 参考 | [Reference Index](reference/README.md) |
| 查看研究总结和周报 | [Reports Index](reports/README.md) |
| 查看项目计划和当前状态 | [`.planning/`](../.planning/PROJECT.md) |

## 当前重点

- [IFC2X3 修复链路与后续路线](architecture/ifc-repair-pipeline-status-and-roadmap.md)
  - 参考成功案例文档排布，完整说明已实现 Repair Pipeline、放行证据、失败路由
    和后续 Roadmap。
- [IFC2X3 Local ChangeSet 评估设计](validation/ifc2x3-changeset/design.md)
  - 既有 IFC 局部修改、紧凑 LLM Context、可扩展 Operation Registry。
- [IFC2X3 Local ChangeSet 实施 Prompt](validation/ifc2x3-changeset/implementation-prompt.md)
  - 实施顺序、离线测试和真实 Provider UAT。
- [当前 text2IFC 工作流与数据流](architecture/current-workflow-and-data-flow.md)
  - 多 Agent、BIM JSON、Gate、IFC 编译、ChangeSet 和报告链路。

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

目录：[`docs/how-to/`](how-to/publish-to-github.md)

- [发布到 GitHub](how-to/publish-to-github.md)

保存面向具体任务的操作步骤。

### Reports

目录：[`docs/reports/`](reports/README.md)

保存项目研究总结、周报和历史汇报。报告不是架构或验收标准的权威来源。

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
- [Dataset Manifest Format](../dataset/manifests/README.md)
- [Authorized BIMNet IFC2X3 Manifest](../dataset/manifests/bimnet-ifc2x3.jsonl)
- [BIMNet Extraction Audit](../dataset/processed/bim-json-2.0/extraction-audit.json)
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
| Phase SPEC/PLAN/VALIDATION/执行记忆 | `.planning/phases/<phase>/` |
| 数据集说明和 provenance | `dataset/` |
| 机器可读 Schema | `schemas/` |

新增持久文档时：

1. 先选择唯一权威目录；
2. 加入对应分区 README；
3. 只有当前重点或主要入口才同时加入本页；
4. Prompt 必须引用设计权威，不能复制并独立演化设计决定；
5. 移动文档后运行本地链接检查，避免 Path drift。
