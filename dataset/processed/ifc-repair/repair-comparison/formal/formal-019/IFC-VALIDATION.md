# formal-019 IFC 格式检查

本次用 IfcOpenShell 0.8.5 重开完整G和D，执行schema＋EXPRESS。

|输入|schema|诊断数|结果|
|---|---|---:|---|
|G：private/reference.ifc|IFC2X3|0|通过|
|D：public/model.ifc|IFC2X3|0|通过|

源文件未改；只移除已列明目标，原型、楼层及其他产品保全。实际网格和数值另见private/checks.json、private/geometry-review.json。

这是本地规则检查，不等于buildingSMART在线验证或usBIM导入／显示核验；未声称模型修复成功。
