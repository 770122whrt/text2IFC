# text2IFC 文档入口

先读当前功能对应的一行。旧执行计划、逐轮讨论和清理过程从固定 Git 版本查询，不作为当前执行指令。

Repair 数据与许可、A–G 结果和题型分析分别见[数据报告](reports/repair-dataset-1200-summary-20261015/README.md)、[实验结果](reports/repair-experiment-summary-20261015/README.md)和[题型统计](reports/repair-task-types-20261017/README.md)；各自维护原始材料与本地保留范围。

| 工作 | 正文 | 验证／证据 |
|---|---|---|
| Generation | [生成流程](architecture/current-workflow-and-data-flow.md)、[语义与外观范围](architecture/semantic-appearance-plan.md) | [Generation Proof](../dataset/processed/proof/generation/)、[研究与文献](reports/generation-demo/README.md) |
| Repair | [Repair 方法与边界](architecture/ifc-repair-pipeline-status-and-roadmap.md) | [Repair Proof](../dataset/processed/proof/repair/)、[研究三文档](reports/repair-demo/README.md) |
| Repair 对比实验 | [实验专题](validation/repair-comparison/README.md) | [当前实验表](../dataset/processed/experiments/repair-comparison/current/README.md)、[20 题审阅](../dataset/processed/ifc-repair/repair-comparison/formal/README.md)；系统、链路、批准状态和用量由专题维护 |
| IFC2Text | [当前入口](validation/ifc2text/README.md)、[门窗部件合同](architecture/text2ifc-component-plan-v1.0.md) | [往返结果](validation/ifc2text/component-v26/README.md) |
| 数据与知识 | [来源和布局](../dataset/data_organization.md)、[IFC 知识来源](reference/ifc2x3-knowledge-sources.md) | [来源目录](../dataset/sources/CATALOG.md)、[Manifest](../dataset/manifests/README.md) |

## 开发所需

- [接管指南](how-to/agent-takeover.md)、[命令地图](../scripts/README.md)。
- [当前状态](../.planning/STATE.md)、[产品约束](../.planning/PROJECT.md)、[路线](../.planning/ROADMAP.md)。当前 UI 结合准备和本地精简从 STATE 与[清理记录](reports/workspace-cleanup-20261017/README.md)进入。
- [Agent 调试与验证协议](validation/agent-capability-evaluation.md)、[Proof 格式](validation/ifc-repair-proof-format.md)。
- [架构索引](architecture/README.md)、[验证索引](validation/README.md)、[合同参考](reference/README.md)、[研究与报告](reports/README.md)。
- [GitHub 发布](how-to/publish-to-github.md)、[main 精简与验证历史（2026-10-07）](reports/lean-branch-20261007/REPORT.md)。

## 文档维护

架构放 `architecture/`，稳定合同说明放 `reference/`，操作步骤放 `how-to/`，验证规范放 `validation/`，研究和执行报告放 `reports/`。
当前状态只在 STATE 维护；其他索引链接到负责该事实的结果页，不复制变化中的统计。Phase SPEC／VALIDATION 保留在 `.planning/phases/`。
已接受证据、原始响应和失败记录保持原字节与状态。历史外链固定到对应 Git 版本，旧交接、完成计划和恢复入口不自动授权重跑。
