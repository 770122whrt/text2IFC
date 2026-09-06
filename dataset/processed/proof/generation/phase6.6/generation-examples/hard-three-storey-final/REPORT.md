# hard-three-storey-final

状态：**accepted**；证据方式：`recorded_accepted_generation`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 创建一栋三层 L 形办公建筑，所有尺寸单位为毫米。坐标原点为建筑西南角，X 向东、Y 向北、Z 向上。所有平面坐标表示构件中心线或明确写出的净空间边界，不允许自行改变坐标基准。
>
> 【楼层与竖向坐标】storey-1 基准标高 0，首层墙体 Z=0..3000，净高 3000。slab-storey-2 Z=3000..3150，厚 150；storey-2 基准标高 3150，二层墙体 Z=3150..6350，净高 3200。slab-storey-3 Z=6350..6500，厚 150；storey-3 基准标高 6500，三层墙体 Z=6500..9500，净高 3000。roof-hard Z=9500..9650，厚 150。首层地板 slab-hard-ground Z=-15

## 实际工作

原 IFC 记录为 3 层、18 个空间、48 面墙。model.json 来自最终来源目录的 candidate.json，IFC 沿用已验收副本。

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
| 证据合同 | [原权威报告](<../../../../../agent-demo/phase6.5-hard-accepted/REPORT.md>)；原权威保持原位 |
| IFCCompare | N/A：generation 案例 |
| genuine run ID | 999d210c233b1c34 |
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
