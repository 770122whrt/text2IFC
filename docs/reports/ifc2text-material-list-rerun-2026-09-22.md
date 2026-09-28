# IFC2Text 材料清单修复与整栋续跑

## 为什么刚才没有继续生成 IFC

新一轮 IFC2Text 写作已完成。随后真实 Brief 读到了 D003–D006 的“金属漆_冷灰、木材”和 D007 的“抛光不锈钢、玻璃、白油漆”，但旧中间格式没有材料清单，因此返回 `draft_required`。当时没有执行新的 Generator，也没有产生新的重建 IFC。

材料清单就是“这扇门使用木材和金属漆”这样的名称集合。原模型没有说各材料有多厚、前后如何排列，也没有说哪种材料对应门框或门板。与之不同，分层材料会明确“20 mm 抹灰、200 mm 砖墙、20 mm 抹灰”。此次支持前一种表达，不能自行把它变成后一种。

输入已经提供了材料名称。阻断的根因是 text2IFC 中间合同缺少表达方式，不是 IFC2Text 漏写，也不是 LLM 没读懂这些名称。

## 修复内容

新增 BIM JSON 2.5 的 `material_list`，编译为 `IfcMaterialList`；重新打开 IFC 后核对名称、数量和关联。Brief 2.8 及对应生成 Prompt 传递这一要求，并从 Brief 独立检查生成结果，避免生成器漏掉一种材料却自行通过。旧版本不改写。

Compare 1.1 按最新决定使用 **≤1 mm 接受、>1 mm 计差异**。位置、尺寸、楼层标高、材料层厚和轮廓距离采用这一线性规则；材料名称缺失仍属于内容差异。历史 Compare 1.0 的 0.1 mm 报告保留，不改写。

## 旧几何差异的来源

旧整栋响应加上 W013 离线替换后，0.1 mm 下有 29 个构件超差。用同一组未舍入测量重新按 1 mm 判断后剩 **23 个**；这不是新生成的结果。

| 类别 | 数量 | 已定位的原因 |
|---|---:|---|
| 其他特殊墙 | 10 | 旧说明没有完整斜切轮廓，生成器用了矩形；新版描述已给出轮廓，仍须用真实生成验证 |
| 特殊开口 | 3 | 旧说明主要给包围盒，未完整表达实际切割形状和方向 |
| 门窗 | 10 | 简化模板默认框深 60 mm；部分源构件还有非对称偏移、突出开口范围的几何或模板上限问题 |
| 微小坐标误差 | 6（已接受） | 约 0.104–0.139 mm，涉及坐标舍入和局部／全局变换；按 1 mm 规则不再计错 |

材料 5 项独立于上述几何数量。完整逐构件追踪见[归因报告](../../dataset/processed/experiments/ifc2text-rerun-20260922/attribution/REPORT.md)，同测量重评分见[记录](../../dataset/processed/experiments/ifc2text-rerun-20260922/historical-rescore-1mm/summary.json)。

## 续跑状态

离线阶段检查 **435 项通过，0 失败、0 跳过**，网络访问为零，耗时 542.40 秒。覆盖完整公共流程、材料遗漏反例、版本兼容、源文件不变和 1 mm 边界；[阶段准入与精确测试命令](../../dataset/processed/experiments/ifc2text-rerun-20260922/material-list-continuation/validation/admission.json)保留完整记录。这是本阶段的离线工程验证，不是系统能力提升证据，也没有运行仓库 Full Preflight。

随后用同一份说明完成两次真实调用：Brief 2.8 返回 `ready`，Generator 返回通过 2.5 合同验证的整栋候选。D003–D007 的材料清单在 Brief 和候选中逐项存在。首轮阻断结果保留在[原始运行](../../dataset/processed/experiments/ifc2text-rerun-20260922/brief-result.json)；新运行使用独立的 `material-list-continuation/` 目录。

真实流程并未取得最终验收，暴露出两个确定性缺陷：

