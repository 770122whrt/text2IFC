# largebuilding-full-replication

状态：**accepted**；证据方式：`deepseek-openai-compatible`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> On IfcWall GlobalId 1F6umJ5H50aeL3A1As_wTm, restore the missing window.
> Create a 915 mm wide and 1830 mm high window, with a 305 mm sill. Its center offset is 3042.5 mm from wall_local_start.
> Reuse the existing Window Type named 'M_Fixed:0915 x 1830mm'.
> The following occurrence-direct IfcPropertySingleValue facts are explicitly authorized. Preserve

## 实际工作

请求涉及 1 个 operation：add_window_with_opening_to_wall。实际损伤、对象和确定性执行见原案例报告；不从 repaired 反推 Gold。

- **Provider 语义选择：** 原验收记录通过；本轮未重新评估模型语义或能力。
- **确定性执行：** 请求涉及 1 个 operation：add_window_with_opening_to_wall。实际损伤、对象和确定性执行见原案例报告；不从 repaired 反推 Gold。
- **输入／私有评估边界：** original 为已冻结 evaluator-only 真值，仅供修复后评估。 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。

## 直接文件

- [01-original.ifc](<01-original.ifc>)
- [02-damaged.ifc](<02-damaged.ifc>)
- [03-repaired.ifc](<03-repaired.ifc>)
- [request.txt](<request.txt>)


## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | 原验收记录通过；本轮未重新评估模型语义或能力。 |
| 确定性执行 | 沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录 |
| 产物 | repaired；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | [原权威报告](<../../../../../../ifc-repair-success-cases/window/single/largebuilding-full-replication/REPORT.md>)；原权威保持原位 |
| IFCCompare | 沿用原案例评估；本案属于 5 个 legacy_unverifiable 历史 Window 案，不得当作新的完整 Proof |
| genuine run ID | 未知；见原 authority 的 source-run / Provider 记录 |
| Provider 调用次数 | 未知；见原 Provider evidence |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- synthetic fallback：`false`；
- preservation：passed；
- Production：L1 passed、L2 passed、L3 not_required；
- Private Ground Truth：L1 passed、L2 passed、L3 not_required；
- Width/Height/Area、IsExternal、Reference 等 L2 事实一致。

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
