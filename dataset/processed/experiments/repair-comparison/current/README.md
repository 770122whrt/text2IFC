# Repair 当前正式实验结果

更新：2026-10-10。20个源IFC、四组80项，采用每题每组最新获准的真实尝试。旧首轮不纳入本表，当前最终失败仍计入。

001～010沿用冻结评分0.2；011～020指标待定，提交仅表示已有正式IFC。不同任务仍包含历史运行版本和预算，后加的B检验回环与D网页代理没有在这80项上重跑；本表不能作为同版本盲测优势证据。

|组别|被测方法|
|---|---|
|A|DeepSeek v4 Flash＋中性通用执行器|
|B|DeepSeek v4 Flash＋仓库Repair Harness|
|C|GPT-6 Sol API＋与A相同的通用执行器|
|D|DeepSeek v4 Flash＋官方完整DSH 0.2.0rc1|

[CSV表](latest-results.csv) · [结果、逐题比较、配置及真实用量](latest-records.json) · [DeepSeek实际返回推理](reasoning.jsonl.gz) · [当前系统说明](../../../../../docs/validation/repair-comparison/README.md)

|题目|任务|A|B|C|D|
|---|---|---|---|---|---|
|[formal-001](../../../ifc-repair/repair-comparison/formal/formal-001/REVIEW.md)|保留洞口补1扇门|[通过（已评）](outputs/formal-001/A.ifc)|[通过（已评）](outputs/formal-001/B.ifc)|无输出|运行失败|
|[formal-002](../../../ifc-repair/repair-comparison/formal/formal-002/REVIEW.md)|补2扇窗及洞口|预算停止|[通过（已评）](outputs/formal-002/B.ifc)|[已提交／未通过（已评）](outputs/formal-002/C.ifc)|预算停止|
|[formal-003](../../../ifc-repair/repair-comparison/formal/formal-003/REVIEW.md)|补1窗＋1门|预算停止|[通过（已评）](outputs/formal-003/B.ifc)|[通过（已评）](outputs/formal-003/C.ifc)|预算停止|
|[formal-004](../../../ifc-repair/repair-comparison/formal/formal-004/REVIEW.md)|补1扇窗及洞口|预算停止|[通过（已评）](outputs/formal-004/B.ifc)|[已提交／未通过（已评）](outputs/formal-004/C.ifc)|预算停止|
|[formal-005](../../../ifc-repair/repair-comparison/formal/formal-005/REVIEW.md)|补2扇门及洞口|预算停止|[通过（已评）](outputs/formal-005/B.ifc)|[已提交／未通过（已评）](outputs/formal-005/C.ifc)|预算停止|
|[formal-006](../../../ifc-repair/repair-comparison/formal/formal-006/REVIEW.md)|补1扇窗及洞口|预算停止|[通过（已评）](outputs/formal-006/B.ifc)|[通过（已评）](outputs/formal-006/C.ifc)|预算停止|
|[formal-007](../../../ifc-repair/repair-comparison/formal/formal-007/REVIEW.md)|跨层墙补1扇窗|预算停止|无输出|[已提交／未通过（已评）](outputs/formal-007/C.ifc)|预算停止|
|[formal-008](../../../ifc-repair/repair-comparison/formal/formal-008/REVIEW.md)|保留洞口补2扇门|[通过（已评）](outputs/formal-008/A.ifc)|[通过（已评）](outputs/formal-008/B.ifc)|[已提交／未通过（已评）](outputs/formal-008/C.ifc)|无输出|
|[formal-009](../../../ifc-repair/repair-comparison/formal/formal-009/REVIEW.md)|保留洞口补3扇门|运行失败|[通过（已评）](outputs/formal-009/B.ifc)|[已提交／未通过（已评）](outputs/formal-009/C.ifc)|[通过（已评）](outputs/formal-009/D.ifc)|
|[formal-010](../../../ifc-repair/repair-comparison/formal/formal-010/REVIEW.md)|补3扇窗及洞口|预算停止|[通过（已评）](outputs/formal-010/B.ifc)|运行失败|[通过（已评）](outputs/formal-010/D.ifc)|
|[formal-011](../../../ifc-repair/repair-comparison/formal/formal-011/REVIEW.md)|补1根梁|预算停止|[已提交／待评](outputs/formal-011/B.ifc)|[已提交／待评](outputs/formal-011/C.ifc)|预算停止|
|[formal-012](../../../ifc-repair/repair-comparison/formal/formal-012/REVIEW.md)|补2根梁|预算停止|[已提交／待评](outputs/formal-012/B.ifc)|[已提交／待评](outputs/formal-012/C.ifc)|预算停止|
|[formal-013](../../../ifc-repair/repair-comparison/formal/formal-013/REVIEW.md)|补1根柱|预算停止|[已提交／待评](outputs/formal-013/B.ifc)|[已提交／待评](outputs/formal-013/C.ifc)|预算停止|
|[formal-014](../../../ifc-repair/repair-comparison/formal/formal-014/REVIEW.md)|补矩形柱，需澄清朝向|预算停止|[已提交／待评](outputs/formal-014/B.ifc)|[已提交／待评](outputs/formal-014/C.ifc)|预算停止|
|[formal-015](../../../ifc-repair/repair-comparison/formal/formal-015/REVIEW.md)|恢复梁规格标记|预算停止|[已提交／待评](outputs/formal-015/B.ifc)|[已提交／待评](outputs/formal-015/C.ifc)|预算停止|
|[formal-016](../../../ifc-repair/repair-comparison/formal/formal-016/REVIEW.md)|恢复柱耐火记录|预算停止|[已提交／待评](outputs/formal-016/B.ifc)|[已提交／待评](outputs/formal-016/C.ifc)|预算停止|
|[formal-017](../../../ifc-repair/repair-comparison/formal/formal-017/REVIEW.md)|恢复门规格标记|预算停止|[已提交／待评](outputs/formal-017/B.ifc)|[已提交／待评](outputs/formal-017/C.ifc)|无输出|
|[formal-018](../../../ifc-repair/repair-comparison/formal/formal-018/REVIEW.md)|恢复墙外墙标记|预算停止|[已提交／待评](outputs/formal-018/B.ifc)|[已提交／待评](outputs/formal-018/C.ifc)|预算停止|
|[formal-019](../../../ifc-repair/repair-comparison/formal/formal-019/REVIEW.md)|补梁＋柱及承重标记|预算停止|[已提交／待评](outputs/formal-019/B.ifc)|[已提交／待评](outputs/formal-019/C.ifc)|预算停止|
|[formal-020](../../../ifc-repair/repair-comparison/formal/formal-020/REVIEW.md)|补窗＋恢复门外门标记|预算停止|[已提交／待评](outputs/formal-020/B.ifc)|预算停止|预算停止|

40项有正式IFC，40项无正式产物；每项终态、无输出原因、问答和已有评分均保存在结果记录。005-B最新已评通过，007-B保留无输出。没有重新调用模型或重算评分。

A／D预算停止主要发生在下一次请求预留检查：完整对话、工具返回和最大输出预留累加，实际消耗尚未达上限时也可能停止。A018执行目录文本搜索返回了大量构件/关系行；D的压缩功能保留，但旧小预算可能在触发压缩前停止。后续预算固定为1.5M／2M／2.5M，同题四组一致；本表保留运行时原预算。

正式题包的源IFC、冻结损伤、请求、私有条件与许可材料保持原位。推理文件保存API实际返回字段；没有返回的推理不会补造。总费用包含已退役尝试，未知用量不会算作零。已提交旧机器证据暂留原位，不参与当前表的选取。
