# 实验与失败诊断记录

本目录独立保存实验和调试历史，含成功、失败、原始Provider响应、token账本、配置、脚本和验证记录。它们不因最终C被验收而自动成为accepted Proof。旧报告中的“下一步”和pending为当时状态，原字节不改。旧路径至当前路径、大小与SHA-256见 [归档索引](c-token-archive-20260911.json)。不收纳可重建的 __pycache__。

原目录已于2026-09-11在备份推送后退役，见 [整理与删除记录](../../../docs/reports/c-proof-archive-20260911/REPORT.md)。归档索引中的source_directories_deleted=false是复制时快照，实际删除状态以该记录为准。

## 阅读顺序

| 内容 | 原记录 | 结论 |
|---|---|---|
| Brief输出额度96K/64K | [实验](c-shaped-brief-budget-experiment-20260910/REPORT.md) | 两次均完整但待澄清；提高上限不能证明稳定性提升 |
| Audit真实full/去重配对 | [实验](audit-token-pair-20260911/REPORT.md) | input减少24.20%；仅一个已见案例，质量非劣效尚未证明 |
| C首次Brief截断 | [原案例](c-shaped-teaching-building-20260910/) | 保留失败；最初缺失的raw响应不能补造 |
| Brief失败记录修复与单阶段诊断 | [记录](c-shaped-brief-debug-20260910/) | 单阶段成功不等于完整IFC成功 |
| C公共链路与入口澄清 | [集成](c-shaped-integrated-20260911/) · [入口](c-shaped-clarified-entry-20260911/REPORT.md) | 入口4.2米是用户真实批准；诊断IFC未获最终放行 |
| 门禁与去重零收益定位 | [记录](c-shaped-gate-debug-20260911/) | 首次Audit没有足量相同大对象，回退full；不能把字节估算当真实token |
| 墙界与局部修复失败 | [记录](c-shaped-wall-join-20260911/REPORT.md) | 旧完整JSON修复丢关系；保留失败分母 |
| 墙约束与名称误报修复 | [记录](c-shaped-plan-constraints-20260911/REPORT.md) | 前一轮IFC及后续离线修复，属于开发比较 |
| 最新C人工验收 | [Proof](../proof/generation/phase6.6/c-shaped-teaching-20260911/REPORT.md) | 新3次真实调用，无修复loop，独立485/485 |

唯一后续计划为 [token-efficiency-plan.md](../../../docs/architecture/token-efficiency-plan.md)。既有 [离线去重分析](../../../docs/validation/token-efficiency/20260911-audit-dedup/REPORT.md) 和 [C消耗归因](../../../docs/validation/token-efficiency/20260911-c-scope-diagnosis/REPORT.md) 仍保留原处，通过此入口串联。

## 计量与复用边界

C累计20次/1,597,750 token包括额度实验等C历史；Audit配对另计2次/171,516 token。各阶段累计值不可求和。reasoning已包含在output中。不同代码、Prompt和随机输出下的两次C运行不是受控token消融。

冻结admission、数据库引用和日志里的原绝对路径仅表示历史环境；不能直接复用为新真实调用准入。原脚本原样保存用于审计，受影响的回归测试应改用本归档路径；任何真实重跑须创建新运行目录并建立当前准入。

## 光庭设计与修复实验

两版光庭成品和全部过程自包含收纳到 [光庭Proof](../proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)。失败归因、原始attempt、累计token和12个一次性测试脚本见 [过程入口](../proof/generation/phase6.6/courtyard-library-20260912/evidence/README.md)，不重复复制一份实验目录。第二版人工验收不提升第一版设计状态。

## 其他案例与开发目录归档（2026-09-12）

[统一整理记录](../../../docs/reports/development-cleanup-20260912/REPORT.md) 说明删除结果、验证及保留边界。[旧路径映射](development-retirement-20260912.json) 定位每份原文件；已有 Proof 副本直接复用，没有重复复制。下列目录是冻结历史，不是新的待执行计划。

| 内容 | 入口 |
|---|---|
| A/B 分支早期失败、重试、预算和运行器 | [完整历史](three-storey-clarification-branches-20260910/)；[最终 Proof](../proof/generation/phase6.6/three-storey-clarification-ab-20260910/REPORT.md) |
| 三层与两层旧展示过程 | [三层](three-storey-human-review-20260909/)；[两层](two-storey-human-review-20260908/) |
| 语义、材料与外观试验 | [初始](semantic-appearance-20260908/)；[第二轮](semantic-appearance-20260908-02/)；[收尾](semantic-appearance-20260908-final/) |
| 开口绑定与门禁路由 | [绑定](pipeline-opening-binding-20260909/)；[路由](pipeline-gate-routing-20260909/) |
| 早期运行 | [Generation 语义](live-semantic-20260908-01/)；[交付](deliverables/)；旧 Repair 过程按下方固定 Git 修订恢复 |
| 离线与准入快照 | [offline](offline-20260904T0431/)；[preflight](preflight-20260904T0431/)；[Phase12](phase12-preflight-20260904/) |
| 一次性诊断脚本、XML、日志与试验输出 | [文件](scratch-20260912/)；[原路径映射与 ZIP 成员](scratch-retirement-20260912.json) |

