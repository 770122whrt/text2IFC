# IFC2Text Phase 1 写作与公共桥 Stage Admission v0.2

日期：2026-09-17
分支：`codex/bim2text-research`
代码基线：`c7f29a7080229a2c9d9a31e3a3fe11ece6588aa9`

## 1. 当前结论

`c7f29a70` 获得 IFC2Text Phase 1 写作与公共 Generation bridge 的 **offline Stage Admission v0.2**。本次重新准入是因为第一次真实 `hxp` 写作揭示了 v0.1 的高基数 section 问题和失败 evidence 落盘缺口；两项机制均在新版本中修复并重新离线验证。

此前 `a333f68b` 的 Admission 仍保留为历史记录，但不再用于当前执行。未运行 Full / repository-wide Preflight。

## 2. 为什么必须重新 Admission

第一次真实写作使用 `ifc2text-outline.v0.1`，Outline 成功，但把 S01 的 34 面墙全部安排到一个 `s01-walls` section。该 section 在 8192 completion-token 上限下以 `finish_reason=length` 截断，Provider adapter 正确 fail closed。

同时发现 IFC2Text stage runner 没有捕获 `OpenAICompatError`，因此预算账本保存了失败计费，但具体 stage 没有独立 `failure.json`。这属于 evidence persistence 的确定性实现缺口。

因此当前实现：

- 保留已经真实运行过的 `ifc2text-outline.v0.1`，不原地改写；
- 新增并启用 `ifc2text-outline.v0.2`；
- 一个 section 最多 12 个 `primary_owned_fact_refs`；
- 总 section 数仍最多 24；
- 高基数墙、开口、门窗或空间必须分块；
- 确定性 validator 独立执行 12-primary 上限；
- `OpenAICompatError` 的脱敏 evidence 必须写入 IFC2Text `failure.json`。

## 3. 固定 Prompt 与代码

当前真实执行使用：

| Stage | Prompt |
|---|---|
| Outline | `ifc2text-outline.v0.2` |
| Section Writer | `ifc2text-section-writer.v0.1` |
| Merge | `ifc2text-merge.v0.1` |

代码与远端分支都核实为：

```text
c7f29a7080229a2c9d9a31e3a3fe11ece6588aa9
```

## 4. Stage Preflight

执行与上一版 Admission 相同范围的离线集合，并加入新的 primary-fact bound 和 failure persistence 负例：

```powershell
.\.venv\Scripts\python.exe -m pytest \
  tests/ifc2text \
  tests/agent/test_prompt_registry.py \
  tests/agent/test_interactive_cli_generation.py::test_ready_phase6_2_session_generates_ifc_report_and_db_artifacts \
  tests/agent/test_phase6_2_openai_compat.py::test_openai_compatible_live_provider_returns_live_provider_result \
  tests/agent/test_phase6_2_openai_compat.py::test_parse_chat_completion_blocks_length_finish_reason \
  tests/agent/test_phase6_2_openai_compat.py::test_deepseek_live_provider_rejects_prompt_over_input_budget_before_call \
  tests/agent/test_phase6_2_openai_compat.py::test_deepseek_live_provider_wraps_connection_failure_without_secrets \
  tests/agent/test_phase6_2_openai_compat.py::test_deepseek_live_provider_retries_transient_connection_then_succeeds \
  -q --basetemp=.pytest-tmp-ifc2text-admission-c7f29a70 -p no:cacheprovider
```

结果：

```text
35 passed in 60.89s
0 failed
0 skipped
network transport attempted: false
```

另外：

```powershell
.\.venv\Scripts\python.exe -m compileall -q src/text2ifc_ifc2text tests/ifc2text
```

退出码为 0；远端 `origin/codex/bim2text-research` 与上述 code commit 一致。

## 5. 第一次真实失败如何保留

历史失败目录：

`dataset/processed/experiments/ifc2text-phase1-20260917/hxp-live-writing-v01/`

预算账本共 5 个真实 attempt：

| Attempt | Stage | 状态 | 实际计费 token |
|---:|---|---|---:|
| 1 | outline | completed | 25,464 |
| 2 | section | completed | 2,337 |
| 3 | section | completed | 1,746 |
| 4 | section | completed | 4,207 |
| 5 | section / `s01-walls` | failed | 19,378 |

总计 53,132 token。失败原因是 `finish_reason=length`。这次失败已经揭示 `hxp`，因此后续同模型重跑只能作为修复后的 viability / regression 证据，不能作为未见能力提升证据。

## 6. 当前 Truth Boundary 与调用边界

保持：

- 写作 LLM 不接收 source IFC；
- 不接收 source path；
- 不接收 source GlobalId；
- 不接收原始 STEP 文本；
- 重建端只接收最终 `design-description-llm.md`。

当前写作结构还有两层硬边界：

```text
总 section 数 <= 24
每个 section primary facts <= 12
```

真实运行仍需另行固定单调用 input / completion 上限和总 task budget。

## 7. 当前允许的下一步

在用户已经授权真实 LLM 的前提下，当前 Admission 允许第二次受控 `hxp` 写作尝试。运行应继续：

1. 保存 v0.1 失败，不覆盖；
2. 使用新的运行目录和 `ifc2text-outline.v0.2`；
3. 保持单调用和总预算上限；
4. 如果真实写作成功，先检查最终 text 与 facts 覆盖；
5. 再把同一份 text 交给现有 text2IFC 公共路径；
6. 最后保存 reconstructed IFC 与 GUID-independent Compare。

当前可声明：v0.2 离线 Stage Admission 成立。
当前仍不能声明：第二次真实写作成功、真实往返完成、或系统能力已经提升。
