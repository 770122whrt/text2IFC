# Phase 09.1 IFC Type 证据与 Prototype 解析验证报告

**验证日期：** 2026-07-21
**范围：** IFC Type/Occurrence 证据分离、人类可用的 Prototype 解析、TypeRecord-backed Production Evidence、LargeBuilding 回归与真实 DeepSeek UAT。

## 结论

Phase 09.1 验收通过。系统不再把 41 个 surviving Window occurrence 上不同楼层的 `Constraints.Level` 聚合成同一个 Window Type 的事实，因此真实 L2 路径不再出现错误的 `PROTOTYPE_TYPE_FACT_CONFLICT`。

用户现在可以通过唯一 Type 名称 `M_Fixed:0915 x 1830mm` 使用 Prototype，而不必知道 GUID；也可以只给 Window 类别和 `915 x 1830 mm` 尺寸，由系统提供一个去重后的 Type 候选并等待明确授权。内部证据仍记录解析后的 Type GUID `2cXV28XOjE6f6irhu0CO_c`。

真实 UAT 的四条路径均完成 Stage 1、确定性解析、Stage 2、IFC application 和 L2 入口。L1、application、preservation 均通过；L2 因尚未完成 Window semantic authoring 而诚实地 `not_evaluable`。所有案例均为 `not_publishable`，只保留 diagnostic candidate，没有 `successful_ifc`。

## 根因与修正

原实现把 occurrence 的合并属性当作 Type 属性来源。LargeBuilding 中同一个 Window Style 被 41 个 Window 共用，而 surviving Window 的 `Constraints.Level` 分布在 Level 1 和 Level 2，于是旧逻辑错误地产生：

```text
PROTOTYPE_TYPE_FACT_CONFLICT:
2cXV28XOjE6f6irhu0CO_c:pset:Constraints.Level
```

修正后的权威链路为：

1. IFC index/extractor v0.2 将可靠 `TypeRecord` 存入独立 SQLite 表，不混入可编辑 occurrence 记录。
2. direct 与 inherited 属性通过同一提取规则区分；occurrence-direct 的 Level、Sill Height 不再成为 Type authority。
3. Prototype GUID、标准化 Type 名称和候选均只解析到可靠 `TypeRecord`。
4. Production Evidence 只从同一 run index 中的授权 TypeRecord 读取 Type 事实；不再使用 occurrence 投票或聚合兼容路径。
5. 每个 OperationDefinition 声明允许的 `prototype_ifc_classes` 和尺寸路径。Window 操作只接受 `IfcWindowStyle`/`IfcWindowType`，因此 DoorStyle、SpaceType 和尺寸不匹配的 Window Type 不会进入候选。

## LargeBuilding 确定性回归

