# 三面特殊墙的编译器能力探针

此目录是离线定位实验，不是新的真实 Text→IFC 往返，也不是 accepted Proof。

- 输入：hxp中W011、W013、W015的已知截面、拉伸和放置参数。
- 路径：独立最小BIM JSON 2.3 → 现有compile_document → IFC2X3 → IfcOpenShell网格和投影比较。
- 结果：三个案例均生成多边形截面的IfcWall；关闭洞口切割后，包围盒坐标、投影轮廓距离与面积对称差的本次测量均为0。
- 证明：底层编译器能表达这三例几何，不能把旧失败简单归因于“不支持特殊墙”。
- 不证明：LLM能从说明生成正确JSON、IfcWallStandardCase语义完整保留、门窗洞口及材料关系、整栋验收、任意复杂墙支持。
- 源IFC字节未修改；没有Provider调用，也没有改变旧Compare容差或旧结果。

复现脚本：scripts/ifc2text/probe_polygon_wall_backend_v01.py。使用新的--out目录，避免覆盖本轮工件。

阅读入口：docs/reports/ifc2text-problem-solution-decision-guide-2026-09-21.md。
