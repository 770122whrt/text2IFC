# IFC Repair Derived Evidence

本目录保存 IFC repair 的派生 fixture、运行证据和验证报告。它不是源数据
入口，也不作为 Provider 的隐式知识库。

## 保留策略

- `retain`：包含 source-bound manifest、Provider trace、private/public
  authority split 或发布证据；删除前必须人工确认。
- `regenerable`：可由已登记源 IFC、脚本和 manifest 重建。
- 历史目录名称不代表已经通过验收；以目录内 terminal state、evaluation
  和 hash manifest 为准。
- 不允许清理脚本根据名称直接删除本目录内容。

## Phase 10.3

| 路径 | 内容 |
|---|---|
| `phase10.3-dataset-audit.json` | dataset manifest 和 processed inventory 只读审计 |
| `phase10.3-compatibility-matrix.json` | 四份 IFC2X3 的解析、链发现和索引矩阵 |
| `phase10.3-vvo-five-window-offline/` | 五窗确定性 damage、repair、L1/L2、private comparator 证据 |
| `phase10.3-vvo-five-window-deepseek-uat/` | 受限网络下如实保留的 provider failure |
| `phase10.3-vvo-five-window-deepseek-uat-network/` | 真实 DeepSeek 五窗成功 UAT |

正式 benchmark 身份由以下文件定义：

```text
dataset/manifests/ifc-repair-benchmarks.jsonl
dataset/manifests/ifc-repair-cases/vvo-five-window-001.private.json
```

详细报告：

```text
docs/validation/ifc2x3-changeset/
phase10.3-five-window-batch-validation-report.md
```
# IFC Repair 运行产物

本目录保存开发阶段的 IFC repair 运行、UAT 和验证证据。面向人工查阅的正式成功案例位于：

- `../proof/ifc-repair-success-cases/`
- 本轮多模型回归：`verification-20260726/REPORT.md`

## 保留规则

- 保留最近一次真实 Provider 成功运行及其必要前序基线；
- 多 IFC 回归只保留最终成功目录和一份简化失败边界；
- `diagnostic candidate` 不视为成功 IFC；
- 临时 pytest basetemp、空目录、被后续成功运行取代的中间重跑可删除；
- Ground Truth、damaged IFC、published repaired IFC、请求、ChangeSet 和 L1/L2 证据必须成组保留。

## 当前关键运行

| 目录 | 用途 |
|---|---|
| `phase10.5-window-fidelity-live-20260726-r22/` | 最新真实 DeepSeek 单窗端到端成功 |
| `phase10.5-window-fidelity-live-20260726-r21/` | r22 之前的成功基线 |
| `verification-20260726/vvo-five-window/` | vvo 五窗离线确定性回归 |
| `verification-20260726/advancedproject-five-window-r4/` | AdvancedProject 五窗大模型回归 |
| `verification-20260726/px4-five-window-r7/` | px4 五窗、多层叠窗二维冲突修复后的回归 |

其余 Phase 9–10.4 目录属于历史阶段证据，除非另行归档，不应作为当前能力结论引用。

## 2026-07-26 清理记录

已删除：

- 四个 pytest 临时目录；
- Phase 10.5 r17–r20 中间运行；
- 空的 BasicHouse 与 px4 r2 目录。

以下旧验证目录已被报告提炼或被最终成功运行取代，但其 `fixture/` 由异常 Windows ACL 保护；普通删除与提升权限删除均返回 access denied，因此暂时保留：

- `verification-20260726/7y3-five-window*`
- `verification-20260726/advancedproject-five-window`、`-r2`、`-r3`
- `verification-20260726/px4-five-window`、`-r3` 至 `-r6`

它们不是当前正式结果。释放 ACL 后可删除；不要删除 `advancedproject-five-window-r4`、`px4-five-window-r7`、`vvo-five-window`。
