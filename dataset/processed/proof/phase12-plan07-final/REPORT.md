# Phase 12 Plan 07 最终人类评估

## 总结

- final-code genuine run：`uat-20260902T180900748385Z`
- frozen case contracts：`4/4 PASS`
- genuine Provider calls：`11`（Stage 1=`4`，Property Resolution=`4`，Stage 2=`3`）
- 成功 repaired IFC：`3`
- 正确的 no-output guard：`1`
- package validation：4 cases、11 calls、5 次 IFC2X3 reopen、guard no-output PASS
- curator 限制：final-code rerun 未安装为第二份 curator collection；这是 changed-scope admission 布局兼容问题，不是语义、IFC 或既有 Proof 失败

## 四案矩阵

| 案例 | Calls S1/PR/S2 | 直接产物 | contract | original/IFCCompare 边界 |
|---|---:|---|---|---|
| [complete](accepted-cases/complete/REPORT.md) | 1/2/1 | repaired.ifc | PASS | physical triplet; private audit N/A |
| [clarification-resume](accepted-cases/clarification-resume/REPORT.md) | 1/1/1 | repaired.ifc | PASS | physical triplet; private audit N/A |
| [window-semantic-canary](accepted-cases/window-semantic-canary/REPORT.md) | 1/1/1 | repaired.ifc | PASS | N/A |
| [program-guard](accepted-cases/program-guard/REPORT.md) | 1/0/0 | no output（按合同） | PASS | N/A |

## Original、damaged、repaired 如何理解

`complete` 与 `clarification-resume` 直接展示三份物理 IFC，便于人工查看；original 明确标为 `physical_fixture_non_private_audit`，当前 private triplet-audit publishability 仍是 N/A。`window-semantic-canary` 没有预先冻结的 case-specific private property mutation truth，不能把共享 pristine 事后改标为 Gold。`program-guard` 的预期就是零输出，产生 repaired IFC 反而会失败。

## Curator 为什么不作为普遍门槛

本次人类视图不重新运行 curator。curator 负责把新 run 安装成受 schema、角色、hash 和完整性约束的 accepted collection；它不是每次阅读、复制入口或报告改写都必须重复的语义裁判。对已有 append-only authority，本次只检查新引入的可发现性风险：声明的文件存在、角色不混淆、IFC 可 reopen、成功案有 repaired、no-output 案没有 repaired、authority 路径可达。
