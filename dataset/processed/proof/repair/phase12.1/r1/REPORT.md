# Repair Milestone R1：逐案证据矩阵

原连续 run 12/12，40 次 genuine 调用；11 个 repaired、H4 正确无输出。原独立 Proof 0.3 冻结记录保留。2026-09-07 使用隔离的已提交代码逐案完成原合同检查：12 案、13 操作、785 文件、23 reopens 全部通过，未新增 Provider 调用。

本表按现有记录整理，不重新评定模型能力、人工审查或 Phase 状态。

调用次数各列按 Stage 1 / Property Resolution / Stage 2 计数。

| 案例与结论 | 状态／证据类型 | 请求 | 输入 IFC／BIM JSON | 输出／无输出原因 | Provider calls |
|---|---|---|---|---|---|
| [E1](<E1/REPORT.md>) | accepted / live | [请求](<E1/request.txt>) | [02-damaged.ifc](<E1/02-damaged.ifc>) | [03-repaired.ifc](<E1/03-repaired.ifc>) | 1/1/1 |
| [E2](<E2/REPORT.md>) | accepted / live | [请求](<E2/request.txt>) | [02-damaged.ifc](<E2/02-damaged.ifc>) | [03-repaired.ifc](<E2/03-repaired.ifc>) | 2/1/1 |
| [E3](<E3/REPORT.md>) | accepted / live | [请求](<E3/request.txt>) | [02-damaged.ifc](<E3/02-damaged.ifc>) | [03-repaired.ifc](<E3/03-repaired.ifc>) | 1/1/1 |
| [E4](<E4/REPORT.md>) | accepted / live | [请求](<E4/request.txt>) | [02-damaged.ifc](<E4/02-damaged.ifc>) | [03-repaired.ifc](<E4/03-repaired.ifc>) | 1/1/1 |
| [M1](<M1/REPORT.md>) | accepted / live | [请求](<M1/request.txt>) | [02-damaged.ifc](<M1/02-damaged.ifc>) | [03-repaired.ifc](<M1/03-repaired.ifc>) | 3/2/1 |
| [M2](<M2/REPORT.md>) | accepted / live | [请求](<M2/request.txt>) | [02-damaged.ifc](<M2/02-damaged.ifc>) | [03-repaired.ifc](<M2/03-repaired.ifc>) | 1/1/1 |
| [M3](<M3/REPORT.md>) | accepted / live | [请求](<M3/request.txt>) | [02-damaged.ifc](<M3/02-damaged.ifc>) | [03-repaired.ifc](<M3/03-repaired.ifc>) | 2/1/1 |
| [H1](<H1/REPORT.md>) | accepted / live | [请求](<H1/request.txt>) | [02-damaged.ifc](<H1/02-damaged.ifc>) | [03-repaired.ifc](<H1/03-repaired.ifc>) | 1/1/1 |
| [H2](<H2/REPORT.md>) | accepted / live | [请求](<H2/request.txt>) | [02-damaged.ifc](<H2/02-damaged.ifc>) | [03-repaired.ifc](<H2/03-repaired.ifc>) | 1/2/1 |
| [H3](<H3/REPORT.md>) | accepted / live | [请求](<H3/request.txt>) | [02-damaged.ifc](<H3/02-damaged.ifc>) | [03-repaired.ifc](<H3/03-repaired.ifc>) | 1/1/1 |
| [H4](<H4/REPORT.md>) | accepted / live | [请求](<H4/request.txt>) | [02-damaged.ifc](<H4/02-damaged.ifc>) | [NO-REPAIR.md](<H4/NO-REPAIR.md>) | 1/0/0 |
| [A1](<A1/REPORT.md>) | accepted / live | [请求](<A1/request.txt>) | [02-damaged.ifc](<A1/02-damaged.ifc>) | [03-repaired.ifc](<A1/03-repaired.ifc>) | 2/0/1 |

迁移验证：[完整结果](evidence/migration-validation.json) · [执行范围与代码版本](evidence/migration-validation-context.json)。

[旧目录与失败运行退役审计](evidence/retirement.json)：10 个匹配失败运行已按用户授权销毁；独立成功历史运行和请求不匹配运行保留。不可从清理后的集合推算历史成功率。
