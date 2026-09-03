# Architecture Documentation

本目录记录系统结构、阶段演进、关键决策和实现边界。验证协议、实验样例与验收
设计放在 [`../validation/`](../validation/README.md)，历史汇报放在
[`../reports/`](../reports/README.md)。

## 当前系统入口

- [IFC2X3 修复链路与后续路线](ifc-repair-pipeline-status-and-roadmap.md)
  - 按 LLM、确定性代码和人工职责说明 Phase 7—10.1 的完整 Repair Pipeline，
    并统一列出属性检索、批量 Window、Door、梁柱和大型 IFC Roadmap。
- [当前 text2IFC 工作流与数据流](current-workflow-and-data-flow.md)
  - 当前端到端流程、数据权威、Agent/Gate/Compiler 职责和失败路由。
- [text2IFC Architecture Overview](text2ifc-overview.md)
  - 总体目标、包结构和阶段边界。
- [主工作流代码审计（2026-07-16）](main-workflow-code-audit-2026-07-16.md)
  - 文档主张与实际代码路径的核对结果。

## 专题设计与决策

- [Feedback Routing Design](feedback-routing/design.md)
- [Feedback Routing Implementation Prompt](feedback-routing/implementation-prompt.md)
- [Text-to-JSON RAG、Fine-tune 与 Agent 决策](text2json-rag-finetune-decision.md)
- [Phase 6 Model Decision](phase-6-model-decision.md)
- [Phase 6 Multi-agent Design](phase-6-multiagent-design.md)

## 阶段总结

- [Phase 2.5 BIM JSON 2.0 IFC Semantic Graph](phase-2-5-summary.md)
- [Phase 3 Text-to-JSON Dataset and Baseline](phase-3-summary.md)
- [Phase 4 High-fidelity IFC Round Trip](phase-4-summary.md)
- [Phase 4 Wave 0 Generated IFC Gate](phase-4-wave-0-generated-ifc-gate.md)
- [Phase 5 Multi-turn Clarification Agent](phase-5-summary.md)
- [Phase 6 Acceptance and Trace Report](phase-6-acceptance-and-trace-report.md)

阶段规格、计划和验证记录的权威位置仍是
[`../../.planning/phases/`](../../.planning/phases/)。
