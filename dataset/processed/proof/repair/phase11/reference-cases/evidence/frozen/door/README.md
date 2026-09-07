# Door 修复成功案例

本目录按案例规模分为 `single/` 与 `batch/`。所有案例均通过独立哈希、IFC
重开、ChangeSet 绑定、L1/L2 和 preservation 校验。

## 单门修复

| 案例 | 方式 | 主要覆盖 |
|---|---|---|
| [LargeBuilding 保留 Opening](single/largebuilding-door-preserve-opening/REPORT.md) | 填充既有 Opening | 复用既有 Door Type |
| [vvo 保留 Opening](single/vvo-door-preserve-opening/REPORT.md) | 填充既有 Opening | 中型模型与既有 Door Type |
| [AdvancedProject 保留 Opening](single/advancedproject-door-preserve-opening/REPORT.md) | 填充既有 Opening | 770,172 entities 大型模型 |
| [LargeBuilding 生成 DoorStyle](single/largebuilding-generated-door-type/REPORT.md) | 新建 Opening + Door | 用户未要求复用 Type 时使用受控模板 |

## 多门修复

- [vvo 五门批量修复](batch/vvo-five-door-preserve-opening/REPORT.md)：一次用户文本，
  一个包含 5 个 Door operation 的统一 ChangeSet，整体通过或整体回滚。

Door/Window 混合案例独立收录在
[`../mixed/door-window/`](../mixed/door-window/)。当前案例均为
`offline_bound_deterministic`，不冒充真实 Provider UAT。
