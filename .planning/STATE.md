---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Phase 12 and 12.1 closed; Repair Milestone R1 accepted 12/12 with Proof 0.3
last_updated: "2026-10-18"
progress:
  total_phases: 13
  completed_phases: 12
  total_plans: 63
  completed_plans: 63
  percent: 96
---

# 当前工作状态

## 当前整理：UI 结合前的本地精简（2026-10-18）

用户授权检查整个仓库的引用与依赖，将重复说明合入现有正文，实际删除确认停用的代码、Prompt 开发说明、旧交接及临时文件；保留当前入口和必要实验依据。不新增文件，不以忽略规则代替删除。本轮起点为 `codex/repair-experiment` / `48f32bba4c1976178a97267a98e569080f44063e`。上轮已确认范围完成实际删除与合并，35 项聚焦离线检查通过。2026-10-18 用户进一步授权处理清单中的权限遗留目录；管理员只读盘点和依赖核对完成后，准确的 30 处目录已全部实际清理，必要实验/Proof 记录保全哈希一致。具体清单、权限处理方式和验证见[现有清理报告](../docs/reports/workspace-cleanup-20261017/README.md#权限受限目录续清理2026-10-18)，本页不复制统计。

下一步是 UI 与当前系统结合；这轮只处理准备工作。产品 Repair 入口为 [CLI](../src/text2ifc_ifc_repair/cli.py) 和 [RepairAPI](../src/text2ifc_ifc_repair/api.py)，专项实验脚本从[运行与维护索引](../scripts/ifc_repair/README.md)进入。版本保留按注册表、生产调用、回归与冻结依赖判断，不把版本后缀当作删除依据。

此前约剩 16% 是 10 月 17 日的历史快照；10 月 18 日已重新核对，当前普通用量可用。外部子模块原有本地删除、私有配置、环境、模型、源数据及冻结 Proof 保留各自状态。

## Repair 实验与数据分析

- 当前报告：[1200 题数据与许可](../docs/reports/repair-dataset-1200-summary-20261015/README.md)、[A–G 结果与校验证据](../docs/reports/repair-experiment-summary-20261015/README.md)、[题型统计](../docs/reports/repair-task-types-20261017/README.md)。提交产物、独立检查与能力提升分别判断。
- formal-40-pairs-25-20261010 的批量流程已在 2026-10-12 冻结并按用户授权启动。阶段状态的唯一权威仍是[cycle 入口](../.tmp/repair-formal-1200-20261011/cycle/README.md)，正式批量结果在[full/results](../.tmp/repair-formal-1200-20261011/full/results/README.md)，冻结绑定在同级 `full/admission/harness-freeze.json`。本页不把当时的启动状态当作今天仍在运行，也不根据目录存在自动重启。
- [实验专题](../docs/validation/repair-comparison/README.md)维护七组映射、恢复方式、单题预算、澄清与单位约定、当前链路和旧失败入口；[前批四组表](../dataset/processed/experiments/repair-comparison/current/README.md)与[20 题审阅](../dataset/processed/ifc-repair/repair-comparison/formal/README.md)保留原批次含义。
- 无 C loop 与完整链路的配对限制、真实失败与未知用量见[分析入口](../docs/reports/workspace-cleanup-20261017/README.md)。已有产出数不能当作修复正确数，揭示后的回归不能充当盲测提升证据。
- 脚本负责批量、等待、续跑与摘要；Codex 处理异常和阶段决定。新的真实调用仍需匹配的阶段准入及费用授权；本轮整理不调用 Provider、不另开 Goal、不运行 Full Preflight。

## 其他功能与已完成里程碑

- Generation 与 IFC2Text：[生成工作流](../docs/architecture/current-workflow-and-data-flow.md)、[IFC2Text 当前入口](../docs/validation/ifc2text/README.md)、[门窗部件计划](../docs/architecture/text2ifc-component-plan-v1.0.md)与[结果](../docs/validation/ifc2text/component-v26/README.md)。成功范围、缺项、失败与预算由各结果页维护。
- Phase 12、12.1 与 Repair R1 已完成；[最终矩阵](../docs/validation/repair-milestone-r1/repair-proof-matrix-2026-09-03.md)与 [R1 Proof](../dataset/processed/proof/repair/phase12.1/r1/REPORT.md)保存 12/12 的原始合同范围。R1 没有合法的 case-specific pristine triplet，不能补造 Ground Truth。Phase 13 未启动，需单独明确任务。
- [Proof 总入口](../dataset/processed/proof/README.md)维护人工状态与机器权威。semantic-appearance 的两个人读包仍为 pending_human_review，未登记为 accepted；已通过字节/角色/重开检查的原样 Git 备份不改变其状态。
- 延后项：v1.0 的 `CLI-08` 最终真人 REPL 验收；曲面/自由形墙体修复；无兼容承诺的 L3 精确性；未启用的自动相似度 Prototype 授权。长期约束见 [PROJECT](PROJECT.md)，阶段安排见 [ROADMAP](ROADMAP.md)，交付史见 [MILESTONES](MILESTONES.md)。

## 历史与恢复

原先叠加在本页的 7–10 月检查点是当时快照，已收口为上面的当前入口。完整原文可从[整理前固定 Git 版本](https://github.com/770122whrt/text2IFC/blob/48f32bba4c1976178a97267a98e569080f44063e/.planning/STATE.md)查阅；阶段 SPEC、VALIDATION、真实运行、失败账本和冻结 Proof 不因本页精简而改写。已退役 Repair 材料按[实验目录恢复说明](../dataset/processed/experiments/README.md#repair-旧材料按需从-git-恢复2026-10-10)获取。
