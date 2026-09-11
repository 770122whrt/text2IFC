# C Proof、实验归档与原目录退役

2026-09-11。用户已人工验收最新C，明确要求收纳Proof、将之前实验单独整理，并在收纳后删除旧run目录。

## 已约定的范围

- 最新C `05c6de3a19ed20f9` 收入 [Generation Proof](../../../dataset/processed/proof/generation/phase6.6/c-shaped-teaching-20260911/REPORT.md)，状态accepted / 人工已验收。保留用户命名generated-C.ifc，并提供标准案例入口。IFC SHA-256为 `52c3e24856775152f62d2179e6c1efd0855da6d9b6d6cfb32a73fab3fbbe81ff`。
- 9组额度实验、Audit去重和C调试原记录独立收纳到 [experiments](../../../dataset/processed/experiments/README.md)。保留失败、真实输入响应、账本、脚本和检查记录，不因最终成功而将历史全部改标accepted。
- 只删除下列10个已完整收纳的原目录；不扩大到整个ifc-presentation-validation、其他Proof、旧A/B、其他任务或全局临时目录。本次没有Provider调用，也没有生产行为改动。
- 原始报告、FILES、运行admission和数据库内历史路径不重写。通过归档索引可还原旧布局。新人工验收状态在独立human-review.json记录。

**收纳备份提交 `687d94dc` 已推送；10个原目录已实际删除完成。** [删除结果](deletion-result.json) · [删除后证据复核](post-retirement-integrity.json)。

## 验证与删除

Proof已重新执行完整Generation确定性Final Acceptance，通过Schema、语义、几何、编译重读、Audit绑定及secret scan；人读验证16份绑定副本、1次IFC重开通过。用户验收的IFC字节未替换为复算文件。冻结原记录153份，实验归档1476份/81,335,214字节，复制后SHA-256一致。

回归测试只调整5个测试文件的夹具路径，涵盖受影响的6个测试模块；删除前37 passed（235.15秒），删除后同37项再次通过（301.23秒）；[验证记录](validation.json)与[删除后原始日志](post-retirement-pytest.txt)可查，不累计为74个不同测试。运行器与评价器保持原字节。删除后再次从Proof运行 [完整确定性Final Acceptance](post-retirement-final-acceptance/acceptance-metrics.json)，仍valid=true、编译重开与几何通过、secret scan为0，证明不需要已删除的源目录。该复算IFC仅用于验证，人工验收文件不替换。相关计划和Proof索引已更新，直接展示案例50→51。

准确源父目录：`E:\code for project\bimnet\dataset\processed\ifc-presentation-validation`。

| 拟退役原目录 | 文件数（含缓存） | MiB |
|---|---:|---:|
| audit-token-pair-20260911 | 41 | 2.53 |
| c-shaped-brief-budget-experiment-20260910 | 54 | 2.03 |
| c-shaped-brief-debug-20260910 | 75 | 2.42 |
| c-shaped-clarified-entry-20260911 | 142 | 8.32 |
| c-shaped-gate-debug-20260911 | 142 | 7.87 |
| c-shaped-integrated-20260911 | 36 | 1.06 |
| c-shaped-plan-constraints-20260911 | 254 | 20.49 |
| c-shaped-teaching-building-20260910 | 645 | 28.59 |
| c-shaped-wall-join-20260911 | 106 | 4.45 |
| c-shaped-current-provider-20260911 | 157 | 9.53 |

总计10目录、1652文件、91,540,529字节（约87.3 MiB）。1629份证据文件均有哈希一致的保留位置；23份.pyc为可重建缓存。[逐文件清单](deletion-proposal.json)记录完整源路径、保留位置、大小和哈希。执行前再次检查完整文件集合、所有源与副本哈希、路径边界及reparse point。

已先提交并推送保留证据，再执行删除；[删除结果](deletion-result.json)记录10个目录全部移除，归档副本保持。删除前后测试结果分别记录，不相加为不同案例。归档与Proof扫描使用既有secret-pattern检查，不能声称通用安全审计。

## 后续工作边界

C主线已用户验收。后续A/B/C token实验仍按独立token-efficiency-plan逐项推进，当前不开展新实验、不增加建筑能力范围。A/B/C属于已见开发场景，不作为盲测；历史不同代码运行不能直接当受控消融。人工验收不代表完整结构、消防、净高或可施工性认证。
