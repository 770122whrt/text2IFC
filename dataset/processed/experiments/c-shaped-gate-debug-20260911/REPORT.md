# C 型楼：门禁修复与阶段结果（2026-09-11）

**入口南移已落实；当前真实 IFC 仍阻断，不是待验收 Proof。两处公共流程缺口已离线修复，下一阻断是 Brief 墙体接合。**

## 真实产物与视觉

- [人类请求](../c-shaped-clarified-entry-20260911/request.txt)、[真实入口澄清](../c-shaped-clarified-entry-20260911/conversation.json)、[真实运行报告](../c-shaped-clarified-entry-20260911/REPORT.md)。
- [诊断用真实 IFC](../c-shaped-clarified-entry-20260911/live-run/runs/9b00e53444a948e7/output.ifc)，SHA256 `6c967b8c172ee21794a483e8fa771c9cc85e1c92a33d639676659850aa37edb4`。
- [整体图](views/overall.png)、[首层俯视](views/ground-plan.png)来自该IFC的64个原生实体网格及样式，助手已查看。暖墙、深色屋面、对齐窗列较协调，C形开敞缺口清晰；俯视仍可见缺口侧墙断开、转角缺口。图片不是AI概念图，也不能证明材料或工程合规。
- [独立重开检查](../c-shaped-clarified-entry-20260911/independent-ifc-check-initial.json)：485项中11项失败。入口、门窗位置与尺寸、分色、物理材料、最小Type等相关项通过；墙体积和两处板洞失败。

## 两处小范围修复

| 边界 | 修改前 | 修改后与原因 |
| --- | --- | --- |
| 多边形轮廓提取 | 只识别列表/points包装，漏读building.outline.polygon；随后跳过板洞预期 | 同时支持明确polygon包装，两个包装冲突时不择一猜测。3红/7绿变为10通过；L形/C形及平移、非法/退化边界覆盖。只提取包围盒，不声称检查凹形拓扑 |
| Repair路由范围 | 早期no_repair_needed、geometry_issue_count=0缺少范围，容易被误读为几何通过 | 新运行时route1.1及metrics标明是否收到几何反馈、计数仅对应所给反馈、不证明几何通过；gate basis明确只检查路由资格。5红变5通过，追加非空失败反馈仍阻断的对照 |

没有修改旧Prompt、已注册Schema或Audit放行规则；真实gate_dispute仍停止。路由元数据说明是否足以改善真实Audit判断尚未重测，不把测试中的字符串命中当作模型理解能力证明。

冻结真实候选副本经公共确定性阶段重检：[结果](recheck-result.json)。原7条问题中的3条楼板预期缺失消失，并新增2条准确的FLOOR_OPENING_BBOX_MISMATCH；总计6条，仍失败。两个洞口相对宿主板多下移150毫米。候选JSON与原运行全部文件哈希不变，未调用Provider。`offline-recheck`是诊断副本，不是第二次真实运行，其继承的旧Audit不能验证重检后的门禁。

验证：108项相关回归通过；补充6项范围测试（与108中5项重叠）通过；4项精确C公共运行器fake检查通过，包括完整编译/独立检查、澄清停止、目录保护和唯一入口预期差异。失败过程保留：首次聚焦绿色运行有3项测试误把候选绑定API当作全artifact绑定API，改为实际候选身份负对照后通过，没有扩大该API合同或宣称修复artifact绑定。没有Full Preflight、新阶段准入、真实修复重试或人工验收。

## 为什么暂停真实 loop

[墙边界诊断](wall-boundary-diagnosis.json)表明问题还在候选上游：Brief推导的首层矩形墙足迹有12对正面积重叠，西南角(0.05,0.05)米未覆盖。原请求要求连接且不堆叠；只把错位墙移回中心，仍会留下Brief本身的接合错误。原生首层墙体积46.224立方米，冻结请求检查目标45.984，差0.240。

下一小步限定为明确墙厚/外轮廓的矩形墙接合合同：区分中心线端点与实体边界，验证Agent派生几何能否同时满足用户约束；不一致退回Agent校正，用户原始尺寸、门窗、空间与已批准入口冻结。先建立矩形/L/C、平移/朝向、接触/重叠及确有用户冲突的正反族，再选择最小代码或新版本Prompt修改。不能把错误Brief当最终权威逼迫候选，不能放宽独立评价器，也不把Agent错误转成重复用户澄清。本轮未实现这一后续项。

## Token 实验与成本

C当前真实Audit输入可逐字重建，去重候选没有可复用大对象：原格式177865字节，实验格式178796字节，自动回退后177865字节，**实际采用的格式节省为0**。[比较记录](audit-context-comparison.json)保留全部源哈希。按预定停点跳过额外影子Audit，新增调用0；此前B修复后24.20%的降幅不能迁移到C首轮。C新格式的真实输出/质量对照未运行。

本次同步推进新增4次真实响应（一次语法失败，随后Brief/Generator/Audit），合计282895 token。C累计8次583435 token、1375.654秒，包含旧失败、额度实验；32次/200万token/3600秒限额不变。逐次input/output/reasoning/cache、response ID和历史账本见 [用量汇总](usage-summary.json)。reasoning包含于output，不能重复相加。请求模型deepseek-v4-flash，响应模型字段deepseek-flash。

这一步证明两个局部边界修复及同一真实候选的检查覆盖改善。没有合格交付分母，不能给出“每个合格模型token成本”的有限值，不能声称系统成功率提升、质量非劣效或全面合规。所有源、attempt与accepted Proof保留；当前不登记Proof。
