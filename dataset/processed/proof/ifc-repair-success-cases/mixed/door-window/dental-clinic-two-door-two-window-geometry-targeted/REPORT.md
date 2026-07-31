# dental-clinic-two-door-two-window-geometry-targeted

本目录是可复核的离线确定性修复证据；Ground Truth 仅供修复后的私有 benchmark comparator 使用。

- 生产修复 IFC 输入：02-damaged.ifc。
- operation 数量：4。
- operation 类型：add_door_with_opening_to_wall, add_window_with_opening_to_wall。
- original、damaged、repaired IFC 均已独立重开为 IFC2X3。
- L0、L1、L2、preservation 与文件哈希均已重新验证；发布结论见 `validation/release-decision.json`。
- 完整三方差异与非阻塞 fidelity warning 见 `validation/AUDIT-REPORT.md`。
- Prompt Profile 与 few-shot 指纹由当前不可变目录重新计算。
- 用户请求和 RepairIntent 均不含 IFC GlobalId、对象 Name 或楼层 Name；宿主墙仅由楼层标高、朝向、墙体长高厚和墙局部位置经确定性索引解析，GUID 只在内部 Bound ChangeSet 中出现。
- damage 同时删除 Door/Window occurrence 与原 Opening；修复从完整墙体重新开洞，不复用残留 Opening。
- synthetic fallback：false。

## 被删除 Door（私有 benchmark 信息）

- `M_Single-Flush:0915 x 2134mm:0915 x 2134mm:229736` (`1byTDaqS91rBnWJlv$n$m2`)
- `M_Single-Flush:0915 x 2134mm:0915 x 2134mm:237881` (`35QeWibpT4DfyH3NIf2nTY`)

## 被删除 Window（私有 benchmark 信息）

- `M_Fixed:1735 x 1000mm:1735 x 1000mm:261994` (`0otfaO0qPDAhynjJ6DmgEk`)
- `M_Fixed:1735 x 1000mm:1735 x 1000mm:254752` (`2g$QZpOGbBUxSNx_ZgxJoj`)
