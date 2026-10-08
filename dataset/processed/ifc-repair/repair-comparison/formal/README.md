# Repair 二十题：当前审题入口

共20个不同源IFC。前十题保持原题；011～020已重制为4道梁柱补建、4道实例属性修复、2道混合题，**新后十题待你审阅，尚未冻结或实验。**

许可：CC-BY-4.0 16份、GPL-3.0-or-later 2份、MIT 2份。多份GNI模型来自同一课程/来源族，不等于20个统计独立建筑。每题保留实际来源、许可和既有格式修复谱系。

新十题的G、D均通过IfcOpenShell0.8.5 schema＋EXPRESS，位置、尺寸、损伤和保全由开发侧核对。你主要检查usBIM显示和请求含义；尚未把自动检查写成你已亲自看过。

|题号|损伤对象|许可|必要澄清|审阅状态|材料|
|---|---|---|---|---|---|
|formal-001|门 1|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-001/REVIEW.md) · [原件G](formal-001/private/reference.ifc) · [损坏D](formal-001/public/model.ifc) · [请求](formal-001/public/request.txt) · [三维](formal-001/VIEW.html)|
|formal-002|窗 2|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-002/REVIEW.md) · [原件G](formal-002/private/reference.ifc) · [损坏D](formal-002/public/model.ifc) · [请求](formal-002/public/request.txt) · [三维](formal-002/VIEW.html)|
|formal-003|窗 1＋门 1|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-003/REVIEW.md) · [原件G](formal-003/private/reference.ifc) · [损坏D](formal-003/public/model.ifc) · [请求](formal-003/public/request.txt) · [三维](formal-003/VIEW.html)|
|formal-004|窗 1|MIT|公开信息充分|保留原记录|[REVIEW](formal-004/REVIEW.md) · [原件G](formal-004/private/reference.ifc) · [损坏D](formal-004/public/model.ifc) · [请求](formal-004/public/request.txt) · [三维](formal-004/VIEW.html)|
|formal-005|门 2|GPL-3.0-or-later|公开信息充分|保留原记录|[REVIEW](formal-005/REVIEW.md) · [原件G](formal-005/private/reference.ifc) · [损坏D](formal-005/public/model.ifc) · [请求](formal-005/public/request.txt) · [三维](formal-005/VIEW.html)|
|formal-006|窗 1|MIT|公开信息充分|保留原记录|[REVIEW](formal-006/REVIEW.md) · [原件G](formal-006/private/reference.ifc) · [损坏D](formal-006/public/model.ifc) · [请求](formal-006/public/request.txt) · [三维](formal-006/VIEW.html)|
|formal-007|窗 1|GPL-3.0-or-later|公开信息充分|保留原记录|[REVIEW](formal-007/REVIEW.md) · [原件G](formal-007/private/reference.ifc) · [损坏D](formal-007/public/model.ifc) · [请求](formal-007/public/request.txt) · [三维](formal-007/VIEW.html)|
|formal-008|门 2|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-008/REVIEW.md) · [原件G](formal-008/private/reference.ifc) · [损坏D](formal-008/public/model.ifc) · [请求](formal-008/public/request.txt) · [三维](formal-008/VIEW.html)|
|formal-009|门 3|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-009/REVIEW.md) · [原件G](formal-009/private/reference.ifc) · [损坏D](formal-009/public/model.ifc) · [请求](formal-009/public/request.txt) · [三维](formal-009/VIEW.html)|
|formal-010|窗 3|CC-BY-4.0|公开信息充分|保留原记录|[REVIEW](formal-010/REVIEW.md) · [原件G](formal-010/private/reference.ifc) · [损坏D](formal-010/public/model.ifc) · [请求](formal-010/public/request.txt) · [三维](formal-010/VIEW.html)|
|formal-011|梁 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-011/REVIEW.md) · [原件G](formal-011/private/reference.ifc) · [损坏D](formal-011/public/model.ifc) · [请求](formal-011/public/request.txt) · [三维](formal-011/VIEW.html)|
|formal-012|梁 2|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-012/REVIEW.md) · [原件G](formal-012/private/reference.ifc) · [损坏D](formal-012/public/model.ifc) · [请求](formal-012/public/request.txt) · [三维](formal-012/VIEW.html)|
|formal-013|柱 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-013/REVIEW.md) · [原件G](formal-013/private/reference.ifc) · [损坏D](formal-013/public/model.ifc) · [请求](formal-013/public/request.txt) · [三维](formal-013/VIEW.html)|
|formal-014|柱 1|CC-BY-4.0|柱截面的短边/长边朝向|待你审阅|[REVIEW](formal-014/REVIEW.md) · [原件G](formal-014/private/reference.ifc) · [损坏D](formal-014/public/model.ifc) · [请求](formal-014/public/request.txt) · [三维](formal-014/VIEW.html)|
|formal-015|实例属性 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-015/REVIEW.md) · [原件G](formal-015/private/reference.ifc) · [损坏D](formal-015/public/model.ifc) · [请求](formal-015/public/request.txt) · [三维](formal-015/VIEW.html)|
|formal-016|实例属性 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-016/REVIEW.md) · [原件G](formal-016/private/reference.ifc) · [损坏D](formal-016/public/model.ifc) · [请求](formal-016/public/request.txt) · [三维](formal-016/VIEW.html)|
|formal-017|实例属性 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-017/REVIEW.md) · [原件G](formal-017/private/reference.ifc) · [损坏D](formal-017/public/model.ifc) · [请求](formal-017/public/request.txt) · [三维](formal-017/VIEW.html)|
|formal-018|实例属性 1|CC-BY-4.0|公开信息充分|待你审阅|[REVIEW](formal-018/REVIEW.md) · [原件G](formal-018/private/reference.ifc) · [损坏D](formal-018/public/model.ifc) · [请求](formal-018/public/request.txt) · [三维](formal-018/VIEW.html)|
|formal-019|梁 1＋柱 1|CC-BY-4.0|梁和柱各自的承重值|待你审阅|[REVIEW](formal-019/REVIEW.md) · [原件G](formal-019/private/reference.ifc) · [损坏D](formal-019/public/model.ifc) · [请求](formal-019/public/request.txt) · [三维](formal-019/VIEW.html)|
|formal-020|窗 1＋实例属性 1|CC-BY-4.0|窗洞下沿标高|待你审阅|[REVIEW](formal-020/REVIEW.md) · [原件G](formal-020/private/reference.ifc) · [损坏D](formal-020/public/model.ifc) · [请求](formal-020/public/request.txt) · [三维](formal-020/VIEW.html)|

