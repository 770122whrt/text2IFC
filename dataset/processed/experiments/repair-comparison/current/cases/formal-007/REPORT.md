# formal-007 · B 当前实验记录

未通过；终态 `no_output`。完整构件 0/1，必要关系 0/3。真实调用 6 次，已知 token 103,293，未知用量 0 次，活动时间 177.9 秒。

[公开请求](../../../../../ifc-repair/repair-comparison/formal/formal-007/public/request.txt) · [损坏 IFC](../../../../../ifc-repair/repair-comparison/formal/formal-007/public/model.ifc) · [无正式产物](NO-REPAIR.md) · [独立评分](evaluation.json)

[原样运行、工具、问答与实际返回推理](../../../history/b-next-five/runs/formal-007-B/records.zip) · [该次原账本与评分备份](../../../history/b-next-five/runs/formal-007-B/REPORT.md)

007 正确定位墙与参照后，在跨层墙的高度换算阶段被拒绝，保留真实失败。

统一采用 `repair-comparison-formal-score/0.2`。评分修正只改变删除新增构件后的保全投影，不改目标、尺寸、关系或容差；原评分字节保存在 history。API 未返回的内部推理保持未知。

本页属于已揭示案例的修复后开发复测；不是 accepted Proof，也不证明同版盲测能力提升。
