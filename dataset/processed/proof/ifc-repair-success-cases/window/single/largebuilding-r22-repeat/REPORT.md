# LargeBuilding 单窗真实 DeepSeek 重复实验（r22）

## 结论

这次实验从 damaged IFC 和一段完整用户文本开始，真实调用 DeepSeek 完成 Stage 1 与 Stage 2，生成统一 ChangeSet，随后由确定性编译器写出新的 IFC。最终结果为 `succeeded`，Production 与私有 Ground Truth 的 L1/L2 均通过，没有使用 synthetic fallback。

| 项目 | 结果 |
|---|---|
| Provider | `deepseek-openai-compatible` |
| Model | `deepseek-v4-flash` |
| Stage 1 | 1 次调用，成功 |
| Stage 2 | 1 次调用，成功 |
| RepairIntent | `text2ifc/ifc-repair-intent/0.4` |
| Bound ChangeSet | `text2ifc/ifc-repair-changeset/0.3` |
| Production | L1 passed；L2 passed |
| Private Ground Truth | L1 passed；L2 passed |
| 发布状态 | `complete_repair_success=true`；`successful_artifact_publishable=true` |
| Provider fallback | `false` |
| Provider 链路耗时 | 100.843 秒 |

## 输入

输入 IFC 是 `02-damaged.ifc`。损伤阶段删除了：

- Window：`M_Fixed:0915 x 1830mm:354395`
- 原 Window GlobalId：`2cXV28XOjE6f6irgi0CO4t`
- 与该窗关联的 Opening、Fills 和 Voids 关系

用户文本位于 `input/request.json`，主要授权如下：

- 宿主墙 GlobalId：`1F6umJ5H50aeL3A1As_wTm`
- 窗宽 915 mm、高 1830 mm、窗台高 305 mm
- 距 `wall_local_start` 的中心偏移 3042.5 mm
- 复用现存 Window Type：`M_Fixed:0915 x 1830mm`
- 明确写入 16 个 occurrence-direct `IfcPropertySingleValue`
- 明确写入 Opening occurrence 的 3 个 `BaseQuantities`

原始 Ground Truth 和损伤清单只供 mutation/evaluator 使用，没有进入 Provider Prompt。

## Agent 与编译输出

Stage 1 将文本解析为 `agent/repair-intent.json`；Stage 2 生成受约束草案 `agent/provider-draft.json`。系统随后完成目标解析、属性确认、模型指纹绑定和确定性补全，产生 `changeset/bound-changeset.json`。

最终发布的窗 GlobalId 为 `366opc$vnGhBMHfcrrv5Kg`。它不是复用已删除窗的原 GlobalId；当前 L3 authoring identity 仍为观察项。

## 验证解释

`validation/production-evaluation.json` 证明 damaged→repaired 的应用、全局 preservation、几何关系和授权语义通过。`validation/private-ground-truth-evaluation.json` 使用原始 IFC 进行独立 L1/L2 对照。

有效属性语义完整匹配为 `true`。字节级/owner 级的 occurrence-direct 完全一致为 `false`，原因是删除后重建会产生新的 Window、Pset 和关系身份；这属于暂不作为发布门槛的 L3 authoring exactness，不代表属性值或作用域缺失。

官方 IfcOpenShell 比较摘要为：

- added：1
- changed：126
- deleted：1

IFC 文件大小不要求逐字节相同。当前成功合同是几何关系、授权语义和非目标 preservation 均通过。

## 文件导航

| 路径 | 用途 |
|---|---|
| `01-original.ifc` | 原始 Ground Truth，仅供比较 |
| `02-damaged.ifc` | 系统实际输入 |
| `03-repaired.ifc` | 通过 gate 后发布的结果 |
| `input/request.json` | 用户文本 |
| `agent/` | 两阶段 Agent 输入解析与原始响应 |
| `changeset/bound-changeset.json` | 可执行统一 ChangeSet |
| `validation/` | mutation、Production、Private GT 与比较证据 |
| `FILES.json` | 文件大小和 SHA-256 |
