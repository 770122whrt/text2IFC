# Repair 人工检查

真实 DeepSeek 经公共 RepairAPI 完成实例属性修复，发布成功；独立重读核对通过。状态为 **pending_human_review**，尚未安装 accepted Proof。

## 原始、破坏、修复三份 IFC

| 角色 | IFC | 可交互视图 |
|---|---|---|
| 原始 dataset 文件 | [01-original.ifc](01-original.ifc) | [原始视图](review-original.html) |
| 删除一条属性关联后，实际输入 | [02-damaged.ifc](02-damaged.ifc) | [破坏视图](review-damaged.html) |
| 真实 RepairAPI 发布的完整输出 | [03-repaired.ifc](03-repaired.ifc) | [修复视图](review-repaired.html) |

来源为 `dataset/external/bimnet/vvo.ifc`。original 的 `private_ground_truth` 角色在执行前冻结，仅供执行后评估；没有向 Provider 提供 pristine 原文件、删除关系的身份或 mutation 配方。

[实际公共请求](request.txt)指定目标墙 `2CsmzAChHF6O6maGXlo6PS`（基本墙:240:223174）的实例 Pset_WallCommon。只删除了一条 IfcRelDefinesByProperties；保留了原属性集和所有几何。公开请求值来自 damaged IFC 中尚存的独立属性集，见 [公开输入事实](public-input-facts.json)。

| 直接实例属性 | 原始 | damaged | repaired | IFC 类型 |
|---|---|---|---|---|
| Reference | "240" | 此直接关联缺失 | "240" | IfcIdentifier |
| IsExternal | true | 此直接关联缺失 | true | IfcBoolean |
| ExtendToStructure | false | 此直接关联缺失 | false | IfcBoolean |
| LoadBearing | false | 此直接关联缺失 | false | IfcBoolean |

注意：损坏的是**实例直接关联**；Type 中已有的继承属性仍可能显示部分值。请查看 DirectProperties，不能只看 EffectiveProperties。[定位原始目标](review-original.html#2CsmzAChHF6O6maGXlo6PS)／[定位损坏目标](review-damaged.html#2CsmzAChHF6O6maGXlo6PS)／[定位修复目标](review-repaired.html#2CsmzAChHF6O6maGXlo6PS)。

## 独立验证及视觉检查

- 三份 IFC 均可重读；每份 152 个可见构件均可网格化。三份的世界网格、有效样式完全相同。
- repaired 相对 damaged 没有修改或删除任何既有 STEP 实体，只新增 4 个属性值、1 个属性集和 1 条关联。Type、材料、样式、几何及其他对象保留。
- 原始 dataset 文件与 damaged 输入哈希未变。恢复的是同值、同类型的合法属性附件，未伪造恢复删除关系的原 GlobalId。
- 实際三维整体视图已检查，修复前后外观相同；本次不美化或升级 Repair 门窗。[整体图](overall-depth.png)。
- [独立核对明细](independent-review.json)；[真实公共结果](result-live-04.json)；[机器评估](runtime-live-04/runs/repair-vvo-property-relation-live-04/.terminal-bundles/6395e2e7aa4c4e3c86e42a9146133e42/evaluation/public-evaluation.json)。

公共评估的 L1 与 preservation 通过；其 conditional L2 属性项为 not_required，不能拿该标签证明请求值正确。本案请求值由独立重读另行逐项核对。该语义评估适用于冻结三元组，不宣称运行了整个 IFCCompare 基准或系统能力评测。

## Attempts 与保留边界

成功的 live-04 有 2 次真实调用（Intent、ChangeSet），模型 deepseek-v4-flash。此前 attempt-02 也有 2 次真实调用，但执行包装器缺少 Windows multiprocessing 主入口保护，校验子进程失败，未发布成功 IFC；其原始响应、诊断 IFC 和失败结果全部保留。offline-03 是明确标记的 fake Provider 回归，不能算真实调用。startup-01 的非法 run-id 在网络前失败，见 startup-01-correction.json。

人工确认三元组和属性后，仍须执行适用 curator／人读格式检查，才能安装到 processed/proof；本页不是 accepted 标记。
