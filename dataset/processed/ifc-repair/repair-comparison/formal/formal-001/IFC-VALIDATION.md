# 损坏 IFC 格式校验：PASS

- 文件：[冻结 damaged.ifc](private/mutation/damaged.ifc)；公开副本与其字节一致。
- 校验器：ifcopenshell.validate，IfcOpenShell 0.8.5。
- Schema：IFC2X3；EXPRESS rules：已执行。
- 诊断数量：0。
- SHA-256：`ba29acc5355a0039e0e7504f5003abebfcd69fa0fb209dea3a55a2d22e255189`。
- [机器结果与全部诊断](private/damaged-ifc-validation.json)。

PASS 表示该文件通过本地 IFC schema／EXPRESS 校验，构件缺失仍是待修任务。
这不表示已经完成修复，也不代表 buildingSMART 在线验证服务已验证。

可在仓库根目录独立复查：

```powershell
.\.venv\Scripts\python.exe -m ifcopenshell.validate --rules <本题 damaged.ifc 的完整路径>
```
