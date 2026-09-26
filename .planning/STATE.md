---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Phase 12 and 12.1 closed; Repair Milestone R1 accepted 12/12 with Proof 0.3
last_updated: "2026-09-03T00:00:00Z"
progress:
  total_phases: 13
  completed_phases: 12
  total_plans: 63
  completed_plans: 63
  percent: 96
---

# Project State

## 当前开发：参数化门窗与 IFC2Text 往返（2026-09-26）

唯一计划为 [门窗部件 v1.0](../docs/architecture/text2ifc-component-plan-v1.0.md)，分支 `codex/bim2text-research`。代码已提交推送至 `61547ecb`；四个独立门窗和两个宿主场景完成真实 loop。hxp 保存候选的真实修复和 Audit 已通过，最终 IFC 经独立 Compare 1.3 匹配 61 项、几何超差 0、材料内容差异 0、已测关系差异 0；原源 66 项中的 5 扇门按人工决定排除，36 项材料元数据差异保留。这是部分重建，不是整栋一致。

i5n_1 暂停分支已测；loop-06 的真实 Brief ready，但 Generator 只生成墙和房间，缺根 provenance；真实修复仅补该字段后暴露两面凹口墙，未发布 IFC。已明确批准补充凹口墙支持，相关编译及公开链检查通过，准备在 continuation-05 用原 Brief 和完整性反馈重新生成。最近一次追加 1,000,000 Provider token 已登记，累计上限 5,696,347；已耗 4,946,461，余 749,886，旧失败与原预算不改写。当前运行状态和产物见[部件验证入口](../docs/validation/ifc2text/component-v26/README.md)。Goal 仍在进行；下方 Repair 和仓库整理状态分别保留。

## 当前整理：旧工作树退役与 LFS 按需恢复（2026-09-24）

