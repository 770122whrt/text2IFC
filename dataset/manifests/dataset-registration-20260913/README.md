# dataset 整理与登记结果（2026-09-13）

新增查看入口：[209 个已删除 IFC 的错误分类](deleted-ifc-failure-summary.md)／[逐文件错误明细](deleted-ifc-failure-details.csv)；[当前 324 个 IFC 按大小降序](ifc-size-desc.md)／[完整排序 CSV](ifc-size-desc.csv)。错误统计来自保留报告，大小排序已核对实际文件字节数。

按用户要求暂停 RVT 工作，保留选定的 50 份 ResBIM 源 RVT 及其 IFC，删除其他 RVT 和明确转换失败的 IFC。全 dataset 以来源、派生、配对、实验、Proof、基线和许可/划分分别登记，保持原有文件位置及消费者合同。

## 当前来源集合

- **324 个唯一 IFC**：原有 274 个登记源 IFC，加 50 个选定 ResBIM；合计 3,568,422,851 字节。
- **277 个 IFC2X3**；其余为 IFC4 30、IFC2X2_FINAL 12、IFC4X3_ADD2 3、IFC4X2 1、IFC4X3_RC2 1。
- 这些是文件与 schema 数量，不是独立建筑数量。训练 eligible 仍仅保留原有 25 份；本轮不修改 split、benchmark 或 Provider 准入。

[当前登记 CSV](active-ifc-register.csv) · [JSONL](active-ifc-register.jsonl) · [50 份 ResBIM 的完整来源选择记录](retained-resbim50.json) · [机器统计](registration-summary.json)

| 来源 ID | 当前文件数 |
|---|---:|
| asunisoft-ifc2x3-sdk | 1 |
| bim-whale-ifc-samples | 6 |
| bim2modelica | 5 |
| bimcollab-example | 9 |
| bimnet | 25 |
| buildingsmart-community | 74 |
| buildingsmart-official | 10 |
| duraark-public | 54 |
| geometrygym-ifc-examples | 1 |
| gni-bim-dataset | 16 |
| ifc-bench | 48 |
| ifctolbd-examples | 1 |
| kaggle-ifc-examples | 9 |
| kit-examples | 2 |
| opensourcebim-ifc-files | 1 |
| opensourcebim-testfiles | 5 |
| r-rijnbeek-ifc-webviewer | 1 |
| resbim | 50 |
| steptools-samples | 2 |
| thatopen-engine-web-ifc | 1 |
| thatopen-web-ifc-three | 1 |
| xbim-essentials-examples | 2 |

## 实际磁盘数量与当前集合不同

external 中还保存成功的历史转换版本和运行副本：**642 个物理 IFC 文件、379 个唯一内容哈希**，其中 324 个哈希属于当前来源集合，另外 55 个为储备。储备由未选入的 50 个 ResBIM、4 个其他来源补充样例，以及 INV-001 的一个早期通过技术检查的不同规范化版本组成；不把这些文件重新算成当前样本。逐路径见 [储备登记](reserve-ifc-files.json)。

整个 dataset 可读取范围：**17,833 个文件、8,348,766,250 字节（约 7.78 GiB）**，其中 IFC 文件 1066 个，包含来源、副本、派生、实验、损坏输入、修复输出和 Proof。不能把这个数字当作可训练建筑数量。压缩包内部成员未展开计数；本登记目录自身、`.git` 目录和 `__pycache__` 不计入快照。

| processed 分区 | 可读取文件数 | IFC 文件数 | 内容 |
|---|---:|---:|---|
| agent-demo | 1367 | 18 | 公共夹具与展示 |
| derived | 67 | 3 | 提取、BIM JSON 等派生数据 |
| experiments | 6195 | 123 | 历史实验、失败诊断和归档运行 |
| ifc-repair | 346 | 48 | Repair 输入、案例及隔离夹具（存在未读目录） |
| ifc-repair-runs | 394 | 27 | 当前运行器依赖的基线 |
| proof | 5649 | 203 | Generation/Repair 冻结成品与证据 |
| text2json | 141 | 2 | 训练评估配对、Gold 和 sidecar |

[清理前逐文件快照](before-files.jsonl) · [清理后逐文件快照](after-files.jsonl) · [分区统计及权限错误](after-summary.json)