| 观察项 | 结果 |
|---|---|
| Source IFC | `dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc` |
| Source SHA-256 | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725` |
| Damaged IFC SHA-256 | `ca703845ddf4a434eea0317498fb29893877f87d66047cf6c890a61cd2844933` |
| Window Type | `M_Fixed:0915 x 1830mm` |
| 内部 Type GUID | `2cXV28XOjE6f6irhu0CO_c` |
| Surviving occurrences | 41，跨 `Level 1`、`Level 2` |
| application / preservation / L1 | passed / passed / passed |
| L2 / L3 | not_evaluable / not_required |
| 错误 Type conflict | 不存在 |
| 发布状态 | not_publishable；只有 diagnostic candidate |

离线回归通过公共 `RepairAPI`，输入只使用 Type 名称，不把 Type GUID 放进用户请求。解析证据仍保存 GUID，用于 ChangeSet、IFC relationship 和 Production Evidence 绑定。

## 真实 DeepSeek UAT

配置检查：

```powershell
.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --check-config
# provider=deepseek-openai-compatible
# model=deepseek-v4-flash
# input/completion guards=65536/65536
```

通过证据目录：

```text
dataset/processed/ifc-repair/phase9-live-uat/uat-20260720T174639706876Z/
```

| 案例 | 用户侧 Prototype 表达 | Stage 1 | Stage 2 | 候选 | 内部 Type GUID | 终态 |
|---|---|---:|---:|---:|---|---|
| complete-input | 明确 Type GUID | 1 | 1 | 0 | `2cXV28XOjE6f6irhu0CO_c` | not_publishable |
| incomplete-then-feedback | Type GUID，几何后续补充 | 2 | 1 | 0 | `2cXV28XOjE6f6irhu0CO_c` | not_publishable |
| type-name-no-guid | `M_Fixed:0915 x 1830mm`，无 GUID | 1 | 1 | 0 | `2cXV28XOjE6f6irhu0CO_c` | not_publishable |
| dimensions-then-prototype-confirmation | fixed window + `915 x 1830 mm` | 1 | 1 | 1 个 `IfcWindowStyle` | `2cXV28XOjE6f6irhu0CO_c` | not_publishable |

四个案例 `contract_pass=true`，合计 Stage 1 调用 5 次、Stage 2 调用 4 次。候选确认路径记录 `prototype_confirmed=true`；候选包含名称、类型、允许的尺寸、41 个 occurrence 和两个 storey，但不暴露完整 Type Psets、密钥或 private Gold。

沙箱内运行曾在 Stage 1 收到 `APIConnectionError`。扩展后的安全异常链为 `APIConnectionError → ConnectError → PermissionError`，证明该失败来自执行环境禁止外部 socket，而非 Prompt、Schema 或 RepairAPI。使用明确授权的外部网络权限执行同一命令后，四案例全部通过。失败证据保持原样，未被改写为成功。

此外，UAT 的 `.env` 合并原先使用 `setdefault`，可能让陈旧进程变量覆盖仓库配置；现在与既有 live CLI 一致，由显式 `--env-file` 覆盖同名进程变量，并由独立 RED/GREEN 测试固定。Provider 层仅对连接/timeout 类异常执行最多 3 次的有限退避重试，不重试 Schema 或模型内容错误。

## 当前真实 L2 边界

Type conflict 修正后，L2 的剩余 `not_evaluable` 项均为 Phase 10 的真实 Window authoring 缺口：

- `window.base-quantities`
- `window.classification`
- `window.height`
- `window.host`
- `window.instance`
- `window.material`
- `window.width`

这表示 Type authority 已正确，但新建 Window occurrence 尚未完整写入冻结的 Pset、quantity、material、classification、host/instance 与宽高语义。Phase 09.1 不放宽 Evaluation 0.2，也不把 Type 信息误当成全部 occurrence authoring 已完成。

## 验证命令

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair -q --basetemp=.pytest-tmp-phase-09-1-final
# 388 passed, 1 skipped in 179.41s

.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\ifc_repair
# exit 0

.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --live
# exit 0; four cases contract_pass=true

git diff --check
# exit 0
```

唯一 skip 是既有 Windows symlink 权限分支；非跳过的 reparse/junction 测试继续覆盖同一安全边界。

Provider 兼容层回归 `tests/agent/test_phase6_2_openai_compat.py` 另有 `31 passed`，覆盖 DeepSeek 64k、脱敏失败、有限连接重试与 `.env` 配置行为。

## Phase 10 交接

Phase 10 只接收上述 Window L2 semantic authoring 缺口，并保持以下边界：

- `WIN-01`、`WIN-02` 继续 pending，直到 LargeBuilding 的 L1 与冻结 L2 都通过。
- L3 authoring/identity exactness 继续记录但不承诺兼容。
- Door、单独 Opening、Beam、Column 通过 Operation Registry 的 Prototype class/尺寸接口扩展，不在 Phase 09.1 实现。
- vector/similarity 只能用于候选检索，不能自动授权 Prototype；128k 仍留待后续实验。
