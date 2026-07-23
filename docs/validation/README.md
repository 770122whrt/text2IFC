# Validation and Evaluation Documentation

最新报告：[Phase 10.1 显式 IFC 属性写入与验证](ifc2x3-changeset/phase10.1-validation-report.md)。
本阶段完成精确标量 Pset authoring、occurrence scope 保护、Type 复用/模板
fallback 和 reopened L2；属性检索/RAG 仍属于独立的 Phase 10.2。

本目录集中保存可执行的验证设计、评估协议、样例冻结规则和配套实施指令。

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
