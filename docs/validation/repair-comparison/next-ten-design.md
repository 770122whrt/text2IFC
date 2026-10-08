# 后十题的结构与属性覆盖建议

2026-10-08：用户已认可重制方向，要求先核对当前Pipeline，再生成损坏IFC、自然请求和REVIEW，由用户在查看器检查，通过后才实验。前十题保留；011～020已原位替换，后十旧题及运行由提交3fbae1d8和独立历史备份保留。新题为pending_human_review，不继承旧技术接受状态，没有新题模型调用。统一材料见[二十题审阅入口](../../../dataset/processed/ifc-repair/repair-comparison/formal/README.md)。

|拟题号|损伤与公开修复意图|关键验收|
|---|---|---|
|011|删掉一根水平矩形梁，请按位置、中心轴两端与截面补回|轴端点、矩形截面、Type、楼层归属|
|012|删掉两根不同位置的水平梁，请分别补回|2/2、没有重复补建或误改原梁|
|013|删掉一根方柱，请按柱脚、柱顶和截面补回|高度、轴线、方形截面、柱脚楼层|
|014|删掉一根非方矩形柱，请恢复；可缺少必要截面朝向形成澄清|宽深与朝向分别核验，不按包围盒猜朝向|
|015|已有梁的承载属性被误改或删除，请恢复明确值|Pset_BeamCommon.LoadBearing、Boolean类型、实例作用域|
|016|已有柱的承载属性被误改或删除，请恢复明确值|Pset_ColumnCommon.LoadBearing、同Type其他柱不变|
|017|已有门的真实规格标记“88.5 x 2.26”被误改，请恢复原文字|Pset_DoorCommon.Reference、IfcIdentifier类型、几何不变|
|018|已有墙的外墙属性由true误改为false，请恢复外墙标记|Pset_WallCommon.IsExternal、只改目标实例；本源没有共享Pset|
|019|一梁一柱被删除，请补回并恢复明确属性|几何、属性、关系全部正确；整题原子发布|
|020|删除窗及洞口、恢复墙面，同时把现存外门标记误改为false；重新开洞补窗并修正属性|跨操作族定位，补窗与Pset_DoorCommon.IsExternal分别验收|

公开请求继续用自然语言方位、楼层、几何位置定位，不出现Name或GUID；受损原件Name写在私有REVIEW。尺寸、位置、必要事实、损伤与保全由技术检查核对，用户主要检查显示和题意。不能从几何推导的承载性等应由请求或预审答复卡明确，不从私有G给运行时补答案。保留已认可的损伤等级，以及格式正确、schema＋EXPRESS通过的D。属性题优先损伤源里真实存在的值；占位耐火文本、自闭值缺失和源里不存在的共享Pset，不冒充真实损伤，实际属性项目将在材料中据实调整后交用户审核。

当前实际支持的结构范围是水平直梁、竖直柱和矩形截面；梁柱操作用于补建，不用于移动或修改现有构件尺寸。柱归属柱脚楼层，结构参数使用楼层局部坐标。制题必须核对世界坐标到楼层局部坐标的换算，避免007的高度基准错误。斜梁、斜柱、曲线、圆/I/H/变截面和自动逐层拆柱暂不纳入。属性操作仅改适用标准单值Pset的实例属性，不改共享Type，也不把任意IFC字段或Quantity当作已支持范围。

接线完成情况与下一步：

1. 扩展题包及独立评分。当前`formal_batch.py`只制作门窗损伤，`formal_scoring.py`只接受window/door目标；梁柱和纯属性题不能直接交给该评分器。新增题卡应固定目标、位置、截面、属性值/类型/单位、关系分母及允许变化。纯属性题的新增数量指标不适用，不人为记满分。
2. 接通B原有自然语言属性Runtime。`isolated_b.py`已以可选配置注入产品已有`property_knowledge_runtime`，复用Stage 1.5的BGE/Qdrant检索，没有添加硬编码中文别名；未启用时保持原B行为。独立镜像已构建，真实Linux和假Provider的7条基本路径及1条共享属性路径已通过。单独绑定写回、通用假Provider链路和每道题真实模型结果分别记录。
3. 实际选定十个新许可源：011 GNI203、012 HTSM Test model、013 GNI4_structure、014 GNI123、015 GNI1_structure、016 IFC-Bench sixty5 str、017 GNI39、018 GNI128、019 GNI174、020 GNI148，均为CC-BY-4.0。选择源里真实存在的矩形梁柱和标准实例属性，没有先造构件再删掉。与前十题无资产或文件哈希重合；同来源族不等于统计独立建筑。
4. 结构与属性操作支持、通用属性Runtime的假模型路径及019/020整题答后绑定检查已完成。用户审阅后，仍需扩展统一评分并为新题包建立四组阶段准入、预算与冻结记录。后十题新设计不混入旧门窗任务分母，实际人审状态据实记录。

