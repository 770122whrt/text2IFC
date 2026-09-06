# output-713-success

状态：**accepted**；证据方式：`historical_authorized_deterministic_revision`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 创建一栋两层 L 形办公建筑，所有尺寸单位为毫米。坐标原点是建筑西南角，X 向东、Y 向北、Z 向上。L 形外轮廓中心线按顺序经过 (0,0)、(10000,0)、(10000,5000)、(6000,5000)、(6000,8000)、(0,8000)，最后回到 (0,0)。每个转角都由两段独立直墙以 90 度连接，不生成单个折线墙。墙厚 200，净高 3000，楼板厚 150。首层 storey-1 标高 0，二层 storey-2 标高 3150。每层六段外墙都必须独立生成：storey-N-wall-south 从 (0,0) 到 (10000,0)；storey-N-wall-east-lower 从 (10000,0) 到 (10000,5000)；storey-N-wall-n

## 实际工作

原 IFC 记录为 2 层、11 个空间、24 面墙。model.json 来自最终来源目录的 candidate.json，IFC 沿用已验收副本。本案包含已授权的确定性边界修订，不是新 genuine run。

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
| 证据合同 | [原运行材料](<../../../../../agent-demo/phase6.5-medium-100mm-gap-fix>)；原权威保持原位 |
| IFCCompare | N/A：generation 案例 |
| genuine run ID | N/A（已授权确定性修订，无新 genuine run） |
| Provider 调用次数 | 未知；见来源 Provider traces |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- 原记录 success：True
- 原记录 compile_reopen_success：True
- 原记录 formal_validation_issue_count：0

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
