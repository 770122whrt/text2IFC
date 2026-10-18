# case-002：给二层唯一的空室内门洞补门

> 状态：pending_human_review。开发样例，不计入正式成绩；没有运行修复模型，也没有 repaired.ifc。

## 先看这几个文件

- [公开修复要求](public/request.txt)
- [损坏 IFC：给被测系统的副本](public/model.ifc)
- [损坏前参考 G](private/reference.ifc)
- [冻结损坏 D](private/mutation/damaged.ifc)
- [私有任务条件](private/task.json)／[受控答复卡](private/answer-card.json)
- [完整检查记录](private/checks.json)／[损坏记录](private/mutation/mutation_manifest.private.json)

上述整目录仅供审阅。后续只导出 public/；目录分层本身不证明运行时沙箱隔离。

## 来源、许可与样本身份

- 源：`dataset/external/buildingsmart-community/Duplex Apartment/Duplex_A_20110907.ifc`
- SHA-256：`b347a2c8aa8fff6db896a4417a9c50c22ac0ccd7c5cfc22b99b8d29336c606ed`
- 许可：CC BY 4.0；保留来源署名、许可链接和修改说明；登记用途：research-evaluation。
- 场景族：`Duplex Apartment`；开发中已使用，正式未见样本应排除同族和变体。
- 参考角色：原始登记字节作为事前选择的损坏前参考。原门开向不是必须恢复的隐藏答案，当前请求允许合理的左右开启方式。

- [来源／许可材料 1](private/attribution/01-source-notices.md)

损伤规模：S1，主目标 1 个，组合 single。洞口等附属结构不重复计作主目标；规模不等同于实际难度。

[损坏 IFC 的格式校验结果](IFC-VALIDATION.md)

## 公开请求与可解性

```text
请给二层那个空着的室内门洞补一扇单扇门。门洞的平面中心约在模型全局坐标X=1.915米、Y=-6.188米处，底部标高Z=3.100米。门的名义宽度为864毫米、高度为2032毫米；门框截面、门扇造型和表面外观，以同层平面中心约在X=6.889米、Y=-11.612米处的那扇现有门为准。把门安装在空洞内，左右开启均可。保留现有门洞的位置和大小，墙及其他门保持原样。
```

- 2026-09-29 用户认为仅为开向偏好而强设澄清不合适；当前题改为信息充分的简单补门任务。
- 仅用 D 核对：二层墙体上、门高范围的未填充洞口只有一处，底标高3.1m；不依赖隐藏身份即可定位。Duplex 没有声明 TrueNorth，不凭空写东南西北。
- D 的洞口及指定同层参照可确定864×2032mm尺寸；公开坐标取保留洞口与参照门的世界几何包围盒平面中心，保留三位小数用于定位；不是1mm定位验收值。左右开启均可，不将原 G 的开向变成用户义务。

## 实际损坏与检查

| 对象类别 | 损坏前 | 损坏后 |
|---|---:|---:|
| IfcDoor | 14 | 13 |

- damaged_native_validation_passed: `True`
- no_new_native_diagnostics: `True`
- no_products_created: `True`
- no_unexpected_modified_products: `True`
- only_expected_products_removed: `True`
- required_geometry_available: `True`
- required_relation_edges_verified: `True`
- retained_opening_empty_and_hosted: `True`
- schema_preserved: `True`
- source_native_validation_passed: `True`
- source_unchanged: `True`
- 原生 schema＋EXPRESS 诊断：G=0，D=0，新增=0。这是制题检查，不是修复成绩。

[实际 IFC 几何包围盒俯视定位图](private/location.svg)仅用于定位；完整形状、开向和外观请打开 IFC 查看。

## 怎样才算完成：待你确认

主目标分母：1；应修关系分母：2。

