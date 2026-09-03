---
phase: 09-general-ifc-text-repair-orchestrator
plan: 02
subsystem: ifc-repair-orchestration
tags: [state-machine, atomic-persistence, clarification, json-schema, tamper-detection]

requires:
  - phase: 09-general-ifc-text-repair-orchestrator
    provides: Exact-versioned RepairIntent and public request-understanding contract from Plan 09-01
provides:
  - Exact-versioned run-state, clarification, transition, and compact result contracts
  - Hash-chained atomic run persistence with source/request/version binding
  - One validated clarification answer path for interactive and non-interactive adapters
  - Deterministic restart recovery and immutable terminal/result reads
affects: [09-03-resolution-binding, 09-04-terminal-publication, 09-05-cli]

tech-stack:
  added: []
  patterns:
    - Per-run O_EXCL lock with temporary-file fsync and atomic replace
    - State document as commit pointer over create-new hash-chained transition records
    - Frozen public records with exact Draft 2020-12 schemas and bounded JSON

key-files:
  created:
    - schemas/agent/ifc-repair-run-state-0.1.schema.json
    - schemas/agent/ifc-repair-clarification-0.1.schema.json
    - schemas/agent/ifc-repair-result-0.1.schema.json
    - src/text2ifc_ifc_repair/run_models.py
    - src/text2ifc_ifc_repair/run_store.py
    - tests/ifc_repair/test_run_state.py
    - tests/ifc_repair/test_clarification_state.py
  modified: []

key-decisions:
  - "state.json is the durable commit pointer; a validated transition tail not referenced by it is treated as an interrupted, uncommitted append and may be replaced only while holding the per-run lock."
  - "Clarification answers are validated against the persisted run/version, conditional answer schema, and stored opaque candidate tokens; caller-supplied IFC identity is never authority."
  - "Compact results contain only status and safe relative artifact references; stage payloads, IFC bytes, prompts, and complete evaluation evidence remain outside the public envelope."

patterns-established:
  - "Compare-before-append: lock, reload and verify chain/source, compare expected version, validate transition, append record, atomically replace state head."
  - "No-follow boundary: generated safe run IDs, resolved-root containment, source symlink rejection, and relative artifact path/symlink checks."

requirements-completed: [PIPE-01, PIPE-03]

duration: 18 min
completed: 2026-07-20
---

# Phase 9 Plan 2: Durable Run and Clarification State Machine Summary

**以哈希链、原子版本提交和统一 clarification 合约实现可跨进程恢复、拒绝篡改与竞态的 IFC repair run 状态机**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-19T22:39:51Z
- **Completed:** 2026-07-19T22:57:58Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- 新增三个 exact-version Draft 2020-12 schema，以及冻结的 run、source binding、transition、clarification candidate 和 compact result 模型。
- `RunStore` 使用安全生成的 run ID、create-new run 目录、每 run 独占锁、temp + fsync + atomic replace、单调 state version 和 canonical SHA-256 链持久化状态。
- start/continue/read 在每次变更前重新验证 source SHA-256、完整 transition 链、state head、expected version、clarification ID、答案 schema 与候选 token。
- process restart 会忽略不完整临时文件；若崩溃发生在 transition 落盘后、state head 提交前，下一次持锁转换只会验证并替换该未提交尾记录。
- terminal state、已提交 transition 和已完成 stage hash 均不可变；重复读取 compact result 是幂等的。

## Task Commits

TDD 三个门均原子提交：

1. **Task 1 RED: freeze lifecycle, clarification, and persistence invariants** - `bba7548f` (test)
2. **Task 2 GREEN: implement exact schemas and atomic run store** - `f18e91e9` (feat)
3. **Task 3 REFACTOR: prove recovery, immutability, and bounded public records** - `0fc5c352` (refactor)

## Files Created/Modified

- `schemas/agent/ifc-repair-run-state-0.1.schema.json` - 私有 durable state 与嵌套 hash-chained transition 合约。
- `schemas/agent/ifc-repair-clarification-0.1.schema.json` - target、parameter、conflict、Prototype 共用的 resumable clarification 合约。
- `schemas/agent/ifc-repair-result-0.1.schema.json` - 有界、引用式公共结果 envelope。
- `src/text2ifc_ifc_repair/run_models.py` - 闭集阶段、稳定错误码、冻结记录、canonical JSON/hash 工具。
- `src/text2ifc_ifc_repair/run_store.py` - 原子 start/transition/continue/read、锁、路径与篡改验证、崩溃恢复。
- `tests/ifc_repair/test_run_state.py` - 生命周期、source/request/hash binding、竞态、篡改、恢复、terminal immutability 覆盖。
- `tests/ifc_repair/test_clarification_state.py` - 统一原因/候选/答案 schema、重放、EOF/cancel、Prototype 授权和公共边界覆盖。

