# text2IFC dataset 总入口

当前 IFC 文件资产入口为 [external/IFC_DATASET.md](external/IFC_DATASET.md)（2026-09-26）：**387 条来源记录、386 份唯一首选内容；可用 224、可修复 0、当前无已验证自动修复方案 162**。可用集 196 份 IFC2X3、202 份小于 10 MB；34 份 IFC2X3 建筑专业候选，小型优先描述候选 16 份。完整执行结果和母族/变体讨论见[本轮报告](external/_checks/ifc-expand-20260926-v8/REPORT.md)。文件数不等于独立建筑数；139核心场景和50份ResBIM保持不变。

直接查看 [三分类总表 CSV](external/ifc-condition-register.csv)；[全部资产 CSV](external/ifc-asset-register.csv)／[JSONL](external/ifc-asset-register.jsonl)，或 [核心场景 CSV](external/ifc-core-register.csv)／[JSONL](external/ifc-core-register.jsonl)。登记保留稳定 ID、路径、哈希、schema、来源许可、检查状态、保守建筑分组及规范化副本的原件引用。原有 split、benchmark 和 Proof 合同保持不变。

此前 [324 份清理登记 CSV](manifests/dataset-registration-20260913/active-ifc-register.csv)／[JSONL](manifests/dataset-registration-20260913/active-ifc-register.jsonl)是本轮扩充前的基线：原 274 份＋50 份 ResBIM，277 份 IFC2X3。旧统计与清理证据保留，不代表全部通过本次严格检查。

便于挑选：[按文件大小从大到小排序](manifests/dataset-registration-20260913/ifc-size-desc.md)／[完整排序 CSV](manifests/dataset-registration-20260913/ifc-size-desc.csv)。清理原因见 [209 个失败 IFC 的统计](manifests/dataset-registration-20260913/deleted-ifc-failure-summary.md)。

| 内容 | 入口 | 登记及使用方式 |
|---|---|---|
| 当前来源 IFC | [external](external/IFC_DATASET.md) | 387 个来源资产；139 个核心场景，派生副本不重复计数 |
| 选定 ResBIM | [50 个 IFC](external/RVT/IFC/dataset-resbim50-20260913/ResBIM/) | 合成住宅单元；严格检查通过，未建立完整建筑或训练划分准入 |
| 来源、许可与论文 | [sources](sources/CATALOG.md) | 保留各来源用途依据；公开下载不等于训练许可 |
| 正式及专项清单 | [manifests](manifests/README.md) | 原 canonical IFC、兼容清单、benchmark 与新总登记表各有明确范围 |
| 场景划分 | [splits/bimnet-scene-splits.json](splits/bimnet-scene-splits.json) | 保持既有 scene-family 划分；未自动给 ResBIM 分 train/test |
| 派生 BIM JSON、提取结果 | [processed/derived](processed/derived/README.md) | 原始输入的派生产物，不重复计为新建筑 |
| 文本训练与评估数据 | [processed/text2json](processed/text2json/README.md) | 保持配对、Gold、sidecar 和公私边界 |
| Generation/Repair 成品与证据 | [processed/proof](processed/proof/README.md) | 保持已验收文件与冻结 manifest；不当作失败转换清理 |
| 实验与历史运行 | [processed/experiments](processed/experiments/README.md) | 独立于来源模型统计；保留真实尝试与诊断 |
| 活动离线夹具、运行基线 | [processed](processed/README.md) | agent-demo、ifc-repair、ifc-repair-runs 保留消费者依赖 |
| BIMNet 上游资料说明 | [data_organization.md](data_organization.md) | 上游历史布局说明；不是当前 text2IFC 物理结构 |

## RVT 清理阶段的历史结果和统计边界

已暂停 RVT 扩充、统计研究及转换，只保留选定的 50 份 ResBIM 源 RVT。按用户要求删除其他 RVT 和转换输入副本共 266 个、有匹配失败报告的 IFC 共 209 个，以及两个跨来源 RVT ZIP 和一个 100 份 ResBIM 7z。BIM Whale 的五份 RVT 已按用户单独确认删除，其六份 IFC 保留。

成功转换但未选入当前集合的文件仍作为历史储备；运行副本、旧合集、参考 ZIP、变体和 Proof 文件不重复加入当时的 324 份来源基线。原 274 份 canonical 登记完整性审计通过，哈希保持不变；这项登记审计不等于所有文件解析或 EXPRESS 检查通过。50 份 ResBIM 的来源、验证依据和抽样视觉结果仍可追溯；后续 IFC 资产审查没有恢复 RVT 转换。

全目录登记和按用途统计见 [本轮整理登记报告](manifests/dataset-registration-20260913/README.md)。普通用户权限仍无法展开的 13 个 processed 隔离目录单列，不把它们视为空目录或已丢失；因此全盘文件总数和字节数是可读取范围快照。external 的本次删除范围已完整核对。

新来源总表是文件库存，不替代训练准入。原记录中训练 eligible 的仍为 25 份 BIMNet；ResBIM 的来源许可支持训练用途，但没有自动生成场景独立划分或设定训练 eligible。
