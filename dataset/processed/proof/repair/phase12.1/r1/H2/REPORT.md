# H2

状态：**accepted**；证据方式：`live`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 将 Level 4 中 GlobalId 为 1jI3nV6Sn2LfeyEYxROCeh、Tag 为 468036 的门的防火等级设置为 EI60，同时将同层 GlobalId 为 2HaS6zNOX8xOGjmaNi_r5s、Tag 为 187497 的墙的隔声等级设置为 Rw 50。两项修改在同一个原子事务中执行。

## 实际工作

冻结 terminal class：SUCCESS。R1 从真实 IFC 和冻结请求出发，并非预先损伤的私有三元组 benchmark。具体属性、构件和阻断行为见下方逐案摘要。

- **Provider 语义选择：** Door 与 Wall 的 property authority 分别从各自 offered set 选择。
- **确定性执行：** 两个目标 operation 原子应用。
- **输入／私有评估边界：** 没有 original；不补造私有 Gold。 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。

## 直接文件

- [request.txt](<request.txt>)
- [02-damaged.ifc](<02-damaged.ifc>)
- [03-repaired.ifc](<03-repaired.ifc>)


## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | Door 与 Wall 的 property authority 分别从各自 offered set 选择。 |
| 确定性执行 | 沿用原操作／编译结果；具体执行与 gates 见下方原记录摘录 |
| 产物 | repaired；本轮已验证产物绑定与原合同，完整结果见下文 |
| 证据合同 | [原权威报告](<evidence/authority/REPORT.md>)；原权威字节已集中；旧路径由集合迁移索引解释 |
| IFCCompare | N/A：R1 没有运行前冻结的 case-specific private triplet |
| genuine run ID | repair-de5a7bd04fb44cd59e8188fd2675b050；集合运行 r1-20260902T152701658266Z |
| Provider 调用次数 | 1/2/1 |
| 人工审查 | accepted；本轮不提升状态 |

### 原记录中的适用检查

- genuine Provider calls（Stage 1 / Property Resolution / Stage 2）：`1/2/1`
- L0 / L1 / L2：`PASS / PASS / PASS`
- 独立 Proof 结果：IFC2X3 reopen、L0/L1/L2、双 authority、atomicity 与 preservation 均 PASS。

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。

2026-09-07 迁移复核：本案原合同完整检查通过；[集合结果](../evidence/migration-validation.json) 与 [验证范围](../evidence/migration-validation-context.json)。原冻结证据字节与验收状态未改写。
