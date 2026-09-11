# vvo 五窗批量修复报告

## 1. 结论

系统在 `vvo.ifc` 上完成一次真实 DeepSeek 五窗修复：

- 一段中文文本描述 5 个缺失 Window；
- Stage 1 调用 1 次，输出 5-operation RepairIntent；
- Stage 2 调用 1 次，输出一个统一 ChangeSet；
- 五项作为一个 all-or-nothing 事务写入；
- repaired IFC 重新打开；
- 五项 L1、五项 L2 和全局 preservation 全部通过；
- `complete_repair_success = true`；
- `successful_artifact_publishable = true`。

## 2. IFC 输入与输出

| 文件 | 实体 | Root | Wall | Opening | Window |
|---|---:|---:|---:|---:|---:|
| `01-original.ifc` | 48,935 | 1,830 | 77 | 57 | 23 |
| `02-damaged.ifc` | 48,807 | 1,783 | 77 | 52 | 18 |
| `03-repaired.ifc` | 49,046 | 1,828 | 77 | 57 | 23 |

Damage 确定性移除 5 组 Window/Opening。宿主墙、楼层和被指定复用的
Window Type 仍存在于 damaged IFC。

## 3. 用户输入

完整中文请求位于 [input/request.txt](input/request.txt)。每个 operation
明确给出：

- 楼层、Wall 名称和 GlobalId；
- 相对 `wall_local_start` 的中心位置；
- Opening 宽、高和窗台高；
- 复用 Window Type 的名称和 GlobalId；
- `Pset_WindowCommon.IsExternal` 与 `Reference`；
- 非目标 preservation 和整批失败约束。

第 4、5 个 Window 位于同一面宿主墙，但水平位置不同。这一安排验证了同墙
多洞口不是重复 target 冲突，且宿主墙体积应按本批洞口体积总和评估。

## 4. Agent 输出与执行

| 阶段 | 输出 |
|---|---|
| Stage 1 | `agent/repair-intent.json` 中的 `op1` 至 `op5` |
| Deterministic resolver | 唯一 Wall、Window Type 和 property authority |
| Stage 2 | `agent/provider-draft.json` |
| Binder/Audit | `changeset/bound-changeset.json`，5 个 operation |
| Applicator | `03-repaired.ifc`，一次原子事务 |

Provider 为 `deepseek-openai-compatible / deepseek-v4-flash`。真实运行未使用
synthetic fallback。

## 5. Production 验证

`validation/production-evaluation.json` 的终态为：

| 项目 | 结果 |
|---|---|
| application | passed |
| preservation | passed |
| operation | 5/5 passed |
| L1 | 5/5 passed |
| L2 | 5/5 passed |
| L3 | 5/5 not_required |
| complete repair | true |
| publishable | true |

L1 分别测量每个 Window 的 Opening/Wall/Fills/Voids 链、位置、尺寸和朝向，
同时对共享宿主墙使用 batch aggregate void volume。L2 分别验证 Type、Host、
Storey、尺寸和文本授权的 Pset。

## 6. Original 与 repaired 的差异

三个 IFC 的字节数和实体数不同，属于预期：

- 新 Window/Opening 使用新的 GlobalId；
- 新 relationship 和 Pset 可能使用不同实体组织；
- repaired IFC 由 IfcOpenShell 重新序列化；
- L3 不要求 STEP 或 authoring identity 完全相同。

`validation/ifc-comparison.json` 结合全模型 diff 与原/repaired Window 跨 GUID
映射。Production 发布依据不是文件大小，而是每项 L1/L2 和全局 scope
preservation。

## 7. 原子性

该链路不是逐个写出五份局部 IFC 再拼接。一个 ChangeSet 中任何 operation
发生 target、重叠、授权或 L1/L2 失败时，整批不发布 successful artifact。
现有负例已验证重叠的第 5 个洞口会在写入前拒绝整个 transaction。

## 8. 文件说明

| 路径 | 作用 |
|---|---|
| `01-original.ifc` | 原始 vvo Ground Truth |
| `02-damaged.ifc` | 删除五窗后的实际输入 |
| `03-repaired.ifc` | 真实 DeepSeek 发布产物 |
| `input/request.txt` | 完整五窗中文输入 |
| `agent/repair-intent.json` | Stage 1 五 operation 输出 |
| `agent/provider-draft.json` | Stage 2 draft |
| `changeset/bound-changeset.json` | 原子执行合同 |
| `validation/mutation-manifest.private.json` | evaluator-only 删除对象映射 |
| `validation/production-evaluation.json` | 五项 L1/L2 发布证据 |
| `validation/ifc-comparison.json` | 原始与 repaired 比较 |
| `validation/run-summary.json` | Provider 和终态摘要 |
| `FILES.json` | 文件来源、大小与 SHA-256 |

## 9. 当前边界

本案例只证明同类 Window operation 的五项原子批次。它没有证明 Door、
Opening-only 或 Window + Door 异构批次已经实现。
