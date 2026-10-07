# 当前状态

更新：2026-10-07。本次在独立 `精简版本` 分支清理开发历史、合并重复实现，并在验证后移除测试源码；用户已授权通过 PR 检查风险与冲突后合入 main。
基线：main `d8ee81607c3c1239256c40c4b6dfff1761f40db3`（2026-09-28）。
本轮结果见 [精简记录](../docs/reports/lean-branch-20261007/REPORT.md)，以其中实际验证和发布状态为准。

## 产品基线

- Generation：支持 `legacy_full` 与显式 `staged`，保留所有已注册 Schema／Prompt 和公共入口。
- Repair：Phase 12／12.1 与 R1 的既有验收保持原义。源码仍执行确定性绑定、原子应用、L0/L1/L2 和保全检查。
- IFC2Text：参数化门窗与 hxp／i5n_1 的往返结果见[当前入口](../docs/validation/ifc2text/README.md)。部分重建、误差与预算以结果页为准。
- Proof、真实失败、原始响应、来源和授权记录保持原字节与状态；本次工程验证不升级研究能力声明。

## 接续边界

本次任务不启动新 Provider 实验。后续真实调用必须重新确认授权、预算和对应阶段准入。
测试已移出本分支时，须恢复验证材料再执行需要测试的 preflight；不得改成自动通过。
Phase 13、大型模型／128k 实验及未支持 operation 仍需要独立任务。

旧逐轮状态、清理过程、预算和工作树位置是历史事实，不作为本轮执行指令。
需要追溯时读取[清理前 STATE](https://github.com/770122whrt/text2IFC/blob/d8ee81607c3c1239256c40c4b6dfff1761f40db3/.planning/STATE.md)。
