# IFC2Text 归因验证 v0.1

本目录包含对旧 hxp 往返的诊断和两次新的真实公共 Brief 调用，不是新生成成功案例。

阅读顺序：

1. `probe-summary.json`：A/B真实调用的终态、结构化归属、成本和对照条件；除request标识不同外，证据与few-shot内容一致。
2. `counterfactuals.json`：空间字段投影0→5、未解决项8→3；三面源多边形墙与重建矩形墙的无开口范围差异。
3. `attribution.json`：源事实—文本行—原Brief—原Generator候选的追踪。源/候选文件字节不变。
4. `live-original/`和`live-explicit_containment/`：请求、响应、解析、控制器结果；Generator未调用。SQLite会话文件保留本地但不纳入本次Git工件。
5. `validation/`：33项离线检查及阶段准入。临时测试目录不纳入Git。
6. `budget-final.json`：旧账本延续，累计占额1283761 tokens、写作19次、重建侧10次；其中293791是历史用量未知的保守占额。

完整结论和下一步：`docs/reports/ifc2text-attribution-and-next-steps-2026-09-21.md`。

对照每组仅运行一次，不能证明跨建筑提升；模型对“不支持”的文字解释不能替代Schema或编译器测试。原基线IFC仍为diagnostic_not_accepted。
