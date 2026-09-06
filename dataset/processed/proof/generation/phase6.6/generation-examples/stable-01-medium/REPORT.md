# stable-01-medium

状态：**accepted**；证据方式：`recorded_accepted_generation`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> ## 3.3.2 Medium 能力边界输入：三间办公室与受支持主入口门
>
> 创建一个单层小型办公区。办公区整体为封闭矩形，内部净尺寸为东西方向 12 米、南北方向 6 米。
>
> 南侧设置一条东西向公共走廊，净尺寸为 12 米 × 2 米。走廊占据办公区南侧完整宽度，走廊西端由西侧外墙封闭，东端由东侧外墙封闭，不设置开放端。
>
> 走廊北侧从西向东依次设置：
>
> - 办公室 A：4 米 × 4 米；
> - 办公室 B：4 米 × 4 米；
> - 办公室 C：4 米 × 4 米。
>
> 三间办公室并排填满办公区北侧：办公室 A 的西侧边界与办公区西侧外墙相接，办公室 C 的东侧边界与办公区东侧外墙相接，三间办公室的北侧外墙连续闭合。办公区的南、北、西、东四侧外墙共同构成完整闭合的外轮廓。
>
> 办公区净高为 3.2

## 实际工作

原 IFC 记录为 1 层、4 个空间、11 面墙。model.json 来自最终来源目录的 candidate.json，IFC 沿用已验收副本。

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
| 证据合同 | [原权威报告](<../../../../../agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/REPORT.md>)；原权威保持原位 |
| IFCCompare | N/A：generation 案例 |
| genuine run ID | 8c8ef9a111e326d7 |
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
