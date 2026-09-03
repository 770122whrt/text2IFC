# Repair Milestone R1 Proof Readiness Re-audit

日期：2026-08-30

分支：`codex/workflow-dataset-links`

复审基线：`d6e77005dc658148397c9aab004f8f7d9b011a21`

R1 freeze checkpoint：`09d5611ae0642b23146566e6b4fb262ee74f2aa9`

## 1. 本轮边界

本轮只修复并复审 R1 Proof 0.3 validator、curator、live evidence 与 preservation
合同。没有调用 DeepSeek 或其他 Provider，没有执行 Plan 07 四案或 R1 十二案 genuine
matrix，没有 curate 新 Proof，没有运行 final IFCCompare，也没有关闭 Phase 12.1、
Repair Milestone R1 或启动 Phase 13。

冻结的十二案例语义、请求、模型、Gold、Prompt、operation registry、Proof schema 和
acceptance threshold 均未修改。

## 2. 独立终审结论

独立子 agent 对实际实现、冻结合同和最终测试进行交叉审核后给出：

`APPROVE_PROOF_REAUDIT`

当前 R1 Proof re-audit 层没有剩余 P0/P1/P2。这个结论只批准 Proof 基础，不批准
genuine R1 execution；生产执行仍有第 5 节列出的四个 blocker。

## 3. 已闭合的 Proof 缺口

| 缺口 | 最终合同 |
| --- | --- |
| H1 mixed preservation | 对完整 atomic ChangeSet 一次执行全局 L1；Beam 创建与 Window property mutation 共同组成 whole-model allowed delta，不静默跳过 property operation。 |
| Property whole-model preservation | IfcRoot 可达图继续由 normalized L1 审计；新增 source/repaired unreachable non-Root canonical Counter 精确相等检查，拒绝孤立实体新增、删除或修改。 |
| H3 target clarification | 从 hash-valid RunStore state 取得稳定 GlobalId，投影到初始 intent 副本，再用 source IFC、当前 index 和真实 resolver 重放；candidate rank 不具授权意义。 |
| H4 unsupported guard | 独立重放 supported Beam + unsupported analysis node 的 atomic stop；验证真实 production 三件失败包 `manifest/evaluation/evidence`，不再使用手工二件 fixture。 |
| H4 terminal evaluation | Public evaluation 必须精确等于 production `ifc-repair-evaluation-public/0.2` failure shape；拒绝额外 candidate、伪 L0 字段、错误 check id 或任何成功宣称。 |
| Live Provider provenance | Stage 1、property_resolution、Stage 2 按 clarification lineage 分轮；验证 profile/template、few-shot identity/hash、attempt chain、raw/parsed response、retry、thinking/model metadata、no fallback 与 private-input isolation。 |
| M1 property clarification | 冻结 answer `改为 EI60。`、相邻 clarification/add-detail、`clarification_id` 与 `generation == transition_id == state_version` 精确绑定。 |
| FILES/core/report authority | Canonical profile/freeze、core roles、REPORT 和 FILES hash 全部互相绑定，不能用 self-signed drift 替换。 |
| Curator integrity | 在 private staging 中 fresh validate，写入 destination-rebound `PROOF-VALIDATION.json`，验证 schema/hash 后原子发布；外部 validation 不能绕过 fresh result。 |

H4 的零 Stage 2、零 apply 和零 repaired output 不依赖 terminal evidence 自报计数，而是
分别由 stage-aware attempts、hash-valid state transition、exact manifest entries、
FILES 全角色扫描和 source hash 独立推出。

## 4. 离线验证证据

### 4.1 TDD 关键 RED

- H4 真实三件 bundle：旧 helper 对 production artifact set 报错，证明手工二件 fixture
  与真实 `RepairAPI` 漂移。
- H4 hash-valid semantic tamper：额外 top-level candidate、nested `l0_pass` 和错误
  `check_id` 在修复前均为 `DID NOT RAISE`。
