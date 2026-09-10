# C 型教学楼：Design Brief 单阶段诊断

本次只增加一次真实 Design Brief 响应。相同渲染 Prompt 的重试成功返回 ready，Schema/语义结构校验0项问题，没有触发校正或用户澄清；未执行 Generation、Audit、IFC编译或人工验收。上一次失败及缺失响应的事实原样保留。

[用户输入](../c-shaped-teaching-building-20260910/request.txt) · [成功 Brief](live-attempt/design-brief/design-brief.json) · [本次执行](live-attempt/execution.json) · [诊断摘要](diagnosis.json) · [授权](authorization.json)

## 1. 原因定位到什么程度

**确定事实：** 上次 Provider 返回 finish_reason=length。此次真实重试返回 stop，输出完整合法 Brief。新旧渲染 Prompt 的SHA-256完全相同；沿用相同请求模型、thinking enabled和65,536单次输出上限。此次请求模型为 deepseek-v4-flash，Provider返回模型名为 deepseek-flash，两者原样记录；不将服务端别名视为已验证的底层模型版本。

| 指标 | 上次失败 | 本次单阶段重试 |
|---|---:|---:|
| 输入 token | 未保存拆分 | 18,460 |
| 输出 token（含 reasoning） | 未保存拆分 | 45,174 |
| 其中 reasoning token | 未保存 | 33,759 |
| 可见输出 token（由差额得出） | 未知 | 11,415 |
| 总 token | 83,996 | 63,634 |
| 活动时间 | 282.296秒 | 165.359秒 |
| 终态 | 截断异常，无Brief | ready，合法Brief |

**强证据支持的推断：** 若相同Prompt的输入分词数量不变，则上次83,996 − 18,460 = 65,536，恰好命中单次输出上限。因此更符合“单次生成耗尽输出额度”，不是200万整轮预算耗尽，也不是IFC编译失败。此次成功输出也包含大量reasoning，说明需求整理的生成开销较高。API将length定义为输出/上下文长度限制，见 [DeepSeek官方接口说明](https://api-docs.deepseek.com/api/create-chat-completion/)。

**仍未知：** 上次原始响应已丢失，无法确认它截在reasoning还是JSON正文，也无法确认是否重复生成、卡在某条约束或其他随机行为。一次同配置重试成功不能证明稳定性已经解决，更不能证明Prompt版本冲突导致了截断。

## 2. 本轮已经修复的通用问题

**初始公共Brief异常留痕缺失。** `run_design_brief_stage`现在在Provider抛异常时复用既有安全trace机制，保存异常携带的请求、响应、usage及失败类别，再继续传播异常；连接或预算拒绝不伪造响应。每个attempt目录在写入输入前独占声明，已有输入/响应或已声明目录不得重复使用。预算结算和无输出行为保持。真实旧响应不能追补，本轮只保证今后相同异常路径能保留已有证据。

失败族修改前14失败/3通过；修复后公共入口、CLI、澄清、语义校正及生成公共路径合并覆盖220个不同测试项通过。另用精确诊断runner做ready和truncated两个fake对照，确认原账本继承、Prompt完全相同、错误落盘及单响应限制。这些属于离线验证，不是真实Provider能力证据。

测试中发现三处旧Phase6.1成功夹具没有后来合同要求的明确空semantic_requirements；修改前代码重放也拒绝同一夹具，证明不是本轮引入。只给对应无材料/属性/Type请求的夹具补明确空清单，保留完整性门禁。

**普通Brief Prompt的版本自相矛盾。** v2.7正文/Schema要求2.3，最终输出检查残留2.0；设计审查v2.8的最终要求已经正确。独立失败测试先得到普通版本失败、审查版本通过。新增普通Prompt v2.9，只将这句2.0改为2.3，追加registry条目并更新普通2.3入口；原v2.7/v2.8及所有Schema字节不变。此修正发生在本次成功真实响应之后，只有离线验证，不能说本次真实成功是v2.9带来的。后续验证详见 [验证记录](validation/verification.json)。

## 3. 当前边界与下一步

本次Brief没有列出missing_facts、ambiguities或unsupported_requests。这仅说明此次模型没有报告问题；尚未执行Audit及独立IFC检查，不能据此宣称C型设计合理、语义完整或可以施工。

下一步可以将本次合法Brief接回Generation公共链路，并继续用原冻结请求预期独立检查最终IFC。本轮不自动扩成完整生成，也不为看见成功而增加真实尝试。若后续仍遇截断，先看已保存响应中reasoning/正文的真实占比和重复模式，再针对Brief做阶段性输出开销控制；不直接提高全局预算、关闭全部推理或为C型项目增加特判。

当前C任务累计2次调用、147,630 token、447.655秒，仍受32次/200万/3600秒原上限约束。原账本字节保持；下一次接续必须继承 [最新账本](live-attempt/generation-budget.json)，不能再从旧的1次调用账本开始。`run_brief.py`是本次一次性诊断入口，其admission保留运行前版本快照；之后新增Prompt版本使旧绑定不再适合直接重跑，需要更新适用准入和接续入口。

没有新IFC、没有新Proof；A/B已验收状态保持。Full Preflight未运行，未push。修复只支持“失败留痕和版本冲突已修复”，不支持系统成功率提升声明。
