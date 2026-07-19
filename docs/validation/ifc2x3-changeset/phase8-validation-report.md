# Phase 8 L1/L2 Evaluation Contract 验证报告

**验证日期：** 2026-07-20
**范围：** IFC2X3 修复的 Evaluation 0.2、L1/L2 联合成功门、Benchmark Gold 隔离、公开投影，以及 LargeBuilding 离线基线。

## 结论

Phase 8 已通过目标验证与安全审计：11/11 个 must-have 已验证，12/12
个计划内威胁已缓解，代码审查发现的 10 个问题全部修复。最终 IFC repair
测试集为 `210 passed in 156.08s`；最新安全聚焦回归为
`144 passed in 18.03s`。

完整修复成功现在必须同时满足 application、preservation、mandatory L1
和 mandatory L2。L3 保留为非门禁信息。旧 Evaluation 0.1 仍可读取历史
L1/几何指标，但缺失的 L2 会明确表示为 `not_evaluable` /
`legacy_assurance_unavailable`，并强制
`complete_repair_success=false`、
`successful_artifact_publishable=false`。

生产评估输入在类型边界拒绝 original IFC、Gold 和 private mutation
mapping。Benchmark 仅在 ChangeSet 已应用后读取私有 original/mapping；私有
报告保留 expected/actual 细节，公开报告由正向 allowlist 构造，并对
Provider 输入和最终公开证据包执行 canary 扫描。

## 合同版本

| 合同 | 版本 |
|---|---|
| 私有完整评估 | `text2ifc/ifc-repair-evaluation/0.2` |
| 公开 allowlist 投影 | `text2ifc/ifc-repair-evaluation-public/0.2` |
| 运行聚合策略 | `phase8.1` |
| Window L2 operation policy | `window.add-with-opening.l2` / `0.1` |
| L3 策略 | v1.1 为 `not_required`，只记录、不参与成功聚合 |

## L1 与 L2 的判定边界

- L1 独立重开 source/repaired IFC，检查 schema、source hash、实际变更范围、
  host/opening/filling 拓扑、containment、重复关系、几何与版本化容差。
- Applicator 自报的变更不能授权 collateral drift；实际 diff 必须同时得到
  Registry policy 和 ChangeSet scope 授权。
- L2 仅接受 request、surviving IFC facts、approved prototype 或 benchmark
  private original 等明确授权来源，并保留 provenance。
- Material、Pset、quantity、classification、label 等事实只在有授权证据时
  成为必检项；有要求但无法取得证据时为 `not_evaluable`，经验证无授权要求
  时为 `not_required`，不能由邻近对象、名称匹配或 LLM 猜测补齐。
- 每个 operation 通过统一 Registry policy/evaluator seam 评估，为后续 Door、
  Opening、Beam、Column 留出了操作级扩展接口。

## 隐私与发布边界

- `ProductionEvaluationInputs` 不包含 original IFC、Gold 或 private mutation
  mapping；把 private fact 传入生产评估会立即拒绝。
- `BenchmarkEvaluationInputs` 组合生产输入与 evaluator-only private truth，且
  只在 application 成功后调用。
- original 与 repaired 元素按语义角色映射比较，不要求复用 original GlobalId。
- 公开报告不包含 expected/actual value、私有 ID/路径、mapping token 或可能含
  Gold 标识符的动态 fact-key 后缀。
- canary 扫描覆盖 Provider 输入、public spec/context、公开 evaluation/report/
  manifest、诊断候选和成功输出边界；发现泄漏时 fail closed，错误信息也不回显
  canary。
- `failed`、`partial`、`not_evaluable` 均不能成为成功终态或发布成功产物；
  候选 IFC 只能作为 immutable diagnostic evidence 保留。

## LargeBuilding 离线验收

源文件：`dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc`

| 观察项 | 实测结果 |
|---|---|
| Source SHA-256（运行前后） | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`（不变） |
| Provider calls | `0` |
| L1 | `passed` |
| L2 | `failed` |
| L3 | `not_required` |
| Complete / publishable | `false` / `false` |
| Diagnostic retained | `true` |
| L2 remediation categories | `classification`, `is_external`, `label`, `pset`, `quantity` |
| Material activation | 原始模型存在 `Glass`、`Sash`，检查被激活且为 `passed` |

该结果是刻意保留的真实基线，不通过修改 Window authoring 让测试变绿。
L1 的几何、Host/Opening/Filling、containment 与 preservation 已通过；L2 如实
暴露 Pset、quantity、`IsExternal`、classification 和 label 差异。Material
在当前授权证据下等价，因此不是本次失败类别。

Phase 8 没有调用真实 Provider。它验证的是离线确定性评估闭环；Window L2
authoring 修复和真实 Provider UAT 属于 Phase 10。

## 可复现命令与证据

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair -q
# 210 passed in 156.08s

.venv\Scripts\python -m pytest `
  tests\ifc_repair\test_evaluation_contract.py `
  tests\ifc_repair\test_evaluation_policy.py `
  tests\ifc_repair\test_l1_evaluator.py `
  tests\ifc_repair\test_benchmark_evaluation.py `
  tests\ifc_repair\test_phase8_large_building.py -q
# 144 passed in 18.03s

.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\agent
# exit 0
```

权威审查产物：

- `.planning/phases/08-l1-l2-evaluation-contract/08-REVIEW.md`
- `.planning/phases/08-l1-l2-evaluation-contract/08-REVIEW-FIX.md`
- `.planning/phases/08-l1-l2-evaluation-contract/08-VERIFICATION.md`
- `.planning/phases/08-l1-l2-evaluation-contract/08-SECURITY.md`

## 已记录的后续工作

- Phase 9：提供统一 IFC + 文本入口，并从允许的非 Gold 权威来源构造生产
  semantic evidence。
- Phase 10：修复 Window L2 authoring，使 LargeBuilding 在离线和真实 Provider
  UAT 中同时通过 L1/L2。
- Phase 11/12：通过相同 Registry seam 扩展 Opening、Door、Beam、Column。
- L3 authoring/identity 精确恢复、vector matching 和 128k 实验继续延期；它们
  不属于 Phase 8 成功声明。
