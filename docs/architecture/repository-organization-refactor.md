# text2IFC 目录瘦身与后续重构方案

记录日期：2026-09-06。当前目录清理与人读 Proof 迁移已获批准；下面的后续重构是建议，尚未实施。产品名称 text2IFC；BIMNet 保留数据来源含义。

## 结论

主要占用来自运行证据、外部 IFC、模型和 Git 对象，而不是 Python 源码。大幅减少体积需要明确存储与保留策略；把 src 改名或把 scripts 再套一层目录不会释放这些空间。

本轮已采用的组织原则是：人读 Proof 按 workflow / phase / collection 展示；机器证据维持冻结位置；可再生 pytest 缓存与真实运行分开处理。

## 实测占用

以下只枚举元数据，没有全仓库哈希或读取大文件内容。统计是执行过程快照；不可读目录对应的数值为下界，不是完整占用。文件体积为逻辑字节，未等同 NTFS 实际占用。

| 目录 | 可读文件总量 | 文件数 | 完整性 |
|---|---:|---:|---|
| `.git/lfs/objects` | 2.97 GiB | 3,372 | 元数据可读 |
| `.git/objects` | 1.74 GiB | 26,498 | 元数据可读 |
| `.cache` | 4.29 GiB | 34 | 元数据可读 |
| `.deps` | 0.15 GiB | 2,868 | 元数据可读 |
| `.venv` | 1.09 GiB | 42,341 | 元数据可读 |
| `dataset/external` | 5.61 GiB | 651 | 元数据可读 |
| `dataset/processed/ifc-repair` | 3.12 GiB | 3,352 | 86 个不可读目录，另跳过 0 个链接 |
| `dataset/processed/ifc-repair-runs` | 7.94 GiB | 23,415 | 23 个不可读目录，另跳过 4 个链接 |
| `dataset/processed/agent-demo` | 0.07 GiB | 2,853 | 元数据可读 |
| `dataset/processed/proof` | 2.12 GiB | 1,903 | 元数据可读 |
| `.tmp/dataset-acquisition` | 0.00 GiB | 4 | 元数据可读 |

`proof/` 包含本轮新增的人读副本，因此和整理前不可直接当作同一快照。约 427 MiB 的参考 IFC 副本是已批准的可发现性开销；R1 与 Plan 07 人读目录采用迁移，避免再各复制一整套。Git LFS 本地对象与 checkout 不是两份可随意互删的数据。

## 建议次序和验收边界

| 次序 | 准确范围 | 建议 | 开始条件／验证 |
|---|---|---|---|
| 1 | `dataset/processed/ifc-repair-runs/`、`dataset/processed/ifc-repair/` | 按 run 建立用途、是否 genuine、引用关系和可恢复性索引；先识别可以丢弃的 offline 临时子树 | 每项列出保留副本／重建命令；不可读目录与真实 attempts 不自动删除 |
| 2 | `.cache/models/`、`.cache/ifc2x3/`、`.cache/property-resolution/` | 将模型与可再生检索索引分开；评估多个 checkout 共用只读模型存储 | 先确认当前消费者和配置入口；模型版本、离线可用性与路径切换验证通过；不得直接删模型 |
| 3 | `dataset/manifests/`、`src/text2ifc_dataset/` | 收敛到 source/file authority，加兼容投影；逐个迁移旧消费者 | `audit.py`、`phase6_manifest.py`、`ifc_repair_benchmarks.py` 仍使用旧 manifest；消费者为零且等价性通过后才移除旧文件 |
| 4 | `scripts/dataset/` | 将获取脚本重复的下载、manifest 登记、幂等去重归入一个内部模块，保留已有 CLI 入口 | 先比较脚本实现；选两个独立来源试点；使用离线 fixtures，不顺带重新下载 |
| 5 | `scripts/ifc_repair/` | 分清运行器、Proof 收纳工具和分析工具；先建立入口索引，再考虑迁移重复 helper | 不重构 Provider/repair 状态机；冻结 CLI、source fingerprint 和发布路径行为 |
| 6 | `.git/objects/`、`.git/lfs/objects/` | 先核查哪些历史对象仍被 refs/worktrees 使用，确认远端和恢复条件，再考虑普通维护 | 本轮不 gc/prune，不重写历史，不 force push；不能按对象文件名手删 |

## 目前不建议做的事情

- 不整体搬走或压缩 genuine run 权威：现有路径、manifest、FILES、runtime 和评估绑定需要专门的迁移例外。若采用外部归档，须先验证完整恢复、回链与权限，再决定本地保留策略。
- 不把 `.venv`、`.deps`、模型下载统一清空；它们分别承担环境和离线运行依赖。
- 不合并 `scripts/bim_json/` 与 `scripts/bim_json_v2/` 或对应 tests；它们承载不同版本合同。
- 不因为 case 曾失败就删 source/attempt；错误 Proof 可退出有效索引，原始失败与回归 fixture 仍有独立价值。
- 不立即拆分 `src/text2ifc_ifc_repair/` 大模块：当前该目录有其他任务的未提交行为修改；应在行为合同稳定后另行做模块接口审查。

## 文档组织

`docs/README.md` 是唯一总入口。`docs/architecture/` 放结构方案；`docs/validation/` 放跨阶段验证合同；`.planning/` 放 Phase 执行权威。`docs/handoffs/` 与 `docs/context-handoff/` 目前有不同用途，优先补索引，不为美观合并。旧报告记录的历史路径不改写成新的实验事实。

## 下一轮建议的最小工作包

优先只做“运行目录保留索引 + 两个数据获取脚本的重复实现审查”。交付一份可审批的准确迁移／删除列表和一组保持 CLI 行为的离线测试，再决定是否执行。这样能同时处理占用大户和代码重复，避免把整个仓库重构成一个无法审查的大提交。

[Proof 入口](../../dataset/processed/proof/README.md) · [文档索引](../README.md)

## 本轮已执行与验证

已清理获批的 pytest 缓存、Python 字节码和一个重复浏览器快照：660 个文件、24,781,716 字节（23.63 MiB，逻辑体积）。缓存可由相应离线测试重新生成；重复快照保留较早的同内容文件。根目录终端历史移动到 `docs/reports/terminal-session-history.md`，原文字节保留。已提交文件的旧版本可从 Git 历史提取到独立目录。

Proof 共有 45 个独立人读案例；历史 UAT 另引用 2 个已有案例。106 次 IFC reopen 和 157 项来源一致性检查通过；17 个聚焦测试通过。导航和迁移不修改冻结机器权威，不产生新能力结论，不关闭 Phase；未运行 Full Preflight、Provider、IFCCompare 或完整 curator。模型、外部数据、真实运行、不可读目录及其他任务修改继续保留。
