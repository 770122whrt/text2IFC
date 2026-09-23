# Repair Milestone R1 / Phase 12.1 Closure Handoff — 2026-09-03

> 2026-09-07 导航更新：证据已集中到 [工作流 Proof](../../../dataset/processed/proof/README.md)，旧路径见集合 manifest 的 legacy_bundles。Plan07 已获用户人工审查通过；下文日期、原运行结论与冻结记录仍表示历史事实。


## Final state

Repair Milestone R1, Phase 12 and Phase 12.1 are closed on
`codex/workflow-dataset-links`. The accepted run is
`r1-20260902T152701658266Z`: a new uninterrupted E1→E2→E3→E4→M1→M2→M3→H1→H2→H3→H4→A1
execution with 12/12 frozen contracts passed and 40 genuine Provider calls.

The accepted Proof root is
`dataset/processed/proof/repair/phase12.1/r1/`.
Proof validation 0.3 passed with 12 cases, 13 operations, 785 checked files,
23 IFC reopens, 12 independent recomputations, one intentional no-output case,
zero errors and zero limitations.

The final implementation also passed a separate rerun of the original Plan 07
four cases: `uat-20260902T180900748385Z`, 4/4 with 11 genuine calls (4/4/3).
Its three repair paths reopened with L0/L1/L2 PASS; its program guard performed
zero mutation and produced no output.

## Important interpretation

- H3 was repaired generally at the opening-filling geometry/index boundary;
  no H3 identity, dimensions, prompt phrase or case id was special-cased.
- H4 correctly has no repaired IFC because the frozen unsupported atomic guard
  requires zero mutation and zero publication.
- R1 has no lawful private triplets, so its IFCCompare status is N/A. The
  existing truth-bearing accepted collection passed its final IFCCompare gate.
- Historical failed and interrupted genuine attempts remain append-only.
- Historical Plan 07 false/pending eligibility fields remain unchanged; the
  original Plan 07 Proof, final-code 4/4 compatibility run, additive R1 Proof
  and closure reports establish final eligibility.
- The final-code run was not installed as a second Plan 07 Proof collection:
  the current curator only accepts a run-local full preflight tree and stopped
  at `LIVE_PREFLIGHT_EVIDENCE_MISSING` for the runner-accepted changed-scope
  admission layout. This is a retained evidence-packaging limitation, not a
  semantic, IFC, L0/L1/L2 or guard failure; it can be repaired later without
  another Provider run.
- Phase 13 remains unstarted.

## Canonical continuation references

- `docs/validation/repair-milestone-r1/repair-proof-matrix-2026-09-03.md`
- `.planning/phases/12.1-property-resolution-rag-reranker/12.1-07-SUMMARY.md`
- `docs/validation/ifc2x3-changeset/phase12-beam-column-validation-report.md`
- `dataset/processed/proof/repair/phase12.1/r1/evidence/run-original/r1-execution-result.json`
- `dataset/processed/proof/repair/phase12.1/r1/evidence/frozen/PROOF-VALIDATION.json`
- `dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/live-uat-result.json`

No Phase 13 work should be inferred from this handoff. Starting it requires a
separate explicit task.

## 2026-09-23 整合补记：9 月 1 日检查点如何到达收尾

本节合并[9 月 1 日检查点](https://github.com/770122whrt/text2IFC/blob/c58888fb5eb10aceb25e03e1eb8b4f8262074e38/docs/handoffs/repair-milestone-r1-checkpoint-2026-09-01.md)中仍需保留的历史事实；不是新的运行或验收。后续只维护本交接入口，早期未完成事项不再作为当前待办。

| 时点 | 实际发生的事 | 解读与证据入口 |
|---|---|---|
| 9 月 1 日，检查点 `223e46e7` | 有 Stage 1／1.5／2 来源记录、混合语义绑定、属性写入隔离及相关回归；当时尚未闭合 R1 | [当时的真实执行矩阵](../../validation/repair-milestone-r1/plan07-r1-genuine-execution-matrix-2026-09-01.md)保留诊断和阶段证据 |
| 9 月 1 日，`r1-20260901T055419268779Z` | 9 案通过，H3 以 `LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED` 停止，H4／A1 未执行；停止前 33 次调用（12／11／10） | H3 公开目标候选为空，冻结回答不能绑定到未提供的目标；该失败不得改写成最终 12／12 成功的一部分 |
| 后续收尾 | H3 在 opening／filling 几何索引边界作通用修复，再取得本页所列新的完整 12 案运行 | 完整运行的 40 次调用与前轮 33 次分开；不会拼接为一次连续成功 |
| Plan 07 | 早期四案的 case-contract PASS 与当时 pending 的 Proof 字段是不同事实 | 保留原始 pending 字段；最终兼容运行与收纳限制见本页 Important interpretation |

旧检查点的“先诊断 H3，再重跑 R1”顺序已完成，不再重启；Phase 13 仍不能由这份交接自动获得执行授权。早期 run、H3 诊断、失败分母和独立 Proof 继续在各自证据位置保留。本文不将回归通过或这些案例解释为全系统成功率。
