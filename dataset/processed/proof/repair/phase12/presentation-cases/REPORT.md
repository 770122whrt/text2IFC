# 材质与外观：逐案矩阵

运行通过与人工审查分别记录；本次不提升验收状态。

| 案例 | 状态 | 请求 | 输入 | 输出 | 报告 |
|---|---|---|---|---|---|
| case-01-type-reuse | run PASS / pending_human_review | [请求](case-01-type-reuse/request.txt) | [damaged](case-01-type-reuse/02-damaged.ifc) | [repaired](case-01-type-reuse/03-repaired.ifc) | [中文结论](case-01-type-reuse/REPORT.md) |
| case-02-explicit-color | run PASS / pending_human_review | [请求](case-02-explicit-color/request.txt) | [damaged](case-02-explicit-color/02-damaged.ifc) | [repaired](case-02-explicit-color/03-repaired.ifc) | [中文结论](case-02-explicit-color/REPORT.md) |
| case-03-mixed-material-color | run PASS / pending_human_review | [请求](case-03-mixed-material-color/request.txt) | [damaged](case-03-mixed-material-color/02-damaged.ifc) | [repaired](case-03-mixed-material-color/03-repaired.ifc) | [中文结论](case-03-mixed-material-color/REPORT.md) |

相关生产实现及新 schema 的提交由来源进程负责。本次只收纳稳定成功快照，不吸收该进程的暂存改动，也不宣称当前已提交代码能够完整重放这些新案例。
