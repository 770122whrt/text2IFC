# 混合构件修复成功案例

本目录保存一次请求同时修复多种 IFC 构件的成功案例，并按构件组合继续分类。

## Door + Window

- [vvo 两门两窗混合修复](door-window/vvo-two-door-two-window-mixed/REPORT.md)：
  一次无 GUID 的用户文本生成一个统一 ChangeSet，其中包含 2 个 Door operation
  与 2 个 Window operation。公开 RepairIntent 使用名称、楼层、墙名称、保留
  Opening 名称及墙局部位置定位；确定性解析完成后，内部 Bound ChangeSet 才绑定
  GlobalId。

该案例通过 IFC application、4 项 L1/L2、全模型 preservation、IFC2X3 重开和
文件哈希校验，证据模式为 `offline_bound_deterministic`。
