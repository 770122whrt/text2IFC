# vvo-five-door-authority-public-repair

本目录是可复核的离线确定性修复证据；Ground Truth 仅供修复后的私有 benchmark comparator 使用。

- 生产修复 IFC 输入：02-damaged.ifc。
- operation 数量：5。
- operation 类型：fill_existing_opening_with_door。
- original、damaged、repaired IFC 均已独立重开为 IFC2X3。
- L0、L1、L2、preservation 与文件哈希均已重新验证；发布结论见 `validation/release-decision.json`。
- 完整三方差异与非阻塞 fidelity warning 见 `validation/AUDIT-REPORT.md`。
- Prompt Profile 与 few-shot 指纹由当前不可变目录重新计算。
- 用户请求和 RepairIntent 均不含 IFC GlobalId、对象 Name 或楼层 Name；Wall 或既有 Opening 仅由用户给出的有界几何约束经确定性索引解析，GUID 只在内部 Bound ChangeSet 中出现。
- synthetic fallback：false。

## 被删除 Door（私有 benchmark 信息）

- `单扇 - 与墙齐:800x2480:255008` (`2IUEnGd5v4Yfg1ZlPtd0qa`)
- `单扇 - 与墙齐:800x2480:255190` (`2IUEnGd5v4Yfg1ZlPtd0tI`)
- `单扇 - 与墙齐:760x2440:257419` (`08xWVL$9z6JRwr3oWJHoYK`)
- `单扇 - 与墙齐:760x2440:257461` (`08xWVL$9z6JRwr3oWJHoYg`)
- `四扇推拉门:M2424:258870` (`08xWVL$9z6JRwr3oWJHpOf`)

## 被删除 Window（私有 benchmark 信息）

- 本案例不删除 Window occurrence。
