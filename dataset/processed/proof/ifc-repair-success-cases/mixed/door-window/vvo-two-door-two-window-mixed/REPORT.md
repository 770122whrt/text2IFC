# vvo-two-door-two-window-mixed

- 证据模式：offline deterministic bound ChangeSet。
- operation 数量：4。
- operation 类型：add_window_with_opening_to_wall, fill_existing_opening_with_door。
- original、damaged、repaired IFC 均已独立重开为 IFC2X3。
- application、L1、L2、preservation 与文件哈希均已重新验证。
- Prompt Profile 与 few-shot 指纹由当前不可变目录重新计算。
- 用户请求和 RepairIntent 均不含 IFC GlobalId；名称、楼层与墙局部位置经确定性索引解析后，才在内部 ChangeSet 绑定 GUID。
- synthetic fallback：false。

## 被删除 Door

- `单扇 - 与墙齐:800x2480:255008` (`2IUEnGd5v4Yfg1ZlPtd0qa`)
- `单扇 - 与墙齐:935x2400:275772` (`1B$rgWypT66viEf2CI1iIv`)
