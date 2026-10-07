# Repair 二十题

20 个不同的 IFC 源文件，共 38 个待补门窗。许可分布：CC-BY-4.0 9份、GPL-3.0-or-later 2份、MIT 9份；损伤规模：S1 7题、S2 8题、S3 5题。

20题损坏输入均通过本地 IfcOpenShell schema＋EXPRESS。尺寸、坐标、参照、保全及澄清可解性仍以各题实际技术审题记录为准；本页是题包入口，模型成绩与运行状态见独立实验结果。

用户已委托本批技术审题，记录为 accepted_by_delegation、Codex、human_viewed=false，不表示用户逐题在 usBIM 查看。

|题号|损伤规模|许可|目标数|必要澄清|材料|
|---|---|---|---:|---|---|
|formal-001|S1|CC-BY-4.0|1|公开信息充分|[审题](formal-001/REVIEW.md) · [请求](formal-001/public/request.txt) · [损坏 IFC](formal-001/public/model.ifc)|
|formal-002|S2|CC-BY-4.0|2|公开信息充分|[审题](formal-002/REVIEW.md) · [请求](formal-002/public/request.txt) · [损坏 IFC](formal-002/public/model.ifc)|
|formal-003|S2|CC-BY-4.0|2|公开信息充分|[审题](formal-003/REVIEW.md) · [请求](formal-003/public/request.txt) · [损坏 IFC](formal-003/public/model.ifc)|
|formal-004|S1|MIT|1|公开信息充分|[审题](formal-004/REVIEW.md) · [请求](formal-004/public/request.txt) · [损坏 IFC](formal-004/public/model.ifc)|
|formal-005|S2|GPL-3.0-or-later|2|公开信息充分|[审题](formal-005/REVIEW.md) · [请求](formal-005/public/request.txt) · [损坏 IFC](formal-005/public/model.ifc)|
|formal-006|S1|MIT|1|公开信息充分|[审题](formal-006/REVIEW.md) · [请求](formal-006/public/request.txt) · [损坏 IFC](formal-006/public/model.ifc)|
|formal-007|S1|GPL-3.0-or-later|1|公开信息充分|[审题](formal-007/REVIEW.md) · [请求](formal-007/public/request.txt) · [损坏 IFC](formal-007/public/model.ifc)|
|formal-008|S2|CC-BY-4.0|2|公开信息充分|[审题](formal-008/REVIEW.md) · [请求](formal-008/public/request.txt) · [损坏 IFC](formal-008/public/model.ifc)|
|formal-009|S3|CC-BY-4.0|3|公开信息充分|[审题](formal-009/REVIEW.md) · [请求](formal-009/public/request.txt) · [损坏 IFC](formal-009/public/model.ifc)|
|formal-010|S3|CC-BY-4.0|3|公开信息充分|[审题](formal-010/REVIEW.md) · [请求](formal-010/public/request.txt) · [损坏 IFC](formal-010/public/model.ifc)|
|formal-011|S2|CC-BY-4.0|2|公开信息充分|[审题](formal-011/REVIEW.md) · [请求](formal-011/public/request.txt) · [损坏 IFC](formal-011/public/model.ifc)|
|formal-012|S3|CC-BY-4.0|3|公开信息充分|[审题](formal-012/REVIEW.md) · [请求](formal-012/public/request.txt) · [损坏 IFC](formal-012/public/model.ifc)|
|formal-013|S1|CC-BY-4.0|1|第一扇窗洞底高度|[审题](formal-013/REVIEW.md) · [请求](formal-013/public/request.txt) · [损坏 IFC](formal-013/public/model.ifc)|
|formal-014|S1|MIT|1|公开信息充分|[审题](formal-014/REVIEW.md) · [请求](formal-014/public/request.txt) · [损坏 IFC](formal-014/public/model.ifc)|
|formal-015|S2|MIT|2|公开信息充分|[审题](formal-015/REVIEW.md) · [请求](formal-015/public/request.txt) · [损坏 IFC](formal-015/public/model.ifc)|
|formal-016|S2|MIT|2|第一扇窗洞底高度|[审题](formal-016/REVIEW.md) · [请求](formal-016/public/request.txt) · [损坏 IFC](formal-016/public/model.ifc)|
|formal-017|S3|MIT|3|公开信息充分|[审题](formal-017/REVIEW.md) · [请求](formal-017/public/request.txt) · [损坏 IFC](formal-017/public/model.ifc)|
|formal-018|S2|MIT|2|公开信息充分|[审题](formal-018/REVIEW.md) · [请求](formal-018/public/request.txt) · [损坏 IFC](formal-018/public/model.ifc)|
|formal-019|S1|MIT|1|公开信息充分|[审题](formal-019/REVIEW.md) · [请求](formal-019/public/request.txt) · [损坏 IFC](formal-019/public/model.ifc)|
|formal-020|S3|MIT|3|第一扇窗洞底高度|[审题](formal-020/REVIEW.md) · [请求](formal-020/public/request.txt) · [损坏 IFC](formal-020/public/model.ifc)|

门损伤分为“删门保留空洞”和“删门及洞口、恢复墙面”；后者的修复要求重新开洞并补门。窗损伤删除窗及洞口。S1/S2/S3分别表示1/2/3个主目标，不以规模代替难度。

004 原 Jasmin 源及兼容性候选均因用户确认的显示问题而弃用，当前使用 MIT 许可的 TallBuilding。旧拒收事实见原题 [记录](formal-004/private/rejected-source.json)。新源已验证实际网格与格式，没有直接验证当前 usBIM 的显示。

公开包仅含 model.ifc、request.txt。损坏前 G、损伤映射、真实 Name、答复卡和全部评价条件只保留在 private/ 与审题材料中。A/B/C/D 获得同题同一份公开输入，各自的工作副本、会话和产物独立。

多份 ResBIM IFC 使用同一生成器，Tafraout、GNI 等也共享来源族；不同文件不等于20个统计独立建筑。源、权利记录和原有格式修复谱系逐题保留，不把历史修复副本称为未经修改的下载原件。

REVIEW.png 使用真实世界坐标网格作同尺度剖切；VIEW.html 可旋转查看完整对照。参照位于另一标高时，剖切图明确说明，应在三维查看器中看该层；这些图不代替原生 IFC 校验。
