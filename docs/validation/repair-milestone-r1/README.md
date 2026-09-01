# Repair Milestone R1 最终验收冻结包

本目录是 `Repair Milestone R1 — IFC2X3 Bounded Semantic Repair Closed Loop`
的执行前冻结包。权威任务边界来自
[`repair-milestone-r1-final-acceptance.md`](../../handoffs/repair-milestone-r1-final-acceptance.md)。

本冻结包建立时只声明当前实现、选择公开 IFC2X3 模型、绑定测试请求并规划未来
Proof；该段是冻结时的历史边界。2026-09-01 的 genuine 执行状态见下方“执行
checkpoint”。最终 IFCCompare、R1 Proof 0.3 和 Phase 12.1/R1 闭合仍未完成。

## 冻结结论

- R1 新验收集：4 个公开 IFC2X3 模型、12 个案例。
- 难度：Easy 4、Medium 3、Hard 4、Capability-driven 1。
- 单操作 9；多操作/原子事务 3。
- 成功路径 9；值不兼容后纠正 1；自然澄清后续跑 1；不支持事务守卫 1。
- family：Beam、Column、Window、Door、Wall；Opening/Door fill/Window add 的注册
  能力不纳入本次 R1 最终声明。
- 属性：`IsExternal`、`FireRating`、`Reference`、`AcousticRating`、
  `LoadBearing`。
- IFC value type：`IfcBoolean`、`IfcLabel`、`IfcIdentifier`。
- R1 diversity case 没有合法的 pristine/damaged/repaired 私有三元真值；因此
  不制造 IFCCompare Ground Truth。所有成功路径仍需 source/repaired preservation
  对比与 L0/L1/L2。

`SUPPORTED_AND_ACCEPTANCE_ELIGIBLE` 在这些文档中表示“当前生产合同允许进入待执行
的冻结验收集”，不表示 genuine case 已经通过。只有后续真实执行、独立复算与 Proof
curation 全部通过后，才能升级为已接受能力。

## 文件

- [当前能力声明](repair-capability-manifest.md)
- [模型选择与多样性](repair-acceptance-model-selection.md)
- [冻结案例规格](repair-bound-testcases.md)
- [能力覆盖矩阵](repair-capability-coverage-matrix.md)
- [未来 Proof Matrix 计划](repair-proof-matrix-plan.md)
- [机器可读冻结清单](repair-acceptance-freeze.json)
- [R1 Proof profiles](repair-proof-profiles.json)
- [R1 evaluator 预算补充说明](repair-evaluation-budget-addendum.md)
- [Plan 07 / R1 genuine execution matrix](plan07-r1-genuine-execution-matrix-2026-09-01.md)
- [2026-09-01 checkpoint handoff](../../handoffs/repair-milestone-r1-checkpoint-2026-09-01.md)

## 后续执行顺序（本任务不执行）

1. 人工审查并明确批准本冻结包。
2. 在相同最终代码版本上重跑原 Plan 07 四案；它们仍是独立的 Phase 12.1
   closure evidence，不计入本 R1 12 案。
3. 按 `E1 → E2 → E3 → E4 → M1 → M2 → M3 → H1 → H2 → H3 → H4 → A1`
   执行 R1 genuine cases；任何 deterministic/infrastructure defect 保留失败并停止。
4. 成功后使用复用现有 Proof 架构的 R1 后继合同独立复算和 curate Proof：
   validation 0.3、collection 0.2、terminal 0.1、profile 0.1。历史 Plan 07
   继续使用原 validation 0.2 / collection 0.1，二者不混写。
5. 仅对具有合法私有三元真值的既有独立集合运行 final IFCCompare；R1 diversity
   cases 为 0 个。

## 执行 checkpoint — 2026-09-01

- Plan 07 四案已有 genuine Provider case-contract 结果，但顶层 Proof eligibility
  仍为 false/pending，不能据此关闭 Phase 12/12.1。
- R1 fresh ordered run 已完成 E1-E4、M1-M3、H1、H2，共 9/12；H3 以
  `LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED` fail-closed，H4/A1 未执行。
- 九个成功案保留 repaired IFC 和记录的 L0/L1/L2；尚未执行 R1 Proof 0.3、
  final IFCCompare 或 Phase closure。
- 新对话应从 checkpoint handoff 和 execution matrix 开始，先诊断 H3 target
  resolution。不得把不同 run 的成功行拼成 12/12，也不得启动 Phase 13。
