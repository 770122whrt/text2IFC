# text2IFC Source IFC 目录

每个子目录对应来源；包括 BIMNet、buildingSMART、IFC-Bench、BIM Whale、KIT、STEP Tools 和已登记的其他公开示例来源。

- [来源级 authority](../manifests/ifc-sources.json)
- [canonical 文件 authority](../manifests/ifc-files.jsonl)
- [来源说明与许可材料](../sources/CATALOG.md)
- [获取记录](../manifests/acquisitions/)

BIMNet 已迁到 `bimnet/`，原 train/test 物理目录不再作为 canonical 位置；split 仍由 `dataset/splits/bimnet-scene-splits.json` 管理。

`bim-whale-ifc-samples/` 与 `ifc-bench/` 是独立 Git 子模块；子模块内未提交工作由其所属任务管理，不能从父仓库清理时擅自恢复、删除或提交。

Source 文件、同一建筑的 discipline / schema variants、下载候选及回归 fixture 有不同职责。只在逐文件相同且 provenance 已保留时去除真正重复；不把公共下载等同训练许可。旧 raw-files / external-corpora manifests 仍有兼容消费者，暂时保留。

已跟踪 IFC 使用 Git LFS。模型缓存、依赖与外部数据不属于普通 pytest 缓存。
