# A/B 真实运行记录：Brief 外观字段合同阻断

状态：**A 已阻断，无可交付 IFC；B 未启动；未登记 Proof、未人工验收。** 代码提交 `2231c06b`。原始参考 IFC 与所有旧运行均保留。

本轮先解决“缺少语义提取却授权删除”的问题：新增 Brief 2.2、逐类语义检查、真实用户轮次绑定，以及最多一次、共用任务预算的语义校正。校正不能改变尺寸、位置、楼层、用户决定，也不能删除已结构化的要求。旧版 Schema/Prompt 文件保持不变；CLI 可显式选择 `--design-brief-schema-version 2.2`，普通默认版本与 legacy_full 默认策略保持。

离线阶段有效覆盖 658 个独立用例。完整阶段运行含 390 项接口检查、145 项公共流程及120项原生 IFC 检查；其中一个旧 CLI 夹具需要明确空语义清单，保留失败记录后重跑该文件9项通过。随后增加3个非 ready/unresolved 边界案例，76项聚焦复验通过。冻结20项旧失败族已通过。这是回归和可行性证据，不是系统能力提升或建筑规范认证；没有运行 Full Preflight。

## 本次真实过程

A 从冻结中文原文和已批准对话重新开始，会话 `135976189dc358f9`，没有复用旧 Brief 或候选。新运行收到4次真实 Provider 响应：初次 Brief、Brief 语义校正、Generation、Audit。随后 ChangeSet 在本地输入 token 门控被拒绝，没有发送该次请求。

初次 Brief 已保留19项材料要求、19项门窗模板要求，但外观检查声明为 specified，实际没有对应记录。新检查在生成前发现了这个冲突，触发一次校正。

校正保持了几何和已结构化要求，却新增34项“外观”对象，例如窗记录使用 `frame_color`、`frame_profile`、`glazing_transparency` 和 `profile`。这些属于部件风格说明，并不是现有整件 appearance 的合法字段。现有 BIM JSON 2.1 整件外观只支持数值 RGB 与透明度，Brief 2.2 的对象约束过宽，错误地通过了这批记录。

后续 Audit 阻断了输出；修正这些错误时构造的 ChangeSet 输入超过本地上限。因此本轮没有 IFC，也没有用参考图片冒充结果。问题已经收窄到 **Brief 源头的外观字段格式与部件/整件作用范围**；19项材料记录没有再被当作“无要求”清空。

本任务 A 累计预算记录16个槽位，其中15个有真实 Provider 响应，1个为本地发送前拒绝。累计真实响应 usage 为909712 token；预算账本含失败预留，共计1265772 token、1277.047秒。保留原账本，不手动退回失败预留。B 本任务仍为0次调用。

## 后续修复边界

从实际 BIM JSON 外观 Schema 派生 Brief 的字段约束；不为本例建立文字别名或偷偷将文字颜色转换为整件覆盖。新增版本说明：整体主题放入 profile/style_notes；默认窗框、玻璃与门扇分色由已批准的主题和模板表达；只有明确的整件数值覆盖进入构件 appearance。超出支持范围的明确要求应说明或澄清。

先冻结合法 RGB/透明度、文字值、未知部件字段、空对象和跨构件案例，验证非法记录在 Brief/校正边界被拒绝。完成离线验证前，不继续 Provider；本轮失败保留在本目录，后续使用新的运行目录并继承预算。

## 核查入口

- [A 原始输入](inputs/A-revise/request.txt)、[A 已批准澄清](inputs/A-revise/clarification.txt)、[B 原始输入](inputs/B-retain/request.txt)、[B 已批准澄清](inputs/B-retain/clarification.txt)
- [阶段准入与补充复验](admission.json)、[76项聚焦结果](validation-nonready/nonready-authority-scoped-20260910.xml)
- [初次 Brief 检查](A-revise/runtime/runs/135976189dc358f9/calls/01-design-brief/initial-validation.json)
- [校正后的 Brief](A-revise/runtime/runs/135976189dc358f9/calls/01-design-brief/semantic-repair/design-brief.json)
- [候选 JSON](A-revise/runtime/runs/135976189dc358f9/generator/candidate.json)
- [Audit](A-revise/runtime/runs/135976189dc358f9/audit/audit-report.json)
- [发送前拒绝记录](A-revise/runtime/runs/135976189dc358f9/changeset-round-01/provider-error.json)
- [完整预算账本](A-revise/runtime/runs/135976189dc358f9/generation-budget.json)、[运行状态](A-revise/execution.json)、[后续调用暂停记录](RUN-HOLD.json)
