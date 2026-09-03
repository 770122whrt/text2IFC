# BimNet Proof 证据根目录

本目录只收纳已经冻结、可追溯的 Proof 或历史证据包。“已收纳”不等于所有目录具有相同证据等级；每个集合必须以自己的 manifest、validator 和报告为准。失败运行继续保留在 dataset/processed/ifc-repair-runs，不会混入成功 Proof。

机器可读总索引见 [PROOF-INVENTORY.json](PROOF-INVENTORY.json)。人类可读收纳标准见 [IFC Repair Proof 人类可读收纳规范](../../../docs/validation/ifc-repair-proof-format.md)。

## 当前权威集合

| 目录 | 证据类型 | 当前用途 |
|---|---|---|
| ifc-repair-success-cases/ | 已接受历史案例，以及独立 plan07-manifest.json 管理的 Plan 07 待人工检查批次 | IFCCompare、跨版本回归、Plan 07 人工验收入口；不能把 review manifest 当作主 manifest accepted |
| repair-milestone-r1/ | [人类入口](repair-milestone-r1/README.md) + `r1-20260902T152701658266Z-curated/` 机器权威 | R1 12 案报告、直接可见 IFC 与 Proof 0.3 |
| phase12-plan07-final/ | [人类入口](phase12-plan07-final/README.md) + `uat-20260902T180900748385Z/` 机器权威 | final-code 四案兼容性 Proof；不冒充第二份 curator-installed Proof |
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

## 人类阅读入口

- [Phase 12 Plan 07 待人工检查矩阵](ifc-repair-success-cases/PLAN07-REPORT.md)
- [Repair Milestone R1 总报告](repair-milestone-r1/REPORT.md)
- [Phase 12 Plan 07 总报告](phase12-plan07-final/REPORT.md)

成功案的 repaired IFC 直接放在各自案例根目录。Plan 07 新视图使用 operation family / case kind / case-id；R1 与旧 final-code 集合使用各自已发布的布局。H4 和 program-guard 没有 repaired IFC 是冻结安全合同的正确结果，并在各自 NO-REPAIR.md 中解释。

## 校验入口

    .venv\Scripts\python scripts\ifc_repair\validate_success_cases.py --json
    .venv\Scripts\python scripts\ifc_repair\assemble_repair_milestone_r1_proof.py --help
    .venv\Scripts\python scripts\ifc_repair\validate_human_proof_layout.py --root dataset\processed\proof\repair-milestone-r1 --json
    .venv\Scripts\python scripts\ifc_repair\validate_human_proof_layout.py --root dataset\processed\proof\phase12-plan07-final --json
    .venv\Scripts\python -m pytest tests\ifc_repair\test_target_query_filling_geometry.py -q

根据变更风险选择验证器；README 或导航更新不自动要求重复 curator。各集合的完成声明仍必须来自适用的冻结合同与对应 validator，而不是本索引本身。