本轮核对证据：现有梁柱应用、实例属性及Stage1.5离线家族25项通过。十份新题的G/D schema＋EXPRESS均0诊断。五份结构草案经现有公开runner完成绑定、apply、重开、生产评价和保全，R实体网格独立匹配G；这是离线几何支持证据，未证明自然语言完整运行。GNI203原先被合法多containment误拒；已冻结红例，最小修复后46项家族及62项旧回归通过，本题独立答后操作检查通过。属性源里的真实布尔值和规格文字逐项登记，属性草案通过实例写回、重开与几何保全。019梁柱补建＋两项承重属性、020补窗＋门外门属性均经标准registry、manifest和binder，在各自一个原子ChangeSet中通过，第二操作失败时回滚且不发布；结果原生诊断均0，020还独立逐项核对933个既有对象及Type的属性，仅目标门的IsExternal改变。GNI203/174的原Axis在梁上沿，请求以实际实体端面中心为准；014源Name写450×450而真实网格200×450，REVIEW明确这一差异。

用户已确认保留三道必要澄清题：014柱截面的短边/长边朝向，019梁和柱各自的承重布尔值，020窗洞下沿标高。公开初始请求不包含这些答案；事实在制题前写入私有卡，只按实际模型问题回复相关事实，不替模型提问、不整张卡注入、不临时从G补答案。

用户已批准属性运行环境安装与离线验收。独立`text2ifc/repair-tools:py312-ifc085-property-v1`镜像已从既有v2构建成功，耗时400.078秒，固定qdrant-client1.18.0、sentence-transformers5.6.1、transformers5.14.1与CPU torch2.9.0；仅从官方PyPI/PyTorch下载包，没有下载新模型。只读挂载现有4.59GB BAAI-bge-m3缓存，使用独立可写Qdrant任务缓存，不覆盖旧镜像或旧状态。正式Dockerfile位于[scripts/ifc_repair/repair_comparison/property-runtime.Dockerfile](../../../scripts/ifc_repair/repair_comparison/property-runtime.Dockerfile)。

构建遵守4CPU/8GiB、60分钟及新增20GiB停止阈值。真实Linux的BGE/Qdrant＋假Provider已通过7条基本路径和1条共享属性路径，包含中文、持久澄清恢复、非法值、截断、混合和原子回滚；测试无网络，不读取真实模型密钥、不调用付费模型。共享Pset复制发现一处通用格式缺陷，`copy_deep`的exclude须使用IFC类名`IfcOwnerHistory`；最小一行修复后18项故障家族及61项相关回归通过，原native失败保留，新节点复验通过。属性状态卷导出/导入尚未另做原生验证，正式准入未建立。首次独立索引构建会计入B任务活动时间，离线复用标准索引的warm测试不代表正式cold时延；预算和时间口径在后续冻结时决定。

020先从GNI131开始，制题进程原生退出；更换GNI148后，阶段日志表明G/D格式和网格收集完成后仍异常。检查发现私有制题helper在删除窗后继续使用其native wrapper（包括隐式真假判断和Name读取）；已改为删除前保存GUID/Name文字，删除后只用普通布尔值和快照。这些失败属于制题工具记录，不能据此认定源IFC有格式或显示缺陷，也不是B模型修复失败。GNI148首次选中的4.6米楼层窗挂在首层跨层墙上，触及B已知归属限制；保留该候选筛选负证据，改选同源中窗与墙均归属首层的目标，必要窗洞底标高仍留作澄清，不为此扩展跨层支持。完整混合检查另修正了临时helper的现有schema协商与指纹前缀用法，原失败保留，没有修改生产schema或放宽检查。最终403.703秒的答后绑定检查通过，不能记作模型耗时或自然澄清成功。

代码与合同依据：默认操作见[注册表](../../../src/text2ifc_ifc_repair/operations/__init__.py)，边界见[梁](../../../src/text2ifc_ifc_repair/operations/beam.py)、[柱](../../../src/text2ifc_ifc_repair/operations/column.py)、[实例属性](../../../src/text2ifc_ifc_repair/operations/occurrence_property.py)及[Phase12 SPEC](../../../.planning/phases/12-beam-and-column-operations/12-SPEC.md)。接线见[隔离B](../../../scripts/ifc_repair/repair_comparison/isolated_b.py)和[API属性分支](../../../src/text2ifc_ifc_repair/api.py)。只运行本轮改动及草案所需的聚焦离线检查，没有Full Preflight、新题付费调用或能力提升声明。浏览器桥接不可用，VIEW静态脚本与网格数据检查不代替usBIM实际查看。
