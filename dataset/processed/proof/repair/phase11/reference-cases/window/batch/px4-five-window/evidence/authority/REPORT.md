# px4 五窗批量原子修复

## 结论

本案例在包含 501,401 个 IFC 实体的 `px4_1.ifc` 上，一次删除并修复五扇 Window。系统从一段统一文本生成一个包含五项 operation 的统一 ChangeSet，完成全有或全无的 IFC 应用。Production 与 Private Ground Truth 的五项 L1/L2 均通过，成功 IFC 已发布。

该案例使用离线确定性 Provider 验证完整编译、应用和评估链路，不属于真实 LLM UAT。真实 DeepSeek 证据见 LargeBuilding r22 案例。

## 被删除和修复的 Window

1. `固定:840x1775:237502`
2. `固定:370x370:249432`
3. `固定:370x370:249553`
4. `塑钢窗-三扇中固定:DSC2415:266052`
5. `固定:1100x1875:289339`

五条链路均满足：

- Window、Opening、Wall 关系闭合；
- 宿主墙为当前支持的直墙；
- Window 与宿主墙楼层一致；
- 被删除后仍有 surviving Window Type 可供复用；
- 原始 Window 几何位于对应 Opening 范围内。

## 本案例覆盖的关键能力

- 五个 operation 使用一个统一 ChangeSet；
- 同一面墙上存在水平位置相同、但高度不同的上下叠窗；
- Opening 冲突使用墙面二维矩形相交，而不是仅比较水平区间；
- duplicate-chain 判断包含窗台高度；
- occurrence-direct Pset、Window/Opening Quantity 和 Type 复用；
- 任一 operation 冲突时整批拒绝，不发布部分成功 IFC；
- 501,401 实体模型的 preservation、L1、L2 和 Private GT 对照。

## 冻结指纹

| Artifact | SHA-256 |
|---|---|
| Original | `8c336ee9af66a55fb4cac26b608bef11ace5a3a0a490931205045e4f87b4c46d` |
| Damaged | `0630c9bd509bde693c3c3368bcea9e041a3af8d5d1c34d6f797c0f41fb7d0e6c` |
| Repaired | `7f5cc6c61b0007ff1616a9f567c545762a593f0df5b764c230337e514de0eb4a` |

Bound ChangeSet 的 `base_model_fingerprint` 与上述 damaged SHA-256 完全一致。该 frozen damaged IFC 在 r8 成功进程退出前直接导出，避免重新执行 mutation 时 STEP 排序变化造成指纹漂移。

## 文件导航

| 路径 | 用途 |
|---|---|
| `01-original.ifc` | 原始 Ground Truth |
| `02-damaged.ifc` | 系统实际输入 |
| `03-repaired.ifc` | 通过 gate 后发布的 IFC |
| `input/request.txt` | 单次五窗修复文本 |
| `agent/repair-intent.json` | Stage 1 结构化意图 |
| `agent/provider-draft.json` | 离线确定性 Stage 2 草案 |
| `changeset/bound-changeset.json` | 绑定 damaged 指纹的统一 ChangeSet |
| `changeset/semantic-manifests.json` | 确定性语义 authoring 权威 |
| `validation/production-evaluation.json` | Production L1/L2 |
| `validation/private-ground-truth-evaluation.json` | 私有 Ground Truth 对照 |
| `FILES.json` | 文件大小、角色和 SHA-256 |
