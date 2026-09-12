# 光庭阅读馆第一版：真实 Audit 通过，设计保留待改

2026-09-12。**机器终端检查通过；用户要求保留本版，按概念图右上角重新设计。当前不登记为人工已验收或 accepted Proof。**

## 查看入口

- [最终 IFC](live-run/final-acceptance/output.ifc)（645369字节）
- [完整中文输入](../request.txt) / [真实运行与来源](live-run/execution.json)
- [实际 IFC 交互查看器](final-review/views/viewer.html)
- [整体](final-review/views/overall.png) / [隐藏屋面](final-review/views/courtyard-roof-hidden.png) / [二层俯视](final-review/views/upper-floor-plan.png)
- [隐藏墙和屋盖的剖看](final-review/design-recheck/structure-cutaway.png) / [隔离楼梯](final-review/design-recheck/stairs-isolated.png) / [隔离栏板](final-review/design-recheck/railings-isolated.png)
- [门部件](final-review/views/IfcDoor.png) / [双面板窗](final-review/views/IfcWindow.png)
- [设计偏差与下一版边界](DESIGN-RECHECK.md)

最终 IFC SHA-256：38457bfad619c0c35ab536209001a00db65e3b8fc4f570e0139e779f290308ab。以上图像直接来自最终文件，83个可显示构件，网格化失败0。剖看仅隐藏构件，不补画、重着色或修改 IFC。早期 review-views / design-recheck 是离线重放模型的视图，保留其原来源；本页主入口使用 final-review。

## 是否真正经过 Provider

**Brief、Generator、Audit 三个 LLM 阶段均有真实 Provider 调用，但不是一次无中断的全链路成功。**

1. [原真实运行](../rerun-04/live-run/execution.json)完成 Brief、语义修正和 Generator。Generator 响应 c71fd68d-5df7-4e56-91b3-444eb4937315 正常结束，产生173个实体、14条关系，但漏写55组门窗 void/fill。原自动 loop 保持失败状态。
2. 离线失败族和公共链路验证后，生产确定性恢复只追加110条缺失关系。原实体、原关系及冻结请求不变；没有手工制作替代候选或伪造 Generator。
3. 本目录通过明确的阶段续跑继承原候选和累计预算，重新检查并完成真实 Audit。响应 e6ee79c7-ce98-4caf-96ae-eb3c91b95ae1 建议 accept；生产 final-acceptance 输出本页 IFC。
4. [续跑记录](live-run/execution.json)的 source_unchanged 为 true。[授权拦截记录](authorization-block.json)属于补充确认之前的历史；用户明确“你发送这个audit吧”后调用成功。原响应、失败、预算和离线重放全部保留。

目的地 api.deepseek.com；请求模型 deepseek-v4-flash，响应记录 deepseek-flash。只发送本案例请求、对话、Brief、候选 JSON、生产检查和运行元数据；未发送 IFC 字节、概念图片、独立评价器或其结果、private Gold、其他案例或凭据值。

## 机器结果和设计差距

模型含2层、16个空间、20面墙、3块楼板/屋面板、40窗、15门、4块玻璃栏板、1座楼梯及1个梯段、58个开口、10个项目内 Type/Style。实际部件已核对深灰框 #333D40、木色门扇 #A87950。

用户指出的差距成立。栏板只是20毫米玻璃板，没有立柱和扶手；0.75透明度加上接近楼板的米棕色，使其很难辨认。楼梯连接0米与3.6米，却藏在西侧封闭楼梯间。8×6米光庭只占24×18米轮廓的11.11%，完整外墙和宽屋盖形成封闭盒子。板面沿用米棕色主题，没有充分落实输入中“浅暖灰”的定性要求。

原概念图右上角具有向前开敞的围庭关系、可见沿庭楼梯、细杆护栏、框架与竖向窗组。**主要偏差发生在 Agent 将概念方向细化为冻结请求时**：为适应现有能力，输入主动要求封闭楼梯间、玻璃整板和不加梁柱。这是 Agent 的委托设计选择，不能伪称用户逐字要求。旧检查器验证了这些参数，没有验证概念意图是否保留。

本次 Audit2.0 的 design_review_context_sha256 为 null，未收到概念图或此次设计异议。accept 不代表视觉满意或设计全面合规。Audit 原文将部分代理设计约束称为 user instructions，本报告纠正来源归属，原响应不改写。

## 验证、限制与 token

|检查|实际结果|
|---|---|
|生产编译、重开、几何和最终门禁|[通过](live-run/final-acceptance/acceptance-metrics.json)|
|冻结请求独立 IFC 检查|[1084/1084通过](final-review/check_ifc.json)|
|门窗部件颜色独立核对|[72/72通过](final-review/check_part_colours.json)|
|关系恢复、透明度、旧路由等聚焦测试|[84通过、2 deselected](scoped.xml)|
|legacy_full / staged 公共路径|[2通过、37 deselected](public-loops.xml)，staged为原路径回归|
|续跑与请求不符、源改动、截断阻断|[4通过](public-continuation-final.xml)，这些测试的 Audit 明确为 fake|
|真实 Audit|[accept，7项 info，无阻断](live-run/audit/audit-report.json)|
|最终产物敏感信息扫描|[0发现](live-run/final-acceptance/secret-scan.json)|
|全仓 Full Preflight / accepted Proof curator|本轮未运行；没有安装 accepted Proof|
|设计验收、完整通行/结构/消防合规|未通过设计验收；其他未认证|

Audit 保留了房间相对开门方向、楼梯斜向扶手、板材层 offset=-200 与放置原点关系未核实的问题。存在构件或 represented 标签不等于通行、临边防护和构造安全完整。

本次真实 Audit 输入114277、输出9465（其中 reasoning 7524），合计 **123742 token**，43.578秒。全部真实尝试累计 **9次 / 750000 token / 1458.922秒**；共用上限32次、200万token、3600秒。所有失败纳入账本。不主张 token 节约或系统能力统计提升。

## 修复和证据保全

- 新部件配色合同 Brief2.5 / BIM JSON2.2 及对应新 Prompt：逐部件、逐通道写入重读，旧注册版本未覆盖。
- 缺失关系恢复：冻结身份、宿主、放置链和唯一性一致时才追加；冲突、重复、缺事实或后续校验失败则整批不应用，不重建几何掩盖局部问题。
- 透明度单通道：不再错误强制同时提供 RGB；未指定颜色保留主题，重读只检查明确通道。主题效果不满意仍需设计修正。

失败 XML、测试夹具问题及修复过程全部保留，没有删除失败或改变冻结评价器。代码 a9c2d652、c9a21448、644b7bf7，前期证据 c5696115 已推送当前分支。

用户要求保留第一版，并按概念图右上角准备新 IFC。这是保留授权，不是人工接受第一版设计。本目录作为可追溯运行和设计反例保留；新设计使用独立目录、输入和预期，不覆盖本包、不改旧机器结果、不登记为 accepted Proof。
