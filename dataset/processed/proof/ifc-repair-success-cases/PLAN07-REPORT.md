# Phase 12 Plan 07 Proof — 人工验收入口

本页只汇总修正后的 Plan 07 证据，不包含 Repair Milestone R1。案例目录按既有 door/batch/vvo-five-door-authority-public-repair 的方式组织：IFC 直接位于案例根目录，输入、Agent、ChangeSet、验证和私有评估分别归档。

当前状态：待人工检查。这些目录尚未写入主 manifest.json 的 accepted 列表；检查通过后再完成 Plan 07 最终状态更新。

## 案例矩阵

| 案例 | 证据类型 | Provider calls | 产物 |
|---|---|---:|---|
| [phase12-v2-vvo-beam-loadbearing-restoration](structural/single/phase12-v2-vvo-beam-loadbearing-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-v2-vvo-column-loadbearing-restoration](structural/single/phase12-v2-vvo-column-loadbearing-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-v2-vvo-beam-column-atomic-restoration](structural/batch/phase12-v2-vvo-beam-column-atomic-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-v2-vvo-beam-material-present-restoration](structural/single/phase12-v2-vvo-beam-material-present-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-v2-vvo-column-material-absent-restoration](structural/single/phase12-v2-vvo-column-material-absent-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-v2-vvo-door-window-beam-column-atomic-restoration](mixed/door-window-beam-column/phase12-v2-vvo-door-window-beam-column-atomic-restoration/REPORT.md) | 离线确定性 | 0 | repaired IFC |
| [phase12-plan07-live-beam-column-complete](structural/batch/phase12-plan07-live-beam-column-complete/REPORT.md) | 真实 Provider | 4 | repaired IFC |
| [phase12-plan07-live-column-clarification-resume](structural/single/phase12-plan07-live-column-clarification-resume/REPORT.md) | 真实 Provider | 3 | repaired IFC |
| [phase12-plan07-live-window-property-repair](window/single/phase12-plan07-live-window-property-repair/REPORT.md) | 真实 Provider | 3 | repaired IFC |
| [phase12-plan07-live-structural-program-guard](guard/unsupported/phase12-plan07-live-structural-program-guard/REPORT.md) | 真实 Provider | 1 | 无输出（正确 guard） |

## 总结

- 离线矩阵：6 个 repaired case，12 个 operation；证明通用 restoration、原子性和保存性路径。
- Genuine run：uat-20260903T095045509630Z，11 次真实调用；3 个 repaired case、1 个 expected no-repair guard。
- 结构几何线性容差：0.01 mm；方向容差：0.1°。
- 旧 offsite Beam/Column 结果已撤下，只作为负向回归 fixture 保留。
- R1 不属于本次人工验收范围，后续单独处理。

## 证据边界

离线与 live 证据明确分开。Live 案例的 01-original.ifc 只承担物理对照角色，不伪装成 case-specific private Ground Truth；因此没有合法私有 truth 的案例不会声称 publishable IFCCompare。
