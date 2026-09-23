# IFC-SemRepair：三份主文档导航

更新：2026-09-23。给老师汇报先读技术文档，再按需要查 Claim 和文献；三份主文档继续分别维护，不新增平行主稿。本轮补齐 Type、材料、外观和真实证据边界，不启动新实验。IFC-SemRepair 是 Repair 论文暂定名，项目仍为 text2IFC。

### 三份持续维护文档

| 文档 | 唯一维护内容 |
|---|---|
| [Literature：文献矩阵](repair-literature-matrix-20260921.md) | 原论文做了什么、来源与阅读程度、方法和任务差异、对候选 Claim 的冲突 |
| [Demo Method：Repair Loop、方法与案例](../../architecture/ifc-repair-pipeline-status-and-roadmap.md) | 用于老师汇报和论文方法整理：问题、设计思路、三个 Part、两类 Demo、当前结果与适用范围；不承担代码交接 |
| [Claim、创新边界与实验登记](claims-and-experiments.md) | 研究问题、贡献措辞、novelty 状态、实验设计／批准状态、真实运行记录、效果及局限 |

本页只做导航，不是第四份研究正文。文件路径保持稳定，在正文更新日期、版本与变化记录，不为每轮讨论另起平行“最新方案”。literature 文件名中的日期保留为首次建立标记。

### 本对话的维护约定

持续维护上面三份固定路径文档，用于 Repair 文献调研、技术路线与技术说明、Claims 与实验设计。后续讨论分别回写对应正文，必要时同步另两份的引用和结论，不另起平行“最新稿”。

- 文献矩阵说明前人做了什么、依据读到哪里，以及与本研究的联系；维护日期不等于重新阅读了论文。
- 展示版 Method 沿用上传原稿的“总体路线图—分 Part 解释—贯穿案例”风格，采用研究者向老师汇报的叙述方式；用图说明澄清、有限纠正、核验与下一轮请求，过时状态按当前证据更新；不写函数、代码路径、内部数据结构清单或调试交接流程；必要术语用其方法作用解释，不保留助理对话措辞。
- Claims 与实验设计区分候选主张、已有证据、待验证问题和实验批准状态；文档更新不等于用户审阅通过或同意执行实验。

技术原稿已确认为 [Text2IFC-Pipeline-Feishu-2026-08-29.md](archive/Text2IFC-Pipeline-Feishu-2026-08-29.md)，不是 9 月 3 日 Plan 07 handover。它按原字节保存为历史来源，当前技术说明仍在原固定路径维护。飞书[Repair 技术文档](https://xcnn3ovwdml4.feishu.cn/wiki/LGB0wgMkliWUr7kBRvGchADgn7b)是技术正文的汇报副本，不另立第四份主稿。

### 更新分工

方法或能力变化更新展示版 Method；新论文或原文勘误更新 literature；Claim 决定、实验设计与结果更新第三份文档。方法待验证问题链接到 Claims 与实验设计，不把工程交接细节写入展示正文。论文候选不因写入文档就变成已成立创新，实验设计不因记录就等于批准或执行。

实验记录应保留 proposed／approved／executed／verified 等实际状态，以及输入、版本、失败／重试、L0／L1／L2、参考角色、成本和产物入口。旧失败和已接受 Proof 不重写。48 个任务／288 次运行方案现为未批准历史草案，不作为默认排期。

### 历史材料：保留引用，不再并行维护

[旧 Claim 攻击快照](archive/claim-novelty-audit-20260921.md)、[v0.3 研究与实验草案](archive/research-question-claims-experiments-20260921-v0.3.md)、[v0.3 三方比较协议草案](archive/damage-repair-compare-protocol-20260921-v0.3.md)已移入 archive，仅解释此前讨论。现行决定进入第三份主文档。

[SGSS 全文阅读快照](sgss-fulltext-review-20260921.md)保留前作阅读证据；新原文核查统一在 literature 更新，不作为第四份现行综述。Generation 的计划与历史材料保持其原有职责。

### 本轮执行记录

技术主文档重写为汇报正文，补齐材料／Type／外观，核对 R1 和三个 presentation 案例；相关三份聚焦测试文件 29 passed，仅离线回归。历史草案归档并修复引用，未删除文档、修改生产代码或运行新 Provider 实验。全体文档分类见[分类与归档目录](../../document-catalog.md)。

9 月 23 日 v0.7 进一步恢复原稿的图解结构：三个 Part、七幅流程图，以及 Type／材料、梁柱补全两个贯穿案例；同步 Claims 中的闭环边界，未新增文献或实验结论。

9 月 23 日 v0.8：技术主文档定位为展示版 Demo Method，正文按问题、闭环、三个 Part、两个案例及论文验证组织；去除代码入口、内部对象清单和交接记录。后续沿用此写作定位。
