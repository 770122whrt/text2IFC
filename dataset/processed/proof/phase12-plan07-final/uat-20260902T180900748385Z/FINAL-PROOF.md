# Plan 07 最终 Proof

- Proof package：phase12-plan07-final-uat-20260902T180900748385Z
- Final-code genuine run：uat-20260902T180900748385Z
- Provider/model：DeepSeek OpenAI-compatible / deepseek-v4-flash
- Thinking：enabled
- 结果：4/4 frozen case contracts PASS
- genuine calls：11（Stage 1=4，Property Resolution=4，Stage 2=3）
- 结论：Plan 07 已由原独立 Proof、最终代码兼容性运行和 R1 Proof 0.3 的 additive evidence 闭合

## 1. 证据构成

本包在编写 package metadata 前收纳了 238 个 payload 文件、8 个 IFC：

- raw-run/：四案完整 case result、Provider attempts、Prompt/renderer input、Stage 1 intent、target/property resolution、candidate/admissibility、Stage 2、bound ChangeSet、apply、state/transitions、terminal evidence、evaluation、repaired IFC 与 staging candidate；
- admission/：最终代码 changed-scope 的零网络 admission；
- source-fixture/public-input/02-damaged.ifc：四案实际使用的 production source；
- source-fixture/private-evaluator-only/01-original.ifc 和 mutation_manifest.private.json：仅供修复后评估，未进入 Provider 或 production repair path；
- source-fixture/authority/：冻结 fixture 的 manifest 与文件角色记录。

本包没有移动或替换原 run，也没有改写 live-uat-result.json 内历史保留的 acceptance_eligible=false、proof_acceptance_eligible=false 和 pending_plan_12_14。最终闭合是 additive decision，不是篡改旧结果。

## 2. 四案最终矩阵

| Case | Calls S1/PR/S2 | 语义/执行结果 | Artifact | Proof 解释 |
|---|---:|---|---|---|
| complete | 1/2/1 | Beam + Column 原子完成 | repaired IFC；IFC2X3 reopen；L0/L1/L2 PASS | 原 Plan 07 accepted structural bundle 含完整 original/damaged/repaired；当前 validator strict structural recomputed，private triplet-audit publishability 为 N/A |
| clarification-resume | 1/1/1 | stable property identity 澄清后恢复并完成 Column | repaired IFC；IFC2X3 reopen；L0/L1/L2 PASS | 原 Plan 07 accepted structural bundle 含物理三元组；当前 validator strict structural recomputed，private triplet-audit publishability 为 N/A |
| window-semantic-canary | 1/1/1 | 从当前 offered set 选择 IsExternal authority 并写入 | repaired IFC；IFC2X3 reopen；L0/L1/L2 PASS | contract/source→repaired evidence；没有预先冻结的私有 property mutation truth，不能事后制造三元组 Gold |
| program-guard | 1/0/0 | STRUCTURAL_ANALYSIS_UNSUPPORTED | 无 repaired IFC；零 mutation、零 publish、source 不变 | no-output safety Proof，L0/L1/L2 与三元组均 N/A |

三个 successful case 的 repaired IFC 位于各自 raw-run/cases/<case>/runtime/runs/<run>/.terminal-bundles/<bundle>/successful/ 目录。精确路径记录在 [manifest.json](manifest.json)。

## 3. 哪些 Plan 07 内容有合法三元组

### Accepted structural bundle 中的物理三元组

以下两个原 Plan 07 live success case在 final-code rerun 之前已经完成独立收录，每个目录均含 original、damaged、repaired、request、Provider evidence、Prompt profile、intent、resolution、ChangeSet、application、evaluation、strict reopen 和 three-way audit：

- ../../ifc-repair-success-cases/structural/live/phase12-live-deepseek-complete/
- ../../ifc-repair-success-cases/structural/live/phase12-live-deepseek-clarification-resume/

这两案是 Plan 07 的 accepted、strict-recomputed structural Proof authority；三份 IFC 均真实存在，但当前 validator 将 private triplet-audit publishability 标记为 N/A，而不是 true。

### 不能作为 private triplet 的两案

window-semantic-canary 是针对 surviving Window 的 property authority canary。它有真实 damaged/source、真实 repaired、完整执行链和 L0/L1/L2，但没有在看到输出前冻结的 case-specific private property mutation truth。虽然共享 fixture 有一份 pristine IFC，也不能在运行后把它重新解释成这个属性请求的 Gold。

program-guard 的预期语义是拒绝混合了 unsupported structural-analysis 的原子请求；生成 repaired IFC 反而意味着安全门失败。因此它合法地只有 source IFC 和 no-output/immutability evidence。

## 4. Curator 限制

对 final-code run 的第二次 curator installation 曾停止于 LIVE_PREFLIGHT_EVIDENCE_MISSING。原因是 curator 只识别 run-local 完整 preflight/ 树，而本次 runner 使用的是已接受的 changed-scope admission 引用。

这项限制只影响“能否把 final-code rerun 再安装成第二份 curator collection”的包装形式，不影响：

- 四案 genuine Provider transcript 与 call count；
- 三个 repaired IFC 的 reopen 和 L0/L1/L2；
- program guard 的零 mutation/零 publish；
- 原 Plan 07 已 accepted 的两个 strict-recomputed structural Proof bundle；
- R1 独立 Proof 0.3。

因此本包明确标记为 additive final-code compatibility Proof，不声称完成了第二次 curator installation。该兼容问题后续可以离线修复，无需再调用 Provider。

## 5. 最终判断

Plan 07 的四种冻结行为均在最终代码上重跑通过；两个 structural repair case 已有 pre-existing physical triplet 和 strict recomputation，但其 private triplet-audit publishability 为 N/A；property canary 保留为 source→repaired 的语义/执行/产物证据；unsupported guard 保留为 no-output safety evidence。

以上证据与 repair-milestone-r1/r1-20260902T152701658266Z-curated/ 的 Proof-validation 0.3 共同支持 Plan 07、Phase 12 和 Phase 12.1 闭合，同时没有伪造 Gold、弱化 offered-set/admissibility/preservation 门槛或隐藏 curator 限制。

## 6. Fresh package validation

PACKAGE-VALIDATION.json 重新检查了 17 个 manifest 引用、4 个 case、11 次 retained transport call、5 次 IFC2X3 reopen、2 个 source-fixture copy identity，以及 program guard 的 no-output 条件，结果为 PASS。它验证的是收纳完整性和既有 case contract，不是第二次 curator installation。


## 7. Fresh accepted-collection validation

2026-09-03 重新运行现有 success collection validator，结果为 PASS：24 cases、60 operations、588 checked files、72 IFC reopens、19 independently recomputed cases、12 truth-bearing triplet audits publishable、0 errors。5 个早期 Window case 保留 legacy-unverifiable 限制；它们不用于增强 Plan 07 或 R1 的闭合结论。compact summary 位于 ../../IFC-REPAIR-COLLECTION-VALIDATION-20260903.json。