受损原件的Name只在REVIEW和私有材料中列出，公开请求使用方位、楼层和几何位置，不加入GUID、Name定位或工具方法提示。纯属性题015～018保留所有几何，G、D画面相同，请在属性面板核对原值与损坏值。020同时删除窗及洞口并恢复墙面，另一扇门只改外门标记。

014、019、020保留三道必要澄清。答案在实验前写入私有卡；只回复模型实际问到的相关事实，不整卡注入，不临时从G查新答案。014源Name写450×450，真实实体为200×450，REVIEW说明这一差异。

各题PIPELINE-CHECK区分确定性绑定操作支持与通用B运行时检查，不把假模型或绑定探针记为真实成绩。共有操作支持、失败和安装证据见[B结构与属性开发检查](../../../experiments/repair-comparison/development/structural-property-readiness/README.md)。浏览器桥接不可用，尚未进行WebGL/usBIM实际显示验收。

公开运行包仅含public/model.ifc、public/request.txt；G、删除映射、真实Name、答复卡、VIEW和离线候选只供审阅/评价。A/B/C/D正式运行时同题同公开信息，各自工作副本和产物独立。

后十旧题与原运行已在提交3fbae1d8及[历史备份](../../../experiments/repair-comparison/history/README.md)保留。[当前真实实验表](../../../experiments/repair-comparison/current/README.md)仍为B001～010的9/10，不混入新题离线检查。

**原plan.private.json、batch-checks.json是旧二十题冻结记录，不适用于当前后十草案，不能据此恢复原80槽位。** 新题审阅、扩展评分、预算与四组准入尚待重新冻结；当前task为draft candidate、provider_calls_allowed=false。

[本批技术检查与20源登记](expanded-review-checks.json) · [后十题设计及边界](../../../../../docs/validation/repair-comparison/next-ten-design.md)
