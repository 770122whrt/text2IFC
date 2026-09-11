# 证据来源与历史

人读入口是[案例报告](../REPORT.md)。人工验收记录位于[human-review.json](../human-review.json)；机器判断与人工判断分别保存。

- [正式门禁](frozen/geometry-continuation/runs/5cd2006f0891913f/gate-summary.json)：overall_status=failed。
- [真实 Audit](frozen/geometry-continuation/runs/5cd2006f0891913f/audit/parsed-output.json)：blocking=true。
- [独立 IFC 复验](frozen/geometry-continuation/completion-recheck-independent.json)：167 项通过。
- [调用预算](frozen/geometry-continuation/runs/5cd2006f0891913f/generation-budget.json)：真实消耗和未知预留保持原样。
- [冻结的完成情况报告](frozen/completion-recheck/REPORT.md)：人工验收前的历史判断，未重写其字节。
- [原始 Generator](frozen/geometry-continuation/runs/5cd2006f0891913f/generator/response.raw.json)、[首次失败 Generator](frozen/runtime/runs/148bdf3872e74ccd/generator/response.raw.json)。
- [本次使用的阶段准入](frozen/admission/roof-admission.json)。

collection 的 review-manifest.json/legacy_bundles 将源目录每个原路径映射到当前位置，并保存 SHA-256 与大小。旧报告内的相对链接属于旧布局；请通过映射定位，不以旧报告状态覆盖当前人工记录。源目录仍保留，未做删除或就地修改。
