# Generation 人工检查

> **pending_human_review · 未登记**。仅供人工检查，不更新总索引、accepted 名单或阶段结论。

真实 DeepSeek 已返回 Design Brief 和完整 Formal 2.1；确定性代码已生成可重读的完整 IFC2X3，45 项独立请求核对通过。真实 Audit 已接受，最终验收通过；当前状态为 **pending_human_review**。本结果经历真实失败、通用代码修复和同例复验，不是完整 CLI 首次成功或盲测能力提升；尚未登记为 accepted Proof。

## 输入与输出

- [实际用户输入](request.html)；[澄清回答](evidence/frozen/clarification-answer-01.txt)：6000 沿 X、4000 沿 Y，其他要求不变。该演示输入和回答由 Codex 按授权编写。
- [完整待检查 IFC](generated.ifc)；[交互查看模型](review.html)。打开属性区域可查看实际 IFC 直接／有效属性。
- [整体图](evidence/views/overall.png)、[双面板窗近景](evidence/views/window-double.png)、[单面板窗近景](evidence/views/window-single.png)、[门框门扇近景](evidence/views/door.png)。这些是实际 IFC 网格渲染，颜色受查看器照明影响。

| 明确要求 | IFC 独立重读结果 |
|---|---|
| IFC2X3、毫米 | 通过 |
| 室内净尺寸 6000×4000×3000 | 通过，原点位于地坪中心 |
| 四面砖墙，厚 200、高 3000 | 通过；IfcWallStandardCase 的砖以合法单层 usage 表达 |
| 混凝土地坪厚 150、顶面 Z=0 | 通过，覆盖 6400×4400 外包范围 |
| 南面居中左单开门 1000×2100 | 通过；门框与门扇分色，左开由 IFC2X3 DoorStyle 表达 |
| 东侧双竖面板窗、西侧单面板窗 | 各 1600×1200，窗台 900，居中；实际存在 2／1 片玻璃 |
| 开口、宿主、框深和位置 | 开口名义宽高一致、穿透墙厚；门窗均位于允许的安装深度范围 |
| warm-residential 协调风格 | 米色墙、棕色门扇、深色框、淡色玻璃；实际玻璃 transparency=0.45 |
| 未指定的材料与性能属性 | 未创建；仅有内部身份、构造参数来源、外观溯源属性及最小合法门 Style |
| 明确无屋顶、无吊顶 | 未创建 |

[独立检查的 45 项及实际值](evidence/frozen/final-independent-review.json)不使用 Agent 的 represented 标签作为证据。[冻结请求](evidence/frozen/frozen-expectations.json)在 Provider 前建立，未按输出改写。

## 真实过程及限制

共 5 次真实调用：初始 Brief 提出轴向澄清，回答后 Brief ready；第一份 Generator 候选重复旋转窗体，被正确阻断；第二份真实 Generator 响应纠正放置。该响应未被人工改写。后续离线调试修复了稳定 ID 映射、墙体子类计数、几何／宿主匹配以及关系名称编译问题。

最新确定性检查在 [corrective-02-general-revalidation](evidence/frozen/corrective-02-general-revalidation/binding-admission.json)。它复用了第二份真实响应；这是开发纠错后的同例回放，不是盲测或能力提升证据。用户明确批准具体载荷后，真实 Audit 已接受，响应 ID `a7baee6f-658a-4856-8e4c-d9d464c7d67e`；[最终验收](evidence/frozen/corrective-02-general-revalidation/acceptance-metrics.json)的编译、重读、几何和敏感信息扫描均通过。此前 [审批阻断记录](evidence/frozen/audit-approval-blocked-02.json) 和 [本地载荷预览](evidence/frozen/audit-payload-preview/audit/prompt-rendered.md)作为历史保留。完整历史与失败响应保留在 runtime 和 corrective-attempt-02。

人工检查重点：整体颜色是否协调；单窗、双窗分格是否清晰；框／扇比例是否合适；尺寸和材料是否忠实于输入。门为关闭状态，不含把手、复杂五金或开门动画。视觉审查不能代替模型尺寸、类型和属性检查。

最终发布 IFC 已独立复核 45 项。其网格、样式、GUID 及直接／继承属性与已查看模型完全一致，见 [视图等价检查](evidence/frozen/final-view-equivalence.json)，因此已有整体图和门窗近景仍适用；最终查看器明确绑定最终 IFC。

## 中文请求全文

请生成一个单层矩形接待室的完整 IFC2X3 文件，单位为毫米。室内净长 6000、净宽 4000，墙高 3000、墙厚 200，四面墙闭合。地坪顶面标高 0，厚 150，覆盖整个房间及墙底。为便于检查室内，本次明确不建屋顶或吊顶。设一个室内空间。
正南面墙正中设置一樘左单开门，宽 1000、高 2100，门底与地坪齐平。正东面墙正中设置一樘双竖面板窗，正西面墙正中设置一樘单面板窗；两窗均宽 1600、高 1200、窗台标高 900。开口与各自门窗名义宽高一致并穿透墙厚；门窗居中安装，保留窗框、玻璃、门框和门扇细节，不加外伸门套或复杂五金。
四面墙材料明确为砖，地坪材料明确为混凝土；其他构件不指定物理材料。采用 warm-residential 协调风格，窗玻璃透明、窗框与门扇有协调的部件分色。没有提供任何耐火、承重、强度、热工性能或普通属性，请不要自动添加这些属性。没有共享 Type 要求。不改变上述尺寸和位置；模型原点取室内地坪中心，X 向东、Y 向北、Z 向上。


[完整证据导航](evidence/README.md) · [案例文件绑定](FILES.json)
