# 显式闭合单墙：两次真实复验与容差口径

日期：2026-09-21。保持 text2IFC 正向系统和注册 Prompt 不变，仅复验上一轮已经输出的 W013 单墙说明。没有更改源 hxp、归属整理副本或既有20 mm比较容差。

## 目标与输入

输入固定为 `ifc2text-wall-recovery-20260921-v07/closeout-v08/single-wall-description-v08.txt`。本轮不重写说明，也不追加源 IFC/facts/参考 JSON。一次真实公共 Brief、一次现有 Generator 阶段，若合法则由既有编译器生成 IFC，并独立重开测量。只验证扣洞前单墙，不含洞口、材料、空间或整栋 Audit/最终接受。

## 容差不是观测误差

此前约0.055 mm是一次测量结果，11面墙中的实际最大值为0.0552060993 mm。不是预先定义的阈值，也不是完整轮廓正确的充分条件。坐标按mm保留一位小数，每轴舍入最多0.05 mm；对应二维顶点位移上界sqrt(2)*0.05≈0.07071 mm（对应点、连线结构不变）。闭合、无自交、底标高与高度另行检查，不能靠距离小取代。

本轮预先增加 **0.1 mm单墙轮廓/包围范围诊断检查**，作为数值传递专项检查，不替换原20 mm往返门槛，不宣称建筑施工容差。阈值依据舍入上界与小幅数值余量，而不是把观测最大值向上凑；两种结果和原始差值同时报告。轮廓采用离散对称Hausdorff并对线段加密，明确其近似性质，同时报告面积对称差与Z范围。

IFC的RepresentationContext.Precision是表示上下文的数值精度，不等于本研究的源/重建差异验收阈值，本轮不改此属性。
来源：buildingSMART IFC2x3 TC1 IfcGeometricRepresentationContext；Shapely hausdorff_distance官方文档。
https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcgeometricrepresentationcontext.htm
https://shapely.readthedocs.io/en/latest/reference/shapely.hausdorff_distance.html

## 累计额度

本次明确授权：重建侧12→14，总token仍2000000，仅用于显式闭合单墙复验。起点写作21、重建12、累计占额1342637，未知历史占额原样计入。

新预算分支保存完整前序快照并继承其所有token及调用数；原账本继续保持暂停。只允许本次两次重建调用，不允许写作或新的预算重置。失败、重试和用量未知均保留、计入；检测到前序变化或未结算调用即阻断。新权威入口为本实验 `budget/authorization.json` 与 `budget/goal-budget.json`，不修改历史授权文件。

## 验证与证据

先提交脚本、测试和本计划。复用已准入且未改变的公共 Brief/Generator/编译器链路，补充预算继承、两次上限、失败恢复阻断、显式闭合、自交负例、既有公共链离线编译检查；网络拦截下运行，不做Full Preflight。

通过后执行新目录 `dataset/processed/experiments/ifc2text-closed-wall-retry-20260921-v08/`。不得编辑收到的JSON、补点后冒充真实成功、修改容差或覆盖旧失败；若成功，仅允许声明该单墙的真实几何复验通过，不推广到整栋或未知建筑。
