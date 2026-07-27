# Phase 9 Stage 1 合同修复与双路径 UAT 报告

**日期：** 2026-07-20
**范围：** RepairIntent Stage 1 Prompt、Provider 输出 Schema、系统指纹封装、缺参澄清状态机，以及两组真实 DeepSeek UAT。
**结论：** Stage 1 合同修复通过；完整输入与“缺参后补充”两条真实路径都成功进入 Stage 2。整体 IFC 仍因既有 L2 Production Evidence 冲突而 `not_publishable`，未发布成功 IFC。

## 1. 修复前问题

修复前存在不可同时满足的合同：

- Prompt 禁止模型编造缺失事实；
- Window Registry 要求 `position`、`opening`、`window` 参数完整；
- RepairIntent 没有合法的缺参状态；
- `model_fingerprint` 等系统绑定字段却要求由模型计算并返回。

因此第一次真实 UAT 中，模型先因省略 `opening` 被拒绝，纠正时又填写无意义的
`1 mm` 占位值，并因无法可靠计算模型 SHA-256 而被拒绝。API 也没有 Stage 1
缺参暂停点：只区分“完整 intent”与“Provider 失败”。

## 2. 修复后的合同

### 2.1 Provider 只生成语义正文

新增 Provider 输出合同：

```text
text2ifc/ifc-repair-intent-body/0.1
```

正文只包含：

- `operations`；
- `target_query`；
- 用户明确给出的部分 `parameters`；
- attribute / Pset / material intent；
- 显式 Prototype intent；
- public provenance。

以下字段由运行时确定性封装，不再交给 LLM：

- `request_id`；
- `source_request_hash`；
- `prompt_fingerprint`；
- `model_fingerprint`。

真实 UAT 中 Provider 报告模型为 `deepseek-v4-flash`，运行时生成的模型指纹为：

```text
sha256:f61ff5cf8e1cc88da6944d6bcd3e2e7da5ff27dd3288a8781908018cb8240cd6
```

### 2.2 缺参是合法业务状态

Registry 现在分别执行：

1. partial shape validation：验证已经提供的值，不因尚未提供的 required 字段而拒绝；
2. deterministic constant injection：只注入 Schema `const`，例如
   `position.reference=wall_local_start` 和 `window.fit_opening=true`；
3. required-path discovery：确定性计算仍缺少的可执行参数；
4. complete validation：只有全部 required path 齐全后才允许进入目标解析和 Stage 2。

缺参结果写入 `repair-intent-completeness.json`，并进入：

```text
clarification_required / missing_required_parameter
```

缺参不消耗 Provider correction retry，也不再归类为 `provider_failed`。

### 2.3 同一 run 的反馈续跑

状态路径为：

```text
INDEX_READY
  -> Stage 1 partial intent
  -> CLARIFICATION_REQUIRED
  -> 用户 add_detail
  -> INDEX_READY
  -> Stage 1 complete intent
  -> INTENT_READY
  -> target resolution
  -> Stage 2
```

回答与 clarification ID、state version 绑定；旧回答、越权 candidate 和非法 answer
仍由 RunStore fail closed。

## 3. Prompt 修复

Stage 1 Prompt 保留版本 ID `ifc-repair-intent.v0.1`，新 hash 为：

```text
sha256:507796fcdcb2c238f40eaf4b60cea655aeeab0d51332cd04e30183f21bf308c7
```

Prompt 已明确：

- 不输出或计算系统指纹；
- 缺失参数必须省略，禁止数值占位和猜测；
- Registry 负责缺参检测与确定性常量；
- 包含一组完整参数示例和一组缺参示例；
- 示例标识和值不可复制。

## 4. 自动化测试

新增或调整的关键行为测试：

- Provider 语义正文由系统封装四个绑定字段；
- `model_fingerprint` 来自 Provider metadata；
-空 Window 参数成为一次有效的 `clarification_required`，不会触发第二次纠错；
- 缺参清单精确为宽、高、窗台高和中心位置；
- Schema `const` 由 Registry 注入；
- API 在 Stage 2 前暂停；
- feedback 合并到同一 run，重新调用 Stage 1 后进入 Stage 2；
- 原有 target ambiguity、Prototype、CLI、LargeBuilding 和 Prompt registry 路径保持通过。

实施过程中的聚焦结果：

```text
46 passed
30 passed
```

最终 IFC repair 全套结果：

```text
378 passed, 1 skipped in 158.08s
```

单个 skip 是既有 Windows symlink 权限分支，不属于本次 Stage 1 变更。

## 5. 两组真实 DeepSeek UAT

命令：

```powershell
.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --check-config
.venv\Scripts\python scripts\ifc_repair\run_phase9_live_uat.py --live
```

