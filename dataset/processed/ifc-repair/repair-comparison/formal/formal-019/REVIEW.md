# formal-019：补回一根梁和一根柱，并恢复承重属性

**待用户审阅（pending_human_review），尚未接受、冻结或实验。**

本次草案重新制作，未继承旧题的委托接受记录。你可以核对查看器中的构件和损伤是否清楚、请求是否合理；尺寸、坐标、单位、楼层和保全已由开发侧检查，不要求你手工量测。

- [完整原件 G](private/reference.ifc) · [完整损坏 D](public/model.ifc) · [公开请求](public/request.txt)
- [可旋转的实际网格对照](VIEW.html) · [IFC 格式检查](IFC-VALIDATION.md) · [来源与许可](private/SOURCE-LICENSE.md)

G 是事先选择的登记源副本，只供制题、审阅及后续评估；被测系统只接收 public/model.ifc 和 public/request.txt。未声称已在 usBIM 或 buildingSMART 在线验证器检查。

## 哪些原件被损伤

下表是原 IFC 的真实 Name，仅用于审阅查找。名称中的数字不代替几何尺寸；原件身份不写入公开请求。

|原件 Name|类别|本次损伤|
|---|---|---|
|Concrete-Rectangular Beam:16 x 32:480440|IfcBeam|仅移除这一 occurrence 及必要随附关系／独占数据，保留原型与其他构件|
|Concrete-Rectangular-Column:24X24:320343|IfcColumn|仅移除这一 occurrence 及必要随附关系／独占数据，保留原型与其他构件|

保留参照（用于显示损伤位置与检查保全，不额外增加公开请求的修复约束）：

|原件 Name|类别|
|---|---|
|Concrete-Rectangular Beam:16 x 32:480448|IfcBeam|
|Concrete-Rectangular-Column:24X24:320502|IfcColumn|

**梁位置按实际 Body 端面中心核验。** 原 IFC 的 Axis 位于梁上沿；若把它直接当新梁的中心轴，会产生半个梁高的位移。公开请求使用实际梁体中心，不使用该参考线。

梁属于标高4.7米楼层，其梁体中心标高4.2936米；柱属于标高-1米底层，贯通至14.1米。两者楼层归属分别核验，不共用一个楼层。

## 公开请求

模型里少了一根水平梁和一根竖直柱，请分别补回。

梁属于楼层标高4.7米的那层，两个端面中心为（-9.449，5.09，4.2936）米和（-12.249，5.09，4.2936）米，截面宽300毫米、竖向高812.8毫米。

柱的平面中心为（X=-12.549，Y=5.24）米，柱底中心标高-1米，柱顶中心标高14.1米，截面600×600毫米，截面的边平行于模型X、Y方向，归属于柱底所在的-1米楼层。

请把这根梁和这根柱的承重标记也补齐。

以上位置使用模型全局坐标，坐标和标高的单位是米。请保留其余构件及其位置、几何和现有属性。

## 开发侧数值核验

从完整楼层 placement、IFC 长度单位和实际 Body 网格独立核验。公开 XY 保留三位小数、Z最多四位；坐标舍入误差最多1毫米的制题检查界限不等于正式评分容差。

|目标 Name|实际两个中心坐标（m）|请求截面（mm）|最大坐标舍入差（mm）|
|---|---|---|---:|
|Concrete-Rectangular Beam:16 x 32:480440|(-9.449219, 5.090441, 4.2936) → (-12.249219, 5.090441, 4.2936)|300×812.8|0.4922|
|Concrete-Rectangular-Column:24X24:320343|(-12.549219, 5.240441, -1) → (-12.549219, 5.240441, 14.1)|600×600|0.4922|

[完整坐标、单位、楼层、方向和原件网格核验](private/geometry-review.json)。

## 损伤和保全检查

G/D均重开并通过 schema＋EXPRESS；G 0诊断，D 0诊断。
只移除2个目标构件；没有新增构件。原 Type、楼层及所有保留产品未被误改。
实际网格数 G/D：325/323；目标在G可生成网格、在D不存在；其余323个网格与 placement保持一致。
查看器默认只显示目标与参照，避免墙体遮挡；取消相应勾选可显示内置的完整模型。红色是G中的被删除构件，蓝色是保留参照。
[完整损伤、关系与保全核验](private/checks.json) · [实际网格比较](private/visual-inspection.json)。

## 修复验收含义

后续需按公开请求恢复真实构件的几何、各自唯一楼层归属和合适Type，保留其他构件。允许新身份、等价序列化和几何等价的180度矩形截面方向；不要求复用原GUID或名称。
正式评分合同和预算尚未冻结；旧全局计划不能直接套用本草案。

## 澄清与审阅状态

本题保留必要澄清：初始请求要求补齐梁、柱承重标记，但不提供布尔值，也不称它们为承重构件。预写答复分别为梁=true、柱=true；只问其中一项时只回复该项。
按实际问题逐事实答复，不整卡注入，不替模型提出问题，不在运行时临时查询私有G；卡外问题交人工处理。
完整事实bound探针只证明答复事实明确后的执行可行性；未证明初始请求能自然触发澄清或顺利恢复。
[预写答复卡](private/answer-card.json)。
用户审阅记录仍为pending_human_review，human_viewed=false，未把自动技术检查写成用户已亲自看过。

## 原承重属性与链路状态

本题的梁、柱在源G中都已有原生实例承重属性；没有先给G制造属性再删除。

|对象|原属性|原类型和值|
|---|---|---|
|Concrete-Rectangular Beam:16 x 32:480440|Pset_BeamCommon.LoadBearing|IfcBoolean(true)|
|Concrete-Rectangular-Column:24X24:320343|Pset_ColumnCommon.LoadBearing|IfcBoolean(true)|

`add_beam`／`add_column`支持相应occurrence property意图和标准语义写回接口。新增的完整答后bound检查已验证两个补建操作及各自`IfcBoolean(true)`写回、重开、楼层、原件保全和第二操作失败时整题回滚；旧几何探针没有验证属性，不替换旧记录。
B通用属性Runtime已有真实Linux＋假Provider的7条基本路径及1条共享属性路径验收；本题的自然语言模型定位、四组载体与扩展评分尚未验收。此检查使用预写答案和明确的标准属性意图，未运行模型提问、自然属性检索或原会话恢复。
[自包含答后检查](private/offline-support/beam-column-after-answers/README.md) · [结果](private/offline-support/beam-column-after-answers/result.json)。
[原值、类型、来源及操作接口](private/property-requirements.json)。

[离线链路核对](PIPELINE-CHECK.md) · [公开请求实际数值检查](private/request-numeric-review.json) · [查看器静态检查及视觉限制](private/viewer-check.json)。

本题有多个被删除对象，请在 VIEW 的“定位对象”中逐个选择查看；初始视角聚焦第一处，不表示其他目标没有几何。
