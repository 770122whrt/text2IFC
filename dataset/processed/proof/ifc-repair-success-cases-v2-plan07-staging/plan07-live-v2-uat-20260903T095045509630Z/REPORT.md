# Phase 12 Plan 07 genuine Provider evidence v2

本次连续 genuine run 的四个冻结角色全部通过：三案产生并独立重开 repaired IFC，一案按 unsupported guard 正确地产生零 repair。

- Live run：`uat-20260903T095045509630Z`
- Provider/model：`deepseek-openai-compatible / deepseek-v4-flash`
- Thinking：`enabled`
- Calls：`11`（Stage 1=4，Stage 1.5=4，Stage 2=3）

| Case | 结果 | Calls | Operations | L0 | L1 | L2 |
|---|---:|---:|---:|---:|---:|---:|
| complete | repaired | 4 | 2 | True | True | True |
| clarification-resume | repaired | 3 | 1 | True | True | True |
| window-semantic-canary | repaired | 3 | 1 | True | True | True |
| program-guard | expected_no_repair | 1 | 0 | True | N/A | N/A |

## 阅读入口

打开 `cases/<case>/REPORT.md`，同目录直接提供 request、damaged IFC 与 repaired IFC。program-guard 的原因在 `NO-REPAIR.md`。

## 证据边界

这组材料是真实 Provider 与真实 IFC 的单场景证据；不把它夸大为跨场景能力提升。Phase acceptance 仍保持 pending，直到冻结 Plan 12/14 Proof gate 完成。IFC 文件字节大小不是损伤方向判据，判定依据是目标差分、独立重开以及几何、语义和 preservation 检查。
