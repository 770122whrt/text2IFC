# dental-clinic-two-door-two-window-geometry-targeted

状态：**accepted**；证据方式：`offline_bound_deterministic`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 请在一个原子 ChangeSet 中同时恢复以下两扇窗和两扇门；所有宿主墙只按楼层标高、朝向、墙体长高厚与墙局部位置定位，不使用 IFC 标识符或对象名称。
> 窗 1：在楼层标高 4570.000 mm、朝向 north、墙长 40577.439 mm、墙高 5137.000 mm、墙厚 267.000 mm 的直墙上开窗；以 wall_local_start 为基准，洞口中心偏移 4800.354 mm，宽 1000.000 mm、高 1735.000 mm、窗台高 905.000 mm；未指定复用类型，使用系统受控 WindowStyle 模板。
> 窗 2：在楼层标高 0.000 mm、朝向 north、墙长 17081.456 mm、墙高 5027.000 mm、墙厚 267.000 mm

## 实际工作

请求涉及 4 个 operation：['add_door_with_opening_to_wall', 'add_window_with_opening_to_wall']。实际损伤、对象和确定性执行见原案例报告；不从 repaired 反推 Gold。

- **Provider 语义选择：** N/A（没有真实 Provider 语义评测）；原记录为离线确定性 operation-engine 通过。
- **确定性执行：** 请求涉及 4 个 operation：['add_door_with_opening_to_wall', 'add_window_with_opening_to_wall']。实际损伤、对象和确定性执行见原案例报告；不从 repaired 反推 Gold。
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
| 证据合同 | [原权威报告](<../../../../../../ifc-repair-success-cases/mixed/door-window/dental-clinic-two-door-two-window-geometry-targeted/REPORT.md>)；原权威保持原位 |
| IFCCompare | 沿用原案例评估；三元组角色按原冻结记录，不在本轮重新计算 IFCCompare |
| genuine run ID | N/A（离线确定性） |
| Provider 调用次数 | 0 |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- L0、L1、L2、preservation 与文件哈希均已重新验证；发布结论见 `validation/release-decision.json`。
- synthetic fallback：false。

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
