# Validation and Evaluation Documentation

Repair 当前说明见[技术主文档](../architecture/ifc-repair-pipeline-status-and-roadmap.md)，
历史正式验收见[R1 最终矩阵（2026-09-03）](repair-milestone-r1/repair-proof-matrix-2026-09-03.md)。
[Phase 10.5 Window 验证与加速](ifc2x3-changeset/phase10.5-window-fidelity-validation-report.md)
是早期专项报告，不再标为全项目最新结果。

用于汇报和人工检查的 original/damaged/repaired IFC、Agent 输出和验证报告见
[工作流 Proof 入口](../../dataset/processed/proof/README.md)。

本目录集中保存可执行的验证设计、评估协议、样例冻结规则和配套实施指令。

## Repair Milestone R1 最终验收冻结包

- [R1 冻结包索引](repair-milestone-r1/README.md)
  - 保留当时的能力声明、模型／请求、案例冻结与证据约定。
  - R1 已有 12/12 冻结案例合同通过的[最终矩阵](repair-milestone-r1/repair-proof-matrix-2026-09-03.md)：11 个有输出、1 个正确无输出。旧准备稿不代表当前仍待执行；该历史结果也不等于新版本的普遍成功率。

## Agent 能力评测与真实 LLM 准入

- [Agent Debug、能力评测与真实 LLM 准入协议](agent-capability-evaluation.md)
  - 规定单例 Bug、失败类别鲁棒性和系统能力提升三种声明的证据边界。
  - 要求修复前冻结 Failure Family，并进行 Baseline/Candidate 配对评测。
  - 验证分为 scoped validation、阶段首次进入/失效后的 Stage Preflight，以及需要用户明确批准的 Full / repository-wide preflight。
  - 真实 LLM 调用前必须已有当前 stage 的有效 Admission；缺失或失效时 fail-closed，不能自动用 Full Preflight 兜底。

## IFC2Text

- [IFC2Text Validation](ifc2text/README.md)
  - Phase 1 版本化写作 stage、Truth Boundary、Provider seam 与公共 Generation bridge 的离线 Stage Admission；真实 Provider 与真实往返结果单独记录。

## IFC2X3 Local ChangeSet

- [主题索引与运行入口](ifc2x3-changeset/README.md)
  - 权威文档、实现状态、CLI、证据位置和后续能力边界。
- [设计与决策权威](ifc2x3-changeset/design.md)
  - 既有 IFC 作为模型权威；紧凑 LLM Context；增量 ChangeSet Applicator。
  - 首个 Window operation，以及墙洞、门、梁、柱等后续扩展接口。
  - BIM Whale `LargeBuilding.ifc` 样例、曲墙边界和双轨验收。
- [实施 Prompt](ifc2x3-changeset/implementation-prompt.md)
  - 实施顺序、交付物、自动测试和真实 Provider UAT。
- [实现复用地图](ifc2x3-changeset/reuse-map.md)
  - 记录已复用组件、新增职责和已确认的公共测试 seam。
- [实施发现记录](ifc2x3-changeset/implementation-findings.md)
  - 保存实现证据、待审设计冲突及其最终处理决定。
- [Phase 10 Window L2 验证报告](ifc2x3-changeset/phase10-validation-report.md)
  - LargeBuilding 离线与真实 DeepSeek 四路径、Production/private L1/L2、发布证据，以及 10.1 精确属性写入/10.2 检索 RAG 的拆分边界。
- [Phase 10 单链路输入输出说明](ifc2x3-changeset/phase10-single-pipeline-input-output.md)
  - 用一个真实 `complete-request` 案例逐段说明 damaged IFC、Agent、Bound ChangeSet、IFC 写回、L1/L2 和最终发布产物。

## 相关验证资料

- [Generated IFC Gate](../architecture/phase-4-wave-0-generated-ifc-gate.md)
- [Phase 6 Acceptance and Trace Report](../architecture/phase-6-acceptance-and-trace-report.md)
- [Phase 1 Validation](../../.planning/phases/01-bim-json-1-0-contract-and-validator/01-VALIDATION.md)
- [Phase 2 Verification](../../.planning/phases/02-minimum-bim-json-to-ifc2x3-compiler/02-VERIFICATION.md)

## 放置规则

一个验证主题如果包含多份文档，应使用独立子目录：

```text
docs/validation/<topic>/
  design.md
  implementation-prompt.md   # 仅在需要时
  README.md                   # 文档超过两份时添加
```

设计文档负责冻结语义和验收边界；实施 Prompt 不得成为第二个设计权威。
