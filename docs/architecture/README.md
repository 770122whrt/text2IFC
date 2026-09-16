# Architecture Documentation

本目录记录系统结构、阶段演进、关键决策和实现边界。验证协议、实验样例与验收
设计放在 [`../validation/`](../validation/README.md)，历史汇报放在
[`../reports/`](../reports/README.md)。

## 当前系统入口

- [IFC2X3 修复链路与后续路线](ifc-repair-pipeline-status-and-roadmap.md)
  - 按 LLM、确定性代码和人工职责说明 Phase 7—10.1 的完整 Repair Pipeline，
    并统一列出属性检索、批量 Window、Door、梁柱和大型 IFC Roadmap。
- [text2IFC Generation 工作流与数据流（截至 Phase 6.5）](current-workflow-and-data-flow.md)
  - 两种生成策略、数据权威、Agent/Gate/Compiler 职责和失败路由；当前
    milestone 状态仍以 `.planning/STATE.md` 为准。
- [text2IFC Architecture Overview](text2ifc-overview.md)
  - 总体目标、包结构和阶段边界。
- [主工作流代码审计快照（2026-07-16）](main-workflow-code-audit-2026-07-16.md)
  - 基于 `main@67fd3be7` 的历史核对结果；其中运行状态不能替代当前代码和
    `.planning/STATE.md`。

## 专题设计与决策

- [IFC2Text：从建筑模型到可重建的设计说明](bim2text-bidirectional-bridge-research.md)：楼层—房间—构件的解析与描述、程序化往返比较，以及空间推导与描述策略的迭代学习；复用现有 text2IFC，第一阶段开发中，真实往返尚未完成；操作、变更和验证见[实施记录](../reports/ifc2text-phase1-implementation-2026-09-16.md)。

- [两层光庭阅读馆设计](courtyard-library-design.md)：露天光庭与二层回廊已确认；按用户委托确定布局与材料，覆盖适用的已有能力，区分栏杆现有表达与扩展范围。

- [Repair 与 Generation 的 Type、材质、属性和外观计划](semantic-appearance-plan.md)
  - A/B/C 已人工验收，当前推进光庭阅读馆；项目内 Type 按需组织，小型内置模板与 Generation 基础门窗细节；默认配色，不补写缺省材料/性能属性；Repair 保留原几何，不实现跨 IFC 参照。
- [Token 效率与质量保全计划](token-efficiency-plan.md)
  - 一次有界 Audit 真实配对已完成；其他研究后置，主线回到 C 型教学楼。
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

- [目录瘦身与后续重构方案](repository-organization-refactor.md)：基于当前体积和消费者的分步建议；未实施的行为重构另行审查。
