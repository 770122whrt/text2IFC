# IFC2Text Phase 1 Closeout

本目录是 Phase 1 的轻量收尾视图，完整真实运行仍保留在上级 campaign 目录。

- `hxp-description.md`、`i5n-description.md`、`1px-description.md`：三份 v0.6 IFC→Text 结果；坐标 mm、一位小数。
- `three-text-review.json`：三份文本的定量检查与 Agent 文案审查。
- `hxp-reconstructed-diagnostic.ifc`：真实 Provider 说明驱动的重建候选；可重开，但未通过 Generation 最终验收。
- `hxp-diagnostic-compare.*`：修正匹配/材料口径后的诊断 Compare。
- `hxp-brief-result.json`、`hxp-generation-result.json`、`hxp-gate-summary.json`、`hxp-audit-report.json`：说明为何候选只属于 diagnostic。
- `summary.json`：关键结果与累计预算摘要。

完整 Provider prompt/response、重试与历史失败未复制到本轻量目录，仍留在 `../hxp/reconstruction-128k/` 与旧 campaign 目录；本目录不替代机器权威。
