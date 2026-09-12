# 实验与开发历史记录

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

## 开发辅助材料

[历史开发辅助归档](development-support-20260912/README.md) 保存原 .tmp 中319份尚无归档副本的脚本、测试结果和操作日志。它们不加入 pytest 发现范围，不替代原实验结论；会话恢复材料留在原地。源文件待备份推送后另行申请退役。

[Zcode C1–C5 历史离线记录](repair-c1-c5-offline-20260903-v2/README.md) 与 [真实运行 Proof](../proof/repair/phase12/c1-c5-damage-restoration/REPORT.md) 分开收纳。
