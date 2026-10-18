# 第二批执行结果

2026-09-29：E–J 及测试结束自动清理均已获批准。本批已删除 **100,787 个文件、2,911,371,657 字节**。11 个在盘点后被本次开发或并行 Repair 测试更新的编译缓存保留，详见 [执行记录](EXECUTION-EJ.json)。D 的 ONNX 权重继续保留。下表是原批准上限，不是实际删除数。

| 类别 | 文件数 | 容量 | 理由 |
|---|---:|---:|---|
| E：补充读到的旧测试副本 | 44,130 | 1.299 GB | 普通权限可读取的旧 pytest 工作目录，以及本次对话的少量测试产物；此前提升权限盘点未能读取其中部分目录。 |
| F：实验目录内的测试夹具 | 54,794 | 909 MB | 只删除 `validation/pytest-temp` 等内部临时目录，保留同一实验中的正式模型、日志、JUnit 和验收记录。 |
| G：部件阶段旧失败尝试 | 566 | 48.6 MB | 未生成正式成功结果的旧门窗／整楼尝试；已剔除被保留运行引用的文件，失败结论仍在已提交文档中。 |
| H：旧工作树 ZIP | 1 | 591 MB | 已保存其中 5 个独有 RVT 和 414 个历史成功复核文件；剩余主要是测试副本，另有两个旧 Qdrant 缓存标记和退役清单。 |
| I：本次对话的重复盘点中间文件 | 6 | 42.8 MB | 删除全盘快照、原始状态、临时候选表及重复逐行执行日志；保留代码、正式白名单、摘要和成功证据。 |
| J：Python 编译缓存 | 1,301 | 20.4 MB | 位于 src、scripts、tests、docs 的 `__pycache__`；逐项确认对应 .py 源文件仍在，排除虚拟环境、依赖目录和已跟踪文件。 |
| **合计** | **100,798** | **2.912 GB** | 这是待删除文件大小；为保留 H 中数据及成功证据，本轮已新增 81.55 MB，H 精简净释放约 509.5 MB。 |

## 审批和执行范围

[分组路径及理由](NEXT-DELETE-CANDIDATES.csv)；[逐文件白名单](NEXT-DELETE-FILES.csv)。按白名单删除，不能递归删除整个成功实验父目录。E、F 覆盖了这次补查读到的历史测试文件，不把它们误算为新实验数据增长。

后续部件运行引用的 29 份候选文件已保留，见 [引用排除表](NEXT-PRESERVE-REFERENCES.json)。当前 Repair 工作、源 IFC/RVT、代码、D、正式 Proof 和已提交文件不在本批白名单内。执行前仍需核对进程、Git 状态和文件变化；变化项单独暂停。

## H 的保留内容已经落地

- 5 个 RVT：保存到 `dataset/external/RVT/additional/retired-worktree-20260912/`，总计 57,323,520 字节。逐项 SHA-256 与 ZIP 一致，源归档内路径和来源见该目录的 [PROVENANCE.json](../../../dataset/external/RVT/additional/retired-worktree-20260912/PROVENANCE.json)。
- A-revise、B-retain、C-teaching：保存到 `dataset/processed/experiments/retired-generation-recheck-20260912/`，414 个文件、24,225,388 字节，逐项 SHA-256 与 ZIP 一致。保留完整目录相对关系和历史原字节，见[恢复索引](../../../dataset/processed/experiments/retired-generation-recheck-20260912/PROVENANCE.json)。这是历史成功复核的恢复，不是本次新运行或新验收。
- 原 `recovery-index.json` 和退役说明保留。批准删除 ZIP 后更新“从完整 ZIP 恢复”的导航，明确哪些旧测试副本不再保存。

## 文档与代码重复检查

按字节校验了 `docs/` 中正文不少于 100 字节的 209 个 Markdown，以及 `src/`、`scripts/`、`tests/` 中同范围的 946 个 Python 文件。Python 无完全重复组；Markdown 有一组相同 semantic-report，位于两份历史结果记录中，本轮保留正式结果，不因正文相同就删其证据。此检查不声称排除了语义重叠。

已把文档总分类中的 IFC2Text 过时入口改为当前结果与历史索引，避免继续维护旧“最新进展”链接。

## 已接入的自动清理

9 个 IFC2Text 验证入口已接入 `run_pytest_with_cleanup`：正常返回、失败返回和异常退出均在 finally 中清理该次独立工作目录，其他运行目录不受影响。只允许 `.tmp/ifc2text-pytest/<UUID>`，拒绝把正式报告写入将删除的目录；不清理真实 Provider 运行、成功模型或外置日志。进程被系统强制终止时 finally 无法保证执行，遗留目录仍须另行检查。

12 项定向测试通过，包括真实 pytest 子进程的成功／失败返回、JUnit 保留、异常退出、目录隔离和正式证据路径拒绝；[JUnit](SCOPED-AUTOCLEAN.xml)。没有调用 Provider，没有执行 Full Preflight。