- 候选的 `IfcProject` 未提供名称；中间格式允许省略，但 IFC2X3 的 WR31 要求名称存在。编译器现使用已有技术编号作为缺省名称，不编造建筑项目标题，也不改写明确提供的名称。先复现 2 失败／1 通过，修复后的项目名称与材料编译测试 23 项通过。
- Brief 楼层 `S01` 与候选 `storey-S01` 表示同一层，但检查器未统一这两种技术编号，产生 53 条归属误报。修复后，同一候选重评分为 0；将一面墙真的归到 S02，仍检出错误。相关检查及公开路线回归 113 项通过。随后补齐空间几何检查的同一编号映射：5 条空间楼层误报归零，实际放到 S02 的负例仍失败，相关测试 110 项通过。测试组有重叠，不累加；证据见[楼层核查](../../dataset/processed/experiments/ifc2text-material-list-20260922/storey-identity-diagnosis/comparison.json)与[空间核查](../../dataset/processed/experiments/ifc2text-material-list-20260922/storey-identity-diagnosis/geometry-rescore.json)。

Audit 在发送请求前被累计预算挡住：按 UTF-8 字节加最大输出计算，需预留 308,222 token，剩余 303,653，相差 4,569。没有发生 Audit 网络请求。当前 Provider 包装器把这个 `GoalStopped` 误分类为连接错误，报告保留原错误，同时在这里明确实际原因；没有扩大预算或重复生成。累计实际使用 1,696,347 token。后续应单独设置 Audit 输出额度并修正阻断分类。

## 修复后，原样重放这份真实候选

源 IFC、说明、真实 Brief、Generator 候选和旧 ExpectedFacts 的字节均未修改。只以修复后的编译器重放，在新目录输出诊断 IFC。**这属于离线重放真实响应，不是新的真实生成成功或 Audit 通过。**

| 检查 | 结果 |
|---|---|
| IFC 编译、重新打开 | 通过 |
| 五扇门的材料清单 | 全部逐项一致，实际为 `IfcMaterialList` |
| 已比较构件 | 匹配 66，缺失 0，多余 0 |
| 材料内容差异 | **0** |
| 关系与楼层标高差异 | 0 |
| 1 mm 下几何差异 | **14 个构件** |

14 个几何差异为：7 扇门、3 扇窗、O001／O003／O005 三个特殊开口，以及 W005 扣洞后的墙形。W005 扣洞前的轮廓差约 0.051 mm，已通过；扣洞后的中部截面差约 65 mm，说明后续应沿开口切割继续排查。不要继续归因于墙体外轮廓。其余墙、空间、楼板和覆盖层在本比较器已评估指标上通过；34 条墙本征尺寸仍因测量方式不同未评估，完整表面等价也没有得到证明。

另有 36 项材料关联元数据不同，主要是材料层组的原名称被描述中的 `M01` 等编号替代；楼板、覆盖层还去除了 `<Unnamed>` 前的空格。材料名称／层厚内容按既定比较规则一致，不代表 IFC 的全部材料字段逐字相同。

完整材料核验及输入哈希见[重放汇总](../../dataset/processed/experiments/ifc2text-rerun-20260922/material-list-continuation/offline-replay/summary.json)，逐构件测量见[Compare 1.1](../../dataset/processed/experiments/ifc2text-rerun-20260922/material-list-continuation/offline-replay/compare-v1.1.json)。

最后在新的目录重放公共确定性检查，合同、构件数量、楼层归属、开洞关系、语义、编译重开及几何要求等 **10 项检查全部通过**，保留先前失败重放。见[公共检查汇总](../../dataset/processed/experiments/ifc2text-rerun-20260922/material-list-continuation/offline-public-gates-v2/offline-summary.json)。这里的几何检查证明输出满足 Brief 已表达并被检查的要求；源 IFC 的独立 Compare 仍有上述 14 个差异。没有把前者当成与原模型完全一致，也没有补造 Audit。

材料清单这一项已完成。下一步应先处理门窗的实体框深／偏移，以及特殊开口的切割轮廓和方向；这比继续调整已固定的 1 mm 容差更直接。材料层组原名称的保留和 Audit 的额度／错误分类可以分别修订。项目名称与楼层修复发生在真实运行之后；435 项阶段准入记录对应当时的代码，后续修复使用以上针对性回归与公共离线重放，尚未重新发起真实调用。
