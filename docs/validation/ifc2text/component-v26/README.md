# 参数化门窗：首阶段开发与验证

日期：2026-09-25。执行依据：[唯一计划 v1.0](../../../architecture/text2ifc-component-plan-v1.0.md)。

已新增 BIM JSON 2.6 的部件几何和确定性编译路径。整体仍是一扇门／窗；框、叶片、门板、把手是其中的几何部件。源 IFC 的原生挤出解析也已接入。**hxp 与 TallBuilding 各一门一窗均已完成真实 LLM loop；整栋 hxp 尚未生成。** 下方保留分阶段证据。

**最新比较要求：允许 IfcOpenShell 解析后进行容差比较，也允许补充自写算法。** Compare 1.2 继续使用：IFC 解析、单位与变换、布尔并集及网格来自 IfcOpenShell，双向采样距离、拓扑与体积判据由项目实现，不能改称全部是官方库算法。其边界测试覆盖 0.5 mm、1 mm、1.0001 mm、内部孔洞与叶片变化、等价实体拆分和不同单位。现有四个结果不改写、不换版本冒充重测。

已使用本地未修改的 IfcDiff 0.8.5 重查四个单构件，均未报告几何变化；记录位于 `component-v26-ifcdiff-check-20260925-01/official-ifcdiff-results.json`。每对输入仅有一个该类构件，为适配工具的 GlobalId 要求，只在内存中对齐候选编号，源与候选文件字节均未改变。未调用 LLM。

