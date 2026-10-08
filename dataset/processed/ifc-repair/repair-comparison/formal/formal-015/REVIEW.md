# formal-015：恢复一根梁的承重属性

**待你查看和审题：pending_human_review。尚未接受、冻结或请求模型。**

[完整原件 G](private/reference.ifc) · [损坏 IFC D](public/model.ifc) · [请求](public/request.txt) · [三维对照](VIEW.html)

Name 只在本页和私有材料用于人工查找，不写入公开请求。位置和尺寸由开发侧重算；请主要检查显示、损伤和请求含义。

## 损伤的原件

|原件 Name|损伤|原值 → 损坏值|
|---|---|---|
|Glulam-Western Species:240 X 300 mm:468058|仅改实例 Pset_BeamCommon.LoadBearing，保留构件|True → False|

**本题没有删除几何构件。G、D 画面应相同；请在 IFC 属性面板检查损伤值。**

## 公开请求

以下位置按模型世界坐标描述，单位为米。标高 4 米的楼层，平面中心约在（X=-5.100866、Y=7.850659 米）、实体竖向范围为 Z=3.48 至 3.78 米的这根梁的承重标记被误改了，请恢复为承重构件。只修正这一构件的属性，保留全部构件及其几何、位置、尺寸和其他属性。

## 技术核验与现有 Pipeline

目标世界平面中心（-5.100866，7.850659）米，竖向范围 3.48～3.78 米。
G 和 D schema＋EXPRESS 均 0 诊断；已逐个比较 310 个保留对象的实际网格、面和位置，均不变。
原值确为 IfcBoolean(True)，只改目标实例；保留同 Type 对象和其他属性。
当前产品实例属性操作已在该 D 上完成离线绑定写回、重开、精确类型和值及几何保全检查；没有调用模型。
完整自然语言属性检索、四组执行与新题评分准入仍待完成；不能把上述绑定探针记为模型成功。
[详细制题检查](private/checks.json) · [数值和保全](private/geometry-review.json) · [来源许可](private/SOURCE-LICENSE.md)

你确认后再冻结并实验；private、REVIEW、VIEW 仅供审阅和评价，公开输入只含两个 public 文件。
