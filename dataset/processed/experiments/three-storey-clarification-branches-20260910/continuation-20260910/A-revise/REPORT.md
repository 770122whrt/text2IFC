# A：复用真实 Brief 后的续跑

**本次失败，无可交付 IFC，不登记 Proof。** 用户已确认的内部调整方案与原输入保持不变。

本次会话 `60b27145d6d8d3a3` 复用了首次真实会话 `48dcf264b1a6df16` 的 Design Brief，随后执行2次新的真实调用：Generator 和 Audit。两次新增消耗144,164 reported token、202.063秒 Provider 活动时间；连同首次4次，A 累计6次、432,626 token、648.813秒，达到调用数上限。最终状态为 `budget_blocked`，后续 ChangeSet 在 transport 前被预算阻断。

生成结果通过 JSON 合同，但再次增加39个未请求的 Type／Style、39条 Type 关联，以及34项未授权普通属性（如 `Pset_WindowCommon.IsExternal`）。请求级检查明确拒绝这些内容，未进入可发布 IFC；不是 IfcOpenShell 崩溃，也不是尺寸设计需要用户重新选择。Audit 保留了 A 的修订决定并记录 `not_verified`，没有越过硬门。此次问题已从首次的“类型上额外材料”转为“额外 Type 和属性”，证明只修单个字段或继续同样生成不能保证收敛。

已经修复的语义字段权限和楼梯名称检查继续有效，但本轮未实施多余 Type 的自动删除或继承值迁移，因此不能把“准确拦截”说成“自动修复成功”。尚无本次 IFC，可视外观、独立净空与完整请求逐项验收均未执行。

- [原始中文请求](../../A-revise/request.txt) · [A 的授权澄清](../../A-revise/clarification.txt)
- [执行和累计预算](execution.json)
- [本次真实 Generator 候选](runtime/runs/60b27145d6d8d3a3/generator/candidate.json)
- [确定性语义拒绝依据](runtime/runs/60b27145d6d8d3a3/semantic-verification.json)
- [真实 Audit](runtime/runs/60b27145d6d8d3a3/audit/audit-report.json)
- [预算停止依据](runtime/runs/60b27145d6d8d3a3/generation-budget-decision.json)
- [首次失败，完整保留](../../A-revise/REPORT.md)

这是已暴露案例的真实续跑记录，不是盲测能力提升证据。下一步应先处理请求约束如何限制生成和局部改正 Type 图；不再追加调用来碰运气，也不手工改候选后冒充真实生成成功。
