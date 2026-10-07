# text2IFC 文档入口

先读当前功能对应的一行。旧执行计划、逐轮讨论和清理过程已从精简分支移出，历史内容从固定 Git 版本查询。

| 工作 | 正文 | 验证／证据 |
|---|---|---|
| Generation | [生成流程](architecture/current-workflow-and-data-flow.md)、[语义与外观范围](architecture/semantic-appearance-plan.md) | [Generation Proof](../dataset/processed/proof/generation/) |
| Repair | [Repair 方法与边界](architecture/ifc-repair-pipeline-status-and-roadmap.md) | [Repair Proof](../dataset/processed/proof/repair/)、[研究三文档](reports/repair-demo/README.md) |
| IFC2Text | [当前入口](validation/ifc2text/README.md)、[门窗部件合同](architecture/text2ifc-component-plan-v1.0.md) | [往返结果](validation/ifc2text/component-v26/README.md) |
| 数据与知识 | [来源和布局](../dataset/data_organization.md)、[IFC 知识来源](reference/ifc2x3-knowledge-sources.md) | [Manifest](../dataset/manifests/README.md) |

## 开发所需

- [接管指南](how-to/agent-takeover.md)、[命令地图](../scripts/README.md)。
- [当前状态](../.planning/STATE.md)、[产品约束](../.planning/PROJECT.md)、[路线](../.planning/ROADMAP.md)。
- [Agent 调试与验证协议](validation/agent-capability-evaluation.md)、[Proof 格式](validation/ifc-repair-proof-format.md)。
- [合同参考](reference/README.md)、[GitHub 发布](how-to/publish-to-github.md)。
- [2026-10-07 精简、重构与验证记录](reports/lean-branch-20261007/REPORT.md)。

## 文档维护

架构放 `architecture/`，稳定合同说明放 `reference/`，操作步骤放 `how-to/`，验证规范放 `validation/`，研究和执行报告放 `reports/`。
当前状态只在 STATE 维护；新报告不复制整套项目历史。Phase SPEC／VALIDATION 保留在 `.planning/phases/`。
已接受证据、原始响应和失败记录保持原字节与状态。本分支中的历史外链固定到清理前的 Git 版本。
