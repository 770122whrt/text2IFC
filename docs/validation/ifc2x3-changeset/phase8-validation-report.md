# Phase 8 L1/L2 Evaluation Contract 验证报告

**验证日期：** 2026-07-19  
**范围：** IFC2X3 Window 修复的 Evaluation 0.2、Benchmark Gold 隔离、公开投影、诊断发布语义，以及 LargeBuilding 冻结基线。

## 结论

Phase 8 验收通过。生产评估输入在类型层面不能接收 original IFC、Gold 或 private mutation mapping；Benchmark 仅在 ChangeSet 已应用后读取私有 original/mapping。私有报告保留 expected/actual 细节，公开报告由正向 allowlist 构造，并对 Provider 输入和全部公开证据文件执行 canary 扫描。

冻结 LargeBuilding Window 案例的结果是：L1 `passed`、L2 `failed`、L3 `not_required`、`complete_repair_success=false`、`successful_artifact_publishable=false`。候选 IFC 只保存在 `diagnostic/repaired-candidate.ifc`，没有成功产物路径；Provider 调用数为 `0`。

## 合同版本

| 合同 | 版本 |
|---|---|
| 私有完整评估 | `text2ifc/ifc-repair-evaluation/0.2` |
| 公开 allowlist 投影 | `text2ifc/ifc-repair-evaluation-public/0.2` |
| 运行聚合策略 | `phase8.1` |
| Window L2 operation policy | `window.add-with-opening.l2` / `0.1` |
| L3 策略 | v1.1 `not_required`，只观察、不参与成功聚合 |

Evaluation 0.1 仍由兼容 reader 读取，但不会被解释成具有 L1/L2 assurance，也不能据此发布成功产物。

## 隐私与发布边界

- `ProductionEvaluationInputs` 不含 original IFC、Gold 或 private mutation mapping 字段；向其传入 Gold 参数会触发 `TypeError`。
- `BenchmarkEvaluationInputs` 组合 production inputs 与私有 original/mapping，且 workflow 只在 application 成功后调用私有 evaluator。
- original 与 repaired Window 通过语义角色映射比较，不要求复用 original GlobalId。
- 公开报告仅保留状态、稳定 check/category、safe source kind、原因和 remediation 标记；expected/actual value、私有 ID、私有路径、mapping token 和动态 fact-key 后缀不进入公开投影。
- canary 扫描覆盖 repair request、public spec/context、Provider 证据、TargetQuery/ChangeSet 测试边界、公开 evaluation/report/manifest、诊断候选和成功输出路径；泄漏时 fail closed，错误消息不回显 canary。
- `failed`、`partial`、`not_evaluable` 均不能成为成功终态或成功发布；候选只按 immutable diagnostic evidence 保存。

## LargeBuilding 冻结证据

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
| Material activation | original 中存在 `Glass`、`Sash`，检查已激活并为 `passed`，不是 `not_required` |

本结果没有通过修改 Window authoring 让测试变绿。L1 的几何、Host/Opening/Filling、containment 和 preservation 继续通过；L2 如实暴露 original 证据建立的 Pset、quantity、`IsExternal`、classification 和 label 差异。Material 值在当前 inherited/type 证据下等价，因此本次实测不把 material 记为失败类别。

## 可复现命令

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair\test_benchmark_evaluation.py tests\ifc_repair\test_phase8_large_building.py tests\ifc_repair\test_offline_e2e.py -q
# 10 passed in 64.74s

.venv\Scripts\python -m pytest tests\ifc_repair -q
# 191 passed in 216.24s

.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\agent
# exit 0

git diff --check
# exit 0
```

## Phase 10 已知缺口

Phase 10 负责让 Window authoring 恢复本报告指出的 L2 语义，包括 instance Psets、quantities、`IsExternal`、classification 及有授权证据的 labels；本阶段只定义并执行评估与发布契约。若后续证据表明 Material 值或关联语义不等价，Material check 必须转为非通过，而不能降级为 `not_required`。

以下仍明确延期：Door、Opening-only、Beam、Column 策略与 authoring，Phase 9 通用自然语言 orchestration，L3 authoring/identity 精确恢复，vector matching，以及 128k 实验。
