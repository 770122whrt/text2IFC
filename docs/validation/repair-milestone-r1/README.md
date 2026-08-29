# Repair Milestone R1 最终验收冻结包

本目录是 `Repair Milestone R1 — IFC2X3 Bounded Semantic Repair Closed Loop`
的执行前冻结包。权威任务边界来自
[`repair-milestone-r1-final-acceptance.md`](../../handoffs/repair-milestone-r1-final-acceptance.md)。

本冻结包只声明当前实现、选择公开 IFC2X3 模型、绑定测试请求并规划未来
Proof。它没有调用 DeepSeek，没有执行 genuine E2E，没有运行最终 IFCCompare，
没有整理新的 Proof，也没有关闭 Phase 12.1 或 R1。

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

## 后续执行顺序（本任务不执行）

1. 人工审查并明确批准本冻结包。
2. 在相同最终代码版本上重跑原 Plan 07 四案；它们仍是独立的 Phase 12.1
   closure evidence，不计入本 R1 12 案。
3. 按 `E1 → E2 → E3 → E4 → M1 → M2 → M3 → H1 → H2 → H3 → H4 → A1`
   执行 R1 genuine cases；任何 deterministic/infrastructure defect 保留失败并停止。
4. 成功后使用现有 validation 0.2、FILES 0.2、collection 0.1 约定独立复算和
   curate Proof。
5. 仅对具有合法私有三元真值的既有独立集合运行 final IFCCompare；R1 diversity
   cases 为 0 个。

## 当前停止点

冻结包已准备，等待人工 freeze approval。不得从本 README 推断已经获得 Provider
或 Proof 结果。