同名 `success-cases` 的 80 份文件全部复用现有 Repair Proof，按映射访问。调试源码仅作历史审计；保留通用回归在 `tests/`，不会因已通过而删除其覆盖。

三个旧目录经删除前复核发现 Windows 权限隐藏的子目录，追加保存 883 文件；[补充映射](development-retirement-permission-supplement-20260912.json) 与原映射共同组成完整来源记录，未覆盖先前归档。

## 更早 Phase 的运行与调试

[Phase 6、9–12 历史入口](phase-history-20260912/README.md)记录旧工作区的来源绑定。Repair 的38个旧 ZIP 已改为从固定 Git/LFS 修订按需获取；Generation 文件和现有 Proof 保留原位。历史失败、响应与账本的原字节可按清单恢复。

## main 已保留的开发历史与 Zcode 记录

[Zcode 历史恢复与重构参考](zcode-history-20260913/README.md) 接续原根 archive：保留轻量合同、清单与 66 份重构代码差异，完整旧运行／失败／数据快照通过固定 Git/LFS 修订恢复。整套旧镜像不再作为待合并任务；当前 Proof 不迁移。

[开发辅助归档](development-support-20260912/README.md) 保存此前收纳的 319 份脚本与测试记录；其旧目录是否已退役，以最新[整理报告](../../../docs/reports/development-cleanup-20260912/REPORT.md)及逐路径映射为准。

[Zcode C1–C5 历史离线记录](repair-c1-c5-offline-20260903-v2/README.md) 与[真实运行 Proof](../proof/repair/phase12/c1-c5-damage-restoration/REPORT.md) 分开保留，不将 offline replay 计为真实 Provider 成功。

## 早期 JSON 局部修复

[旧 JSON 修复示例](legacy-jsonfix/README.md) 保留原 processed/jsonfix 的完整 14 份材料；只归档，不新增验收。

## Repair 四组实验

[当前20题四组结果](repair-comparison/current/README.md)是唯一现行汇报入口，包含产物、比较、问答、用量和实际返回推理。旧已提交实验包仅作为受保护机器证据留存，不代表当前成绩。

## Repair 旧材料按需从 Git 恢复（2026-10-10）

仅退役超过两周且无现行用途的 Repair 材料：656 个旧实验文件、134 份已完成计划／报告／交接、6 个一次性脚本，另含38个纯 Repair 旧 ZIP，共 834 个文件、376.70 MiB 工作文件。删除前逐项核对旧版本、未提交改动和远端备份；29 个 IFC 路径对应的 11 个 Git LFS 对象已从远端取得并验证。38个 ZIP 均匹配 Git LFS OID，远端逐对象范围请求返回可取结果；未下载整套归档。本地不另存归档副本。

恢复基点为远端 `codex/repair-experiment` 已保存的 `11f29030f3f3b5967535d16c4c4b31085e21ff64`。按需从这一修订恢复所需路径，IFC 通过 Git LFS 获取；冻结的旧运行应连同对应代码版本恢复，不能沿用其准入运行今天的 Harness。

| 已退役目录 | Git 中的完整原文 |
|---|---|
| `repair-mixed-20260905` | [旧混合修复实验](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/repair-mixed-20260905) |
| `live-a1-20260904` | [旧 A1 运行](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/live-a1-20260904) |
| `restoration-20260904` | [旧恢复实验](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/restoration-20260904) |
| 38个纯 Repair 旧 ZIP | [原 ZIP 与恢复映射](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/phase-history-20260912) |
| Repair 完成计划与报告 | [阶段材料](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/.planning/phases)、[旧报告](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/docs/validation/ifc2x3-changeset)、[旧脚本](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/scripts/ifc_repair) |

当前实验、原始 IFC、独立 Proof、仍被测试使用的 C1–C5 数据及注册提示词保留。旧过程中的原始失败仍能从固定修订恢复，不把它们改成成功记录。

清理后验证：27项兼容入口／准入依赖／无 Provider readiness 检查通过；对应3例独立 Proof 的12份绑定副本与9份 IFC 重开通过。当前 Harness 与冻结 Proof 的216个受保护文件原样未变，受影响导航没有指向已退役文件的本地链接。
