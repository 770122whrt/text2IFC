# text2IFC 仓库交接：结构、整理结果与接续边界

记录日期：2026-09-13。本快照面向下一位 Agent 或维护者，记录本次文档更新前核实的仓库状态。长期目录与代码地图见[接管指南](../how-to/agent-takeover.md)，重要文档见[总索引](../README.md)。本文件不替代产品合同，也不授权自动开始实验、删除文件或合并分支。

## 1. 接手时先确认什么

本地根目录为 `E:\code for project\bimnet`，产品名称为 **text2IFC**。以下提交号是本快照的基线，后续以实际 Git 状态为准：

| 分支／位置 | 本次核实状态 | 含义 |
|---|---|---|
| 当前 `codex/workflow-dataset-links` | `ae4e0272`；当时与对应 origin 跟踪引用相同 | 已包含 main 的整合，再追加 processed／根目录整理 |
| `main` | `b4eb7ccf`；当时与 origin/main 跟踪引用相同 | 已合并此前当前分支与 Zcode 成果，尚未包含 `ae4e0272` 整理提交 |
| `origin/Zcode` | `d0e18fa0`，已是 main 的祖先 | 保留历史分支；不需重新把旧实现覆盖当前代码 |
| main 工作树 | `.tmp/main-integration-20260912` | 活动 Git 工作树，不能作为 tmp 垃圾删除 |

本轮交接文档的提交会继续增加在当前分支上，不在文档里写入自身提交号。准备 push 或 merge 前重新 fetch、比较来源／目标分支并核对工作树，不能把上述远端跟踪引用当成永久状态。

本次检查发现以下本地内容，均不属于文档修改，保持原样：

- `dataset/external/ifc-bench` 子模块本地改动。
- 未跟踪的 `dataset/external/ResBIM_IFC2X3_50.zip`、`dataset/external/Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip`。
- 未跟踪的 `dataset/processed/proof/generation/phase6.6/semantic-appearance-20260908/`、`dataset/processed/proof/repair/phase12.1/semantic-appearance-20260908/`。未据目录名判断其内容、验收状态或可删除性，也未加入正式索引。

只暂存当前任务的明确路径。尤其不要为得到“干净状态”吸收子模块、压缩包或未跟踪 Proof，也不要从受限沙盒的权限错误推断文件真实删除。

## 2. 仓库从哪里读

