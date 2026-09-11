# Validation and Evaluation Documentation

最新报告：[Phase 10.5 Window Occurrence Fidelity 与验证加速](ifc2x3-changeset/phase10.5-window-fidelity-validation-report.md)。
本阶段增加 occurrence 属性输入/授权复用、Ground Truth Comparator 和不可变
validation cache；AdvancedProject 冷/热完整验证均进入 180 秒 / 4 GiB
门槛。真实 DeepSeek r21 已通过 RepairIntent 0.4、Bound ChangeSet 0.3、
Production/private L1/L2 与 occurrence fidelity，且没有 synthetic fallback。

用于汇报和人工检查的 original/damaged/repaired IFC、Agent 输出和验证报告见
[IFC Repair 成功案例集](../../dataset/processed/proof/ifc-repair-success-cases/README.md)。

本目录集中保存可执行的验证设计、评估协议、样例冻结规则和配套实施指令。

## Repair Milestone R1 最终验收冻结包

- [R1 冻结包索引](repair-milestone-r1/README.md)
  - 冻结当前 IFC2X3 bounded semantic repair 能力声明、4 个公开模型与 12 个
    待执行案例。
  - 包含模型/请求 SHA、稳定 IFC identity、能力覆盖、现有 Proof 约定和明确
    non-claims；当前状态仅为等待人工 freeze approval，不代表 genuine E2E 或
    final IFCCompare 已执行。

## Agent 能力评测与真实 LLM 准入

- [Agent Debug、能力评测与真实 LLM 准入协议](agent-capability-evaluation.md)
  - 规定单例 Bug、失败类别鲁棒性和系统能力提升三种声明的证据边界。
  - 要求修复前冻结 Failure Family，并进行 Baseline/Candidate 配对评测。
  - 验证分为 scoped validation、阶段首次进入/失效后的 Stage Preflight，以及需要用户明确批准的 Full / repository-wide preflight。
  - 真实 LLM 调用前必须已有当前 stage 的有效 Admission；缺失或失效时 fail-closed，不能自动用 Full Preflight 兜底。

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
