# text2IFC Source IFC 目录

最新报告：[2026-09-26建筑扩充与修复](_checks/ifc-expand-20260926-v8/REPORT.md)。可用集 196 份 IFC2X3、202 份小于 10 MB；34 份 IFC2X3 建筑专业候选，小型优先描述候选 16 份；新增8份、修复采用5份，技术检查与许可分列。母族/变体后训练方案仅讨论，未自动实施。

Generation 论文与实验选材请看 [外部数据集说明与可用目录](GENERATION_DATASETS.md)：沿用现有统计，区分本地可用 IFC、完整生成任务和待核实的外部基准。

当前入口为 [IFC文件资产集合](IFC_DATASET.md)：**387 条来源记录、386 份唯一首选内容；可用 224、可修复 0、当前无已验证自动修复方案 162**。核心场景139份（132 IFC2X3＋7 IFC4），核心全部小于10 MB。[全部登记 CSV](ifc-asset-register.csv)／[JSONL](ifc-asset-register.jsonl)和核心登记直接位于external，模型按来源保留目录。

此前 274 份原有 IFC＋50 份 ResBIM 的 [324 份清理登记](../manifests/dataset-registration-20260913/active-ifc-register.csv)是扩充前的历史基线。当前资产、历史储备、运行副本与 Proof 使用不同统计口径；规范化副本不计为独立新模型。

模型来源子目录包括 BIMNet、buildingSMART、IFC-Bench、BIM Whale、KIT、STEP Tools 和已登记的其他公开示例来源。`_checks/` 是外部数据检查及交接材料，不作为模型来源或已准入样本计数。

历史入口：[两个 ZIP 的检查、迁移和后续修复交接](_checks/incoming-ifc-audit-20260910/README.md)。其中 ResBIM 曾包含 50 份 IFC，另一包曾包含 29 份转换 IFC 加 1 份 Circular 原有示例。用户于 2026-09-13 确认已因 IFC 不合格主动删除 `Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip` 和 `ResBIM_IFC2X3_50.zip`；历史检查记录保留，不计为当前可用模型，不自动补回。

RVT 工作已按用户要求暂停：[RVT/](RVT/README.md) 只保留选定的 50 份 ResBIM 源 RVT，并以对应 50 份 IFC 为当前集合。其他 RVT、输入副本、有失败报告对应的 IFC 和未选模型压缩包已按逐路径清单删除；许可核实、失败报告及删除记录保留，不能从历史 acquisition 清单推定模型仍存在。

IFC-bench：用户已于 2026-09-10 确认主动排除 `projects/sixty5/arc.ifc` 与 `projects/sixty5/plumbing.ifc` 两份过大文件。本地保留 48 份 IFC，其中 25 份 IFC2X3；不将两份排除项当作意外丢失，也不擅自补回。

- [来源级 authority](../manifests/ifc-sources.json)
- [canonical 文件 authority](../manifests/ifc-files.jsonl)
- [来源说明与许可材料](../sources/CATALOG.md)
- [获取记录](../manifests/acquisitions/)

BIMNet 已迁到 `bimnet/`，原 train/test 物理目录不再作为 canonical 位置；split 仍由 `dataset/splits/bimnet-scene-splits.json` 管理。

`bim-whale-ifc-samples/` 与 `ifc-bench/` 是独立 Git 子模块；子模块内未提交工作由其所属任务管理，不能从父仓库清理时擅自恢复、删除或提交。

2026-09-13 用户明确批准删除 BIM Whale 的五份源 RVT，保留六份 IFC；本地清单已同步为 54 个文件。子模块因此显示五个有意删除项，不应运行 update/restore 自动补回。详见 [删除日志](../manifests/dataset-registration-20260913/deletion-journal.jsonl)。

Source 文件、同一建筑的 discipline / schema variants、下载候选及回归 fixture 有不同职责。只在逐文件相同且 provenance 已保留时去除真正重复；不把公共下载等同训练许可。旧 raw-files / external-corpora manifests 仍有兼容消费者，暂时保留。

已跟踪 IFC 使用 Git LFS。模型缓存、依赖与外部数据不属于普通 pytest 缓存。
