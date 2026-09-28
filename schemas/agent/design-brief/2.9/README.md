# Design Brief 2.9：参数化门窗部件

此版本对应 BIM JSON 2.6、Draft 1.6、作者合同 1.6。旧版本文件保持不变。

门窗在 `known_facts.doors/windows` 中保留实例编号、类别、楼层、名义尺寸和构件放置。完整部件说明放入同一实例的 `semantic_requirements[].component_geometry`；几何语法与 BIM JSON 2.6 一致。`semantic_review.component_geometry` 是必填检查项。

- 部件是同一扇门窗内的几何，不是额外产品。不得递归把部件颜色识别成另一个 IFC 对象。
- 部件自身的 RGB／透明度保存在部件内部；整体物理材料仍使用已有材料字段，不推断材料属于哪个部件。
- `installation=standalone` 仅用于明确不建立宿主和洞口的独立门窗；需要实例编号和可确定楼层。其他门窗保留既有宿主／开口要求。独立构件不能与明确宿主同时声明。
- 缺少截面、深度、位置等参数时返回澄清。BRep、任意曲线和未支持操作不能被模板或包围盒替代。
- IFC2Text 1.0 的公开说明已列出的部件不能在 ready Brief 中遗漏；说明明确标记不支持时必须继续讨论。这个检查不替代重建后与源 IFC 的数值比较。
- 后续语义校正不能删除或修改初始 Brief 已保留的部件要求。

公开 API 显式选择 `text2ifc/design-brief/2.9`；CLI 使用 `--design-brief-schema-version 2.9`。此时完整生成自动使用 BIM JSON 2.6。当前部件路径采用 `legacy_full`，尚未启用 staged 生成。
