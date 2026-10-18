# case-001：在两扇现存窗正中补回同型固定窗

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

- 源：`dataset/external/_checks/ifc-assets-20260913-v4/repairs/bim-whale-ifc-samples-largebuilding-102f8123f85e/repaired.ifc`
- SHA-256：`5a0c3abcd22689dd6a4537339aadce4af17678cbc9d6f5cf26742156e0f25262`
- 许可：MIT；保留版权和许可声明；登记用途：research-evaluation。
- 场景族：`LargeBuilding`；开发中已使用，正式未见样本应排除同族和变体。
- 参考角色：事前选择的损坏前参考；采用已登记、通过既有检查的历史修复副本，不是下载原件。本题语义与参考角色仍待人审。

- [来源／许可材料 1](private/attribution/01-source-notices.md)
- [来源／许可材料 2](private/attribution/02-LICENSE)

损伤规模：S1，主目标 1 个，组合 single。洞口等附属结构不重复计作主目标；规模不等同于实际难度。

[损坏 IFC 的格式校验结果](IFC-VALIDATION.md)

## 公开请求与可解性

```text
一层最西边那栋楼的西侧长外墙上，从北往南数第二扇和第三扇现有窗之间缺了一扇窗。请在这两扇窗中心连线的中点补一扇固定窗：宽915毫米、高1830毫米，窗台距这一层地面305毫米。窗框截面、框内分格、玻璃和表面外观以刚才数到的第二扇窗为准；沿墙安装，朝向与它一致，并在墙上开出对应的窗洞。其余窗和墙的其他部分保持原样。
```

- 2026-09-29 用户要求改为自然语言和方位定位；公开请求不使用 GUID、构件 Name、类型名或方法提示。
- 仅用 D 核对：IFC TrueNorth 约为(0,1)，最西侧长外墙的一层现存窗由北向南排序，第二、第三扇正是两扇保留参照；其中心Y约3.2942与0.2642m。
- 中点、915×1830mm、窗台305mm及明确指定的第二扇窗样式均由 D 中公开参照确定；不要求恢复原 Tag、GUID 或隐藏属性。关系术语不写入请求，开洞、安装和楼层语义由任务表达。

## 实际损坏与检查

| 对象类别 | 损坏前 | 损坏后 |
|---|---:|---:|
| IfcOpeningElement | 60 | 59 |
| IfcWindow | 42 | 41 |

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

主目标分母：1；应修关系分母：3。

- 新增一扇 IfcWindow，具备可生成的窗框和玻璃几何，宽915 mm、高1830 mm、窗台305 mm，方向与两侧一致。
- 新窗中心位于同墙两侧公开参照窗中心的中点；拟定中心墙局部X=12227.5 mm，数值用于私有核对，公开依赖两侧参照。
- 建立一处相应洞口；墙的开洞区域与窗匹配，host/void/fill与楼层关系满足上列三条边。
- 框/玻璃部件、表面外观和摆放与参照一致；不把原始序列化、隐藏Tag或未请求的性能属性加入义务。

| 应修关系 | 依据 |
|---|---|
| IfcRelVoidsElement / host_void | 新洞口必须切开请求指定的存活墙；G–D 中对应一条 void 关系消失。 |
| IfcRelFillsElement / opening_fill | 新窗填充新洞口；G–D 中对应一条 fill 关系消失。 |
| IfcRelContainedInSpatialStructure / storey_containment | 新窗属于 Level 1；按窗到楼层的一条成员边计数，不把关系实体数量当分母。 |

公开请求只表达安装、开洞及楼层位置，不给 IFC 关系术语或修复方法。评分仍检查这些任务必需的语义；能否由模型自然补全，留待获准后的真实实验验证。类型关联不作为强制分母，允许实例表达等价语义。

## 视觉检查与具体删除对象

[打开同步视角网格查看器](VIEW.html)：红色为 G 中删除的对象，蓝色为保留参照；两侧共用世界坐标和视角。仅供人工审阅，不能送入被测系统。

删除对象：`IfcWindow`，Tag=`354004`，Name=`M_Fixed:0915 x 1830mm:354004`。
删除前世界包围盒（米，依次X/Y/Z）：`[[-14.7827, -14.5827], [1.3217, 2.2367], [0.305, 2.135]]`。下表坐标仅为阅读四舍五入，原始精度见JSON。

| 保留对象 Tag / GUID | 世界包围盒（米） | G/D 放置、顶点、面索引 |
|---|---|---|
| 353953 | `[[-14.7827, -14.5827], [2.8367, 3.7517], [0.305, 2.135]]` | 完全一致 |
| 354078 | `[[-14.7827, -14.5827], [-0.1933, 0.7217], [0.305, 2.135]]` | 完全一致 |

网格数量 G/D：174/172；生成失败：0/0。
[具体网格核对和诊断](private/visual-inspection.json)。查看器使用三角网格，但不渲染原材质，也不代替原生 IFC 校验。

允许替代：

- 新增窗、洞口及必要关系可以采用新 GlobalId、不同STEP编号。
- 允许几何等价的表示；可以复用或新建固定窗类型，也可在实例表达所需语义。IfcRelDefinesByType不设为必修边，不要求复制原实体树。

保全要求：

- 除目标窗与必要洞口、关系外，不新增或删除其他构件。
- 允许目标墙因重新开洞发生相应体积变化；墙轴线、厚度、高度、材料和其他洞口不变。
- 两个参照窗及其他现存对象保持身份、几何、属性与关系。

匹配：按 D 中最西侧长外墙及自北向南第二、第三扇现存窗的中点匹配唯一新增窗；粗区域前后各0.5 m，尺寸和关系另行评分，不以它们挑选最有利对象。
数值规则草案：`{'status': 'pending_human_review', 'length_mm': 1.0, 'angle_degrees': 0.1, 'note': '开发审阅草案；需要评分器自检支持后再冻结，不继承IFC2Text旧阈值。'}`；尚未正式冻结。

## 澄清与答复卡

本题拟为信息充分题；公开参照已足以确定目标。仍允许普通提问，不预设必须提问。

只回答实际问到的事实；卡外问题留待人工处理，不查 G 临时补答案。未问碰巧做对与合格澄清分别计分。

## 请你审阅

1. 损坏是否符合题意，有没有误伤其他部分？
2. 公开请求是否自然且充分；澄清题是否确有必要的用户选择？
3. 主目标、应修关系、允许替代和保全条件是否合理？
4. 答复卡草案及拟定容差是否接受，还是需要修改？

请按本题编号给出接受／修改意见。程序不会自动写 accepted；任何题意、输入或答复事实变更均需重新审阅。
