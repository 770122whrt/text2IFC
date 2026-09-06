# A1

状态：**accepted**；证据方式：`live`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 在 00 begane grond 添加一根新的水平直线矩形梁，中心轴从 (25000, 58000, 3000) mm 到 (31000, 58000, 3000) mm，截面宽 500 mm、高 800 mm，并精确复用 GlobalId 为 12jWe1_Rb2cR0ot5ICgwf_、名称为 28_SF_AT_balk vierkant beton:balk vierkant_gen_500x800 (C35/45) 的现有 IfcBeamType。

## 实际工作

冻结 terminal class：SUCCESS。R1 从真实 IFC 和冻结请求出发，并非预先损伤的私有三元组 benchmark。具体属性、构件和阻断行为见下方逐案摘要。

- **Provider 语义选择：** 保留 Stage 1 纠错后，请求复用精确的现有 Type。
- **确定性执行：** 创建 Beam 并绑定该 existing Type；本案没有 property resolution 阶段。
- **输入／私有评估边界：** 没有 original；不补造私有 Gold。 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。

## 直接文件

- [request.txt](<request.txt>)
- [02-damaged.ifc](<02-damaged.ifc>)
- [03-repaired.ifc](<03-repaired.ifc>)


## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | 保留 Stage 1 纠错后，请求复用精确的现有 Type。 |
| 确定性执行 | 沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录 |
| 产物 | repaired；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | [原权威报告](<../../../../repair-milestone-r1/r1-20260902T152701658266Z-curated/cases/A1/REPORT.md>)；原权威保持原位 |
| IFCCompare | N/A：R1 没有运行前冻结的 case-specific private triplet |
| genuine run ID | r1-20260902T152701658266Z |
| Provider 调用次数 | 2/0/1 |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- genuine Provider calls（Stage 1 / Property Resolution / Stage 2）：`2/0/1`
- L0 / L1 / L2：`PASS / PASS / PASS`
- 独立 Proof 结果：IFC2X3 reopen、L0/L1/L2、exact-Type relation 与 preservation 均 PASS。

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