## 删除执行与保留验证

已逐路径验证绝对位置、父目录无 reparse point、文件大小与 SHA-256，然后用 PowerShell `Remove-Item -LiteralPath` 删除普通文件，没有递归删除目录：

| 删除类别 | 文件数 |
|---|---:|
| 未选 RVT 与转换输入副本 | 266 |
| 有匹配失败报告的 IFC | 209 |
| 两个跨来源 RVT ZIP＋100 份 ResBIM 7z | 3 |
| 合计 | **478** |

删除字节 **3,205,179,582（约 2.99 GiB）**。这不是 266 个不同建筑；含重复 RVT 副本。五个 BIM Whale RVT 已得到用户另外明确确认，其六个 IFC 保留，本地 corpus 登记由 59 个文件更新为 54 个。其他 IFC 成功输出、所有运行日志及失败原因、原 metadata 和规范化说明保留。

原两份各 25 个 ResBIM 的 ZIP 仍作为所保留 50 个源文件的交接备份；没有删除 metadata 中的历史参考结果压缩包，压缩内容不属于当前模型库存。仅对本次已删除文件的空父目录另行核实后移除，见 [空目录记录](removed-empty-directories.json)。

[授权范围与逐文件删除清单](deletion-plan.json) · [实际删除日志](deletion-journal.jsonl) · [删除执行脚本](delete_reviewed_files.ps1)

保留的 **1066 个可读取 IFC 的 SHA-256 全部与清理前一致**。processed 可读取的 **14,160 个文件**均保持大小和修改时间不变，其中 IFC 另做内容哈希验证。未改写任何 Proof、split、benchmark 或模型几何。

项目已有 `audit_ifc_source_dataset.py` 对原 274 条 canonical 记录审计通过；`audit_dataset.py` 的 BIMNet、raw-files 和两个 corpus 清单审计通过，见 [原项目审计](project-dataset-audit.json)。该通用审计的 processed 部分运行在受限沙箱，目录统计口径与本登记的普通用户权限扫描不同，不用它替代下面的权限例外清单。

## 无法展开的 13 个目录

普通用户权限下仍拒绝访问的目录如下，均在 processed 中且不属于本次删除目标。未调整 ACL、未删除、未按空目录计数；全盘数量为可读取范围下界，external 清理范围不存在未读取目标。
- `dataset/processed/ifc-repair/cases/large-building-window-repair-001-deepseek-live-20260718-v1`
- `dataset/processed/ifc-repair/cases/large-building-window-repair-001-offline`
- `dataset/processed/ifc-repair/phase10.3-vvo-five-window-offline/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/advancedproject-door-preserve-opening/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/largebuilding-door-preserve-opening/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/largebuilding-generated-door-type/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/vvo-door-preserve-opening/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/vvo-five-door-preserve-opening/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/vvo-two-door-two-window-mixed/fixture`
- `dataset/processed/ifc-repair/phase11-door-offline/vvo-two-door-two-window-mixed/window-fixture`
- `dataset/processed/ifc-repair/phase12-acl-quarantine/.tmp-phase12-provenance-mixed/proof/mixed/door-window-beam-column/phase12-vvo-door-window-beam-column-atomic`
- `dataset/processed/ifc-repair/phase12-acl-quarantine/.tmp-phase12-provenance-single/proof/structural/single/phase12-d7n-beam-loadbearing`
- `dataset/processed/ifc-repair/phase12-acl-quarantine/proof/structural/single/phase12-d7n-beam-loadbearing`

最初沙箱将部分 Plan07 Proof 目录显示为缺失，普通用户只读检查已确认这些 Proof 仍存在。上面的 13 个条目是进一步扫描时发现的真实访问限制，不与 Git 的沙箱显示混为一谈。

## 后续使用

从 [dataset 总入口](../../README.md) 和当前 324 文件登记表选择数据。`external/RVT/current-dataset.json` 已写入 `paused_by_user`。旧 RVT 获取索引、86/136 模型统计、历史转换 manifest 和报告保留为历史，不应据此重新提取、补回或继续转换。当前只保留 50 份 ResBIM 的原始 RVT；本轮不再研究其他 RVT 的许可或转换途径。

没有提交或推送 Git；BIM Whale 子模块中的五个删除项是用户授权的有意状态。
