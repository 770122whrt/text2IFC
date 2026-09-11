# text2IFC Source IFC 目录

模型来源子目录包括 BIMNet、buildingSMART、IFC-Bench、BIM Whale、KIT、STEP Tools 和已登记的其他公开示例来源。`_checks/` 是外部数据检查及交接材料，不作为模型来源或已准入样本计数。

本批入口：[两个 ZIP 的检查、迁移和后续修复交接](_checks/incoming-ifc-audit-20260910/README.md)。两个原 ZIP 仍在本目录，未解压落盘或修改；其中 ResBIM 是 50 份 IFC，另一包是 29 份转换 IFC 加 1 份 Circular 原有示例。

IFC-bench：用户已于 2026-09-10 确认主动排除 `projects/sixty5/arc.ifc` 与 `projects/sixty5/plumbing.ifc` 两份过大文件。本地保留 48 份 IFC，其中 25 份 IFC2X3；不将两份排除项当作意外丢失，也不擅自补回。

- [来源级 authority](../manifests/ifc-sources.json)
- [canonical 文件 authority](../manifests/ifc-files.jsonl)
- [来源说明与许可材料](../sources/CATALOG.md)
- [获取记录](../manifests/acquisitions/)

BIMNet 已迁到 `bimnet/`，原 train/test 物理目录不再作为 canonical 位置；split 仍由 `dataset/splits/bimnet-scene-splits.json` 管理。

`bim-whale-ifc-samples/` 与 `ifc-bench/` 是独立 Git 子模块；子模块内未提交工作由其所属任务管理，不能从父仓库清理时擅自恢复、删除或提交。

Source 文件、同一建筑的 discipline / schema variants、下载候选及回归 fixture 有不同职责。只在逐文件相同且 provenance 已保留时去除真正重复；不把公共下载等同训练许可。旧 raw-files / external-corpora manifests 仍有兼容消费者，暂时保留。

已跟踪 IFC 使用 Git LFS。模型缓存、依赖与外部数据不属于普通 pytest 缓存。
