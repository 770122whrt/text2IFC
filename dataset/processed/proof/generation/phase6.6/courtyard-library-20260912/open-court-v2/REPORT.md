# 第二版：人工已验收的敞开光庭

2026-09-12人工验收完成。真实全新Brief → Generator → Audit → IFC，run `ce8116ce095acdcf`，api.deepseek.com / deepseek-v4-flash，legacy_full；没有复用旧候选或调用Provider修复。

- [中文输入](request.txt) · [批准对话](conversation.json) · [完整候选](model.json)
- [最终IFC](generated.ifc) · [交互查看器](views/viewer.html)
- [整体图](views/overall.png) · [正面敞口](views/courtyard-front.png) · [屋盖隐藏视图](views/courtyard-roof-hidden.png) · [楼梯](views/stair-detail.png)
- [窗](views/IfcWindow.png) · [门](views/IfcDoor.png) · [护栏](views/IfcRailing.png)
- [独立IFC检查](independent-ifc-check.json) · [原始用量与待审快照](usage-summary.json) · [当前人工验收](../human-acceptance.json)

两层24×18m，二层3.6m，南向敞开的U形光庭与回廊。20柱6梁、14细杆护栏（含2段斜护栏）、44双竖面板窗、6单开门；外露楼梯20级、每级180mm。米白主体、砂色梁柱、深青灰框与栏杆、木色门扇均来自实际IFC。物理材料为混凝土、木材、钢材；未指定的强度、耐火、热工性能未创建。

最终IFC SHA256：`650accdb5131b1ae3fdc26e5af000029deb4860fe6f38571dcad174d8ff9b39d`，1,161,796字节。图片来自该正式IFC，111个实体网格成功，0失败。屋盖隐藏及部件隔离只影响查看方式。

机器终端通过，独立545/545通过；成功loop3次、317,533 token。使用HEX8请求精度的评价修订及原失败完整保留。人工验收确认模型和表现可作为Proof，不认证锚固、排水、结构计算或完整建筑规范。

完整历史报告和机器权威见 [evidence](evidence/README.md)。原usage-summary保留`pending_human_review`与`proof_registered=false`，那是交付时快照；当前状态以集合manifest及新增人工验收记录为准。
