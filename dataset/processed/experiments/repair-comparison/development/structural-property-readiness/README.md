# B 结构与属性：开发检查记录

2026-10-08。本页保存011～020重制过程中发现的共性缺陷与离线接线证据，不是新题模型成绩、正式准入或已接受Repair Proof。[当前真实实验表](../../current/README.md)仍为此前B001～010的9/10；原失败不覆盖。

|检查范围|有效红例与最终结果|证据|
|---|---|---|
|梁柱多containment|合法多关系被误拒；46项家族通过，62项旧回归通过|[报告](b-multi-containment-validation.json) · [完整证据](b-multi-containment-evidence.zip)|
|共享Pset写入|4/18红例出现重复应用登记；一行类名排除修复后18项全通过，61项相关回归通过|[报告](b-shared-pset-validation.json) · [完整证据](b-shared-pset-evidence.zip)|
|B属性Runtime接线|12项接线、11项旧B回归通过；真实Linux的7条基本路径及1条共享属性路径通过|[节点报告](b-property-runtime-result.json) · [完整证据](b-property-runtime-evidence.zip)|
|题包制备工具|020原生删除wrapper失效、混合版本及指纹前缀错误均保留；首层新候选和整题答后操作检查通过|[制题报告](preparation-validation.json) · [制题证据](preparation-evidence.zip)|

多containment修复检查全部既有关系的冲突，为新构件建立独立关系，不改原成员。共享Pset修复将`copy_deep`排除项从属性名`OwnerHistory`改为IFC类名`IfcOwnerHistory`，保留原元数据图；只分离目标实例，不改Type或其他构件。修复在通用机制，无formal编号兜底。

属性Runtime复用产品已有BGE/Qdrant链路，实际索引包含1832条标准记录中的488条可写单值属性，向量维度1024。假HTTP覆盖英文、中文、持久澄清恢复、非法值、截断、混合补窗＋属性、写后回滚，以及修复后的共享Pset。成功结果另外经过容器schema和宿主IfcOpenShell0.8.5 EXPRESS检查，均0诊断。生产检查未放宽；测试中的容器EXPRESS依赖缺失、无效假响应、真实共享复制拒绝及工具环境失败均按原类别保留。

安装由用户明确批准。独立镜像`text2ifc/repair-tools:py312-ifc085-property-v1`构建400.078秒，固定CPU依赖；模型缓存只读复用，没有下载新模型。测试无网络、无真实密钥、无付费Provider，任务状态独立；测试容器已退出。第一次独立索引构建和模型加载计入正式B活动耗时，warm离线测试的时延不代表cold时延。原生持久澄清恢复已验，属性状态卷导出/导入尚未单独进行原生检查。

ZIP保存原日志、失败、输入和输出、源码快照及成员清单；JSON报告保留原路径，由包内MANIFEST映射。模型权重不打包，不伪造未保存的历史源码。这里的测试数不作为能力指标。每题确定性操作支持见[题包入口](../../../../ifc-repair/repair-comparison/formal/README.md)及各题PIPELINE-CHECK；新题仍须用户审阅、扩展评分与当前阶段四组准入后才可实验。

020制题的原生退出来自删除后的IFC实体wrapper使用，随后两次混合检查卡点来自临时helper的schema版本和指纹前缀；没有据此认定源IFC坏、产品修复失败或模型失败。首次选中的高层窗挂在首层跨层墙上，仅作为支持边界筛选负证据保留，未运行完整混合探针。新目标为同源中窗与墙都归属首层的实例，保留洞底标高澄清；019和020的完整答后绑定操作、原生格式及原子回滚检查已通过，自包含证据保存在各题private/offline-support中。没有新题模型调用或四组正式评分。