- 在二层唯一空室内门洞处新增一扇 IfcDoor，OverallWidth=864mm、OverallHeight=2032mm，正确填充保留洞口。外框包围尺寸不与Overall尺寸混淆。
- 门框和门扇几何可生成，样式与公开坐标指定的现存参照门一致。左右开启均允许；不以与G原开向不同判错，也不要求为此提问。
- fill、Level 2 containment两条应修边正确；保留洞口的void关系和几何不变。

| 应修关系 | 依据 |
|---|---|
| IfcRelFillsElement / opening_fill | 新增门填充保留洞口；原 fill 被删除。保留的墙–洞口 void 已正确，不计入应修分母。 |
| IfcRelContainedInSpatialStructure / storey_containment | 新门加入 Level 2 的成员边；删除前G中的这条成员边在D缺失。 |

公开请求只表达安装、开洞及楼层位置，不给 IFC 关系术语或修复方法。评分仍检查这些任务必需的语义；能否由模型自然补全，留待获准后的真实实验验证。类型关联不作为强制分母，允许实例表达等价语义。

## 视觉检查与具体删除对象

[打开同步视角网格查看器](VIEW.html)：红色为 G 中删除的对象，蓝色为保留参照；两侧共用世界坐标和视角。仅供人工审阅，不能送入被测系统。

删除对象：`IfcDoor`，Tag=`150378`，Name=`M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378`。
删除前世界包围盒（米，依次X/Y/Z）：`[[1.4073, 2.4233], [-6.275, -6.101], [3.1, 5.208]]`。下表坐标仅为阅读四舍五入，原始精度见JSON。

| 保留对象 Tag / GUID | 世界包围盒（米） | G/D 放置、顶点、面索引 |
|---|---|---|
| 1xS3BCk291UvhgP2dvNozF | `[[1.4833, 2.3473], [-6.25, -6.126], [3.1, 5.132]]` | 完全一致 |
| 150478 | `[[6.3813, 7.3973], [-11.699, -11.525], [3.1, 5.208]]` | 完全一致 |
| 159734 | `[[1.342, 2.358], [-11.699, -11.525], [3.1, 5.208]]` | 完全一致 |

网格数量 G/D：265/264；生成失败：0/0。
[具体网格核对和诊断](private/visual-inspection.json)。查看器使用三角网格，但不渲染原材质，也不代替原生 IFC 校验。

允许替代：

- 新增门与关系允许新GlobalId及等价几何表示，不恢复已删除门的Tag或隐藏属性。
- 可以复用相容门类型、创建语义和外观等价的新类型，或在实例表达所需语义。IfcRelDefinesByType不设为必修边；当前任务不把开向列为必答事实。

保全要求：

- 不移动或缩放保留洞口，不改变墙的轴线、厚度、高度、材料或其他洞口。
- 两种现存参照门及其他对象保持身份、几何、属性与关系；不重复补门。

匹配：按 D 中二层唯一空室内门洞的位置匹配唯一新增 IfcDoor，粗匹配取洞口中心0.5m范围；fill关系和尺寸在匹配后独立检验。
数值规则草案：`{'status': 'pending_human_review', 'length_mm': 1.0, 'angle_degrees': 0.1, 'note': '开发审阅草案；Duplex项目单位是m，检查统一换算mm。'}`；尚未正式冻结。

## 澄清与答复卡

本题拟为信息充分题；公开参照已足以确定目标。仍允许普通提问，不预设必须提问。

只回答实际问到的事实；卡外问题留待人工处理，不查 G 临时补答案。未问碰巧做对与合格澄清分别计分。

## 请你审阅

1. 损坏是否符合题意，有没有误伤其他部分？
2. 公开请求是否自然且充分；澄清题是否确有必要的用户选择？
3. 主目标、应修关系、允许替代和保全条件是否合理？
4. 答复卡草案及拟定容差是否接受，还是需要修改？

请按本题编号给出接受／修改意见。程序不会自动写 accepted；任何题意、输入或答复事实变更均需重新审阅。
