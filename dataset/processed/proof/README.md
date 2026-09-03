# BimNet Proof 证据根目录

本目录只收纳已经冻结、可追溯的 Proof 或历史证据包。“已收纳”不等于所有目录具有相同证据等级；每个集合必须以自己的 manifest、validator 和报告为准。失败运行继续保留在 dataset/processed/ifc-repair-runs，不会混入成功 Proof。

机器可读总索引见 [PROOF-INVENTORY.json](PROOF-INVENTORY.json)。

## 当前权威集合

| 目录 | 证据类型 | 当前用途 |
|---|---|---|
| ifc-repair-success-cases/ | 冻结 repair success collection；包含合法 original/damaged/repaired 三元组、输入、ChangeSet 和验证材料 | IFCCompare、跨版本回归、Plan 07 accepted structural Proof |
| repair-milestone-r1/r1-20260902T152701658266Z-curated/ | R1 Proof 0.3，12 案独立复算 | R1 与 Phase 12/12.1 闭合权威 |
| phase12-plan07-final/uat-20260902T180900748385Z/ | final-code 四案兼容性 Proof 包；完整 raw run、admission、source fixture 和最终报告 | 证明最终代码仍为 4/4；不冒充第二份 curator-installed Proof |
| phase11-live-uat/ | Phase 11 历史 live UAT 包 | 历史追溯，不用于提升 R1 结论 |
| text2ifc-success-cases/ | Text-to-IFC 生成成功案例 | 生成链路证据，不是 repair 三元组证据 |

## IFC 三种角色

合法三元组必须在运行前已经具有以下角色和边界：

1. original / pristine：损伤前的 evaluator-only Ground Truth；
2. damaged：唯一允许进入 repair production path 的 IFC 输入；
3. repaired：由 damaged 输入实际生成并通过 reopen、L0/L1/L2、preservation 与发布门槛的输出。

不能在看到 repaired 结果以后再指定某个文件为 original，也不能根据结果补写 mutation truth。这样得到的“Gold”会发生数据泄漏，不能用于独立 IFCCompare。

## 为什么 R1 没有 12 组三元组

R1 的 E1-A1 是 frozen diversity/request-contract 案例。它们从真实 source.ifc/damaged 输入出发，验证 property authority、target resolution、clarification identity、atomicity、preservation、reopen 和 L0/L1/L2；它们不是由一份预先冻结的 pristine IFC 按 private mutation recipe 制造出来的 benchmark。

因此 R1 的合法 artifact 形态是：

- 11 案：source.ifc → repaired.ifc；
- H4：source.ifc → no output，并证明零 mutation、零 publish；
- 0/12 案拥有可用于独立 IFCCompare 的 R1 private triplet。

这不是执行证据缺失，而是评估设计不同。为 R1 事后补造 original 会降低证据可信度，所以明确标记 IFCCompare 为 N/A。真正具备 pre-declared private truth 的三元组继续由 ifc-repair-success-cases/ 承担。

## 本次整理做了什么

- 保持既有 accepted Proof append-only，不移动、不重命名；
- 为所有顶层 Proof 集合建立统一索引；
- 将 final-code Plan 07 四案的 238 个 payload 文件集中复制到新的 Proof 包：raw Provider/runtime 过程、零网络 admission、公共 damaged 输入和 evaluator-only original/mutation truth；
- 写明 Plan 07 两个 accepted、strict-recomputed structural bundle（含物理三元组但 private triplet audit 为 N/A）、一个 source/repaired semantic canary 和一个 no-output guard 的不同证据等级；
- 保留当前 curator 对 changed-scope admission 布局的兼容限制，不将其改写成语义或 IFC 失败。

## 校验入口

    .venv\Scripts\python scripts\ifc_repair\validate_success_cases.py --json
    .venv\Scripts\python scripts\ifc_repair\assemble_repair_milestone_r1_proof.py --help
    .venv\Scripts\python -m pytest tests\ifc_repair\test_target_query_filling_geometry.py -q

各集合的完成声明必须来自对应 validator 的最新结果，而不是本索引本身。
