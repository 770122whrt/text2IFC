# Phase 9 IFC + 文本修复编排验证报告

**验证日期：** 2026-07-20  
**范围：** 单一 `RepairAPI`、薄 CLI、离线一般编排、LargeBuilding Window 诊断、可选 DeepSeek UAT。

## 结论

Phase 9 的确定性验收通过。调用者只需提供 IFC2X3 路径与自然语言；`RepairAPI` 统一组合 RepairIntent Stage 1、指纹绑定 SQLite 索引、持久化 run store、确定性解析、ChangeSet Stage 2 与 `RepairOrchestrator`。CLI 只调用 API 的 `start`、`continue_with_answer` 和 `read_result`，不拥有索引、Provider、Audit、apply 或 Evaluation 实现。

一般离线 fixture 的完整成功路径为 Stage 1/Stage 2/apply/evaluation = `1/1/1/1`；双操作失败路径为 `1/1/1/0`，整笔事务回滚且没有成功路径。两条路径都保持 caller IFC SHA-256 不变，且没有网络调用。

LargeBuilding 通过同一公共 API 接收测试准备阶段生成的 damaged IFC 与自然语言。测试准备所需 original/mutation mapping 没有进入 API 参数、Provider stage 或公共 evidence。实测结果为 L1 `passed`、L2 `not_evaluable`、L3 `not_required`、complete/publishable `false/false`，仅保留 diagnostic candidate；没有修改 Window authoring 或 L2 期望来制造通过。

## 合同、策略与 Prompt 版本

| 项目 | 版本 / SHA-256 |
|---|---|
| RepairIntent | `text2ifc/ifc-repair-intent/0.1` |
| Run state / clarification / result | `text2ifc/ifc-repair-*-0.1` |
| ChangeSet | `text2ifc/ifc-repair-changeset/0.1` |
| Public Evaluation | `text2ifc/ifc-repair-evaluation-public/0.2` |
| Evaluation policy | `phase8.1` |
| Stage 1 prompt | `ifc-repair-intent.v0.1` / `sha256:d8e48fbdce5ecc7553329849aeaa015b47d92fc25a657e9837bd7a3200ea4e1c` |
| Stage 2 prompt | `ifc-repair-changeset.v0.2` / `sha256:958f7f38be22d7c89a90112dcd811620c706a209ec4dc506b4980e395693de44` |
| DeepSeek guards | input `65536`, completion `65536` |

六个 `ifc-repair-*-0.1.schema.json` 均通过 Draft 2020-12 schema 自检。

## 离线验收证据

| 路径 | Stage 1 | Stage 2 | apply | evaluation | 结果 |
|---|---:|---:|---:|---:|---|
| 单操作完整成功 | 1 | 1 | 1 | 1 | succeeded，成功 IFC + manifest |
| 双操作第二项失败 | 1 | 1 | 1 | 0 | not_publishable，无部分输出/成功路径 |

测试入口没有 benchmark ID、original IFC 或 mutation mapping 参数。fake stages 为进程内确定性实现，不建立网络连接。

### LargeBuilding

| 观察项 | 实测结果 |
|---|---|
| Original source SHA-256 | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`（运行前后不变） |
| Caller damaged IFC SHA-256 | `309a165798b1f601e4130e13b50ba9cdedc8840005cebe7c9aca16aa248225b3`（运行前后不变） |
| Provider calls | Stage 1 `1`，Stage 2 `1`（离线 fake） |
| L1 / L2 / L3 | `passed` / `not_evaluable` / `not_required` |
| Complete / publishable | `false` / `false` |
| 输出 | diagnostic candidate；无 `successful_ifc` |

该结果是 Phase 10 前的真实语义边界：几何/关系 L1 已通过，但生产 L2 缺少足够授权事实，因此 fail closed 为 `not_evaluable`。

## CLI 终端矩阵

| 状态 | exit class |
|---|---:|
| `succeeded` | 0 |
| `clarification_required` | 2 |
| `invalid_input` / `unsupported` | 3 |
| `provider_failed` | 4 |
| `audit_failed` / `application_failed` | 5 |
| `not_publishable` | 6 |
| state/tamper/unknown run | 7 |
| `cancelled` / EOF cancel | 8 |

默认 human 输出为中文优先的短摘要；`--json` 只写一个紧凑、版本化 JSON 到 stdout；`--quiet` 不写正常进度；`--non-interactive` 不读取 stdin。澄清候选只显示 GUID/class/name/storey/position/evidence，EOF 与取消均 fail safe。

## 真实 DeepSeek UAT

```powershell
.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --check-config
# exit 0; status=ready; max_input_tokens=65536; max_completion_tokens=65536

.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --live
# exit 0; terminal status=provider_failed; publishable=false
```

证据目录：`dataset/processed/ifc-repair/phase9-live-uat/uat-20260719T235252588248Z/`。

实际 Provider 尝试为 Stage 1 `2`、Stage 2 `0`。第一次 Stage 1 输出缺少必需 `opening` 参数；纠正尝试因 `REPAIR_INTENT_MODEL_FINGERPRINT_MISMATCH` 被确定性绑定拒绝。Stage 2、application 与 L1/L2 Evaluation 均未到达，因此本次 UAT 不构成“两阶段成功”，也没有 L1/L2 成功声明。结构化结果为 `provider_failed`、complete/publishable `false/false`，没有成功 IFC；响应 ID、usage 与脱敏尝试均保存在 run evidence 中，密钥和 base URL 未输出。

## 可复现命令

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair\test_repair_cli.py tests\ifc_repair\test_phase9_offline_e2e.py tests\ifc_repair\test_phase9_large_building.py -q

.venv\Scripts\python -m pytest tests\ifc_repair -q

.venv\Scripts\python -m pytest tests\ifc_repair\test_orchestrator_security.py tests\ifc_repair\test_request_stage.py tests\ifc_repair\test_general_changeset_stage.py tests\ifc_repair\test_repair_cli.py -q

.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\ifc_repair

git diff --check
```

最终 CLI/offline/LargeBuilding 聚焦结果为 `21 passed in 17.82s`；全套结果为 `356 passed, 1 skipped in 128.58s`；安全/Prompt 聚焦为 `45 passed in 3.36s`。`git diff --check` 退出 0，仅打印既有工作树文件的 CRLF 提示。

安全检查覆盖 public/private canary、路径逃逸、状态篡改、Provider 脱敏、bounded stdout、未知 run 与完整 manifest。详细 payload 始终在非覆盖 run 目录内，caller source 只读。

## 后续边界

- Phase 10：修复 Window 的 Pset、quantity、Material、Classification、`IsExternal` 等 L2 authoring；Phase 9 不宣称完成。
- Phase 11/12：通过 Registry seam 扩展 Opening、Door、Beam、Column；Phase 9 不实现这些 operation。
- Phase 13：vector retrieval/授权策略与 128k near-limit 实验；当前仍为 65536 guard。
- 更后阶段：L3 authoring/identity exactness 与 curved/free-form wall；不属于当前成功门。
