# formal-013：补回一根方柱

**待用户审阅（pending_human_review），尚未接受、冻结或实验。**

本次草案重新制作，未继承旧题的委托接受记录。你可以核对查看器中的构件和损伤是否清楚、请求是否合理；尺寸、坐标、单位、楼层和保全已由开发侧检查，不要求你手工量测。

- [完整原件 G](private/reference.ifc) · [完整损坏 D](public/model.ifc) · [公开请求](public/request.txt)
- [可旋转的实际网格对照](VIEW.html) · [IFC 格式检查](IFC-VALIDATION.md) · [来源与许可](private/SOURCE-LICENSE.md)

G 是事先选择的登记源副本，只供制题、审阅及后续评估；被测系统只接收 public/model.ifc 和 public/request.txt。未声称已在 usBIM 或 buildingSMART 在线验证器检查。

## 哪些原件被损伤

下表是原 IFC 的真实 Name，仅用于审阅查找。名称中的数字不代替几何尺寸；原件身份不写入公开请求。

|原件 Name|类别|本次损伤|
|---|---|---|
|Concrete-Rectangular-Column:350 x 350mm:438683|IfcColumn|仅移除这一 occurrence 及必要随附关系／独占数据，保留原型与其他构件|

保留参照（用于显示损伤位置与检查保全，不额外增加公开请求的修复约束）：

|原件 Name|类别|
|---|---|
|Concrete-Rectangular-Column:350 x 350mm:439427|IfcColumn|

## 公开请求

地面标高0米的这一层，在平面中心（X=-10.199，Y=4.73）米处少了一根柱。请补回350×350毫米的竖直方柱，柱底中心标高0米，柱顶中心标高2.5米，截面的边平行于模型X、Y方向。

以上位置使用模型全局坐标，坐标和标高的单位是米。请保留其余构件及其位置、几何和现有属性。

## 开发侧数值核验

从完整楼层 placement、IFC 长度单位和实际 Body 网格独立核验。公开 XY 保留三位小数、Z最多四位；坐标舍入误差最多1毫米的制题检查界限不等于正式评分容差。

|目标 Name|实际两个中心坐标（m）|请求截面（mm）|最大坐标舍入差（mm）|
|---|---|---|---:|
|Concrete-Rectangular-Column:350 x 350mm:438683|(-10.198885, 4.729831, 0) → (-10.198885, 4.729831, 2.5)|350×350|0.2041|

[完整坐标、单位、楼层、方向和原件网格核验](private/geometry-review.json)。

## 损伤和保全检查

G/D均重开并通过 schema＋EXPRESS；G 0诊断，D 0诊断。
只移除1个目标构件；没有新增构件。原 Type、楼层及所有保留产品未被误改。
实际网格数 G/D：85/84；目标在G可生成网格、在D不存在；其余84个网格与 placement保持一致。
查看器默认只显示目标与参照，避免墙体遮挡；取消相应勾选可显示内置的完整模型。红色是G中的被删除构件，蓝色是保留参照。
[完整损伤、关系与保全核验](private/checks.json) · [实际网格比较](private/visual-inspection.json)。

## 修复验收含义

后续需按公开请求恢复真实构件的几何、各自唯一楼层归属和合适Type，保留其他构件。允许新身份、等价序列化和几何等价的180度矩形截面方向；不要求复用原GUID或名称。
正式评分合同和预算尚未冻结；旧全局计划不能直接套用本草案。

## 澄清与审阅状态

本题已给出必需定位、尺寸及方向，没有故意缺失的必答事实；模型若确有疑问仍可提问。第一轮答复只重申已公开事实，不从私有G临时补身份或未知条件。
用户审阅记录仍为pending_human_review，human_viewed=false，未把自动技术检查写成用户已亲自看过。

[离线链路核对](PIPELINE-CHECK.md) · [公开请求实际数值检查](private/request-numeric-review.json) · [查看器静态检查及视觉限制](private/viewer-check.json)。
