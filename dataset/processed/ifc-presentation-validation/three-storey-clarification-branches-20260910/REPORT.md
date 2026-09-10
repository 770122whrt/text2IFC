# 三层 A/B 真实运行报告

**A 已真实运行但失败，B 因共用工程缺陷暂停；尚无两份新 IFC，不登记 Proof。**

| 分支 | 实际结果 | 入口 |
| --- | --- | --- |
| A：澄清后调整 | 4次调用、288,462 token；材料门禁阻断，ChangeSet 因范围错误返回 Draft；无 IFC | [完整报告](A-revise/REPORT.md) |
| B：坚持原要求 | 0次调用；等待共用缺陷离线修复及更新准入 | [状态说明](B-retain/REPORT.md) |

确认的工程缺口是材料报错路径在修复范围中被截断，以及合法起止层楼梯名称被误判；新 Audit 保留决定和已知问题的行为已在真实响应中观察到。不能把这次失败说成两条链路通过，也不能将预运行离线回归等同真实成功。

[运行汇总](live-run-summary.json) · [具体暂停原因](RUN-HOLD.json) · [离线复现](A-revise/offline-failure-diagnosis.json) · [原参考 IFC](../three-storey-human-review-20260909/generated.ifc)

README 和 admission-initial/admission 保存运行前准备状态；最新执行结论以本报告和 RUN-HOLD 为准。原请求、IFC、全部真实响应和失败证据保留。下一步无需重新选择布局：先修精确字段范围与名称适用性，再按原有授权预算继续。GitHub 推送仍未获本次具体载荷授权。
