# IFC2Text 两项修复：v0.7 执行边界

沿用原双向说明方案。本轮只做异常墙轮廓提取/描述和源数据归属整理，不修改 text2IFC 的 Brief、Generator、Compiler、Schema、Gate 或比较容差。

## 已冻结的判断与动作

1. hxp 的“地板标高”包含34墙、7门、1楼板及5个空间；“标高 3”只包含3窗；“天花板标高”含1覆盖层。三窗只有一个containment，放置依附实际洞口，不能仅因宿主与记录层不同就判源IFC违法。按宿主层统一是合理的建模整理选择，不是已证明的标准缺陷修复。
2. 保留 dataset/external/bimnet/hxp.ifc。按本轮源组件整理方向，创建 hxp-host-normalized.ifc 工作副本，只调整已核查三窗的包含关系；实体、几何、Placement、GUID、材料和楼层记录不变。副本不替代旧实验真值，不重算旧结果后冒充LLM改善。
3. 新增 versioned wall-detail/0.7，只读取单个竖直拉伸体的真实闭合直线轮廓，转换为世界XY底面、底面Z、拉伸高度。普通矩形继续紧凑描述；非矩形或轴参数无法复现的轮廓单列。曲线、内洞截面、多实体/布尔/斜拉伸明确未支持，不用bbox补造。
4. 对原模型和整理副本都生成增强说明。沿用已有 ifc2text-compact-narrator.v0.6 进行导读整理，新增确定性轮廓说明版本，不覆盖旧Prompt。后续需要改系统Prompt时另立版本，本轮不改。
5. 用公开文本单独验证一面已揭示的W013：真实Brief一次、真实Generator一次，然后确定性编译和比较。范围是扣洞前单墙，源IFC和evaluator-only文件不得传给模型。此实验不评估材料、洞口、房间和全楼验收，也不称为新的独立建筑。

## 验收

- 异常截面完整写出并保持mm一位小数；完整原事实不变。矩形、凹口同bbox、旋转/平移、斜拉伸负例、无法提取与禁止覆盖是冻结回归族。
- 整理副本重开后，除包含关系外的所有IFC实体序列化定义必须逐项相同；非目标构件归属不变，空包含关系清理但楼层不删除。
- 新运行先提交实现/配置，再按当前范围复验。复用未改动text2IFC的祖先准入及故障注入，不运行Full Preflight。
- 支付预算仍为累计200万tokens、写作26次、重建侧12次；起点写作19、重建侧10，已占额1283761。最多新增1次写作和2次重建侧调用；失败保留并计入，不自动增加额度。
- 新单墙比较同时记录形状类型、轮廓Hausdorff、包围盒和Z范围；20mm原容差不改，并单独报告实际小数误差。模型不能完成时保留失败，不直填正确JSON代替。

标准核查来源：buildingSMART IFC2x3 TC1 IfcWindow，分别定义FillsVoids、ContainedInStructure和PlacementRelTo；并不以宿主同层差异单独证明源记录错误。
https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindow.htm

本轮产物：dataset/processed/experiments/ifc2text-wall-recovery-20260921-v07/。结果以实际报告为准，不预填成功。

## 首次导读复核后的同范围修正

52项离线验证通过后，首次v0.6导读把已有M11材料的覆盖层所在楼层说成“材料关联亦未确认”。已保存原响应和拒绝记录，暂停付费并回到离线。全局材料摘要不足以支持每层材料判断，因此新增IFC2Text专属 narrator.v0.7：楼层导读只说空间和构件，材料事实继续由各层既有确定性明细承担。追加对应失败用例及旧Prompt不变检查。Brief/Generator/Compiler及其Prompt仍不变。重新提交与针对性验证后，仅再用1次写作（仍在26次总上限内）替代拒绝稿；重建侧仍最多2次。原数字明细、轮廓数据和源文件均不改。
