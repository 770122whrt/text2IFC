# AdvancedProject 五窗大型 IFC 修复报告

## 1. 结论

系统使用真实 DeepSeek 生成的 RepairIntent 和统一 ChangeSet，在
`AdvancedProject.ifc` 上恢复 5 组 Window/Opening。经过 Comparator 0.2 和
两个窄范围 evaluator alignment 修复后，保存的 ChangeSet 无需重新调用
Provider 即可完成：

- deterministic application：passed；
- repaired IFC 重新打开：passed；
- global preservation：passed；
- 5 项 L1：passed；
- 5 项 L2：passed；
- L3：not_required；
- `complete_repair_success = true`；
- `successful_artifact_publishable = true`。

## 2. 大型 IFC 输入输出

| 文件 | 大小 | 实体 | Root | Wall | Opening | Window |
|---|---:|---:|---:|---:|---:|---:|
| `01-original.ifc` | 44,337,371 B | 770,172 | 47,248 | 390 | 427 | 263 |
| `02-damaged.ifc` | 44,228,167 B | 769,814 | 47,072 | 390 | 422 | 258 |
| `03-repaired.ifc` | 44,242,439 B | 770,044 | 47,114 | 390 | 427 | 263 |

三个文件均为 IFC2X3，并已重新打开。Damage 删除五组 Window/Opening，但
保留五面宿主墙、楼层和用户指定的 Window Type。

## 3. 用户输入

完整输入位于 [input/request.txt](input/request.txt)。五项跨越 Level 1 和
Sixth Floor，Opening 尺寸包括：

- 1000 × 2200 mm；
- 1000 × 600 mm；
- 2000 × 2200 mm；
- 3000 × 2200 mm。

用户指定四种 BALANS Window Type，并要求保留宿主墙身份、放置、材料、类型、
属性、楼层、空间和所有非目标构件。任何一项不能安全完成时整批失败。

## 4. 真实 Agent 与确定性重放

原始真实运行：

```text
run_id: repair-291e0bde96974f62b37efc8ffeeab961
provider: deepseek-openai-compatible
model: deepseek-v4-flash
Stage 1 calls: 1
Stage 2 calls: 1
```

结构化证据：

- `agent/repair-intent.json`：5 个 `add_window_*` operation；
- `agent/provider-draft.json`：Stage 2 draft；
- `changeset/bound-changeset.json`：绑定 damaged SHA-256 的 ChangeSet 0.2；
- `changeset/semantic-manifests.json`：每项 L2 authoring authority。

首次运行在 application 后被旧 evaluator 拒绝，没有伪造 successful IFC。
后续定位到两个 evaluator/evidence false negative：

1. 映射 Window Type 的实体窗框可在 Opening 内均匀内缩，旧 L1 错误要求
   frame bbox 与 Opening 边界完全相同；
2. occurrence-direct material 应优先于 Type material，旧 L2 把两者错误并集。

修复后使用同一 request、同一 damaged SHA-256、同一 saved ChangeSet 和同一
semantic manifests 重放。没有再次调用 Provider，也没有从 Ground Truth
修改 ChangeSet。

## 5. Production 与 Comparator

最终 `validation/production-evaluation.json`：

| Gate | 结果 |
|---|---|
| application | passed |
| preservation | passed |
| operations | 5/5 passed |
| L1 | 5/5 passed |
| L2 | 5/5 passed |
| L3 | 5/5 not_required |
| successful artifact | published |

全模型 Comparator 0.2 的三次测量：

| Run | Comparator | Open + compare | Peak RSS |
|---:|---:|---:|---:|
| 1 | 40.097 s | 51.764 s | 1.083 GB |
| 2 | 39.638 s | 50.878 s | 1.081 GB |
| 3 | 39.234 s | 50.683 s | 1.082 GB |

median comparator 为 39.638 秒，低于 120 秒预算；峰值 RSS 低于 4 GiB
预算。最终完整重放约 94 秒。

## 6. 如何解读 original 与 repaired

repaired 恢复了 Window 数量、Opening 数量、五项关系和用户授权语义，但实体
总数仍少于 original。原因包括：

- 新 Window/Opening/relationship 使用新的 GlobalId；
- 原作者模型可能包含不同的 occurrence-direct Pset 组织；
- Type 和 mapped representation 被复用，而不是复制所有底层表示实体；
- L3 authoring exactness 当前不作为发布要求。

因此，本案例可证明大型 IFC 上的几何关系、语义和 preservation 成功，不能
声称 STEP、GlobalId 或作者工具内部组织与 Ground Truth 完全一致。

## 7. 文件说明

| 路径 | 作用 |
|---|---|
| `01-original.ifc` | 大型 Ground Truth，evaluator/manual review 使用 |
| `02-damaged.ifc` | 五窗缺失的实际修复输入 |
| `03-repaired.ifc` | 最终通过并发布的 IFC |
| `input/request.txt` | 完整中文五窗请求 |
| `agent/repair-intent.json` | 真实 Stage 1 输出 |
| `agent/provider-draft.json` | 真实 Stage 2 draft |
| `changeset/bound-changeset.json` | 最终重放的统一 ChangeSet |
| `changeset/semantic-manifests.json` | L2 authoring authority |
| `validation/application.json` | IFC 写回和角色映射 |
| `validation/production-evaluation.json` | preservation 与五项 L1/L2 |
| `validation/comparator-benchmark.json` | 大型模型性能证据 |
| `validation/mutation-manifest.private.json` | evaluator-only 原始对象映射 |
| `FILES.json` | 文件来源、大小与 SHA-256 |

## 8. 当前边界

本案例仍只覆盖直线墙上的 Window + Opening。曲面墙、Door、Opening-only、
Beam、Column 和 L3 authoring exactness 均不在本案例成功声明内。