配置检查：`deepseek-v4-flash`，输入/输出预算均为 `65536`，密钥未输出。

两组测试都使用从冻结 `LargeBuilding.ifc` 删除一组 Window + Opening 后得到的
deterministic damaged IFC。目标墙、Prototype 和几何事实只在 UAT 用户文本中明确
提供；private mutation manifest 不进入 Provider 输入。

### 5.1 完整输入

输入摘要：

```text
在墙 1F6umJ5H50aeL3A1As_wTm 上恢复窗，明确使用 Type
2cXV28XOjE6f6irhu0CO_c；开洞 915 x 1830 mm，窗台 305 mm，
中心距 wall_local_start 3042.5 mm。
```

结果：

| 项目 | 实测 |
|---|---|
| Stage 1 Provider calls | 1 |
| Stage 1 issues | 0 |
| completeness | `repair_intent`，missing `[]` |
| clarification | 无 |
| Stage 2 Provider calls | 1 |
| application / preservation | passed / passed |
| L1 / L2 / L3 | passed / not_evaluable / not_required |
| terminal | `not_publishable` |

### 5.2 不完整输入 + feedback

第一次输入保留相同墙和显式 Prototype，但不提供尺寸和位置。

Stage 1 正确输出 partial parameters，Registry 检出：

```json
[
  "/opening/height_mm",
  "/opening/sill_height_mm",
  "/opening/width_mm",
  "/position/center_offset_mm"
]
```

系统问题为：

```text
操作 operation-1 还缺少：窗高、窗台高度、窗宽、窗中心距墙局部起点的距离。
请补充这些数值及单位；系统不会猜测缺失的几何参数。
```

提交的 feedback：

```text
开洞宽 915 毫米、高 1830 毫米、窗台高 305 毫米；
窗中心距 wall_local_start 3042.5 毫米。
```

结果：

| 项目 | 实测 |
|---|---|
| 初次 Stage 1 | valid partial，issues `0` |
| 初次 terminal | `clarification_required` |
| reason | `missing_required_parameter` |
| feedback 后 Stage 1 | valid complete，issues `0` |
| Stage 1 Provider calls 总数 | 2 |
| Stage 2 Provider calls | 1 |
| application / preservation | passed / passed |
| L1 / L2 / L3 | passed / not_evaluable / not_required |
| terminal | `not_publishable` |

两组 application candidate SHA-256 相同：

```text
ea289e756ae519f84b3cf33f24538f9b8b8fe4c12196ad8e0fb1d2082cd3fec5
```

这说明完整输入和经 clarification 补全的输入收敛到了相同的确定性 IFC 产物。

## 6. 为什么整体仍未发布

两组均不是 Stage 1、Stage 2、Audit、application、preservation 或 L1 失败。

直接重放 Production Evidence Builder 得到：

```text
ProductionEvidenceError
PROTOTYPE_TYPE_FACT_CONFLICT
2cXV28XOjE6f6irhu0CO_c:pset:Constraints.Level
```

同一显式 Window Type 在 damaged IFC 索引中关联 41 个 surviving Window record，
其 `pset:Constraints.Level` 出现多个值。当前 Production Evidence 规则将它们聚合为
Prototype Type 事实时 fail closed，因此 L2 为 `not_evaluable`。

这是后续 Production Evidence / L2 authority 建模问题，不是本次 Stage 1 合同回归。
两组都只发布 diagnostic candidate 和 Evaluation；没有 `successful_ifc`。

## 7. 证据

真实 UAT 汇总：

```text
dataset/processed/ifc-repair/phase9-live-uat/uat-20260720T110750461060Z/live-uat-result.json
```

案例目录：

```text
.../complete-input/
.../incomplete-then-feedback/
```

每个 run 保留：

- Stage 1 rendered prompt、raw/live response、attempt record；
- system-enveloped `repair-intent.json`；
- `repair-intent-completeness.json`；
- resolution、Stage 2 ChangeSet；
- diagnostic IFC、Evaluation 和 manifest。

最终回归命令：

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair -q
.venv\Scripts\python -m pytest tests\agent\test_prompt_registry.py -q
.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\ifc_repair
git diff --check
```

## 8. 当前边界

- 缺参接口由 Operation Registry 驱动，可扩展到 Opening、Door、Beam、Column；
- 当前 Window 位置仍要求最终得到数值 `center_offset_mm`；“墙中央”等符号位置的
  确定性派生接口继续保留为后续扩展；
- 多操作缺参按 operation 顺序逐项澄清，不允许一次回答越权修改其他 operation；
- L3、vector matching、curved wall 和 128k 默认预算仍不在本次范围。