- Non-Root orphan：向真实 property-repaired IFC 插入不可达实体后，旧 whole-model
  preservation 为 `DID NOT RAISE`。

### 4.2 Focused GREEN

- H4 state/isolation：`20 passed in 12.20s`。
- Non-Root preservation：`7 passed in 33.95s`，覆盖
  `IfcCartesianPoint`、`IfcPropertySingleValue`、source orphan 修改/删除、
  STEP renumber/reopen、property 正例和 H1 mixed 正例。
- 既有 H1/property preservation：`2 passed, 40 deselected in 22.34s`。
- Compare focused：`2 passed in 4.17s`。

### 4.3 Fresh combined admission

以下九个文件一次性执行：

```text
tests/ifc_repair/test_repair_milestone_r1_proof.py
tests/ifc_repair/test_repair_milestone_r1_proof_reaudit.py
tests/ifc_repair/test_r1_live_attempt_audit.py
tests/ifc_repair/test_repair_milestone_r1_curator_integrity.py
tests/ifc_repair/test_r1_h3_final_authority.py
tests/ifc_repair/test_r1_state_isolation_contract.py
tests/ifc_repair/test_r1_nonroot_orphan_preservation.py
tests/ifc_repair/test_compare.py
tests/ifc_repair/test_compare_fingerprints.py
```

结果：`142 passed in 138.57s`，无 skip、无 network、无 Provider。

### 4.4 Plan 07 compatibility

`tests/ifc_repair/test_phase12_success_cases.py`：
`37 passed, 1 failed in 173.71s`。

唯一失败：
`test_validator_cli_accepts_the_frozen_root_option`。测试在空目录 monkeypatch
`validate_success_case_collection`，但 CLI `main()` 在 dispatch 前先读取
`manifest.json`，因此得到 `FileNotFoundError`。规范化 CRLF 后，本轮
`main()` 与 HEAD 基线从 `def main` 到 EOF 的 SHA-256 均为：

`75c67369fc78543969c1f9ba48493f1dd4a856ec526d111a30439ee2ddde3d35`

所以这是基线已有 fixture/CLI mismatch，不是本轮 R1 Proof 修复引入的回归；本轮没有
为了制造全绿而改写历史 Plan 07 expectation。

## 5. Genuine R1 execution blockers

1. **H1 mixed Stage 2 authority**：`generate_bound_changeset()` 只在 pure
   structural compact mode 向 Binder 传入 `resolved_authority`。Beam + Window
   mixed program 当前仍缺逐 operation fail-closed exact authority binding。
2. **M1 add-detail 可达性**：`continue_with_answer()` 有 `add_detail` handler，
   但 property 已解析、value 无效且 candidates 非空时，公开 answer modes 仍只有
   `select_candidate/cancel`，冻结 M1 resume 路径不可达。
3. **H4 intent/route persistence**：unsupported 会在提交 hash-valid
   `INTENT_READY` intent/route authority 前直接 `_fail`。安全 stop 正确，但不能
   生成 Proof 0.3 要求的完整 state-bound evidence。
4. **Dedicated runner/manifest**：仓库尚无 R1 十二案专用 genuine runner、exact
   case-order execution manifest 或权威 entrypoint。当前 `run_` prefix 仅是已知
   blocked 状态下的 shape check，不是 execution authority。

因此不得开始 genuine R1 matrix，也不得把本轮 offline Proof 通过解释为 production
capability acceptance。

## 6. Deferred Composite prerequisite

未来 large Composite Repair Milestone 若包含多个同 family operation，artifact
predicate 必须由 `operation_id + operation_type` 定位，而不是只按
`operation_type` 要求唯一。当前冻结 R1 十二案没有同 family 多 operation，因此该项
不阻塞本轮 Proof re-audit，也未在本轮实现。

## 7. 最终状态

Proof re-audit 基础：**APPROVED**。

Genuine R1 execution：**BLOCKED**。

`REPAIR_MILESTONE_R1_PROOF_REAUDIT_BLOCKED`
