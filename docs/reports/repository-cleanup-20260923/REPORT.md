# 项目目录清理与引用检查（2026-09-23）

更新至 2026-09-24：旧 main 工作树已归档退役，项目实测从 **40.38 GiB 降至 30.06 GiB**。下面 9 月 23 日的清理记录保留；新的体积、恢复入口与保留边界见[9 月 24 日补记](#2026-09-24旧-main-工作树退役与体积复测)。

## 已批准删除：30 个历史 pytest 临时目录

状态：用户已明确批准 T01–T30，30 个目录全部删除，无跳过。共 3190 个文件，44.43 MiB。普通与提升权限两种读取结果互补，30 个目录均完成文件清单和 SHA-256 检查，未发现重解析点。

这些目录位于仓库根目录，均为忽略的测试运行产物；检索 docs、.planning、scripts、tests 中的 Markdown、Python、PowerShell 与配置未发现对这些具体目录名的引用。删除不涉及测试源码、原默认目录 `.pytest-tmp`、原 pytest 缓存、已接受 Proof 或正式失败记录。未将 `.tmp` 整体列为可删除，其中有数据获取账本和阶段准入材料。

原始产物未纳入 Git。此次按批准范围不保留这批临时产物的字节副本，测试源码仍保留；不能把这些目录当作正式实验结果。执行前已再次核对文件清单、哈希、重解析点与在用进程，全部一致；删除后已确认 30 个目标均不存在。

| 编号 | 已删除目录（相对仓库根） | 文件数 | MiB | 理由 |
|---|---|---:|---:|---|
| T01 | `.pytest-agent-v24-artifact-20260922/` | 130 | 1.443 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T02 | `.pytest-agent-v24-draft-red-20260922/` | 0 | 0.000 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T03 | `.pytest-agent-v24-final-20260922-1/` | 251 | 3.548 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T04 | `.pytest-agent-v24-final-20260922-2/` | 272 | 3.785 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T05 | `.pytest-agent-v24-green-20260922-1/` | 14 | 0.001 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T06 | `.pytest-agent-v24-green-20260922-2/` | 67 | 1.107 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T07 | `.pytest-agent-v24-green-20260922-3/` | 190 | 2.541 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T08 | `.pytest-agent-v24-red-20260922/` | 67 | 1.094 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T09 | `.pytest-agent-v24-regression-20260922-1/` | 1729 | 20.071 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T10 | `.pytest-attribution-20260921-smoke1/` | 40 | 1.330 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T11 | `.pytest-closed-wall-v08-unit-01/` | 6 | 0.003 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T12 | `.pytest-tmp-compare-v10/` | 4 | 0.096 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T13 | `.pytest-tmp-compare-v10-confirm/` | 4 | 0.096 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T14 | `.pytest-tmp-compare-v10-final/` | 159 | 1.782 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T15 | `.pytest-tmp-cross-review/` | 26 | 0.097 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T16 | `.pytest-tmp-polygon-v24-final-20260922/` | 47 | 1.518 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T17 | `.pytest-tmp-polygon-v24-green1-20260922/` | 3 | 0.123 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T18 | `.pytest-tmp-polygon-v24-green2-20260922/` | 21 | 0.758 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T19 | `.pytest-tmp-polygon-v24-green3-20260922/` | 4 | 0.164 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T20 | `.pytest-tmp-polygon-v24-red-20260922/` | 0 | 0.000 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T21 | `.pytest-v07-family-01/` | 9 | 0.129 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T22 | `.pytest-v07-narration-fix-01/` | 43 | 1.515 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T23 | `.pytest-v07-public-seam-01/` | 16 | 0.433 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T24 | `.pytest-v07-public-seam-02/` | 43 | 1.515 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T25 | `.pytest-v08-final-01/` | 9 | 0.129 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T26 | `.pytest-wall-capability-20260921-01/` | 2 | 0.048 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T27 | `.pytest-wall-context-v09-01/` | 13 | 0.485 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T28 | `.pytest-wall-context-v09-final-02/` | 14 | 0.518 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T29 | `.pytest-wall-context-v09-opening-02/` | 2 | 0.071 | 历史 pytest basetemp；有测试源码，不是源码目录 |
| T30 | `.pytest-wall-v07-green-01/` | 5 | 0.033 | 历史 pytest basetemp；有测试源码，不是源码目录 |

## 本轮已执行与保留范围

- D23–D27：依用户批准删除；四份合并正文继续保留，历史原文在已推送提交 `c58888fb5eb10aceb25e03e1eb8b4f8262074e38`。
- 文档按功能归组，并核对入链、出链和报告生成脚本。
- 测试源码静态检查覆盖 411 个 Python 文件、2457 个 `test_` 函数定义；无整文件字节重复。此结果不是全套测试运行结论，也不证明所有断言都不重叠。根目录的三项 JSON→IFC 测试有实际语义覆盖，归入 compiler 组。
- 现有源代码、数据、Prompt 注册表及 IFC2Text 草稿的其他未提交改动单独保留，不随清理提交。



## 文档与测试归组

五份已合并来源 D23–D27 删除；21 份文档移动到功能子目录，另将根目录的一份 JSON→IFC 测试归入 compiler。下面给出全部旧路径与当前入口，历史固定 Git URL 不改写。

| 原路径（相对仓库根） | 当前入口 |
|---|---|
| `docs/reports/generation-demo/broader-method-directions.md` | [docs/reports/generation-demo/archive/broader-method-directions.md](../../../docs/reports/generation-demo/archive/broader-method-directions.md) |
| `docs/reports/generation-demo/claims-and-novelty-synthesis-20260916.md` | [docs/reports/generation-demo/archive/claims-and-novelty-synthesis-20260916.md](../../../docs/reports/generation-demo/archive/claims-and-novelty-synthesis-20260916.md) |
| `docs/reports/generation-demo/coding-agent-knowledge-direction.md` | [docs/reports/generation-demo/archive/coding-agent-knowledge-direction.md](../../../docs/reports/generation-demo/archive/coding-agent-knowledge-direction.md) |
| `docs/reports/generation-demo/research-shortlist-evidence.md` | [docs/reports/generation-demo/archive/research-shortlist-evidence.md](../../../docs/reports/generation-demo/archive/research-shortlist-evidence.md) |
| `docs/reports/generation-demo/text2ids-www2026-demo-overview-and-writing-reference.md` | [docs/reports/generation-demo/archive/text2ids-www2026-demo-overview-and-writing-reference.md](../../../docs/reports/generation-demo/archive/text2ids-www2026-demo-overview-and-writing-reference.md) |
| `docs/reports/Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md` | [docs/reports/generation-demo/archive/Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md](../../../docs/reports/generation-demo/archive/Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md) |
| `docs/architecture/phase-2-5-summary.md` | [docs/architecture/history/phase-2-5-summary.md](../../../docs/architecture/history/phase-2-5-summary.md) |
| `docs/architecture/phase-3-summary.md` | [docs/architecture/history/phase-3-summary.md](../../../docs/architecture/history/phase-3-summary.md) |
| `docs/architecture/phase-4-summary.md` | [docs/architecture/history/phase-4-summary.md](../../../docs/architecture/history/phase-4-summary.md) |
| `docs/architecture/phase-4-wave-0-generated-ifc-gate.md` | [docs/architecture/history/phase-4-wave-0-generated-ifc-gate.md](../../../docs/architecture/history/phase-4-wave-0-generated-ifc-gate.md) |
| `docs/architecture/phase-5-summary.md` | [docs/architecture/history/phase-5-summary.md](../../../docs/architecture/history/phase-5-summary.md) |
| `docs/architecture/phase-6-acceptance-and-trace-report.md` | [docs/architecture/history/phase-6-acceptance-and-trace-report.md](../../../docs/architecture/history/phase-6-acceptance-and-trace-report.md) |
| `docs/handoffs/phase12-plan07-closeout-handover-2026-09-03.md` | [docs/handoffs/repair/phase12-plan07-closeout-handover-2026-09-03.md](../../../docs/handoffs/repair/phase12-plan07-closeout-handover-2026-09-03.md) |
| `docs/handoffs/repair-milestone-r1-closure-2026-09-03.md` | [docs/handoffs/repair/repair-milestone-r1-closure-2026-09-03.md](../../../docs/handoffs/repair/repair-milestone-r1-closure-2026-09-03.md) |
| `docs/reports/ifc2x3-dataset-size-index.md` | [docs/reports/ifc-datasets/ifc2x3-dataset-size-index.md](../../../docs/reports/ifc-datasets/ifc2x3-dataset-size-index.md) |
| `docs/reports/ifc2x3-small-model-meaningfulness.md` | [docs/reports/ifc-datasets/ifc2x3-small-model-meaningfulness.md](../../../docs/reports/ifc-datasets/ifc2x3-small-model-meaningfulness.md) |
| `docs/reports/ifc2x3-small-model-refined-shortlist.md` | [docs/reports/ifc-datasets/ifc2x3-small-model-refined-shortlist.md](../../../docs/reports/ifc-datasets/ifc2x3-small-model-refined-shortlist.md) |
| `docs/reports/ifc2x3-small-model-review-batch.md` | [docs/reports/ifc-datasets/ifc2x3-small-model-review-batch.md](../../../docs/reports/ifc-datasets/ifc2x3-small-model-review-batch.md) |
| `docs/reports/ifc2x3-small-model-web-search.md` | [docs/reports/ifc-datasets/ifc2x3-small-model-web-search.md](../../../docs/reports/ifc-datasets/ifc2x3-small-model-web-search.md) |
| `docs/reports/ifc2x3-small-source-search-followup.md` | [docs/reports/ifc-datasets/ifc2x3-small-source-search-followup.md](../../../docs/reports/ifc-datasets/ifc2x3-small-source-search-followup.md) |
| `docs/reports/kaggle-ifc-examples-small-ifc2x3.md` | [docs/reports/ifc-datasets/kaggle-ifc-examples-small-ifc2x3.md](../../../docs/reports/ifc-datasets/kaggle-ifc-examples-small-ifc2x3.md) |
| `tests/test_json_to_ifc.py` | [tests/compiler/test_json_to_ifc.py](../../../tests/compiler/test_json_to_ifc.py) |

R1 原始验收任务 `docs/handoffs/repair-milestone-r1-final-acceptance.md` 保持原路径和原字节：它被 `repair-acceptance-freeze.json` 与 Proof 校验器按路径及 SHA-256 绑定。新 Repair 目录只提供导航。SHA-256 核对仍为 `bb8c7ecfbf5afd2c231b3be2ef21288101f25f0547e4f3ef770a1b349acff49e`，未修改校验器、冻结清单或其证据副本。

## 路径消费者与防止再次散落

- 六个数据筛选脚本的报告路径同步调整到 `docs/reports/ifc-datasets/`；补齐其中两个脚本的父目录创建。只调整报告存放路径，没有重新采集外部数据或重算旧报告。
- 文档索引、正文出链、计划中的路径与接管指南同步调整；旧稿历史论证链接指向删除前的固定 Git 提交。
- pytest 取消向根目录 `.pytest-tmp` 强制输出，恢复 pytest 管理的系统临时目录；缓存配置为 `.tmp/pytest/cache/`。项目内调试可先建 `.tmp/pytest/`，再指定独立 `--basetemp`。旧默认目录和旧缓存保留，不纳入 T01–T30。
- 原有 IFC2Text 未提交稿件继续保留位置；其现有改动不随本次整理提交。

## 全项目盘点及保留判断

本轮查看各顶层目录及主要子目录的文件数量、大小、Git 身份和调用关系。体积来自清理前可读取的文件；未进入重解析点，部分数据／Proof 路径需更高读取权限，因此下表不是完整磁盘用量，也不是全仓逐行代码审查。

| 范围 | 核查结果与处理 |
|---|---|
| `src/`、`scripts/` | 已按模块组织；仅修改六个报告输出路径及两处父目录创建。兼容入口和生产代码不因名称旧就删除 |
| `tests/` | 411 个 Python 文件，无整文件字节重复；2457 个静态测试函数定义。根目录三项有效测试归入 compiler，不以年龄或低调用频率推定测试无用 |
| `docs/` | 完成五份合并来源的批准删除，21 份按主题移动，四个子目录添加简短入口；保留三份 Repair 主文档与用户上传原稿 |
| `prompts/`、`schemas/` | 注册版本与冻结合同有运行和历史引用，保留；相同渲染副本的旧清理不扩展为删注册版本 |
| `dataset/external/` | 可读取约 7.69 GiB；源模型、授权和来源账本保留。未将数据源名称相似当成字节重复依据 |
| `dataset/processed/` | 可读取约 2.81 GiB；Proof、失败证据、运行基线、派生数据分区已有用途；已有未提交改动和权限状态不作为本轮删除项 |
| `.tmp/main-integration-20260912/` | 9 月 23 日初查约 10.87 GiB，当时先保留；9 月 24 日完成独有文件归档、恢复对象验证和缓存链接核查后，已退役，详见下方补记 |
| `.tmp/cleanup-recovery-20260912/pytest-workspaces.zip` | 231.14 MiB 的历史 pytest 恢复包，已有清理报告记录其用途；保留恢复能力，本次不将它与新批准的 30 个目录混为一批 |
| `.tmp` 中的 stage、admission、acquisition 与 Feishu 目录 | 含阶段准入、采集账本或本地工具状态；不整体删除。此次新增审计中间件仅服务当前操作，不成为新的常驻文档体系 |
| `.cache/`、`.venv/`、`.deps/` | 分别可读取约 4.29 GiB、1.09 GiB、148.76 MiB；模型与运行依赖继续使用，保留 |
| `.git/`、`.planning/`、环境配置、其他工作树 | Git 元数据、执行计划和本地配置保留；仅更新计划中的受影响引用，不删除分支或清理 Git 历史 |

## 验证结果

- 文档本地路径与锚点检查：本轮改动范围无新增失效链接；三个普通身份无法读取的既有 Plan 07 Proof 报告，经只读提升权限确认都存在。
- 六个数据报告输出目标均存在，父目录创建检查与改动 Python 语法检查通过；没有调用外部搜索或数据采集。
- JSON→IFC 三项测试移动前 `3 passed`，移动及路径调整后 `3 passed`；只验证楼层标高、墙属性、门窗尺寸这三个行为。临时目录与缓存配置已实际试跑，最终运行无缓存警告。
- 22 个文件移动目标和 30 个删除目标逐项确认；R1 冻结规格保持原路径、原哈希，用户上传的 8 月文档 SHA-256 不变。
- `git diff --check` 通过；本轮不运行 Full Preflight、全套 pytest 或真实 Provider，不作全仓测试通过或能力提升声明。

工作区已有其他源代码、测试、数据和 IFC2Text 文档改动。提交仅包含本轮整理及引用修正，不表示整个工作树已经干净。

## 2026-09-24：旧 main 工作树退役与体积复测

本次目标是减少约 7 GB 以上的冗余占用，同时保留正在使用的缓存、依赖和研究依据。上轮把“已注册工作树”直接当作保留理由，没有继续判断是否仍被使用；本轮补查后确认，这是一份停留在 9 月 12 日的旧检出，代码和运行配置没有依赖其路径，可以保留恢复依据后退役。

| 项目 | 实测结果 |
|---|---:|
| 清理前项目大小 | 43,361,407,856 字节，40.38 GiB |
| 清理后项目大小 | 32,280,759,487 字节，30.06 GiB |
| 净减少 | 11,080,648,369 字节，10.32 GiB，约 25.6% |
| 删除的旧工作树文件 | 40,340 个，10.87 GiB；另解除一个模型目录链接 |
| 留存的压缩包 | 591,070,666 字节，563.69 MiB；包含 23,502 个文件 |

以上统一按文件大小统计，含隐藏文件及 `.git`，不重复进入目录链接；不是磁盘可用空间变化或 NTFS 实际分配块统计。普通身份不能读取的 92 个目录已通过只读补查计入，两次统计均无未覆盖目录。本轮审计中间文件从最终口径排除并在收尾删除；新增报告与 Git 提交带来的少量字节不影响两位小数。完整计数见[机器记录](worktree-retirement-20260924.json)。

### 删除范围与恢复依据

唯一退役的既有大目录是 `.tmp/main-integration-20260912/`，连同其 Git 工作树登记一起删除。保留 `main` 分支引用 `b4eb7ccfa04bb9b34428f859b32bb78ca5e5a0b0`；该历史已包含在已推送的当前分支中。本轮没有合并或更新 main。

- 跟踪文件来自上述固定 Git 版本。661 个 LFS 文件对应的 463 个本地恢复对象均已完成 SHA-256 核查，共享 `.git/lfs` 未清理。
- 222 个子模块数据副本与当前目录对应文件逐字节哈希一致，保留当前副本。
- 五份不同的旧 RVT，以及独有的测试输入、输出、失败与日志共 23,502 个文件，压缩前共 2,746,055,670 字节，已全部收入本地 ZIP。压缩后逐成员重读并核对长度和 SHA-256，不只检查 ZIP 能否打开。
- 旧代码的 1,074 个 Python 字节码缓存随退役检出删除；当前代码、运行环境和模型缓存没有删除，也无需重新下载。

本地保留目录：`.tmp/retired-worktrees/main-integration-20260912/`。其中 `README.md` 说明恢复方式，`recovery-index.json` 保存固定版本、LFS 对象和重复副本映射，`local-artifacts.zip` 保存独有文件及包内 `RETIREMENT-MANIFEST.json`。该 ZIP **仅保留本地，未上传 GitHub**，应随项目本地备份保存。

ZIP SHA-256：`e3e178cd9ba90712a965a40ba21e0f84ac96abc75989b9e3e5e847988ef2a2b9`。阅读旧输出可直接打开 ZIP；只有需要复现历史版本时才创建恢复工作树，不日常解压回原位置。

### 保留核查

删除前再次核对旧目录文件集合、大小和修改时间，未发现新增或变化文件；跟踪状态干净，无未跟踪文件，未发现显式引用该目录的活动进程。权重链接的真实目标确认为根目录 `.cache/models/BAAI-bge-m3`，先只解除链接，再退役检出。

删除后，旧目录和工作树登记均不存在，main 分支引用不变；当前工作区的未提交／未跟踪状态与清理前逐字节一致。根目录 `.cache`、`.venv`、`.deps` 共 45,243 个文件的大小和修改时间均未变化。当前 Proof、源数据、运行基线和所有失败结论保持原位置与原内容。

此次是已归档旧检出的退役，没有修改生产行为，不运行全套测试、Full Preflight 或真实 Provider。后续临时工作树完成合并和恢复核查后应及时退役，避免再次把完整旧检出长留在 `.tmp` 中。
