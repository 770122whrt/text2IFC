# stable-01-easy

状态：**accepted**；证据方式：`recorded_accepted_generation`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> ## 2.2 Easy：单个矩形房间
>
> 创建一个单层矩形房间，房间净尺寸为东西方向 6 米、南北方向 4 米，净高 3 米。
>
> 墙厚 200 毫米，地板厚 150 毫米。
>
> 在南侧外墙中央设置一樘外门，门宽 0.9 米、高 2.1 米，向室内开启。
>
> 在北侧外墙中央设置一扇窗，窗宽 1.5 米、高 1.2 米，窗台距地面 0.9 米。
>
> 生成楼层、房间空间、四面墙、地板、门和窗，并确保门窗正确依附在对应墙体中。房间应生成对应的 `IfcSpace`。

## 实际工作

原 IFC 记录为 1 层、1 个空间、4 面墙。model.json 来自最终来源目录的 candidate.json，IFC 沿用已验收副本。

- **Provider 语义选择：** 原验收记录通过；本轮未重新评估模型语义或能力。
- **确定性执行：** 确定性代码把最终 BIM JSON 编译为 IFC2X3；编译、重开及原验收结果见下表摘录。
- **输入／私有评估边界：** Generation 没有 repair 三元组。repair L0/L1/L2 与私有三元组 IFCCompare 为 N/A；生成专用 gates 以原记录为准。

## 直接文件

- [request.txt](<request.txt>)
- [generated.ifc](<generated.ifc>)
- [model.json](<model.json>)


## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | 原验收记录通过；本轮未重新评估模型语义或能力。 |
| 确定性执行 | 沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录 |
| 产物 | generated；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | [原权威报告](<../../../../../agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/REPORT.md>)；原权威保持原位 |
| IFCCompare | N/A：generation 案例 |
| genuine run ID | d2f86855a9738b50 |
| Provider 调用次数 | 未知；见来源 Provider traces |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- 原记录 audit_passed：True
- 原记录 compile_reopen_passed：True
- 原记录 deterministic_gates_passed：True
- 原记录 final_status：accepted
- 原记录 schema_passed：True

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
