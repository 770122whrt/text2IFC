# 基础细杆护栏与公共生成路径调试

本目录仅保存离线开发证据，不是已验收Proof，也不是真实Provider结果。第一版保留包已推送为532a4a4c，梁柱冻结预期的前置修复为7df706b2。第二版仍须独立真实运行。

## 原因与修复范围

旧IfcRailing拉伸面板没有细杆和扶手。柱梁虽已有编译能力，此前没有完整进入冻结计数、分包和几何预期；前置提交已补。新护栏是Generation的有界表示，不给Repair旧门窗或栏杆自动升级，不改旧extruded_profile含义。

新BIM JSON 2.3增加basic_railing，仅限IfcRailing实例、metal-picket模板1.0、直线水平或直跑坡向、单一材料和整件样式。每件由编译器生成Posts、Pickets、TopRail、BottomRail，不让LLM展开大量竖杆。尺寸/端点来自请求；默认施工参数由版本合同提供并标记来源。此处没有进行token对照实验，也不声称节省比例或系统成功率提高。

公共路由新增Brief2.6、Draft1.3、ChangeSet1.3，以及新Prompt；此前已注册Prompt/Schema字节和registry旧条目不改。默认CLI版本和legacy_full默认策略不变，staged仍显式选用。

## 命中的失败及证据

- railing-red：旧编译版本拒绝新表示；后续材料字段夹具、元数据保全、IfcOpenShell临时mesh对象生存期问题分别保留，没有将夹具问题算成产品缺陷。
- railing-routing-red：新Brief未选到对应生成版本，斜栏杆丢失独立几何表达，模板家族/作用域未进入适用验证。
- railing-request-red：正确栏杆不能通过冻结template请求核对。
- public-01：新增Prompt登记使用了Windows原始换行哈希，与registry既有LF规范不符；修正仅限新条目。
- public-02：新测试仍返回旧ChangeSet版本；修正测试Provider的版本，不放宽产品检查。另有真实代码缺口：BIM2.3未继承受授权的part_appearance可选字段删除，已补，新旧版本均保留精确作用域和保全限制。
- mirror-red：相同包围盒的反向坡栏杆错误通过。现在还核对冻结起点、水平朝向、竖直轴、升高量和实际杆件，不能仅凭bbox或元数据自报放行。
- railing-final：严格元数据比较曾因4000与4000.0的JSON数字序列化差别拒绝等价几何。新模板解析统一数值表示后复验，未放宽几何或参数范围。
- stage-01：命令引用两个不存在的测试文件名，未收集测试；保留日志，修正路径后重跑为stage-02。

最新聚焦结果：rails-structural-green为83 passed；public-03为23 passed；railing-chain-02为2 passed。集合重叠，不相加为独立样本。stage-02的最终结果以对应XML和命令记录为准，未完成前不得写入admitted。

## 新设计预检

上级request.txt由委托设计草案冻结，expected-independent.json在任何新候选前由prepare_design.py建立；不发送该评价器或期望表给Provider。已核对墙体无正面积重叠、门窗在宿主范围内且相互分离、平台与U形板相接而不重叠、柱脚在板内。

新建筑为两层开敞U形、20柱、6梁、14段细杆护栏、外露楼梯和上端平台、44窗及6门。端点/杆件、完整新公共loop、实际IFC重开与视觉审查均是发布前约束；设计预检不代替最终IFC检查。结构、耐火、无障碍以及扶手抓握/锚固施工细节不在本次自动合规证明范围内。

## 阶段检查收尾

stage-02记录504 passed / 2 failed，用时823.40秒，无跳过。两处失败都来自合法IfcSpace聚合归属被新增共享几何门禁误判为空楼层。spatial-red独立复现一正一负（正确楼层误拒绝，错误楼层仍拒绝）。修复空间聚合读取并保留错楼层拒绝后，stage-03在同两条完整旧链路、新护栏路径、楼层失败族和重开门禁中75 passed，用时139.80秒，无跳过。没有重写原失败，未靠改预期或移除测试通过。

新完整运行包装器runner-01：1 passed，覆盖新Brief、生成、绑定已提出设计异议的Audit3.0、最终IFC、旧预算首条attempt保全；Provider为确定性fake。独立检查器以第一版IFC作负对照，读取原样文件并正确拒绝；这不证明第二版已经成功。

检查范围为本阶段，未运行仓库Full Preflight，尚未调用新的真实Provider。生产来源与private Gold边界、既有Proof字节不变。
