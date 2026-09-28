# IFC2Text Phase 1 写作与公共桥 Stage Admission

日期：2026-09-17
分支：`codex/bim2text-research`
代码基线：`a333f68b9c01f69c5eb80402582117fc5269906d`

## 1. Admission 结论

当前代码基线获得 **offline Stage Admission**，适用于 IFC2Text Phase 1 的版本化写作链及其进入现有 text2IFC Generation 公共路径的下一次受控真实调用。

这不是能力提升声明，也不是已经完成真实 IFC 往返。Admission 只回答：在不联网、使用 deterministic fake / frozen Provider 输出时，当前 Prompt、Schema、写作 stage、Provider seam、Truth Boundary 和公共 Generation bridge 是否能够按合同运行并 fail closed。

未运行 Full / repository-wide Preflight。

## 2. 固定版本

远端 `origin/codex/bim2text-research` 与本地代码基线均核实为：

```text
a333f68b9c01f69c5eb80402582117fc5269906d
```

该基线已经包含：

- `ifc2text-outline.v0.1`；
- `ifc2text-section-writer.v0.1`；
- `ifc2text-merge.v0.1`；
- 三份 `schemas/ifc2text/*-0.1.schema.json`；
- `src/text2ifc_ifc2text/llm_pipeline.py`；
- 楼层命名空间 fact ref，例如 `S01:W001`；
- 24 section 调用量上限；
- deterministic section assembly；
- `reconstruct_description_with_public_text2ifc` 公共桥；
- 离线完整 text → public Generation → compiled IFC 测试。

## 3. 环境

- Python 3.12.4
- Windows 11 `10.0.26200`
- IfcOpenShell 0.8.5
- Shapely 2.1.2

工作树仍包含其他 Dataset/文档任务留下的并行修改。本 Admission 没有清理、覆盖或将这些修改作为证据；IFC2Text 任务代码在上述提交已单独提交和推送。

## 4. 最终离线门禁

运行的 Stage 集合：

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
  -q --basetemp=.pytest-tmp-ifc2text-admission-a333f68b -p no:cacheprovider
```

结果：

```text
33 passed in 59.68s
0 failed
0 skipped
network transport attempted: false
```

另外执行：

```powershell
.\.venv\Scripts\python.exe -m compileall -q src/text2ifc_ifc2text tests/ifc2text
```

退出码为 0。

## 5. 这 33 项具体覆盖什么

### IFC2Text 写作链

覆盖：

- facts → prompt-safe fact index；
- Outline → Section → Merge → deterministic assemble；
- 生成最终 `design-description-llm.md`；
- Prompt registry 版本/hash 可复现；
- source IFC path 和 source GlobalId 不进入写作 Prompt；
- 未知 fact ref 阻断；
- malformed JSON 阻断；
- required fact 静默遗漏阻断；
- Merge 丢 section 阻断；
- Outline 超过 24 个 section 在后续 Provider 调用前阻断。

### Provider adapter seam

覆盖：

- 正常 JSON live-result 适配；
- `finish_reason=length` 截断失败；
- 输入超过 token 上限时 transport 前阻断；
- connection failure 的证据脱敏；
- 可重试瞬时连接错误。

### 公共 Generation bridge

`tests/ifc2text/test_offline_public_bridge.py` 实际执行：

```text
IFC2Text fake writing
→ 最终 design description
→ SessionStore.original_input
→ run_design_brief_clarification_loop
→ run_ready_session_to_ifc
→ Generation gates
→ compile/reopen
→ final acceptance
→ compiled IFC
```

只有 Design Brief、Generator 和 Audit 的模型响应使用明确标记的冻结离线夹具。SessionStore、公共编排、run report sidecar 检查、GenerationBudget、确定性 Gate、IFC 编译/重开和 final acceptance 使用真实生产代码。

该测试开发过程中还证明两个门禁会真实生效：

1. Design Brief sidecar 不完整时，run report 阻断；
2. fake Provider evidence 缺 usage 时，GenerationBudget 采用最保守计费并阻断。

最终没有通过跳过报告或放松预算使测试转绿，而是补齐可审计证据。

## 6. Truth Boundary

当前写作模型输入不包含：

- source IFC 字节；
- source IFC path；
- source GlobalId；
- STEP ID 或原始 STEP 文本。

重建端的建筑输入仍只有最终设计说明文本。源 IFC 和结构化 facts 保留在 evaluator / IFC2Text 本地侧，用于提取、诊断与最终 Compare，不作为 text2IFC 的额外答案输入。

## 7. 会使 Admission 失效的变化

以下变化发生后，应重新判断并通常重新执行 Stage Admission：

- 修改任何 IFC2Text v0.1 Prompt 字节或 registry identity；
- 修改 `schemas/ifc2text/` 合同；
- 修改 `llm_pipeline.py` 的 stage 行为或调用量边界；
- 修改 prompt-safe fact Truth Boundary；
- 修改 deterministic merge assembly；
- 修改当前使用的 OpenAI-compatible Provider transport contract；
- 修改 `reconstruct_description_with_public_text2ifc`；
- 修改当前路径依赖的 Design Brief / `run_ready_session_to_ifc` 公共合同；
- 修改当前路径依赖的 GenerationBudget、compile/reopen 或 final publication 合同。

## 8. 下一步允许做什么

在用户已经明确授权本轮 LLM 调用的前提下，可以在这一 Admission 上进行受控真实调用，但仍应：

1. 先记录真实 Provider、模型、Prompt 版本和本次 token/call 上限；
2. 首先只跑 IFC2Text 写作 stage，保存原始失败或成功；
3. 写作成功后人工/程序核对 text，不把同一案例修补后的结果包装为盲测提升；
4. 再将**完全相同的最终 text**交给现有 text2IFC 公共路径；
5. 保存重建 IFC 并用独立 Compare 报告 missing / extra / position / dimension / relationship 差异。

允许声明：当前 Stage 的离线准入成立。
尚不能声明：真实 Provider 已可用、真实往返成功、IFC2Text 能力已经提升、无 IfcSpace 房间推导语义正确或建筑普遍可重建。
