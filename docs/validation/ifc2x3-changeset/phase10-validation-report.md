# Phase 10 Window L2 语义闭环验证报告

**验证日期：** 2026-07-22

**结论：** 通过

## 验收范围

Phase 10 只验收 IFC2X3 直线墙上的 `add_window_with_opening_to_wall`：从
damaged IFC 与自然语言请求进入 Agent，经 Target/Prototype 解析、语义权限清单、
Bound ChangeSet 0.2、原子 IFC 写回、重新打开、独立 L1/L2 验证，最后由
Evaluation 0.2 决定是否发布成功 IFC。L3 保留记录但不作为兼容性要求。

本阶段没有实现 RAG、向量检索、未知自定义 Pset，亦没有扩展 Door、Opening-only、
Beam、Column 或曲墙操作。

## LargeBuilding 离线验收

| 项目 | 结果 |
|---|---|
| Source | `dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc` |
| Source SHA-256 | `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725` |
| Damaged SHA-256 | `ca703845ddf4a434eea0317498fb29893877f87d66047cf6c890a61cd2844933` |
| 公共输入 | damaged IFC + 自然语言；不包含 original Window/Opening Gold |
| Stage 1 / Stage 2 | 1 / 1 |
| ChangeSet | `text2ifc/ifc-repair-changeset/0.2`，`binding_status=bound` |
| Production | application passed；reopen passed；L1 passed；L2 passed；L3 not_required |
| Private benchmark | L1 passed；L2 passed；L3 not_required |
| 发布 | `successful_ifc` 存在且可重新打开为 IFC2X3 |

离线接受测试位于
`tests/ifc_repair/test_phase10_large_building.py`。Private original 和 mutation
role mapping 只在公共生产结果完成后进入 `BenchmarkEvaluationInputs`；它们不会进入
Agent Prompt、语义 manifest、ChangeSet 或公共 Evaluation。

## 真实 DeepSeek 四路径 UAT

配置：`deepseek-openai-compatible / deepseek-v4-flash`，输入与输出保护预算均为
65,536。通过证据目录：

```text
dataset/processed/ifc-repair/phase10-live-uat/uat-20260722T003815795017Z/
```

| 案例 | Stage 1 | Stage 2 | 澄清/确认 | Bound 0.2 | Production L1/L2 | Private L1/L2 | 输出 SHA-256 | 终态 |
|---|---:|---:|---|---|---|---|---|---|
| `complete-request` | 1 | 1 | 无 | 是 | passed / passed | passed / passed | `8f8e218989f8ea96fc84f85cbd4b9877b512dad8bdde02f8cfad3bd9ea80a078` | succeeded |
| `clarification-completed` | 2 | 1 | 补全几何参数 | 是 | passed / passed | passed / passed | `8f8e218989f8ea96fc84f85cbd4b9877b512dad8bdde02f8cfad3bd9ea80a078` | succeeded |
| `type-name-no-guid` | 1 | 1 | 无；仅给 Type 名称 | 是 | passed / passed | passed / passed | `8f8e218989f8ea96fc84f85cbd4b9877b512dad8bdde02f8cfad3bd9ea80a078` | succeeded |
| `dimensions-then-prototype-confirmation` | 1 | 1 | 用户确认唯一候选 | 是 | passed / passed | passed / passed | `8cc899fed74c64f0fbc0c8d5caa7d505496e250c2964f5b007459acdd0fdcbc6` | succeeded |

每个案例均保存真实 Stage 1 attempt、Stage 2 provider metadata、response ID、模型
名称、调用次数、ChangeSet、公开 Evaluation、成功 IFC 和单独的 private benchmark
报告。`synthetic_fallback=false`。不同请求产生不同的确定性语义关系 GlobalId，因此
Prototype 确认案例的 IFC 文件哈希与其余三例不同，不影响 L1/L2 等价性。

首次沙箱运行保存在
`dataset/processed/ifc-repair/phase10-live-uat/uat-20260721T164902731636Z/`，
四例均如实记录为 `provider_failed`，异常链为
`APIConnectionError -> ConnectError -> PermissionError`，Stage 2 为 0。获得外部网络
授权后执行同一 runner 才产生上述成功证据；失败记录没有被改写或替换。

## 发布门槛

成功发布必须同时满足：

1. Bound ChangeSet 0.2 合同与 base/request/manifest 哈希匹配；
2. 单一临时 IFC 事务完整应用，源 IFC 字节不变；
3. 候选 IFC 能重新打开；
4. 独立 L1 的几何、关系、scope 与 preservation 全部通过；
5. 独立 L2 的 required 与已授权 conditional facts 全部通过。

`tests/ifc_repair/test_phase10_publication.py` 冻结 application、reopen、L1 或 L2
任一失败都不得生成 `successful_ifc` 的终态真值表。

## 最终验证命令

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair -q --basetemp=.pytest-tmp-phase10-final-green-20260722
# 422 passed, 1 skipped in 377.19s

.venv\Scripts\python -m pytest tests\agent\test_phase6_2_openai_compat.py -q --basetemp=.pytest-tmp-phase10-provider-final
# 31 passed in 1.65s

.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\ifc_repair
# exit 0

.venv\Scripts\python scripts\ifc_repair\run_phase10_live_uat.py --check-config
# ready; 65536 / 65536; secret_redacted=true

.venv\Scripts\python scripts\ifc_repair\run_phase10_live_uat.py --live
# exit 0; four cases contract_pass=true; synthetic_fallback=false
```

唯一 skip 是既有 Windows symlink 权限分支；其他 reparse/junction 安全测试仍覆盖相同边界。

## Phase 10.1 交接

后续 Phase 10.1 再设计 IFC2X3 属性标准知识源、项目属性索引、关键词与向量混合
检索、置信度/候选间隔校准、歧义候选澄清，以及每个自定义属性的强制用户确认。
这些能力只能向现有通用 semantic slot、manifest 与 operation registry 接口提供候选
事实，不能绕过授权、Binder、L1/L2 或发布门槛。
