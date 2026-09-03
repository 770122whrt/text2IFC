# vvo-authority-triplet-public-repair

本目录是可复核的离线确定性修复证据；Ground Truth 仅供修复后的私有 benchmark comparator 使用。

- 生产修复 IFC 输入：02-damaged.ifc。
- operation 数量：4。
- operation 类型：add_window_with_opening_to_wall, fill_existing_opening_with_door。
- original、damaged、repaired IFC 均已独立重开为 IFC2X3。
- L0、L1、L2、preservation 与文件哈希均已重新验证；发布结论见 `validation/release-decision.json`。
- 完整三方差异与非阻塞 fidelity warning 见 `validation/AUDIT-REPORT.md`。
- Prompt Profile 与 few-shot 指纹由当前不可变目录重新计算。
- 用户请求和 RepairIntent 均不含 IFC GlobalId、对象 Name 或楼层 Name；Wall 或既有 Opening 仅由用户给出的有界几何约束经确定性索引解析，GUID 只在内部 Bound ChangeSet 中出现。
- synthetic fallback：false。

## 被删除 Door（私有 benchmark 信息）

- `单扇 - 与墙齐:800x2480:255008` (`2IUEnGd5v4Yfg1ZlPtd0qa`)
- `单扇 - 与墙齐:935x2400:275772` (`1B$rgWypT66viEf2CI1iIv`)

## 被删除 Window（私有 benchmark 信息）

- `固定:500x1180:279940` (`2dYMXn0_5AKRbD_0yUIAqJ`)
- `固定:870x2370:255906` (`08xWVL$9z6JRwr3oWJHoAz`)
