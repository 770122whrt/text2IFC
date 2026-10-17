# formal-015：恢复一根梁的规格标记

**用户总体认可后的技术复核已通过；尚未冻结或请求模型。不宣称逐题usBIM验收。**

[完整原件 G](private/reference.ifc) · [损坏 IFC D](public/model.ifc) · [请求](public/request.txt) · [三维对照](VIEW.html)

Name 只在本页和私有材料用于人工查找，不写入公开请求。位置和尺寸由开发侧重算；请主要检查显示、损伤和请求含义。

## 损伤的原件

|原件 Name|损伤|原值 → 损坏值|
|---|---|---|
|Glulam-Western Species:240 X 300 mm:468058|仅改实例 Pset_BeamCommon.Reference，保留构件|240 X 300 mm → 规格待核对|

**本题没有删除几何构件。G、D 画面应相同；请在 IFC 属性面板检查损伤值。**

## 公开请求

以下位置按模型世界坐标描述，单位为米。标高 4 米的楼层，平面中心约在（X=-5.100866、Y=7.850659 米）、实体竖向范围为 Z=3.48 至 3.78 米的这根梁的规格标记被误改了，请恢复成“240 X 300 mm”，保留这段文字的空格和字符。只修正这一构件的属性，保留全部构件及其几何、位置、尺寸和其他属性。

## 技术核验与现有 Pipeline

目标世界平面中心（-5.100866，7.850659）米，竖向范围 3.48～3.78 米。
G 和 D schema＋EXPRESS 均 0 诊断；已逐个比较 310 个保留对象的实际网格、面和位置，均不变。
原值确为 IfcIdentifier(240 X 300 mm)，只改目标实例；保留同 Type 对象和其他属性。
当前产品实例属性操作已在该 D 上完成离线绑定写回、重开、精确类型和值及几何保全检查；没有调用模型。
完整自然语言属性检索、四组执行与新题评分准入仍待完成；不能把上述绑定探针记为模型成功。
[详细制题检查](private/checks.json) · [数值和保全](private/geometry-review.json) · [来源许可](private/SOURCE-LICENSE.md)

委托技术复核已通过；完成新阶段准入与冻结后才实验。private、REVIEW、VIEW 仅供审阅和评价，公开输入只含两个 public 文件。

## 本次属性覆盖修订

原承重值确实存在且为IfcBoolean(true)，没有缺失或补造。本次为减少重复，改测原件已有的Pset_BeamCommon.Reference，原值为IfcIdentifier('240 X 300 mm')；公开请求明确给出恢复值，不需澄清。

[当前属性绑定检查](private/offline-support/property-review/README.md)。旧承重记录保留作历史。
