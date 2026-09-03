# Phase 10.1 显式 IFC 属性写入与验证报告

**验证日期：** 2026-07-23  
**结论：** 通过

## 验收边界

Phase 10.1 只处理用户已经明确给出 `Pset.Property=Value` 的标量属性，不做
别名、模糊匹配、向量检索或 RAG。当前写入范围固定为目标 occurrence，
支持 `IfcPropertySingleValue`；共享 Type 修改仍然拒绝。

Window Type 的处理规则如下：

1. 用户给出可唯一精确解析的 Type 名称或 GlobalId：复用该 Type；
2. 候选不唯一：暂停并要求用户确认；
3. 用户没有给 Type：创建并绑定 operation 专属的确定性系统模板 Type；
4. 不按尺寸或相似 Window 自动猜测 Type。

## 一条完整链路

```text
damaged IFC + 用户文本
  -> DeepSeek Stage 1 / RepairIntent 0.2
  -> 精确 IFC2X3 属性 registry
  -> 标准属性直接授权，未知自定义属性生成 preview
  -> 用户用运行时 preview_hash 确认
  -> DeepSeek Stage 2
  -> Semantic Manifest 0.1
  -> Bound ChangeSet 0.2
  -> 原子 IFC2X3 写回
  -> reopen
  -> Production L1/L2
  -> 发布 successful IFC
  -> 发布完成后才运行 private Ground Truth benchmark
```

LLM 只负责结构化意图和 ChangeSet 草案。属性是否合法、确认是否绑定当前
模型/请求、Type 是否可复用、IFC 图如何修改以及能否发布，均由确定性代码决定。

## LargeBuilding 离线验收

Source：
`dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc`

Source SHA-256：
`102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`

| 案例 | 属性 | Type 决策 | 交互 | Production | Private Gold |
|---|---|---|---|---|---|
| `exact-standard-occurrence` | `Pset_WindowCommon.FireRating=EI30` / `IfcLabel` | 精确复用 `M_Fixed:0915 x 1830mm` | 无 | L1 passed；L2 passed；L3 not_required | L1 passed；L2 passed；L3 not_required |
| `custom-property-confirmation` | `Custom_Asset.AssetCode=W-007` / `IfcLabel` | 无 Type 输入，创建专属系统模板 | `property_confirmation` 后用运行时 preview hash 恢复 | L1 passed；L2 passed；L3 not_required | L1 passed；L2 failed；L3 not_required |

自定义案例的 private L2 `failed` 是预期且必须保留：原始 Gold Window 绑定既有
作者 Type，而用户没有指定该 Type，Production 按已确认文本采用系统模板。
Private Gold 只描述 authoring 差异，不是 Production 发布门；如果把它强行改成
passed，反而会伪造“系统模板等同原始作者语义”的结论。

两案例均验证：

- requested property 是目标 Window 的 occurrence-direct Pset；
- 值和 IFC 标量类型在 reopen 后完全一致；
- source/damaged IFC 字节不变；
- 既有共享 Type 及其所有非目标 occurrence 的归一化语义 hash 不变；
- application、reopen、L1 或 Production L2 任一失败时不暴露
  `successful_ifc`。

离线入口：
`tests/ifc_repair/test_phase10_1_large_building.py` 和
`tests/ifc_repair/test_phase10_1_publication.py`。

## 真实 DeepSeek UAT

最终不可变证据目录：

```text
dataset/processed/ifc-repair/phase10.1-live-uat/uat-20260723T055315222853Z/
```

Provider：`deepseek-openai-compatible`  
Model：`deepseek-v4-flash`  
预算：input 65,536；completion 65,536  
Synthetic fallback：`false`

| 案例 | Stage 1 | Stage 2 | 澄清 | Production L1/L2 | Private L1/L2 | 输出 SHA-256 | 终态 |
|---|---:|---:|---|---|---|---|---|
| `exact-standard-occurrence` | 1 | 2 | 无 | passed / passed | passed / passed | `137b12fbda961b287544541ad98e16d5f1235a593b0b98032c17a56f0a793ef4` | succeeded |
| `custom-property-confirmation` | 1 | 2 | `property_confirmation`；运行时 preview hash | passed / passed | passed / failed（预期 authoring 差异） | `0b00b1eb37aeb4652eab90a9e3751765bac95bfa6818f5759d4e4ff39e7c3732` | succeeded |

两个案例的 `contract_pass=true`，总状态为 `passed`。Stage 2 的两次 attempt
是 Provider/Schema 重试记录，不是离线 fallback；每次真实 attempt 和最终响应均
保存在对应 run 目录。

真实 runner：
`scripts/ifc_repair/run_phase10_1_live_uat.py`。

## 发布门

只有以下条件同时成立才发布 IFC：

1. RepairIntent、确认答案、当前 IFC fingerprint 与请求 hash 一致；
2. 属性解析得到精确标准事实或已确认的自定义事实；
3. Manifest 与 Bound ChangeSet 的 property fact/hash 一致；
4. application 为单一原子事务，输出可 reopen；
5. L1 几何、关系、scope、preservation 全通过；
6. Production L2 能在 repaired IFC 中读回相同值、类型与
   occurrence-direct ownership。

Private Gold 在发布之后运行，不能进入 Prompt、Manifest、ChangeSet 或
Production Evidence。

## 验证命令

```powershell
.venv\Scripts\python -m pytest `
  tests\ifc_repair\test_phase10_1_large_building.py `
  tests\ifc_repair\test_phase10_1_publication.py `
  tests\ifc_repair\test_orchestrator_security.py -q
# 8 passed

.venv\Scripts\python -m pytest tests\knowledge tests\ifc_repair -q `
  --basetemp=.pytest-tmp-phase10-1-final
# 508 passed, 1 skipped in 499.72s

.venv\Scripts\python scripts\ifc_repair\run_phase10_1_live_uat.py --check-config
# ready; 65536 / 65536; secret_redacted=true

.venv\Scripts\python scripts\ifc_repair\run_phase10_1_live_uat.py --live
# status=passed; two cases contract_pass=true; synthetic_fallback=false
```

唯一 skip 是既有平台权限分支。`compileall` 与 Phase 10.1 文件的
`git diff --check` 均通过；完整结果也记录在 `10.1-04-SUMMARY.md`。

## Phase 10.2 交接

Phase 10.1 的输出边界是一个已经精确化的 tuple：

```text
(target occurrence, exact Pset name, exact property name,
 typed scalar value, occurrence_direct ownership, provenance)
```

Phase 10.2 可以接收非精确、多语言或项目化表达，并返回有证据、带置信度的
候选 exact tuples；低置信度、低 margin、冲突或自定义候选必须澄清。检索层
不能直接写 IFC，也不能绕过 Phase 10.1 的确认、Binder、原子 application、
reopen L2 和发布门。
