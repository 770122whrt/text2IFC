# 两个 Repair demo 的四组开发联调

更新：2026-10-03T19:34:58.428083+00:00

本页记录真实开发联调。首批五道正式题只制题、审题及离线检查，未向模型发送。当前开发检查不作为正式比较指标；待答不算失败，已失败任务不自动补跑。

| demo／组 | 状态 | HTTP 次数 | 完整响应的已知 token | 用量缺失次数 | 产物检查 |
|---|---|---:|---:|---:|---|
| case-001-A | 失败终止 | 5 | 16,073 | 0 | 无正式产物 |
| case-001-B | 等待人工答复 | 1 | 24,462 | 0 | 无正式产物 |
| case-001-C | 已提交 | 20 | 147,247 | 0 | 格式失败：24 条诊断；[IFC](../../../.tmp/repair-comparison-demo-live/artifacts/case-001-C/result.ifc) |
| case-001-D | 失败终止 | 23 | 1,093,264 | 1 | 无正式产物 |
| case-002-B | 等待人工答复 | 1 | 25,178 | 0 | 无正式产物 |
| case-002-C | 已提交 | 20 | 185,508 | 0 | 格式失败：1 条诊断；[IFC](../../../.tmp/repair-comparison-demo-live/artifacts/case-002-C/result.ifc) |
| case-002-D | 失败终止 | 7 | 76,913 | 1 | 无正式产物 |
| case-002-A | 预算保护停止（原终态 runtime_error） | 49 | 2,185,669 | 0 | 无正式产物 |

A/B/D 请求同一 `deepseek-v4-flash` 别名，A 与 C 使用同一通用执行器，B 使用原生产 Repair Harness，D 使用官方完整 DSH 0.2.0rc1。C 请求 `gpt-6-sol`。运行区与私有题卡、G、损伤配方和主机密钥隔离。请求名与响应名分别保留，不以代理 API 标签证明具体权重。

A/B 的 Chat 响应标签为 `deepseek-flash`，C 为 `gpt-6-sol`；D 的原始 SSE 标签为 `deepseek-v4-flash`。这既不能证明也不能否定底层权重一致，正式冻结前需核对两种入口的路由。当前已知完整用量合计 3,754,314 token，另有 2 次最终用量未知，不能将已知合计称为全部消耗。

窗题 A 的第 5 次返回含非法 JSON 控制字符，工具参数不能解析，保留为真实失败。窗题 C 虽提交 IFC，深复制带来重复 `IfcApplication`，24 条 EXPRESS 唯一性诊断导致格式失败，未改写该提交。窗题 D 的第 23 次原生流在 `message_stop` 前中断，DSH 返回 `STREAM_CLOSED`，停止容器后没有正式提交。门题 C 的提交还存在 1 条 `IfcPropertySet.PropertyDefinitionOf` 关系基数错误；门题 D 的第 7 次响应被上游截断，HTTP 转发器记录 `RemoteProtocolError`，原生终态仍是 `STREAM_CLOSED`。

门题 A 在 49 个真实请求后被预算保护停止：已返回 2,185,669 token，下一次请求的预留为 320,467，合计超过 2,500,000 上限。初版执行器将网关拒绝记成一般 403／runtime_error。[离线诊断](../../../.tmp/repair-comparison-demo-live/case-002-A-budget-diagnosis.json)从原始会话重建了同一请求，未重新调用模型。预算拒绝的记录／分类已修正，token、次数、活动时间及上游 403 对照在 47 项聚焦回归中通过；原终态与轨迹仍保留，没有把工作区中间文件当作正式提交。

B 窗题原样要求“窗中心距墙局部起点的距离”；公共 D 可推算为 12227.5 毫米，等待用户确认。B 门题提示“目标不唯一或证据不足”，却未提供候选；已呈现给用户。公开请求的 X/Y 是平面中心，Z=3.100 米是洞口底部标高。人工回复只在确认后传回原任务，不从 G 临时找答案。

计账按协议处理：Chat 的缓存命中包含在 prompt 总数中；Messages 的未缓存、缓存读取和缓存写入相加。流开头的输出零值不能证明最终用量。DSH 窗题最初推导的 75,857 token 已由追加更正说明取代：22 个完整响应合计 1,093,264 token，最后一个响应的最终用量未知。未知调用保留预留值，不记零。[Messages 字段说明](https://platform.claude.com/docs/zh-CN/build-with-claude/prompt-caching)。

[原始工作区](../../../.tmp/repair-comparison-demo-live/)保留账本、工作区、唯一提交、HTTP 原始返回、原生 Linux 状态导出和控制日志。六项终止记录另有[Git 可恢复归档](../../../dataset/processed/experiments/repair-comparison-demo-20261004/README.md)，包括两个格式失败的唯一提交；两项 B 尚未收入终止归档。[计账更正](../../../.tmp/repair-comparison-demo-live/accounting-correction.json)为追加说明，原响应、原失败和原结算事件不变。[阶段准入](../../../.tmp/repair-comparison-runtime/stage-admission.json)覆盖两道开发题，计账修复后 42 项聚焦回归通过；最初准入、红测与 scoped 复核日志均保留。两项 B 的待答状态另作只读导出于运行区 `runtime/pending-B/`，Linux 原状态卷保留。当前没有活动任务、在途请求或后台付费调用；人工答复后恢复同一 B 任务。