| 问题 | 权威或入口 |
|---|---|
| 工作规则、验证强度、冻结证据如何处理 | [AGENTS.md](../../AGENTS.md)、[Agent 验证协议](../validation/agent-capability-evaluation.md) |
| 当前做到哪里／还有什么待办 | [STATE 顶部](../../.planning/STATE.md)；其旧 front matter、下方历史检查点不代表最新增量状态 |
| 产品长期约束、Phase 及当前阶段合同 | [PROJECT](../../.planning/PROJECT.md)、[ROADMAP](../../.planning/ROADMAP.md)、[phases](../../.planning/phases/) 内适用 SPEC／PLAN／VALIDATION |
| Type、材料、属性、配色与基础门窗范围 | [语义／外观主计划](../architecture/semantic-appearance-plan.md)；早期 presentation 边界只是历史证据 |
| 光庭设计及两版取舍 | [光庭设计](../architecture/courtyard-library-design.md)、[光庭 Proof](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md) |
| Token 实验及下一步对照 | [独立 Token 计划](../architecture/token-efficiency-plan.md)、[实验索引](../../dataset/processed/experiments/README.md) |
| 代码模块、公共入口与对应测试 | [接管指南项目地图](../how-to/agent-takeover.md#2-项目地图) |
| 数据、来源和旧路径 | [dataset 说明](../../dataset/data_organization.md)、[processed 索引](../../dataset/processed/README.md)、[manifests](../../dataset/manifests/README.md) |
| 人工查看 IFC、请求和报告 | [Proof 总入口](../../dataset/processed/proof/README.md)、[机器索引](../../dataset/processed/proof/PROOF-INVENTORY.json) |

新 Agent 不需要把长计划中的每个失败检查点当作待修问题。先看最新结果和实际实现，再按任务定位历史原因。已注册的 Schema／Prompt 保留多版本；运行版本要查调用参数和证据，不从目录最大版本号推定公共默认。

## 3. 已完成的整理和保留位置

`dataset/processed/` 已收敛为 `proof`、`experiments`、`derived`、`text2json`、`agent-demo`、`ifc-repair`、`ifc-repair-runs` 七个用途目录。职责详见 processed 索引，不再另设一套归档目录。

| 已完成事项 | 继续查证的位置 |
|---|---|
| 当前分支与 Zcode 的生产／合同／Proof 整合 | [首次 main 整合报告](../reports/main-integration-20260912/REPORT.md)、[后续 main 同步报告](../reports/main-sync-20260912/REPORT.md) |
| Zcode 原重构工作区保留 | [refactor-workspace.zip](../../archive/zcode-local-20260905/refactor-workspace.zip)；归档存在不表示其中全部设计已经实施 |
| 光庭及更早 Phase 开发目录退役 | [开发清理报告](../reports/development-cleanup-20260912/REPORT.md)、[实验入口](../../dataset/processed/experiments/README.md) |
| processed 派生目录归并、根 composite 清理 | [2026-09-13 整理报告](../reports/processed-cleanup-20260913/REPORT.md)、[80 份文件的路径映射](../../dataset/manifests/processed-layout-20260913.json) |
| 经明确批准的本轮删除 | [15 项清单](../reports/processed-cleanup-20260913/DELETE-LIST.md)、[执行回执](../reports/processed-cleanup-20260913/deletion-result.json)：97 文件、4,274,221 字节 |
| 无法核实权限的旧 Repair 材料 | [保留边界](../reports/processed-cleanup-20260913/retained-boundaries.json)，仍未删除 |

根目录的 `composite-evidence-setsem-*` 原为集合身份回归的模拟 Provider 输出，已按清单清除。相应源码 `tests/ifc_repair/test_draft_authority_set_semantics.py` 仍保留，已使用 `tmp_path`。不能把 raw-response 之类文件名当作真实调用证据。

`agent-demo`、两个 Repair 根目录和 `text2json` 仍有现行代码／测试消费者。已归档材料不反复搬迁；旧报告的历史路径通过 manifest 解释。`derived/.gitattributes` 保留原数据的换行检出约定，避免日后整理引起整批无意义重写。

## 4. 成品和验证状态

- Generation 的 A/B、C 型教学楼和光庭第二版已人工验收，入口统一在 Proof。光庭第一版是历史参考；A/B 中 B 的已知设计问题仍须随报告保留。
- Repair 保留 Plan07、R1 和 Zcode 的 C1–C5 等集合；材质／外观三例仍标记 `pending_human_review`，不能因其他案例已验收就改为完成。
- 双层社区阅读楼另有人工认可记录，但机器门禁仍 blocked；未计入 accepted machine 索引。具体状态由集合报告和机器记录分别说明。
- 本次目录整理没有重新生成 IFC、提升人工状态或宣称全仓发布通过。后续验证应另存结果，保持原始响应及验收依据。

最近工程验证的范围如下；这些是已有报告结果，本次文档更新不重复运行：

| 变更 | 已有验证 | 限制 |
|---|---|---|
| main 同步 `b4eb7ccf` | 43 项聚焦离线测试；光庭 IFC 重开与文件核对 | 不是完整 Full Preflight |
| processed 整理 `ae4e0272` | 50 项聚焦回归；10 份 Python 语法检查；迁移绑定与 Proof diff 检查 | 首次路径红例和 basetemp 父目录错误保留在报告；没有新 Provider 或完整 curator |

不要把历次重叠测试数量相加作为能力分母。当前指南中“存在正式 IFC”和“最终 accepted”也是不同状态。

## 5. 接续工作与尚未解决的边界

当前这轮只完成文档收尾。下一步需按用户的新任务选择，不默认同时启动下列工作：

1. **后续需要 main 同步时**，先比较远端增量；`ae4e0272` 及本轮文档仍在工作分支，不能报告 main 已包含它们。
2. **语义维护**：跨轮约束来源、适用范围与替代管理仍有后续小步，不把引用轮次存在等同于原话语义已被独立证明。范围以语义计划和光庭设计为准。
3. **Token 研究**：A/B/C 可用于同代码、同冻结输入和评价器的开发对照；T1 真实配对是局部可行性结果，C 的既定区域去重收益为零，原因已记录。后续实验要比较完整 loop 成本，保留失败分母，研究能力另需未见组。
4. **目录维护**：仅在有依赖证据和明确授权时继续处理未跟踪或权限不明项；此前清理批准不自动覆盖新目录。

日常维护只需同步 `STATE` 最新段落和相应索引；产品决定写回其既有计划，实验写入相应报告。只有执行阶段或重大边界改变时再补日期 handoff，避免同时维护多份“当前状态”。