## Decisions Made

- 使用 `state.json` 作为已提交 head，而每个 `transitions/NNNNNN.json` 是 create-new append 记录；这为 Windows 提供不依赖 shell 的明确恢复语义。
- continuation 只消费持久化 clarification 中允许的 answer mode 与 opaque candidate token，不接受 caller 自带 GlobalId 作为选择依据。
- resume transition 仅返回 clarification 记录声明的 `resume_stage`，保留此前所有 immutable stage hashes，不调用或重复执行 Agent/index/Audit/apply/evaluation。
- public result 最大 16 KiB，只公开安全相对路径；完整 stage payload、IFC bytes、prompt 和 evaluation JSON 不进入该记录。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修正两处 RED 测试 fixture 的目录建立错误**

- **Found during:** Task 2 GREEN focused test run
- **Issue:** symlink case 重复以 `exist_ok=False` 创建已经由 `RunStore` 建立的 `runs` 目录；多 case clarification helper 未先创建嵌套临时目录。
- **Fix:** 对前者使用幂等目录建立，对后者在写 source fixture 前创建 case root。
- **Files modified:** `tests/ifc_repair/test_run_state.py`, `tests/ifc_repair/test_clarification_state.py`
- **Verification:** GREEN 后 focused suite 通过；REFACTOR 后为 33 passed、1 platform-permission skip。
- **Committed in:** `f18e91e9`

---

**Total deviations:** 1 auto-fixed test bug.
**Impact on plan:** 只修正测试装置，未扩大生产范围或弱化任何拒绝语义。

## Issues Encountered

- 当前 Windows 账户不允许创建 symlink，因此真实 symlink fixture 条件跳过；测试命令仍以 0 退出。实现仍显式拒绝 source/run/artifact symlink，且 traversal、resolved-root containment 与 existing-link 分支已自动覆盖。

## User Setup Required

None - 不需要外部服务、密钥或手工配置。

## Known Stubs

None. 扫描到的空 mapping 与 `None` 均为冻结模型的合法可选字段或安全默认值，不流向占位 UI，也不阻塞计划目标。

## TDD Gate Compliance

- RED `bba7548f` 在任何生产文件出现前失败，原因是 `run_models` / `run_store` 尚不存在。
- GREEN `f18e91e9` 新增最小 schema/model/store 实现并使 focused suite 31 passed、1 skipped。
- REFACTOR `0fc5c352` 增加 committed-head crash recovery、统一 artifact path 验证和 conditional answer schema，最终 33 passed、1 skipped。

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_run_state.py tests\ifc_repair\test_clarification_state.py -q` - **33 passed, 1 skipped, exit 0**
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair` - **passed**
- `Draft202012Validator.check_schema` for all three new schemas - **3 passed**
- Forbidden orchestration-call scan in `run_models.py` / `run_store.py` - **none**
- `git diff --check` - **passed**

## Next Phase Readiness

- Plan 09-03 可在唯一 state authority 上接入 Phase 7 resolution 与 Stage 2 ChangeSet binding，并把 ambiguity/conflict/missing parameter/Prototype 统一路由到本 clarification 合约。
- source、request、run、version、transition 与 candidate answer binding 均已冻结；Phase 10+ 的 authoring/operation 扩展未被提前实现。

## Self-Check: PASSED

- 七个计划所有权 artifact 均存在，且工作区中无未提交的 09-02 code/test/schema 变更。
- RED `bba7548f`、GREEN `f18e91e9`、REFACTOR `0fc5c352` 均存在且顺序正确。
- focused tests、compileall、三个 schema check 与全工作区 `git diff --check` 均通过。
- 无计划外文件被暂存或提交，`.planning/STATE.md` 与 `.planning/ROADMAP.md` 未修改。

---
*Phase: 09-general-ifc-text-repair-orchestrator*
*Completed: 2026-07-20*