旧 `.tmp/main-integration-20260912` 已退役，项目先从 40.38 GiB 降至 30.06 GiB。用户随后明确：GitHub 可恢复的 LFS 副本不必留在本地。已核对并移除根 LFS 存储中的 518 个副本，释放 5.54 GiB，项目约 24.53 GiB；当前展开的数据和 Proof、模型缓存、依赖及 Git 提交对象保留。3,122 个未获远端确认的对象保留。恢复清单标注每个对象的固定提交、路径、OID 和大小，按需下载，见[清理报告](../docs/reports/repository-cleanup-20260923/REPORT.md#2026-09-24github-lfs-按需恢复已执行)。原四个测试目录归档与 Git 重打包方案未执行。

旧 main 的独有运行文件和五份不同的旧 RVT 仍保存在 `.tmp/retired-worktrees/main-integration-20260912/local-artifacts.zip`，仅本地保留；其 463 个 LFS 恢复对象改为从 GitHub 获取，恢复说明及索引已同步。Zcode 的远端最新提交 `d0e18fa0` 已经由 `f49bbf42` 合入 main，当前分支及远端 main 均包含它；旧镜像不是待合并工作。下方 9 月 13 日的工作树与存储保留描述只表示当时状态。

## 当前重构：接入 Zcode 有效实现（2026-09-13）

用户要求的有效重构已接入：生产／基准评估分离（`2d1a18bb`）、独立 Proof 包（`d9a91212`）、25 个 runner 分类并保留旧入口。当前实现作为基线，未覆盖后续修复或冻结合同。评估 211 项通过；Proof 168 项通过、16 项原有失败已用原代码复现；分组新入口／公共链检查及本轮夹具修复已完成，另确认 2 项旧 Window 数据路径失败。完整分段结果与 18 项既有测试债务见[执行记录](../docs/reports/zcode-refactor-adoption-20260913/REPORT.md)。无新 Provider／Full Preflight／main 合并。

## 当前整理：根 archive 已退役（2026-09-13）

按用户批准方向，将 Zcode 原历史合同、恢复清单和 66 份重构代码差异／37 份文档收纳为约 1.85 MiB 轻量包，备份提交 `dbb94668` 已推送。根 archive 的 18 个文件／2,688,981,263 字节和三个空目录已退役；完整旧运行、真实失败、数据快照和镜像仍可从固定 Git/LFS 修订 `d1639232` 恢复，六个远端对象可用性检查通过。现有 Proof 不改写；历史 Prompt 回归通过，C1–C5 人读包核对通过，未调用 Provider 或 Full Preflight。旧镜像不再作为待整包合并任务；保留两项后续结构优化候选，详见[报告](../docs/reports/archive-retirement-20260913/REPORT.md)与[历史入口](../dataset/processed/experiments/zcode-history-20260913/README.md)。main 与其独立工作树未在本轮同步。

## 当前整理：processed 与根目录（2026-09-13）

当前分支已快进到上一轮 main 整合 b4eb7ccf。processed 派生产物集中到 derived，顶层 17→7 个目录；经用户批准删除根目录 composite 模拟输出等 15 个目标。Proof 字节与人工状态不变，50 项聚焦回归通过，无新 Provider／Full Preflight。见[整理报告](../docs/reports/processed-cleanup-20260913/REPORT.md)。

## 最近整合：清理后分支合入 main（2026-09-13）

本次整合基线为 main 5db5e82e 与 codex/workflow-dataset-links 241a5c24。保留 Zcode 已接入代码、C1–C5 Proof 和重构归档，并纳入最新光庭与旧运行目录退役记录。四处索引／导航冲突按条目并集合并，43 项聚焦离线测试通过；没有新 Provider、Full Preflight 或人工状态提升。详见[合并报告](../docs/reports/main-sync-20260912/REPORT.md)。

## 最近完成：光庭收纳与已完成 Phase 工作区清理完成（2026-09-12）

光庭、其他展示案例及更早 Phase 6、9–12 的清理已完成：464 个清单目录、352 个单独文件、4 个旧测试链接退役，共 253,690 个旧文件／约 9.76 GiB 源字节。57 个早期 Phase 工作区的完整内容压缩保存到 experiments；当前 few-shot、Plan07 来源及其他有依赖的 26 个目录保留。Proof 字节及人工状态不变，没有新 Provider 或 Full Preflight。清理前备份均已普通推送，最终记录随收尾提交；见 [执行报告](../docs/reports/development-cleanup-20260912/REPORT.md) 和 [实验入口](../dataset/processed/experiments/README.md)。

光庭第二版按概念图右上角深化为两层南侧敞开U形、外露楼梯、20柱6梁、14细杆护栏、44窗6门，不含家具植物。第一版完整包532a4a4c已保留并推送，未按新方案验收。当前分支codex/workflow-dataset-links；通用修复2cf18d56区分开敞墙布局检查与完整墙环，ee94b2a4前移属性校验并明确梯段外观目标，1e46a1fb补严格等价矩形表示转换。

第二版rerun-03（ce8116ce095acdcf）已从全新真实Brief完成Generator/Audit并发布IFC，无候选修复调用；本loop317,533 token。独立正式IFC复核545项通过、111实体网格化成功；Agent实际视图检查完成；用户于2026-09-12人工验收，已收入光庭Proof。最终文件SHA256：650accdb5131b1ae3fdc26e5af000029deb4860fe6f38571dcad174d8ff9b39d。

光庭75个目录及24个重复文件已按批准清单删除，实际49,563文件/710.02 MiB；完整证据已在Proof，后续其他开发目录清理另有记录。全部失败保留，累计17次、1,591,587 token、2723.014活动秒。主要局部复验245项、139项与运行包装器1项通过，不累加为能力指标；未运行仓库Full Preflight。报告保留原浮点颜色失败与统一HEX重算、Audit强度等级文字勘误。跨轮约束来源与替代管理仍待后续小步。

入口：[交付报告](../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/open-court-v2/REPORT.md)、[最终IFC](../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/open-court-v2/generated.ifc)、[输入](../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/open-court-v2/request.txt)。A/B/C历史验收保持；下方是历史检查点。

## 历史工作：仓库清理与 main 整合（2026-09-12）

2026-09-12 更新：当前分支与 Zcode 已在隔离工作树完成合并（f49bbf42），生产以当前合同为准，保留 Zcode refactor-workspace.zip。用户收缩为聚焦验证并要求尽快合 main；最终111项聚焦检查通过，全量测试按要求停止，不宣称 Full Preflight 全通过。93份已批准重复文件已删除；其余清理候选保留待批。详见 docs/reports/main-integration-20260912/REPORT.md。

初始计划中的完整离线 Full Preflight 已被用户最新的精简验证要求取代。执行结果与剩余限制见 `docs/reports/main-integration-20260912/REPORT.md`；本轮未调用 Provider。下方 C 验收及 Phase 记录保持历史原义。

## 当前增量工作：C 型 Generation（2026-09-11）

**当前：用户已验收最新C（run 05c6de3a19ed20f9），已收纳 `dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911/REPORT.md`。9组历史实验独立归档至 `dataset/processed/experiments/README.md`；旧运行目录退役结果以 `docs/reports/c-proof-archive-20260911/REPORT.md` 为准。下文是原运行和调试检查点，不再代表待人工审查。**


最新C：代码d0c39dc4上run `05c6de3a19ed20f9`，3次真实调用首次通过，无修复loop，独立IFC485/485。新增220720 token；C累计20次/1597750 token/2628.983秒。最新账本位于Proof的 `evidence/frozen/live-run/runs/05c6de3a19ed20f9/generation-budget.json`。本次收纳只做确定性复核，不追加Provider。Audit“每层9空间”口误保留原响应，报告说明实际每层3个、全楼9个。

历史开发结果保存在 `dataset/processed/experiments/`：`c-shaped-wall-join-20260911`保留丢聚合关系的失败，`c-shaped-plan-constraints-20260911`保留前一轮IFC及名称误报修复，其他失败和token实验由该目录README串联。它们不自动晋升为第二份accepted Proof。旧admission仅为历史快照，新调用必须重新判断准入。

下一步按 `docs/architecture/token-efficiency-plan.md` 讨论A/B/C同代码、同冻结输入、同评价器的token开发实验，保持Proof字节；当前不运行新实验，不把单例或测试数当作系统能力提升。语义/外观唯一计划仍为 `docs/architecture/semantic-appearance-plan.md`，下方Phase/R1状态保持历史原义。

## Codex Task Pilot Checkpoint — 2026-07-31

```text
Mode: CHECKPOINT
Class: EXPERIMENTAL
Goal: Close Phase 11 only after real DeepSeek output independently reopens and
      passes strict L0/L1/L2, with no synthetic fallback.
Phase: Phase 11 COMPLETE
Routing: direct Phase 11 live-UAT workflow; verification-before-completion
State channel: .planning/STATE.md
Context: COMPLETE - prompt/profile contract repair, live Provider acceptance,
         independent Proof recomputation and regression gates are complete.
Acceptance: Real DeepSeek PASS: complete Stage 1/2 = 1/1; clarified total
            Stage 1/2 = 2/1; unsupported Stage 1/2 = 1/0 with exact
            DOOR_OPERATION_TYPE_UNSUPPORTED. Both published IFC files reopen
            as IFC2X3 and pass strict L0/L1/L2. synthetic fallback = false.
            Proof PASS: 16 cases, 45 operations, 247 files, 48 IFC reopens;
            11 cases strictly recomputed and 5 historical Window cases
            explicitly retained as legacy artifact-only evidence.
Next: Preserve the Phase 11 checkpoint and await user direction. Do not begin
      Phase 12 from this checkpoint.
```

### Handoff boundary

- Branch: `codex/workflow-dataset-links`
- Baseline HEAD: `a20b3e6bf5b6d2d08ca1981583b4254c3efbcd46`
- The worktree is intentionally dirty with the completed Phase 11 Door audit,
  regenerated Proof artifacts, schemas, tests and documentation. Do not reset,
  clean or overwrite these changes.

- Canonical implementation/validation documents:
  - `.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md`
  - `.planning/phases/11-wall-opening-and-door-operations/11-VALIDATION.md`
  - `docs/validation/ifc2x3-changeset/phase11-door-validation-report.md`
- Canonical new authority Proofs:
  - `dataset/processed/proof/ifc-repair-success-cases/door/batch/vvo-five-door-authority-public-repair/`
  - `dataset/processed/proof/ifc-repair-success-cases/mixed/door-window/vvo-authority-triplet-public-repair/`
- The known false-positive candidate is frozen only under
  `tests/fixtures/ifc_repair/phase11-door-known-failure/`; it is not a success
  artifact and must never enter production target resolution.

- Do not revisit without new evidence:
  - the overall two-stage RepairIntent → Bound ChangeSet workflow;
  - retained-Opening geometry targeting without user-supplied GUID/Name;
  - Door L1 thresholds (0.95 overlap, 5 mm center, 0.1 degree axis,
    1 mm nominal dimension);

  - damaged-only production boundary and post-repair-only private comparator;
  - contextual Storey policy documented in the Phase 11 erratum.
- Non-goals for the next conversation:
  - Phase 12 Beam/Column implementation;
  - new Door feature expansion;
  - tolerance relaxation or reduced preservation scope;
  - repository-wide cleanup unrelated to the Phase 11 checkpoint.

## Phase 12 Context Checkpoint — 2026-08-03

```text
Mode: DISCUSSION COMPLETE
Phase: Phase 12 Beam and Column Operations
State: CONTEXT FROZEN; READY FOR RESEARCH AND PLANNING
Requirements: OPS-03 Beam and OPS-04 Column remain pending implementation
Canonical context:
  .planning/phases/12-beam-and-column-operations/12-CONTEXT.md
Scope: Straight horizontal rectangular Beam and straight vertical rectangular
       Column; center-axis placement; exact or deterministic Type; optional
       authorized material; Beam/Column completion of the existing IFC2X3 PSD
       retrieval/index/semantic-authoring path.
Acceptance: Real d7n/vvo IFC2X3 scenes, both structural families, mixed-family
            atomicity, Beam and Column RAG evidence, real DeepSeek complete and
            clarification paths, independent strict L0/L1/L2 Proof validation,
            and no synthetic fallback.
Next: Research and plan Phase 12 from the canonical context. Do not implement
      Phase 12 or begin Phase 13 from this discussion checkpoint.
```

## Phase 12 Planning Checkpoint - 2026-08-03

```text
Mode: PLAN COMPLETE
Phase: Phase 12 Beam and Column Operations
State: SPECIFICATION AND PLAN FROZEN; READY TO EXECUTE
Requirements: OPS-03 Beam and OPS-04 Column remain pending implementation
Canonical specification:
  .planning/phases/12-beam-and-column-operations/12-SPEC.md
Planning evidence:
  .planning/phases/12-beam-and-column-operations/12-RESEARCH.md
  .planning/phases/12-beam-and-column-operations/12-PATTERNS.md
  .planning/phases/12-beam-and-column-operations/12-VALIDATION.md
Plans: 12-01 through 12-16 in sixteen sequential waves
TDD: 12-01 through 12-14 are one-feature canonical TDD plans;
     12-15 performs real DeepSeek execution and independent curation;
     12-16 performs regression, reporting and conditional state closure.
Validation: Plan Checker PASS after two bounded revisions. All sixteen plans,
            OPS-03/OPS-04, SPEC requirements 1-16, frozen G/P/T/R/O/F/V
            decisions and threats T12-01..T12-14 are covered.
Next: Execute Phase 12 only from 12-01 and only when explicitly authorized.
      Do not start Phase 13 or reopen the frozen Door workflow, structural
      geometry thresholds, Ground Truth isolation, Storey policy or RAG
      authority model.
```

## Phase 12 Real UAT and Phase 12.1 Planning Checkpoint — 2026-08-21

```text
Mode: EXECUTION IN PROGRESS
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
Trigger: Genuine Phase 12 DeepSeek UAT
Current authority: Phase 12 Plans 12-01 through 12-14 complete; Stage 1 scope,
                   Type-intent and transaction-clause correction baselines are
                   implemented and pushed.
Live evidence: dataset/processed/ifc-repair-runs/phase12-live/
               uat-20260820T135432218011Z
Observed result: The complete Beam+Column case produced valid Stage 1
                 natural_language_property claims for IfcBeam/IfcColumn and
                 phrase "load bearing", then failed before Stage 2 with
                 PROPERTY_NOT_RESOLVED. Clarification/resume and the repair-only
                 program guard passed. No live structural success was curated.
Root boundary: The default production resolver had vector_index=None and the
               remaining local path relied on historical reviewed-alias text.
               This is a property-resolution architecture gap, not an IFC
               property-name alias to add and not evidence that Stage 1 chose
               the wrong target/value.
Frozen correction: target-class applicability -> multilingual vector Top-K ->
                   separate bounded Stage 1.5 LLM reranker -> deterministic
                   admissibility -> program-constructed ExactPropertyIntent ->
                   existing Binder/Stage 2/atomic IFC authoring.
Requirements: RAG-05, RAG-06, RAG-07, OPS-03 and OPS-04 remain pending.
Plans: 12.1-01 through 12.1-05 complete; 12.1-06 through 12.1-07 pending in sequence.
Contract amendment: Phase 12.1 adds no hash/fingerprint authorization or
                    acceptance gate. Stable IDs, explicit versions and persisted
                    candidate membership connect the stages. Each new gate must
                    protect a named product failure; existing source/private-Gold
                    isolation and historical accepted-Proof mechanisms are unchanged.
Next: Execute 12.1-06 only. Do not start Phase 13. If a new deterministic live
      defect appears after the frozen offline admission gates, preserve it and
      stop for user discussion before any patch or retry.
```

## Phase 12.1 Plan 06 Re-admission Blocker — 2026-08-24

```text
Mode: EXECUTION BLOCKED — OFFLINE EVIDENCE CORRECTED
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
State: PLAN 12.1-06 INCOMPLETE; PLAN 12.1-07 BLOCKED
Implementation checkpoints: 2a87020b, 4d2cd7d3
Correction checkpoint: b8cf328e
Production boundary: BGE_M3_UNAVAILABLE remains fail closed; production live
                     runtime construction has no alias/fallback.
Stage boundary: Stage 1 / property_resolution / Stage 2 are independently
                recorded; Stage 1.5 uses immutable template identity and
                wrapped live transports delegate explicit provider evidence.
Proof boundary: validator-to-curator report 0.2 requires strict Stage 1.5
                recomputation for property-bearing live success cases;
                historical property artifacts remain current-ineligible.
Evaluation: Independent review proved the prior Candidate 60/60 was an
            answer-equivalent replay oracle. b8cf328e removes that replay from
            scoring. Real local BAAI/bge-m3 + Qdrant now reports supported
            Top-K recall = 1.0 but blocks semantic Candidate scoring with
            INDEPENDENT_STAGE15_CANDIDATE_OUTPUT_REQUIRED.
Preflight: 0.3 implementation/execution at 4d2cd7d3 is complete and recorded
           six zero-count checks with tests/knowledge + tests/ifc_repair =
           1100 pass. That artifact is rejected as Plan 06 admission because
           its 60-case Candidate evidence was later shown invalid.
Proof validation: existing accepted Proof report 0.2 passed read-only; no
                  current strict Stage 1.5 live success was curated.
Live status: NOT RUN. No genuine DeepSeek call and no new Proof curation.
Next: Resolve the frozen R12 evidence conflict: Plan 06 requires independent
      Stage 1.5 Candidate outputs, but this task forbids a genuine DeepSeek call
      and no pre-Gold frozen Candidate output exists. Do not start Plan 07 or
      Phase 13 and do not restore replay/alias authority.
```

## Phase 12.1 R12/R13 Evaluation Boundary Amendment — 2026-08-26

```text
Mode: CONTRACT AMENDED; ZERO-NETWORK RE-ADMISSION IN PROGRESS
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
Trigger: Independent review proved that a zero-network deterministic Stage 1.5
         semantic Candidate score is either unavailable or Gold-equivalent.
Resolution: Treat the prior state as an evaluation-contract conflict, not a
            production regression or a reason to restore aliases.
Plan 06 owns: unchanged 60-case real local BGE-M3/Qdrant retrieval metrics;
              Stage 1.5 Prompt/parser/orchestration constraints; deterministic
              admissibility; five-family/public full-chain regression; fresh
              zero-skip/zero-timeout/zero-substitution/zero-network preflight.
Plan 06 report: retrieval_capability=evaluated;
                stage_1_5_semantic_evaluation_status=not_evaluated_offline.
Plan 07 owns: the unchanged 60-case genuine Provider Stage 1.5 semantic
              evaluation, followed by the separate four-case DeepSeek E2E
              matrix, independent Proof, IFCCompare and Phase 12/12.1 closure.
Gold boundary: retrieval Top-K and, in Plan 07, Provider decisions must be
               durably persisted before evaluator-only Gold is opened. The
               Provider never receives Gold/expected/authorize/private truth.
Amendment-time state: Plan 06 remained incomplete pending contract review,
                      evaluator report 0.3 alignment and fresh necessary
                      zero-network checks.
Live status: NOT RUN. Plan 07 requires a separate Go/No-Go after Plan 06 closes.
```

## Phase 12.1 Plan 06 Offline Admission Complete — 2026-08-26

```text
Mode: CHECKPOINT; PLAN 06 COMPLETE; LIVE NOT RUN
Phase: Phase 12.1 Property Resolution RAG and Reranker Correction
State: PLAN 12.1-06 COMPLETE; PLAN 12.1-07 UNSTARTED
Summary: .planning/phases/12.1-property-resolution-rag-reranker/12.1-06-SUMMARY.md
Retrieval: report 0.3 passed on the unchanged 60-case corpus using the real
           local production BGE-M3/Qdrant runtime. Supported Top-K recall=1.0;
           empty Top-K=2; policy/ineligible/alias/private/network counts=0.
Semantic boundary: retrieval_capability=evaluated;
                   stage_1_5_semantic_evaluation_status=not_evaluated_offline;
                   semantic scored count=0 and no deterministic oracle/replay.
Preflight: 0.4 passed all seven gates; 89 focused and 1105 complete-suite tests
           passed with zero failure, skip, substitution, timeout or network.
Offline chain: six accepted structural/mixed cases and two expected atomic
               rollbacks; deterministic Provider/runtime fixtures remain
               plumbing evidence only.
Proof boundary: existing accepted Proof validator 0.2 passed read-only; no new
                Proof was curated and final IFCCompare remains Plan 07.
Live status: NOT RUN. DeepSeek transport calls=0; synthetic fallback=false.
Next: Stop at this checkpoint and await explicit Go/No-Go for 12.1-07. Plan 07
      must rerun fresh preflight, compare frozen fixtures to the Plan 06 Git
      checkpoint, then run genuine semantic evaluation before separate E2E.
      Do not start Phase 13.
```

## Phase 12.1 / Repair Milestone R1 Handoff Checkpoint — 2026-09-01

```text
Mode: CHECKPOINT / HANDOFF
Class: EXPERIMENTAL
State: PARTIAL; safe code and documentation checkpoint for a new conversation
Implementation checkpoint: 223e46e7
Plan 07 evidence: the frozen four genuine cases completed their case contracts
                  with 11 Provider calls (Stage 1=4, Stage 1.5=4, Stage 2=3).
                  Three repaired outputs reopened and passed recorded L0/L1/L2;
                  the unsupported-program guard stopped before mutation.
Plan 07 boundary: acceptance_eligible=false, proof_acceptance_eligible=false,
                  proof_validation_status=pending_plan_12_14. This is not final
                  Proof or Phase closure.
R1 evidence: fresh ordered genuine run r1-20260901T055419268779Z passed E1-E4,
             M1-M3, H1 and H2, then stopped fail-closed at H3 with
             LIVE_CASE_PROPERTY_IDENTITY_NOT_OFFERED. H4 and A1 were not run.
             Calls before stop: Stage 1=12, Stage 1.5=11, Stage 2=10.
R1 boundary: nine successful cases retain repaired IFC and recorded L0/L1/L2;
             R1 Proof 0.3, final IFCCompare and Phase closure were not run.
Handoff: [2026-09-01 historical checkpoint](https://github.com/770122whrt/text2IFC/blob/c58888fb5eb10aceb25e03e1eb8b4f8262074e38/docs/handoffs/repair-milestone-r1-checkpoint-2026-09-01.md)
Matrix: docs/validation/repair-milestone-r1/
        plan07-r1-genuine-execution-matrix-2026-09-01.md
Next: Start the next conversation from the handoff. Diagnose H3 target
      resolution before any further live call. Do not splice runs, claim 12/12,
      close Phase 12/12.1, or start Phase 13.
```

## Phase 12 / 12.1 and Repair Milestone R1 Closure — 2026-09-03

```text
Mode: CLOSURE
Class: ACCEPTED GENUINE + INDEPENDENT PROOF
State: CLOSED
Accepted run: r1-20260902T152701658266Z
Execution: 12/12 frozen contracts PASS; 40 calls (S1=17, S1.5=12, S2=11)
Plan 07 final-code compatibility: uat-20260902T180900748385Z; 4/4 PASS;
                                  11 calls (S1=4, S1.5=4, S2=3)
Artifacts: 11 repaired IFC files independently reopened; L0/L1/L2 PASS
Unsupported guard: H4 PASS with zero mutation, zero publish and no repaired IFC
Proof: validation 0.3 PASS; 12 cases, 13 operations, 785 files, 23 reopens,
       12 independent recomputations, 1 no-output, 0 errors, 0 limitations
IFCCompare: existing legitimate truth-bearing collection PASS; R1 0/12 legally
            eligible triplets, therefore N/A without fabricated Ground Truth
Requirements: RAG-05..07 and OPS-03..04 COMPLETE
Reports: docs/validation/repair-milestone-r1/repair-proof-matrix-2026-09-03.md
         docs/validation/ifc2x3-changeset/phase12-beam-column-validation-report.md
Boundary: historical failed attempts and Plan 07 false/pending fields remain
          immutable. The final-code Plan 07 rerun has a documented non-semantic
          changed-scope curator packaging limitation. Phase 13 was not started.
```

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 12 and Phase 12.1 are closed. Repair Milestone R1 has a
new uninterrupted 12/12 genuine run, curated Proof 0.3 and final IFCCompare
boundary. Phase 13 remains unstarted and requires a separate explicit task.

## Current Position

Phase: 12.1 (Property Resolution RAG and Reranker Correction) — COMPLETE
Plan: 7 of 7 complete; Plan 07 closed by accepted R1 Proof

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 11 complete
- Plan: 11-01 through 11-05 complete
- Status: Opening/Door contracts, indexing, deterministic resolution, IFC
  authoring, strict geometry/Storey L1, L2 and occurrence fidelity are
  implemented. Seven offline cases
  cover LargeBuilding, vvo, AdvancedProject, generated Type, five-Door atomic
  repair and two-Door/two-Window mixed repair. All are independently curated
  with three-way L0/L1/L2 release evidence. Real DeepSeek then passed the
  complete, clarification/resume and deterministic unsupported contracts with
  no fallback; both publishable cases independently reopen and pass L0/L1/L2.

- Progress: 12 / 13 major phases complete; 63 / 63 currently planned milestone plans complete.
- Requirements: RAG-01..07, WFID-01..06 and OPS-01..04 are complete.
- Last activity: 2026-09-03 - accepted R1 run `r1-20260902T152701658266Z`
  passed 12/12 frozen contracts with 40 genuine calls. Curated Proof 0.3 passed
  all 12 independent recomputations with zero errors/limitations; existing
  legitimate triplet IFCCompare passed, while R1 correctly remains truth-N/A.
  Final-code Plan 07 run `uat-20260902T180900748385Z` also passed 4/4 with 11
  genuine calls; its changed-scope curator packaging limitation is recorded for
  later work and is not represented as a second curated Proof.

- Phase 11 closure evidence: accepted live run
  `uat-20260731T224900289758Z` passed all three contracts. Two live successes
  were curated into the Proof collection. The current report-0.2 verifier
  passes the expanded accepted collection with 22 cases, 57 operations, 361
  checked files and 66 IFC reopens; 17 cases are strictly recomputed and five
  retain explicit legacy limitations. The Phase 11 accepted artifacts remain
  unchanged. The rejected preflight 0.3 full-suite execution passed 1100 tests,
  but it is not Plan 06 admission because R12 Candidate evidence was invalid.

- Phase 11 design decisions were confirmed on 2026-07-28 and are frozen in
  `11-CONTEXT.md` and `11-SPEC.md`. Five sequential implementation plans,
  research, pattern map and validation strategy are complete. Plans 11-01
  through 11-05 are implemented and validated; the final scoped checkpoint is
  the only remaining repository bookkeeping step in this handoff record.

- The live failure analysis changed the input contract, not the frozen Door
  workflow. Stage 1 now receives exact intent schemas and is explicitly told
  to omit program-derived and unknown fields. Immutable Door profile v0.2
  few-shots demonstrate complete, clarification, Type reuse and unsupported
  paths. No alias such as `center_offset_from_wall_start_mm` and no relocated
  `door.threshold_height_mm` compatibility was added.

- Real live execution also exposed two deterministic evidence bugs unrelated
  to LLM wording: Door canonicalization metadata was incorrectly treated as
  independent semantic authority, and the host relationship recorded the GUID
  value type instead of `IfcWall`. Both boundaries were corrected and covered
  by regression tests before the accepted rerun.

- Phase 11 uses additive RepairIntent 0.5, Prompt Profile 0.1, IFC Index 0.4,
  Semantic Manifest 0.3 and Bound ChangeSet 0.4 contracts. Historical
  RepairIntent, Manifest and ChangeSet schema files remain immutable;
  Provider draft remains 0.2.

- The 2026-07-29 Door audit found that relation-only postconditions accepted a
  reused mapped Door displaced outside its retained Opening and assigned it to
  the host wall's base Storey. Production L1 now requires projected overlap
  >= 0.95, center deviation <= 5 mm, axis deviation <= 0.1 degrees, dimension
  deviation <= 1 mm, exact fill/void topology and the Storey resolved from the
  Opening's world elevation. All seven offline cases were regenerated.

- The first independent re-review rejected the initial helper-only Ground
  Truth boundary because its outer benchmark runner still constructed public
  inputs from original/deleted-object facts. The authoritative rerun now uses
  `run_phase11_public_triplet_repair.py`, whose only inputs are the damaged IFC,
  a frozen geometry-only public request bundle and an output directory.
  Original IFC and private mutation mapping are introduced only by the
  post-repair comparator. The same rerun also closed an undeclared generated
  Window Type-relation Root and made undeclared added Roots release-blocking.

- AdvancedProject retains full schema validation and full-model diff. A fresh
  cold run passed the unchanged 180-second request-to-publication gate at
  166.807 seconds (36.876 seconds application plus 129.931 seconds
  evaluation); warm evaluation was 43.516 seconds. Independently reopened
  models and an isolated validation worker remove duplicate parsing and avoid
  worker-pool failure; no evidence scope or tolerance was reduced.

## Carried Context

- v1.0 shipped and remains archived with 722-test verification.
- Phase 7 supplies the deterministic SQLite index and bounded target context
  for Wall, Door, Window and contextual Space records; vector retrieval remains
  disabled behind an extension seam.

- Phase 8 supplies Evaluation 0.2 with independent mandatory L1/L2 gates,
  evaluator-only benchmark Gold and privacy-safe public projection.

- Phase 9 supplies one public IFC-plus-text API/CLI, versioned RepairIntent,
  resumable clarification, deterministic target resolution, bound unified
  ChangeSet generation, production semantic authority, all-or-nothing apply,
  and crash-recoverable terminal publication.

- Phase 10 upgrades the LargeBuilding Window path to a bound ChangeSet 0.2,
  atomic semantic authoring, Production L1/L2 pass and successful publication.

- Phase 09.1 separates TypeRecord authority from occurrence-direct facts. The
  41-occurrence LargeBuilding Window Style no longer raises a false
  `PROTOTYPE_TYPE_FACT_CONFLICT`.

- Four real DeepSeek paths publish validated IFC results, including exact Type
  name without GUID and a one-candidate dimensions confirmation. All four pass
  Production and private benchmark L1/L2 with no synthetic fallback.

- Current DeepSeek input/output guards remain 65,536 tokens. The 128k
  experiment remains Phase 13.

- Phase 10.1 uses the existing checked-in IFC2X3 official property registry for
  case-sensitive exact lookup only. It does not implement aliases, embeddings,
  vector search or RAG.

- Exact property mutation is limited to the target occurrence. Existing
  authorized Type facts may be inherited, but existing Types are reused only
  after exact unique resolution or affirmative candidate confirmation. Missing
  Type intent creates a deterministic dedicated system-template Type; ambiguous
  Type intent asks the user; shared-Type mutation is deferred.

- Phase 10.1 real DeepSeek UAT passed both the exact standard property and
  confirmed custom property paths with no synthetic fallback. Production L1/L2
  passed for both.

- Phase 10.2 adds bounded IFC2X3 property knowledge retrieval. Qdrant/BGE-M3
  improve recall but do not authorize writes; Stage 2 receives only exact typed
  facts. The LargeBuilding natural-language `IsExternal` UAT passed real
  Stage 1/2, reopen, L1 and L2.

- Private Gold remains evaluator-only. It passes L2 for exact original Type
  reuse and intentionally reports an authoring difference for a no-Type
  system-template fallback; this does not override the Production publication
  contract.

- Phase 10.3 adds source-bound dataset/benchmark manifests and proves one
  five-Window request can become one unified, all-or-nothing ChangeSet. Both
  deterministic and real DeepSeek runs passed five independent L1/L2 gates.

- The same-wall two-Window case is supported through operation-specific
  overlap checks and aggregate host-wall volume evaluation. An injected
  overlap rejects the entire transaction.

- Phase 10.4 replaces repeated whole-model representation expansion with a
  fail-closed, memoized candidate-certificate plus semantic-fingerprint
  comparator. AdvancedProject now completes global preservation in a
  39.638-second median with 1.083-GB peak RSS.

- A minimal evaluator-alignment follow-up closed the AdvancedProject replay.
  Approved mapped Window frames may be centred and contained within the
  opening while retaining nominal dimensions; occurrence-direct material
  associations take precedence over Type materials. The unchanged saved
  DeepSeek ChangeSet now passes application, global preservation, five
  independent L1/L2 gates and publication.

- The Window success Proof collection now freezes three complementary accepted
  baselines: LargeBuilding single-Window effective semantic replication, vvo
  five-Window atomic repair, and AdvancedProject five-Window large-model
  preservation. Nine IFC copies reopen as IFC2X3, and every copied artifact is
  source- and SHA-256-bound.

- Phase 10.5 treats Window/Opening effective occurrence scalar properties and
  relevant quantities as blocking repair fidelity while keeping GUID, STEP,
  serialization, ownership-graph and geometry-node differences diagnostic.

- Missing occurrence values may be supplied directly, deterministically
  derived, copied from one explicitly authorized occurrence, or taken from an
  explicitly authorized unanimous same-Type cohort. An explicitly authorized
  reused Type may satisfy an effective inherited value; a difference from
  Ground Truth occurrence-direct ownership remains an L3 diagnostic.

- Phase 10.5 retains the complete Production evaluator and requires
  AdvancedProject request-to-publication time at or below 180 seconds and peak
  RSS at or below 4 GiB. Cache/parallel acceleration may not reduce evidence
  scope and fails closed.

- Phase 10.5 real DeepSeek r21 passed with one Stage 1 and one Stage 2 call,
  RepairIntent 0.4, Bound ChangeSet 0.3, Production/private L1/L2 and
  occurrence fidelity. The repaired IFC reopens as IFC2X3 and no synthetic
  fallback was used.

- AdvancedProject final cold/warm full evaluation completed in 62.687/23.562
  seconds with approximately 2.24/2.25 GB process-tree peak RSS. Cold cache
  was miss/miss; warm cache was hit/hit; both runs repeated the full diff.

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 authoring/identity exactness is deferred without a compatibility
  commitment.

- Automatic similarity/vector-based Prototype authorization is not enabled;
  Phase 9 permits only formal binding or explicit user authorization.

- IFC index/extractor v0.2 now stores referenced Types separately and treats
  duplicate or unreliable Type GlobalIds as diagnostic-only evidence.

## Next Action

Use `docs/handoffs/repair/repair-milestone-r1-closure-2026-09-03.md` and the linked
final Proof Matrix as the authoritative R1/Phase 12.1 continuation point.
Preserve all genuine runs and curated Proof append-only. Do not start Phase 13
without a separate explicit task.

---
*Last updated: 2026-09-03 at Repair Milestone R1 / Phase 12.1 closure*

## Accumulated Context

### Roadmap Evolution

- Phase 10.3 inserted after Phase 10: Batch Window Repair and Dataset Benchmark Hygiene (URGENT)
- Phase 10.4 inserted after Phase 10.3: Comparator 0.2 Scalable Preservation Gate
- Phase 10.5 inserted after Phase 10.4: Window Occurrence Fidelity and Validation Acceleration
