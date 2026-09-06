# unsupported-complex-door

状态：**historical**；证据方式：`live`。此次只整理展示，不改变原验收或 Phase 状态。

## 请求与输入

完整公共原文：[request.txt](request.txt)。下面是阅读摘要，文件原文未改写。

> 在墙 2cXV28XOjE6f6irgi0COfF 上新开洞并生成一扇 OperationType 为 REVOLVING 的旋转门；要求复杂门框、五金、上亮和两片不同开启轨迹。

## 实际工作

原请求要求 REVOLVING Door。Stage 1 后以 DOOR_OPERATION_TYPE_UNSUPPORTED 终止；Stage 2=0，没有 repaired IFC。旧 UAT 记录判定 contract_pass=true，本次只提供历史阅读入口。

- **Provider 语义选择：** 原记录为正确拒绝该不受支持请求。
- **确定性执行：** 原请求要求 REVOLVING Door。Stage 1 后以 DOOR_OPERATION_TYPE_UNSUPPORTED 终止；Stage 2=0，没有 repaired IFC。旧 UAT 记录判定 contract_pass=true，本次只提供历史阅读入口。
- **输入／私有评估边界：** 没有 original；不补造私有 Gold。 若原评估包含私有删除身份或 mutation mapping，它们仅供修复后评估，不属于 Provider 输入。

## 直接文件

- [request.txt](<request.txt>)
- [02-damaged.ifc](<02-damaged.ifc>)
- [NO-REPAIR.md](NO-REPAIR.md)

## 结果与限制

| 维度 | 结论与来源 |
|---|---|
| 语义结果 | 原记录为正确拒绝该不受支持请求。 |
| 确定性执行 | 正确无输出；Stage 2 / apply / publish 的原记录见下方 |
| 产物 | no_output；本轮只验证可发现性、来源一致性与 reopen |
| 证据合同 | [原运行材料](<../../../../phase11-live-uat/uat-20260731T224900289758Z/unsupported>)；原权威保持原位 |
| IFCCompare | N/A：unsupported 无输出 |
| genuine run ID | repair-091d667e6d334857aa364e8038ffd8e9 |
| Provider 调用次数 | 1/0 (Stage 1/2) |
| 人工审查 | historical；本轮不提升状态 |

### 原记录中的适用检查

- 原报告未单列 reopen / L0 / L1 / L2 / atomicity / preservation 结果：未知；不得从文件存在推断通过。

未在原记录中单列的 atomicity、preservation 或其他门结果记为未知；正确无输出案的输出 reopen/L0/L1/L2 为 N/A。本轮的文件 reopen 只证明文件可打开，不代替这些语义和执行门。

完整过程：[evidence/README.md](evidence/README.md)。这里可进入 Provider attempts、ChangeSet、终端和评估材料；正文不重复展开 runtime 日志。
