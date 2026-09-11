# Phase 12 Plan 07 v2：逐案证据矩阵

6 个离线案例、3 个 genuine repaired 案例和 1 个 no-output guard；11 次 genuine 调用。R1 不包含在该集合中，r1_included=false。

2026-09-07 用户明确确认 Plan07 人工审批通过。此更新只记录人工审查，不重新评定模型能力或 Phase 状态。

| 案例与结论 | 状态／证据类型 | 请求 | 输入 IFC／BIM JSON | 输出／无输出原因 | Provider calls |
|---|---|---|---|---|---|
| [phase12-v2-vvo-beam-loadbearing-restoration](<beam-loadbearing/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<beam-loadbearing/request.txt>) | [02-damaged.ifc](<beam-loadbearing/02-damaged.ifc>) | [03-repaired.ifc](<beam-loadbearing/03-repaired.ifc>) | 0 |
| [phase12-v2-vvo-column-loadbearing-restoration](<column-loadbearing/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<column-loadbearing/request.txt>) | [02-damaged.ifc](<column-loadbearing/02-damaged.ifc>) | [03-repaired.ifc](<column-loadbearing/03-repaired.ifc>) | 0 |
| [phase12-v2-vvo-beam-column-atomic-restoration](<beam-column-atomic/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<beam-column-atomic/request.txt>) | [02-damaged.ifc](<beam-column-atomic/02-damaged.ifc>) | [03-repaired.ifc](<beam-column-atomic/03-repaired.ifc>) | 0 |
| [phase12-v2-vvo-beam-material-present-restoration](<beam-material-present/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<beam-material-present/request.txt>) | [02-damaged.ifc](<beam-material-present/02-damaged.ifc>) | [03-repaired.ifc](<beam-material-present/03-repaired.ifc>) | 0 |
| [phase12-v2-vvo-column-material-absent-restoration](<column-material-absent/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<column-material-absent/request.txt>) | [02-damaged.ifc](<column-material-absent/02-damaged.ifc>) | [03-repaired.ifc](<column-material-absent/03-repaired.ifc>) | 0 |
| [phase12-v2-vvo-door-window-beam-column-atomic-restoration](<four-family-atomic/REPORT.md>) | accepted / offline_bound_deterministic | [请求](<four-family-atomic/request.txt>) | [02-damaged.ifc](<four-family-atomic/02-damaged.ifc>) | [03-repaired.ifc](<four-family-atomic/03-repaired.ifc>) | 0 |
| [phase12-plan07-live-beam-column-complete](<live-complete/REPORT.md>) | accepted / live | [请求](<live-complete/request.txt>) | [02-damaged.ifc](<live-complete/02-damaged.ifc>) | [03-repaired.ifc](<live-complete/03-repaired.ifc>) | 4 |
| [phase12-plan07-live-column-clarification-resume](<live-clarification/REPORT.md>) | accepted / live | [请求](<live-clarification/request.txt>) | [02-damaged.ifc](<live-clarification/02-damaged.ifc>) | [03-repaired.ifc](<live-clarification/03-repaired.ifc>) | 3 |
| [phase12-plan07-live-window-property-repair](<live-window-property/REPORT.md>) | accepted / live | [请求](<live-window-property/request.txt>) | [02-damaged.ifc](<live-window-property/02-damaged.ifc>) | [03-repaired.ifc](<live-window-property/03-repaired.ifc>) | 3 |
| [phase12-plan07-live-structural-program-guard](<program-guard/REPORT.md>) | accepted / live | [请求](<program-guard/request.txt>) | [02-damaged.ifc](<program-guard/02-damaged.ifc>) | [NO-REPAIR.md](<program-guard/NO-REPAIR.md>) | 1 |
