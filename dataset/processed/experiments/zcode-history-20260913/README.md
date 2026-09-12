# Zcode 历史恢复与重构参考

这里是原根目录 `archive/zcode-local-20260905/` 的轻量接续入口。Zcode 的正式提交已合入 main；旧重构镜像的整体采纳明确退役，不再作为一项悬而未决的全量合并任务。

**本目录不是新的 Proof，也不加载进生产 pipeline。** 现有 [C1–C5 Proof](../../proof/repair/phase12/c1-c5-damage-restoration/REPORT.md)及其他 Generation／Repair Proof 保持原位置、字节和人工状态。完整历史成功／失败、原始响应和数据快照保留在固定 Git/LFS 历史中，没有被销毁或重新计为成功。

## 留在当前分支的内容

| 文件 | 内容 |
|---|---|
| [recovery-index.json](recovery-index.json) | 原 18 个文件的路径、大小、SHA-256、Git blob／LFS OID 和保留位置；66 份代码差异与 37 份文档的成员映射 |
| [recovery-metadata.zip](recovery-metadata.zip) | 原始归档说明、逐文件清单、排除项和子模块快照清单，保持原字节 |
| [refactor-reference.zip](refactor-reference.zip) | 旧镜像相对其 source-snapshot 的 66 份变更／新增 Python 文件，以及 37 份审查、交接和设计文档；约 528 KiB |
| [published-contracts/](published-contracts/README.md) | 原字节保留 Zcode 历史 v0.12 Prompt 和 registry；当前回归读取这里，生产 registry 不变 |

完整旧镜像共有 8,755 个文件。当前只保留有差异的代码和相关说明；451 份未变化 Python 源码、重复数据、旧快照和全部运行仍可按下节恢复。参考包不是独立可运行项目，旧文档的状态、测试结论和原有乱码保持历史原义。

## 重构差异的处理决定

检查基线为当前 `d1639232` 与旧镜像的 `8bfcfe07` source-snapshot；本次只做结构与依赖核对，没有运行旧镜像或宣称行为等价。

| 旧成果 | 当前事实与决定 |
|---|---|
| README、目录地图和文档体系 | **已有替代**：当前 README、接管指南、文档索引和 processed 七类目录已覆盖导航目标；不复制旧文档体系覆盖它们 |
| `production_evaluation.py` 与 benchmark 拆分 | **保留为后续小步候选**：当前 `benchmark_evaluation.py` 仍同时声明 public／private 输入，但已有类型与来源门；拆文件是职责改进，不代表当前已发现 Gold 泄露 |
| `src/text2ifc_proof/` | **保留为后续小步候选**：当前仍由 scripts 下的 Proof 工具承担相关职责；可逐个提取并保留旧入口，须适配后续 C1–C5 和新收纳路径 |
| runner 按 uat／offline／curators／audits 分组 | **后置**：旧镜像有 25 个迁移／移除路径，当前已有更多脚本和冻结路径消费者；先在有实际维护收益的模块小范围整理 |
| 整套旧镜像覆盖当前仓库 | **放弃整体采纳**：镜像未包含后续全部修复、版本及数据路径变化；固定历史可恢复，不将其继续挂为待合并分支 |
| 旧数据副本、source-snapshot、旧 Phase 状态 | **退出当前工作目录**：完整保留在 Git/LFS 历史；不恢复旧目录、不覆盖当前 Proof 或重新执行旧授权 |

这些候选不是本轮新增实施计划或模型能力。本轮只更新一项历史 Prompt 回归的读取路径，保留原有正反断言。

2026-09-13 后续用户已明确要求实际融合有价值的重构。上述评估拆分、Proof 包提取与 runner 整理将以当前代码逐项实施，状态在 STATE 和现有仓库重构文档中接续；本包仅保存原始设计与差异，不能用保留包代替实施。

## 如何恢复原大包

固定完整修订：`d1639232f74e4108f3242c46162bcd91bf0909fe`。

- [该修订的原始 archive 目录](https://github.com/770122whrt/text2IFC/tree/d1639232f74e4108f3242c46162bcd91bf0909fe/archive/zcode-local-20260905)
- 每个原文件的路径、Git blob、LFS OID、大小与 SHA-256：见 recovery-index.json 的 `entries`。
- Git 历史只保存大文件指针；恢复 ZIP 还需要对应 LFS 对象，不能把 `git show` 得到的指针当作 ZIP。

需要完整恢复时，在**新的空恢复 checkout** 中检出上述固定修订，使用标准 Git LFS 按需获取 `archive/zcode-local-20260905/<所需文件>`，再按索引核对。不覆盖当前 checkout、Proof 或现有运行目录。原本只在历史 archive 存在的失败与子模块快照仍可由此恢复。

原 [Zcode curator 重放脚本](../../../../docs/reports/main-integration-20260912/recheck_zcode_curator.py)是历史执行记录：它依赖旧运行与旧 Proof 布局，不是当前公共工具。重现时在隔离工作区恢复其固定来源与布局；不要为让旧脚本直接运行而修改当前 Proof。

本次 [远端可用性检查](../../../../docs/reports/archive-retirement-20260913/remote-availability.json)确认六个对象均可下载，且各一次 1 字节范围读取返回 HTTP 206、总大小匹配。原六个本地 ZIP 已与提交中的 LFS SHA-256 匹配；2026-09-05 的[独立完整下载验证](../../../../docs/reports/zcode-integration-20260905/remote-recovery-verification.json)保留。**本次没有重新下载并全量哈希远端 2.50 GiB 数据。**

实际退役状态、准确清单与验证见[本轮报告](../../../../docs/reports/archive-retirement-20260913/REPORT.md)。删除当前工作目录的副本不会缩小 Git/LFS 历史；不执行历史压缩或 LFS prune。
