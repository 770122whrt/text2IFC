# B：明确保留原设计

**真实 Generation 已完成；独立检查通过；用户已于2026-09-10人工验收，现已登记Proof。**

按用户明确决定保留原设计：两个反向梯段仍共用同一平面。它是忠实建模的保留缺陷版本，不能用于证明楼梯安全、工程合理或规范合规。

## 先看这些文件

- [完整中文请求](request.txt)与[已批准澄清](clarification.txt)，[完整对话](conversation.json)。澄清来自本次获批的脚本化分支，并非本轮临场对话能力演示。
- [最终完整 IFC](generated.ifc)。原参考文件未被修改，最终 IFC 从新 Brief 和新候选生成，没有复用历史失败候选。
- [整体视图](views/overall.png)、[内部剖切](views/cutaway.png)、[双竖面板窗](views/window-double.png)、[门框与门扇](views/door.png)。图片均来自该 IFC 的原生网格；剖切只在视图中隐藏屋面、南墙和东墙。

## 逐项结果

| 核对项目 | 本次结果 |
|---|---|
| IFC格式、单位 | IFC2X3、毫米，重开读取通过 |
| 楼层与空间 | 3层、6空间；标高0/3150/6300毫米 |
| 构件数量 | 15墙、3楼板、4门、15窗；楼梯与屋面另按冻结合同核对 |
| 尺寸、位置、开口 | 与该分支冻结预期一致，含梯段、平台、墙门、楼板洞口 |
| 材料 | 明确要求的砖墙、混凝土楼板/屋面存在；无未请求材料 |
| 属性与Type | 未补写未请求性能属性，未额外创建未经请求的类型组织；基础合法附件按合同处理 |
| 外观 | 暖浅色墙面、深色门窗框、玻璃与框/门扇分色；未用颜色推导物理材料 |
| 独立验证 | 重开IFC逐项比较冻结请求，290/290项通过 |

108个垂直采样点中有3个零净空点，最小净空0米；位于一层通往二层楼梯的北端附近。Audit明确记录retained_known_issue。

## 实际运行与边界

运行ID `8b3add702299a50f`，`legacy_full`，Provider `api.deepseek.com / deepseek-v4-flash`。本轮收到5次真实响应，实际响应用量324,504 token。此次任务累计占用5个调用槽位、324,504 token（包含历史失败预留），活动时间327.827秒；原失败账本不退回。详见[运行记录](../evidence/frozen/B-retain/execution.json)、[预算账本](../evidence/frozen/B-retain/runtime/runs/8b3add702299a50f/generation-budget.json)及[原始Audit](../evidence/frozen/B-retain/runtime/runs/8b3add702299a50f/audit/audit-report.json)。

独立采样只覆盖本案例适用的梯段垂直净空，不覆盖完整疏散、侧向空间、结构、栏杆、防火及规范审查。四张静态原生视图已由助手查看，不能替代人工在IFC viewer中的交互审查。本轮实证说明这两个冻结案例可运行，不构成普遍成功率或系统能力提升的统计结论。

机器证据：[290项原生检查](independent-ifc-checks.json)、[6项补充Type检查](independent-type-checks.json)、[净空测量](clearance-checks.json)、[视觉检查记录](visual-review.json)。原生IFC均仅有4个必需门Style，未附材料/属性，每门独立对应一个Style；补充检查没有修改冻结的290项评价器。

## 本轮loop实际修正了什么

首个候选把二层、三层楼板洞口的局部Z坐标多下移150毫米，导致洞口落在楼板底部以下；几何gate报告两项FLOOR_OPENING_BBOX_MISMATCH。一次受限ChangeSet仅将这两个洞口的局部origin.z恢复到0，随后重新编译、重读和Audit通过。它修正的是对已确定洞口位置的错误表达，没有移动梯段、改变楼梯共用平面、扩大洞口或消除用户保留的净空缺陷。

[首轮几何反馈](../evidence/frozen/B-retain/runtime/runs/8b3add702299a50f/evaluation-rounds/round-01/geometry-feedback.json)、[受限ChangeSet](../evidence/frozen/B-retain/runtime/runs/8b3add702299a50f/changeset-round-01/changeset.json)。这提供一次实际loop收敛证据，不代表所有几何错误均能稳定修好。

## 收纳与验收

用户已确认该版本内容无误。集合根保留便于识别的 generated-B.ifc；本案例的 generated.ifc 是相同字节的标准入口。历史运行报告及JSON中的pending状态是验收前快照，保留原样，当前人工状态以[验收记录](../human-review.json)为准。
