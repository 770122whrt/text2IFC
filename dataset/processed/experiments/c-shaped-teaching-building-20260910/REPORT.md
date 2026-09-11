# 三层 C 型教学活动楼：真实运行暂停报告

2026-09-10，本次真实运行停在 Design Brief，尚未进入 Generation、Audit 或修复。没有生成可交付 IFC，因此没有原生效果图、人工验收或 Proof 登记。任何 `offline-*` 中的 IFC 都是手工夹具经 fake Provider 的离线产物，不能作为本次交付。

[中文输入](request.txt) · [具体授权](authorization.json) · [运行记录](live-run/execution.json) · [预算账本](live-run/runs/41edcb4296d1b826/generation-budget.json) · [发送的 Prompt](live-run/runs/41edcb4296d1b826/calls/01-design-brief/prompt-rendered.md)

## 本次实际发生了什么

- 新场景：向东敞开的三层 C 型教学活动楼，13.2×16.8米外包络，6间教学室、两段错开的直跑楼梯、21窗、7门；请求由助手以工程师语言编写，事先冻结后经用户授权运行。
- 从全新请求开始，未复用 A/B Brief、IFC、已知问题或独立评价器；使用 `legacy_full`、普通 Design Brief 2.3，目标 Provider 为 api.deepseek.com / deepseek-v4-flash。
- Run ID：`41edcb4296d1b826`。2026-09-10 13:41:39 至 13:46:26 UTC。唯一一次调用位于 Brief 阶段，异常为 `OpenAICompatError: OpenAI-compatible chat completion is truncated: finish_reason=length`。这条异常由运行终端返回；原始响应未持久化。
- 账本记录1次失败调用、83,996 token、282.296秒活动时间。整轮批准上限为32次、200万 token、3600秒，远未耗尽。单次输出上限与整轮共享预算是两个不同限制；不能通过剩余整轮预算推断这次响应未截断。
- 当前终态为 `exception`，不是 compiled，也没有完成 Brief 内容验证。无法判断模型是否提出了合理性疑点，或 C 型建模能否完成。

## 原因与证据缺口

直接触发原因是 Provider 截断。更深层的输出原因仍不明：本地没有原始响应，不能断言是 Prompt 冲突、重复输出、推理耗尽或 Schema 过大，也不能据此把问题归因于 C 型几何。

同时确认一个确定性的留痕缺口：`run_design_brief_stage` 在 `provider.generate_live` 成功返回之后才调用 `write_live_trace`。适配器抛出截断/无 choices/连接异常时，响应和请求虽附在异常对象上，却没有由这个入口写盘；预算包装器只结算 usage，运行脚本最终也只记录异常类型。进程已结束，这次缺失的原始响应不能从现有文件恢复，不补造、不用重跑替代。

这与已有修复的关系是入口覆盖不完整：CLI Brief invoker、Audit、ChangeSet 及 Brief 语义校正已有各自失败记录；本次使用的初始公共 Brief stage 没有接入同一失败保存机制。尚无证据说明此前那些已修入口发生倒退。

[离线复现脚本](validation/reproduce_brief_failure.py) · [四类观测](validation/brief-failure-family-02/result.json)

复现使用完全合成的 SDK transport，分别输入教室、仓库、住宅、办公室请求：截断、无 choices、连接异常均没有留下 stage 的失败记录；截断和无 choices 的 response 仍在异常中。空内容作为对照正常留下原始响应并被拒绝为无效 Brief，说明缺口在异常路径。第一次诊断脚本误把空内容也预期为异常，已在第二次更正，首次目录保留。这些是缺陷定位证据，不是真实 Provider 结果，也不是修复通过证据。

## 下一步限定范围

1. 在公共 Brief stage 复用已有失败 trace 保存机制，并阻止相同 attempt 目录覆盖历史输入/响应；保留正确预算结算、异常类型和无输出状态。
2. 覆盖直接 stage 与完整公开调用方：截断、空内容、malformed、无 choices、连接失败、无 usage、重复 attempt、正常 ready、澄清及恢复。将该遗漏入口加入准入覆盖，而不是只验证已有 CLI invoker。
3. 先通过这些离线检查并更新局部准入，再考虑同一任务预算内的新 attempt。已有83,996 token、1次调用、282.296秒必须继承，不清零。依据真正保存的响应再决定是否调整阶段输出约束、Prompt 或 Schema；不盲目提高上限。

本次按“遇到问题暂停”的约定停止真实调用，尚未修改产品代码或注册版本，尚未执行以上修复或新的真实尝试。

## 验证边界

运行前已有11项凹形几何测试通过（C/U/L、缩放和镜像），新 runner 的完整 fake 公共链路通过，485项独立原生 IFC 检查通过，5个错误模型对照被拒绝。见 [离线记录](README.md)。本次失败说明原准入对初始 Brief 的异常持久化覆盖不足；这些离线成功不能抵消真实失败。Full Preflight 未运行。

A/B 已在另一集合人工验收：[已验收 Proof](../../proof/generation/phase6.6/three-storey-clarification-ab-20260910/REPORT.md)。本次 C 案例不改变 A/B 状态，也不能用于估计系统稳定成功率。