IfcDiff 的几何变化报告不能直接证明最大表面误差 ≤1 mm。所装版本采用形状摘要比较，几何摘要路径的 epsilon 为固定值，且禁用开口扣除；没有完整材料／颜色比较选项。不能仅设置 IFC Precision 就宣称满足 1 mm 的所有检查。继续以实际几何测量为主、IfcDiff 为辅，采样与未评估项均如实注明；本次讨论已明确，无需再次等待比较方案确认。参见 [IfcDiff 官方说明](https://docs.ifcopenshell.org/ifcdiff.html)；实际实现核对的是本地 0.8.5 源码。

## 已完成的内容

- 新版 schema：矩形、圆形、带孔多边形截面；直线挤出；部件与实体两层放置；定义复用及有限等距重复。模板与部件模式互斥。
- 编译成一个 IfcDoor／IfcWindow 和多个真实挤出实体，用 IfcShapeAspect 保存部件 ID、角色和实体关联。
- 部件颜色／透明度、名义尺寸保留。部件物理材料归属尚未接入。
- 重开后读取真实实体，检查孔洞、尺寸、坐标、部件归属、颜色和名义尺寸。故意篡改深度、孔、坐标、数量、角色、颜色及名义尺寸，检查器均应阻止发布。
- 拒绝不合法轮廓、未知引用、重复 ID、零间距重复、近乎平行于截面的挤出、混用模板等输入。构建器抛出几何错误时返回结构化失败，保留已有输出。
- 修复旧 2.4／2.5 版本逐部件显示被默认配色覆盖、写入与校验同时漏检的问题。
- 原生源解析处理产品坐标、刚体映射、截面坐标和长度单位。源文件中不支持的实体返回具体 STEP 项和原因，整个门窗不生成简化替代物。

技术合同见 [BIM JSON 2.6](../../../../schemas/bim-json/2.6/README.md)。后续 S2 接入的 [Brief 2.9](../../../../schemas/agent/design-brief/2.9/README.md)、Draft 1.6、作者合同 1.6 和交互恢复见本文末尾。

## 真实来源的确定性诊断

运行脚本：`scripts/ifc2text/component_native_probe.py`。预先选择两份文件的**全部门窗**，源 SHA、GlobalId、每项结果与拒绝原因见 [native-summary.json](native-summary.json)。这不是 LLM 实验，Provider 调用次数为零。

| 来源 | 预选门窗 | 编译并通过几何诊断 | 明确拒绝 |
|---|---:|---:|---:|
| hxp | 10 | 5：3 窗＋2 门 | 5 门 |
| TallBuilding | 26 | 25：21 窗＋4 门 | 1 门 |

对于通过的构件，使用 IfcOpenShell 从**源父构件完整 Body**和重建构件获取实际网格，计算双向顶点最近距离、面积和体积。没有按已识别实体列表过滤源几何。

- hxp 最大双向顶点距离约 `1.04×10⁻¹² mm`；最大相对体积差约 `3.80×10⁻¹³`。
- TallBuilding 最大双向顶点距离约 `1.82×10⁻¹² mm`；最大相对体积差约 `2.45×10⁻¹²`。
- 固定线性判据为 ≤1 mm；本次原生几何诊断另设面积／体积相对差 ≤10⁻⁶。后两者没有套用长度单位。
- 两份源 IFC 的运行前后 SHA 一致。

这些数值表示原生参数重编译的近浮点误差一致性，不代表自然语言生成也能达到同样精度。网格比较不是严格连续曲面的 Hausdorff 距离；安装关系、完整建筑、源材料和文本传播在本实验中均未评估。两个建筑是不同来源的诊断数据，不声称统计泛化提升。

工作区内的完整实验目录为 `dataset/processed/experiments/component-v26-native-20260924-02/`；每个成功案例有 `source-components.json`、`bim.json`、`rebuilt.ifc`、`compare.json`。拒绝案例保留来源与逐项理由，没有替代 IFC。完整运行产物留在本地实验目录，本目录只提交紧凑结果和复现实验入口。

## 不支持项与讨论

hxp 的 4 扇木门包含直线与圆弧组合的复合截面，不能用已定的纯多边形或完整圆截面等价替代；另 1 扇门使用 BRep。TallBuilding 的另 1 扇门也使用 BRep。2026-09-25 已明确选择：本轮不扩展圆弧截面；hxp 排除 D003–D007 后继续，保留墙体与开口，交付部分重建及拒绝清单。决定记录在 `dataset/processed/experiments/component-v26-hxp-scope-20260925-01/`。其他不支持项仍须逐项解释，由 human 选择排除后继续或暂停。

这里的首阶段拒绝结果是解析 API 与实验清单的行为。后续 S2 已通过产品澄清、持久化回答和恢复的离线测试；该测试与上表原生几何诊断是两类证据。

## 验证、失败与回退

测试采用先红后绿。开始时保存未提交代码的字节快照；必要的 2.4／2.5 编译依赖单独提交为 `4ff01db5`，其余工作区变更保持原状。新功能独立提交，旧版本显式选择和旧模板回放仍保留。

本阶段完成的验证包括：单门、单窗；圆形把手；含孔窗框；14 片旋转叶片；坐标组合；源映射原点非默认值；米到毫米；缩放／反射拒绝；IFC4 未准入拒绝；逐项显示；旧模板、墙体、材料、类型与失败原子性。

最终合并的定向回归：**226 passed，294.24 秒**。范围为新部件编译／源解析，以及既有 basic_filling、part_appearance、polygon_wall_hosts_v24、material_list_v25、project_name_fallback、v2_geometry、v2_compilation、coordinated_appearance、compiler_boundary、geometry、placement、type_family_boundaries。未运行全仓库 Full Preflight，未调用真实 Provider；此结果不构成 S2／S3 的公开 Agent 链路准入。

规模探针实际编译并重开 128 部件／512 实体（约 8.4 秒）及 512 部件／2,048 实体（约 25.8 秒）。据此保留相应资源上限。这是本机离线编译结果，不是运行时 SLA，也不证明 LLM 能可靠输出这个规模。

保留的失败与纠正：

1. 初始 pytest 默认临时目录无权限；改用工作区临时目录后基线 117 项通过。
2. 第一批原生实验漏传顶层 provenance，30 个输入被拒绝；该批次原样保留在 `component-v26-native-20260924-01`，不计作成功重建。
3. 第二批汇总脚本的 `source` 键被同名网格指标覆盖；逐案例 IFC、测量和状态未受影响。额外写入 `summary-index-recovery.json`，由运行前 selection 的 SHA 映射恢复路径，保留原 summary 文件。本目录结果带有恢复来源和 SHA。
4. 映射测试曾因 Python 临时几何对象生命周期得到空网格；保留 shape 对象后再取数组，测试通过。没有以放松几何阈值解决问题。

首阶段后的工作进入 S2；当前进展如下。

## S2：公开描述与会话链路

新增描述版本 1.0，在楼层内列出门窗的完整部件说明：整体世界坐标、部件坐标、实体坐标、截面与内孔、挤出方向／深度、部件引用和显示参数。源 STEP 编号、GUID、源文件路径保留在提取证据中，不作为生成端的隐蔽几何输入。不支持一个必要实体时拒绝整个门窗的完整重建，不输出剩余实体组成的替代物。

Brief 2.9、Draft 1.6、作者合同 1.6 及配套新提示词已经贯通公开入口。单门、单窗分别通过真实生产 API 的离线响应测试，最终产物由 IfcOpenShell 重开。支持缺参数后回答并恢复；不支持时返回问题、保存回答、重开数据库恢复，无回答时不新增调用。“继续”不能使尚不支持的 BRep 变成已支持能力。

输出部件除与候选自检外，还和冻结的公开 Brief 要求比较：检出缺叶片、角度变化、孔被填实、重复实体、部件角色／显示差异；允许同一部件几何等价地拆成多个实体。使用实际表面采样、拓扑及体积检查，线性距离 ≤1 mm；这不是连续表面 Hausdorff 的数学证明。0.5 mm、1 mm 通过，1.0001 mm、2 mm 不通过。

本阶段发现并修复了三类衔接问题：旧遍历把部件颜色误当独立产品；版本选择遗漏新 Brief／BIM JSON；独立门窗被一律要求宿主开口。新版保留显式实例编号，并区分独立构件和安装门窗，不取消建筑中的宿主检查。

开发测试及失败记录见 [stage2-summary.json](stage2-summary.json)。主要记录包括：45 项早期新链路测试通过；相关旧功能回归 307 项通过、3 项测试版本标注错误，修正后对应 5 项测试通过；编号与关系专项回归 40 项通过；既有实验与预算工具回归 61 项通过。后续新测试的断言／stdin 测试输入错误也原样记录，并有对应修复后的定向检查。各轮存在重叠，不相加为一个能力指标。

两份实际来源模型的公开说明已生成，源文件哈希未变，真实 Provider 调用为零：

| 来源 | 公开说明 UTF-8 大小 | 门窗可描述／拒绝 | 准备耗时 |
|---|---:|---:|---:|
| hxp | 44,898 字节 | 5／5 | 约 3.4 秒 |
| TallBuilding | 87,451 字节 | 25／1 | 约 10.3 秒 |

文件位于 `dataset/processed/experiments/component-v26-text-prepared-20260924-01/`。状态均为 `prepared_requires_component_review`；这是描述准备，不是重建成功。接下来先建立当前代码对应的真实模型阶段准入，再做单门、单窗真实 loop 和宿主场景，随后处理整栋实验及明确拒绝项。
## S3 独立比较与真实输入准备（2026-09-25）

- Compare 1.2 在原有 1.1 的匹配、材料、墙体测量之外，读取源文件与重建文件的完整门窗 Body，展开实际映射，比较世界坐标下实体并集、双向表面采样距离、连通分量、Euler 数与体积。几何容差固定 1 mm；未识别的 Body 项明确记为未评估，不能过滤后报告一致。该采样不是连续 Hausdorff 距离的严格证明。
- 对之前全部 36 个原生门窗样例重新计分：30 个通过、6 个仍拒绝，分母未减少。证据位于 `dataset/processed/experiments/component-v26-body-compare-20260924-01/`；这是冻结原生候选的重新计分，不是文本往返。
- 从 hxp 与 TallBuilding 各选择一门一窗，复制原 IFC 后仅在副本中移除其他产品，保留原生几何、材料、样式与 Type 关系。四份独立输入与原构件的完整实体比较均通过；源文件未修改。宿主安装从该单构件测试范围明确排除。输入位于 `dataset/processed/experiments/component-v26-single-inputs-20260924-01/`。
- 独立比较测试 10 passed；副本提取测试 2 passed；冻结输入与真实建筑上下文测试 3 passed。两座完整建筑的描述通过实际公共 Brief 入口和离线替身接入，记录时间、进程内存峰值及请求大小，遇到不支持项停止。仍没有新的真实 Provider 调用。

本阶段正式准入由 `scripts/ifc2text/component_campaign.py validate --config scripts/ifc2text/component-campaign-v1.0.json` 执行。该命令仅运行代码内列出的阶段测试，涵盖公共完整链、澄清恢复、截断/格式错误、Provider seam、原子失败、源文件保护、实际几何、终态发布和真实规模上下文。它记录精确文件快照、命令和日志哈希；配置、代码或冻结输入变化会阻止后续真实调用。未通过时不得调用 Provider，也不自动运行仓库级 Full Preflight。

## S3 真实单窗结果与单门调试

第一次阶段准入为 379 passed、0 failed、0 skipped（513.86 秒，无网络）；说明格式 1.1 的后续定向复验为 21 passed。实际 Provider 请求为 `deepseek-v4-flash`，响应标识为 `deepseek-flash`；本轮向 `api.deepseek.com` 发送派生说明及后续 Brief/BIM JSON 已获明确授权，源 IFC 不发送。

hxp 单窗在说明格式 1.1 下得到 ready Brief、formal 候选、accepted Audit 和 compiled IFC。源与输出均有 15 个实际实体；完整 Body 的双向表面采样最大距离约 **3.342×10⁻¹⁰ mm**，拓扑相同，已评估的几何、材料、关系、楼层标高均无差异。它仍是独立单窗，不是宿主场景或整栋保真结论。

- [实际重建单窗 IFC](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-02/hxp-window/runs/bc6346f966e8480e/output.ifc)
- [独立 Compare 1.2](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-02/hxp-window/compare-v1.2.json)
- 同目录 `brief-source-parameter-trace.private.json` 为评价端定位记录：Brief 与源部件参数只有数值输出舍入差，未发现非数值内容差异；该记录未送入 Generator。

保留的真实失败和修正：首次单窗 Brief 把楼层名称“标高 3”与真实标高 40 mm 误判为冲突，停在澄清，未生成 IFC。说明 1.1 将名称加引号并单列 `楼层标高=`；原说明 1.0 和首轮响应保留。单门第一次 Brief 把同一完整门记录同时放在顶层和楼层内，严格校验拒绝它，仍未生成 IFC。新增规范化仅合并完整 JSON 内容相同、明确属于同一楼层的冗余门窗副本；冲突、缺字段、不同楼层和重复候选仍拒绝。原模型响应及逐项规范化记录保留，部件参数不改写。单门原失败响应离线重放后校验通过；这不是新的模型试验。

规范化开发检查：36 passed；随后覆盖重复副本的门／窗完整公开链路为 13 passed，各轮有重叠，不合并为能力指标。此项改变了公共 Brief 入口，下一次真实调用前使用新配置 `component-campaign-v1.2.json` 重新建立阶段准入。

该阶段准入已完成：404 passed、0 failed、0 skipped，473.87 秒，无网络。随后单门第二轮实际尝试（`component-v26-single-loop-20260925-03/hxp-door/`）仍停在 Brief，未生成 IFC：模型保留了全部五个部件，却将公开编号改成内部 ID，未保留显式对应，校验器原先误报为部件缺失。其自动语义修复不能修改被冻结的门记录，第二次响应仍失败；两次真实响应均计入预算并保留。

定位重放仅给原门记录补上公开 `label`，其余几何参数不变，校验从失败转为通过；这是评价端离线诊断，不送入生成链。通用修正采用新 Brief 提示 2.30／2.31：要求每个公开部件目录编号对应唯一父构件；沿用原编号，或明确保留 label。校验分别报告编号丢失、编号歧义与部件缺失；前两项不进入无法改变对象身份的语义修复。无前后缀推断、场景特判或几何替代。相关测试先出现 5 个预期失败，再通过包含旧合同／编译检查的 70 项定向回归；真实重试仍须新配置 1.3 的阶段内复验。

i5n_1 作为混合支持案例已获确认：先测暂停不生成，再排除 D002 并生成带拒绝说明的部分模型，保留墙、开口与其他支持对象。D002 含 22 项 BRep；源模型 42 面墙和 24 个开口均通过当前原生参数提取。此处仅是输入适用性与人工决定，尚未完成该整楼重建。决定保存在 `component-v26-i5n-scope-20260925-01/human-decision.private.json`。

公开编号修正已提交推送 `6ed0e67a`。阶段内复验为 153 passed、0 failed、0 skipped，129.90 秒，无网络；未变动的编译器／Provider／比较器证据继承前一轮 404 项阶段检查，不累加测试数。第三次单门 Brief 保留 D001 和全部五个部件，生成 formal 候选、accepted Audit 并输出 IFC。Compare 1.2：源与候选均为 5 个实体，拓扑相同，最大双向表面采样距离 **1.728×10⁻¹⁰ mm**，匹配 1、缺失 0、多余 0、几何／材料／关系差异 0。hxp 的独立单门和单窗均已得到真实往返结果；这不包含宿主安装与整栋。

- [实际重建单门 IFC](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/hxp-door/runs/0207af2c723d324c/output.ifc)
- [单门独立比较](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/hxp-door/compare-v1.2.json)

TallBuilding 的独立单窗与单门也均一次经过真实 Brief→Generator→Audit→IFC 并通过 Compare 1.2，最大双向表面采样距离分别约 1.044×10⁻¹⁰ mm、5.093×10⁻¹¹ mm。四个选定单构件现均通过已测几何、关系、材料与标高检查。它们是已揭示诊断案例，不是盲测统计或通用建筑能力证明。

- [TallBuilding 单窗](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/tall-window/runs/d458c396db836911/output.ifc)、[比较](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/tall-window/compare-v1.2.json)
- [TallBuilding 单门](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/tall-door/runs/d84a78710b6772af/output.ifc)、[比较](../../../../dataset/processed/experiments/component-v26-single-loop-20260925-04/tall-door/compare-v1.2.json)

## S4 安装场景准备

新增原生宿主场景提取：保留一扇门／窗、整面宿主墙及其所有开口，其他产品仅从副本移除。对源与副本检查完整门窗 Body、墙体切洞后网格、各开口网格及关系，避免删除另一开口而改变墙体。门、窗以及无宿主拒绝测试 3 passed。hxp 两份实际输入均保留各自的一墙、一开口、一门窗，原生几何检查通过；文件位于 `component-v26-hosted-inputs-20260925-01/`。

两个离线公开链测试均通过真实 IFC2Text、Brief 入口、编译、终态发布与独立比较，模型响应为明确注入的离线夹具。没有原生墙 Axis 的夹具保留墙长／厚／高未评估状态，同时断言墙体切洞前后实测几何、门窗完整 Body 和安装关系通过；未修改比较器来清除这一限制。

剩余开发的调用次数重新分配见 `component-v26-budget-20260925-01/allocation.json`：沿用累计 token 上限 **3,696,347**，完整继承已耗 **2,338,826** 和 34 次重建调用，再配置 24 个调用位置。没有新增 token 授权或清空旧账；旧账变化、未结算或失败暂停均阻止后续调用。预算与传输定向检查 13 passed。宿主真实调用使用 `component-campaign-hosted-v1.0.json`，须先完成新阶段离线准入。

### S4 首轮真实运行与回显诊断

安装阶段准入已通过：**426 passed、0 failed、0 skipped**，464.10 秒，网络调用为零。证据在 `component-v26-hosted-loop-20260925-01/validation/`；这是阶段检查，不是仓库 Full Preflight。

带宿主单门已通过真实 Brief→Generator→Audit→IFC：3 个对象匹配，无缺失、多余、几何超差或关系差异。门的完整 Body 仍为 5 个实体，采样表面最大差约 **3.392×10⁻⁷ mm**；墙体切洞前后实测偏差 **0.04450 mm**，在 1 mm 内。原始报告保留 `evaluated_scope_consistent=null`：源墙有 Axis，候选以网格主轴测尺寸，因此内在尺寸测法变化未评估。材料内容相同，层方向／偏移也相同，但层集合名称由源名称变为 `M01`，记一项元数据差异。见 [单门比较](../../../../dataset/processed/experiments/component-v26-hosted-loop-20260925-01/hxp-hosted-door/compare-v1.2.json) 和同目录 `wall-metadata-diagnosis.private.json`；不能据此声称整栋或全部字段相同。

带宿主单窗首轮在 Brief 控制器终止，未生成 IFC。模型将原始请求从 5,844 字符回显为 5,843 字符，唯一差异是连续空行少一条；尺寸和文本没有变。原始调用、失败终态及计费 55,020 token 均保留在 `component-v26-hosted-loop-20260925-01/hxp-hosted-window/`。

修正只作用于 Brief 2.9 的冗余原始请求回显：连续空行数量不同且全部其余字符、段落边界相同时，恢复会话保存的精确输入，独立记录原始值和 SHA；不改 known_facts，不增加模型调用。文字、数字、缩进、段落边界变化和 fenced literal 输入仍严格拒绝。新测试先 15 failed／1 passed，修改后连同重复记录、编号和失败证据检查共 59 passed。真实失败响应经公开 invoker／controller 离线重放达到 ready，仅 `original_request` 字段恢复，所有 known_facts 不变；重放不是新的真实成功证据。后续真实重试使用新配置 1.1，并先完成阶段内受影响路径复验。

阶段内复验 155 passed、0 failed、0 skipped，149.65 秒，无网络；空行修正提交为 `90152293`。随后单窗第二次真实 Brief 再次被原文检查拒绝：这次仅将末尾中文句号改成英文句点，空行修正规则按预期没有接纳它。该失败及计费仍保留在 `component-v26-hosted-loop-20260925-02/hxp-hosted-window/`。

不继续增加标点归一化规则。新提示 **2.32／2.33** 改为让模型在 `original_request` 返回精确的 `__TEXT2IFC_SAVED_REQUEST_V1__`，由宿主程序从保存的首条用户消息填入原文，然后照常进行完整 Brief 校验。该标记只在指定的新提示版本下解析；旧提示、其他文本改写以及拼错的标记不能借此通过。raw response 和替换前 JSON 保留；事实、参数、澄清记录不变。原有 2.30／2.31 与 schema 文件未改写，新提示已登记 SHA。新增测试先 8 failed／16 passed，更新后包含提示注册、编号、重复和失败保留的 78 项检查通过。第三次尝试使用配置 1.2，须先完成新的阶段内复验；前两次失败不改称成功。

新提示提交 `c0f27eb9`，随后 174 项阶段内复验通过，152.29 秒，无网络。单窗第三次真实 Brief 使用精确引用并达到 ready；Generator 输出 formal，IFC 编译／重开和语义几何检查通过，但终态为 **audit_blocked**。独立 Compare 1.2 测得 15 个窗体实体均在、拓扑一致、最大采样表面差 **8.284×10⁻⁸ mm**；墙体最大坐标差 **0.04686 mm**，缺失／多余／几何超差／关系差异均为零。墙尺寸测法与材料集合名称的报告限制同前，不宣称全字段一致。官方 IfcDiff 对门、窗各自的宿主场景都只标记墙有变化，没有标记门窗变化；这是附加检查，不是 1 mm 判据。

阻断来自旧动态检查：它强制填充构件相对开口使用 `[1,0,0]`，而该窗明确要求反向局部坐标。候选相对开口为 `[-1,0,0]`，组合父级变换后的世界位置与说明相符。修正以公开 Brief 的部件参数构造 IfcOpenShell 参考几何，比较明确要求的世界放置与候选完整父级变换在参考顶点上的位移，固定 ≤1 mm；不从候选自己的几何推导误差尺度。没有这类明确要求时保留旧规则，宿主和开口关系检查也保留。

另外，实际 Audit 提示只拿到失败总标志，没有收到动态检查的具体错误，导致模型报告总标志矛盾。已在实际发送的确定性结果中加入逐项 gate 详情，不更改旧提示文件。两处问题先复现为 11 failed／4 passed；修正后相关动态检查与 Audit bundle 等 47 项通过，四个完整门窗公开链（含反向坐标）及 Audit 上下文检查另 40 项通过。原始真实候选与原始 expected-facts 不变的离线重验中，四项动态检查全部通过；旧 audit_blocked 终态保留，配置 1.3 下的真实新尝试仍须阶段内复验。
