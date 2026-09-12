# 光庭阅读馆第二版：真实完整生成，待人工验收

已完成全新真实 **Brief → Generator → Audit → IFC**，运行 `ce8116ce095acdcf`，Provider 为 api.deepseek.com / deepseek-v4-flash。采用 legacy_full，未复用先前 Brief/候选，没有候选修复调用。独立重开复核通过，人工验收尚未进行，**未登记 accepted Proof**。

- [最终 IFC](generated-open-court.ifc)（IFC2X3，1,161,796字节）
- [完整中文输入](request.txt) · [已批准对话](conversation.json) · [交互查看器](views-final/viewer.html)
- [整体图](views-final/overall.png) · [正面敞口](views-final/courtyard-front.png) · [隐藏屋盖查看回廊](views-final/courtyard-roof-hidden.png) · [楼梯近景](views-final/stair-detail.png)
- [窗框与双玻璃面板](views-final/IfcWindow.png) · [门框与木门扇](views-final/IfcDoor.png) · [细杆护栏](views-final/IfcRailing.png)

最终IFC SHA256：`650accdb5131b1ae3fdc26e5af000029deb4860fe6f38571dcad174d8ff9b39d`。顶层文件与正式发布文件逐字节相同；最终图片和检查均重新绑定正式发布后的IFC。`views/`及`independent-provisional.json`为Audit等待期间的中间检查，不作为最终文件证据；正式发布重编译改变文件哈希后已重新检查和渲染，保留中间结果。

## 输入与实际结果

尺寸是Agent在用户委托下深化的设计，不伪称用户逐字指定。配色微调经用户委托，模型本轮输入与rerun-01一致。原第一版保持，第二版以概念图右上角的南侧敞开、外露楼梯、围庭回廊为目标；没有家具、植物或渲染补画。

|项目|实际结果与复核|
|---|---|
|总体|两层24×18m；首层0m、二层3.6m；南侧敞开U形楼板和屋盖|
|采光庭|X7.4–16.6m、Y0–10.6m，向南连通；实际U形投影检查通过|
|围护与空间|16墙、12空间；室外回廊使用原生EXTERNAL属性|
|梁柱|20根混凝土柱、6根混凝土梁，尺寸位置及楼层归属通过|
|楼梯|1楼梯总装、1真实梯段，20级×180mm、300mm踏深、1.8m宽；上端独立平台连接二层回廊|
|护栏|14段钢质细杆护栏，包含2段斜护栏；1.1m高度，实际杆件与基线通过|
|门窗|44双竖面板窗、6左/右单开木门；50开口和宿主/填充关系通过|
|材质|物理材料仅混凝土、木材、钢材；未根据颜色猜测性能|
|配色|主体#E6E0D3，梁柱#D2C7B3，框/栏杆#304B4D，门扇#A66F43；玻璃透明度0.65|
|Type/属性|没有模型额外建立的Type；仅6个编译器最小合法门Style附件。无普通/性能Pset，只有身份、构造与外观元数据|

## 验证与视觉检查

正式结果 [执行记录](live-run/execution.json) 为compiled，Audit accepted，repair route为no_repair_needed。原始提示、响应、候选、运行SQLite和每个门禁均保留于live-run。最终IFC的独立检查 [independent-final-v3.json](independent-final-v3.json) 共545项通过，111个实际构件成功网格化，0个网格化失败。

评价修订公开保留：原 [严格浮点检查](independent-final-strict.json) 有111项颜色比较失败（61整件、50部件），其几何、材料和其他检查不失败。原因是HEX为8位RGB，而模型用三位小数表达0–1通道；例如0.902/0.878/0.827回读为230/224/211，即#E6E0D3。补充评价器按请求精度逐通道回读HEX，仍拒绝相邻不同色值、缺失、多义及非法样式，透明度仍按原精度检查；18项评价器测试通过。旧被拒候选使用同一评价器重算后仍有1项楼梯颜色失败，见 [对照重算](../property-debug/rejected-candidate-rescored-v3.json)。不删除原失败、不以新评价器修改IFC，不将这次已观察案例当作盲测。

Agent已查看正式IFC整体、正面、隐藏屋盖图及梯段/门/窗/护栏近景：南侧保持敞开，回廊和细杆护栏清楚可见，楼梯有真实踏步，两层窗格与梁柱节奏一致，米白和深青灰配色协调。整体/正面图未隐藏构件；隐藏屋盖图和隔离近景均明确标注。图片是实际模型技术预览，不等同于已达到顶刊配图要求或工程验收。

## 真实用量与失败保留

|本次成功loop阶段|输入token|输出token（含reasoning）|总token|
|---|---:|---:|---:|
|Brief|26,041|49,984|76,025|
|Generator|59,377|59,334|118,711|
|Audit|110,763|12,034|122,797|
|合计|196,181|121,352|317,533|

本loop Provider活动时间400.359秒。含先前全部成功、失败及预留结算的累计账本为17次、1,591,587 token、2723.014活动秒，仍在32次/200万token/3600秒上限内。输入缓存命中等原始字段保留于metrics；未把缓存命中当成输入token减少。

|第二版尝试|真实调用|结果|
|---|---|---|
|初次f6ff16398bbd1f6e|Brief，78,490token|开敞布局误用完整墙环，未进入Generator|
|rerun-01 d2c21f51c9bb69f6|Brief/Generator/Repair，369,606token|非法空间Pset与修复越界；未发布IFC，未Audit|
|rerun-02 53fe782c609b1d1b|Brief，75,958token|矩形边界对象与轮廓数组格式差异，未进入Generator|
|rerun-03 ce8116ce095acdcf|Brief/Generator/Audit，317,533token|完整成功；待人工验收|

通用修复与所有离线失败记录见 [诊断报告](../property-debug/REPORT.md)、[墙布局诊断](../brief-envelope-debug/REPORT.md)。主要局部复验245项、139项、新运行包装器1项通过，集合不相加为能力成功率。未运行仓库Full Preflight、独立真实Repair、跨场景盲测或新token实验。等价矩形转换本次没有触发，因此没有声称本次实际省下一个调用。

## Audit勘误与剩余边界

原 [Audit](live-run/runs/ce8116ce095acdcf/audit/audit-report.json) 对三项设计关注均保留not_verified，机器accept不等于工程批准。其limitations第2条误写“材料强度等级均由用户给定”，与原请求及同份Audit后文矛盾：本例**没有指定、没有建立强度等级**；本报告按实际请求和重开IFC勘误，原响应不改写。平台/梯段连接节点、栏杆锚固、防水排水、结构计算及完整规范审查仍未完成；模型不作为直接施工文件。

本轮提升的是已定位的通用边界与局部回归覆盖，没有宣称系统级可靠性提升。跨轮约束来源的语义支持、局部替代和有效状态管理仍是下一小步，不以source_turns存在性检查代替意义核验。

人工检查建议先打开整体IFC，确认空间感与配色，再看正面敞口、右侧外露楼梯和二层回廊。通过后才另行办理Proof收纳与人工状态变更。
