# 第一版：完整保留的历史设计参考

本版机器终端通过，但用户要求按概念图右上角改成南侧敞开、可见楼梯和细杆护栏，因此不登记为第二版设计的人工验收。当前验收的是旁边的open-court-v2；本目录保留第一版成品与全过程。

[中文输入](request.txt) · [IFC](generated.ifc) · [模型JSON](model.json) · [查看器](views/viewer.html) · [整体](views/overall.png) · [隐藏屋盖](views/courtyard-roof-hidden.png)

真实Brief和Generator后，原loop因缺55组void/fill关系失败；离线修复后确定性追加110条关系，保留实体与原关系，再进行真实Audit续跑。不称为无中断的全新完整loop。

IFC SHA256：`38457bfad619c0c35ab536209001a00db65e3b8fc4f570e0139e779f290308ab`，645,369字节。原独立检查1084/1084、部件颜色72/72通过。封闭外围、较小内庭、隐藏楼梯和透明整板栏杆导致视觉意图偏离，原因与原始图像保留于 [原报告](../evidence/v1/continuation-01/REPORT.md)。

[完整证据](evidence/README.md)。第一版累计9次/750,000 token已包含在后续17次总账中，不重复相加；未认证完整工程合规。
