# phase12-v2-vvo-door-window-beam-column-atomic-restoration

状态：**pending_human_review**；证据方式：`offline_bound_deterministic`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 请在一个原子 ChangeSet 中恢复两扇窗和两扇门。不得使用对象 GlobalId 或 Name 定位。窗 1：在楼层标高 -2213.701 mm、朝南、长 17765.292 mm、高 3581.701 mm、厚 240 mm 的直墙上，以 wall_local_start 为基准在中心偏移 4701.961 mm 处开一个宽 1180 mm、高 500 mm、窗台高 2670.828 mm 的窗，未指定复用 Type，使用受控模板。窗 2：在楼层标高 -2213.701 mm、朝东、长 13455.561 mm、高 4175.094 mm、厚 240 mm 的直墙上，以 wall_local_start 为基准在中心偏移 9315.561 mm 处开一个宽 870 mm、高 237

## 实际工作

输入包含门、窗、梁、柱四类冻结损伤。确定性代码执行 6 个 operation，涵盖 add_beam、add_column、add_window_with_opening_to_wall、fill_existing_opening_with_door；整组按原子 ChangeSet 应用。

- **Provider 语义选择：** N/A（没有真实 Provider 语义评测）；原记录为离线确定性 operation-engine 通过。
- **确定性执行：** 输入包含门、窗、梁、柱四类冻结损伤。确定性代码执行 6 个 operation，涵盖 add_beam、add_column、add_window_with_opening_to_wall、fill_existing_opening_with_door；整组按原子 ChangeSet 应用。
- **输入／私有评估边界：** original 为已冻结 evaluator-only 真值，仅供修复后评估。 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。

## 直接文件

- [01-original.ifc](<01-original.ifc>)
- [02-damaged.ifc](<02-damaged.ifc>)
- [03-repaired.ifc](<03-repaired.ifc>)
- [request.txt](<request.txt>)


## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | N/A（没有真实 Provider 语义评测）；原记录为离线确定性 operation-engine 通过。 |
| 确定性执行 | 沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录 |
| 产物 | repaired；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | [原权威报告](<../../../../ifc-repair-success-cases-v2-plan07-staging/mixed/door-window-beam-column/phase12-v2-vvo-door-window-beam-column-atomic-restoration/REPORT.md>)；原权威保持原位 |
| IFCCompare | 沿用已冻结 private restoration / comparator 记录；本次不重跑 |
| genuine run ID | N/A（离线确定性） |
| Provider 调用次数 | 0 |
| 人工审查 | pending_human_review；本轮不提升状态 |

### 原记录中的适用检查

- Provider calls：0
- Operations：6
- Operation types：add_beam, add_column, add_window_with_opening_to_wall, fill_existing_opening_with_door
- Application：passed
- Preservation：passed
- Structural restoration：passed

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
