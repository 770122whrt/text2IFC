# A/B 全新运行与诊断审查（2026-09-10）

**A 已完成3次真实 Provider 调用后被共用 pipeline 缺口阻断，没有发布 IFC；B 按遇错停止要求暂停，尚未调用。** 本包保留真实失败证据，不登记 Proof，不标为人工验收。自动审批的首次拒绝已由用户后续明确授权解决，当前阻断来自产品代码。

| 分支 | 人工输入与决定 | 本次结果 |
| --- | --- | --- |
| A：调整内部布局 | [原请求](inputs/A-revise/request.txt)、[布局澄清](inputs/A-revise/clarification.txt)、[完整对话](inputs/A-revise/conversation.json) | `audit_blocked` / `scope_unresolved`；[运行记录](A-revise/execution.json) |
| B：忠实保留原布局 | [原请求](inputs/B-retain/request.txt)、[保留缺陷的澄清](inputs/B-retain/clarification.txt)、[完整对话](inputs/B-retain/conversation.json) | 未启动；避免在同一共用缺口下继续真实调用 |

A 从全新的真实 Design Brief 开始，未复用旧 Brief、候选或预算。实际策略为 `legacy_full`。每个分支整次 loop 共用32次调用、200万 token、3600秒活动时间上限，保留3轮反馈、无进展、重复候选和 Provider 失败等停止条件；本次没有耗尽预算。脚本对话是已获用户批准的固定输入，不称为本次自然发生的人机澄清。

## 1. 问题出在哪里

1. **请求投影混入了说明文字。** 新 Brief 的外观包含 `profile=warm-residential` 和 `style_notes`；后者是风格说明。`request_semantics_for_case` 把整个外观对象复制成硬性要求，`request_contract_issues` 随后要求候选逐键相等。
2. **两个合同无法同时满足这段文字。** BIM JSON 2.1 顶层 appearance 只允许 `profile`、`seed`，且 `additionalProperties=false`，因此候选不能合法携带 `style_notes`。此次候选已正确选用 warm-residential，仍触发两条 `REQUEST_APPEARANCE_MISMATCH`，编译在请求校验前置门被挡住。两条相同来源来自 Brief 和冻结 expected facts 的重复投影，不是两个独立设计错误。
3. **反馈缺少可执行目标。** Audit 尊重门禁返回 blocked；随后 `/appearance` 和编译失败摘要被归入 context-only issue。`scope-resolution.json` 的 actionable issue 为空，局部 scope 无法定位实体或关系，因此没有发起 ChangeSet 调用。通用编译失败摘要还掩盖了真正的外观合同原因。

刚发现时曾初步怀疑额外 seed；实际代码及只读反事实复现已排除这一解释：移除 seed 仍失败，仅从机器比较中排除 style_notes 后这项误报消失。这里没有改写运行中的请求、候选或任何发布 Schema。

这次候选包含75个实体，**没有额外 Type/Style**；四项动态完整性、归属、名称及 void/fill 门均通过。上一轮的 Type/身份错误没有在本次候选中复现，但这也不能证明那些修复提升了整体收敛率。此次根因位于更早的请求投影与顶层外观校验，不是 Type 图补丁再次破坏几何。由于未编译出 IFC，不能据候选 JSON 声称几何、材料或视觉审查通过。

## 2. 建议的小范围修复

- 从现有外观合同派生机器可检查字段，只将受支持、已冻结的 profile/seed 等结构化选择纳入严格比对。实际字段错误仍须阻断，不能靠忽略全部 appearance 来放行。
- 风格说明及其来源继续保留给 Audit 和中文报告；涉及可量化颜色或未支持要求时按已有语义/澄清规则处理，不静默丢弃用户要求，也不让自然语言备注成为不可能满足的 Schema 字段。
- 先修并验证这条投影边界，覆盖合法说明、真正 profile/seed 冲突、缺失值和恢复时冻结值保全，以及 legacy_full/staged 公共链路。顶层文档字段的受控修复是独立范围，不直接扩大全文编辑权限。本次尚未实施产品修复或改 Prompt/Schema。

已冻结[只读复现脚本](diagnostics/appearance-projection-reproduction.py)与[结果](diagnostics/appearance-projection-reproduction.json)：原案例两条误报，去 seed 仍失败；内存中只排除 style_notes 的比较不再报错。14项跨主题、中英文说明与 seed 正反边界中，4项合法说明案例在当前实现中误报；复现命令按设计退出1。它们是离线失败族，不是新 Provider 结果或能力指标。仅比较器通过不证明 IFC 合规，修复后仍须完整编译重读及公共路径回归。

## 3. 真实调用和证据

目的地 `api.deepseek.com`，模型 `deepseek-v4-flash`。会话 `026823cac75af845`：

| 环节 | 实际 reported token | Provider活动时间 | 结果 |
| --- | ---: | ---: | --- |
| Design Brief | 43,713 | 96.922秒 | ready |
| Generator | 79,389 | 135.172秒 | Schema合法候选，后续请求外观校验失败 |
| Audit | 49,206 | 27.813秒 | blocked，未覆盖确定性门禁 |
| 合计 | 172,308 | 259.907秒 | 3次调用；没有 ChangeSet transport |

[原始 Brief 调用](A-revise/runtime/runs/026823cac75af845/calls/01-design-brief/response.raw.json)、[原始 Generator 调用](A-revise/runtime/runs/026823cac75af845/generator/response.raw.json)、[原始 Audit 调用](A-revise/runtime/runs/026823cac75af845/audit/response.raw.json)、[预算账本](A-revise/runtime/runs/026823cac75af845/generation-budget.json)、[请求检查](A-revise/runtime/runs/026823cac75af845/request-semantics.json)、[scope 解析](A-revise/runtime/runs/026823cac75af845/changeset-round-01/scope-resolution.json)、[生产运行报告](A-revise/runtime/runs/026823cac75af845/report.md)均保留。运行墙钟约272.87秒，不能与 Provider 活动时间混用。

[载荷预览](payload-preview.json)、[用户明确发送确认](explicit-egress-confirmation.json)、[首次自动审批拒绝记录](execution-hold.json)保留；拒绝发生在进程创建前，不算 Provider 失败。新的[产品缺口暂停记录](RUN-HOLD.json)阻断后续真实调用，须先离线修复和适用准入复核。

## 4. 验证范围与未完成事项

基线 `60191979`，当前[阶段准入](admission.json)记录运行前状态。环节243、公共完整链路124、IFC重读120项，共487 passed，零失败/错误/跳过；另新运行器2项聚焦离线测试通过。范围见[命令/时间/日志哈希](validation/checks.json)和[环节日志](validation/seams.log)、[公共日志](validation/public-chain.log)、[IFC日志](validation/reopened-ifc.log)。compileall和适用 diff 检查通过。准入绑定619份文件；真实运行暴露新缺口后，该准入不能不经修复复核继续放行。

旧首次运行174份、续跑335份冻结文件哈希保持；旧 IFC、旧失败记录与旧 RUN-HOLD 不改。487项离线测试未覆盖本次风格说明投影缺口，所以不能由通过数推断所有组合都正确。新增失败族及这一次失败需一起保留。

未执行：新的 B Provider 调用、A/B 成功 IFC 发布、新 IFC 逐项检查或视觉检查、人工验收、accepted Proof 安装、Full Preflight、GitHub push。没有新的 IFC 可以交付审查，不以旧 IFC 或手工修改候选替代。B 的用户确认零净空问题仍保留，今后也不能写成合理性或建筑规范通过。本次结论为**真实运行失败并定位通用边界缺口**，不是完整 A/B 通过或系统能力提升。
