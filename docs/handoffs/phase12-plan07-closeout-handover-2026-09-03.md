# Phase 12 Plan 07 收尾与 IFC Repair 技术 Handover

日期：2026-09-03

分支：codex/workflow-dataset-links

面向对象：继续维护 IFC repair、检查 Plan 07 Proof 或接续 R1 的开发者/Agent

## 1. 当前结论和阅读顺序

Plan 07 修正后的证据已按人读优先结构放入 [Plan 07 人工 Proof 入口](../../dataset/processed/proof/ifc-repair-success-cases/PLAN07-REPORT.md)。该 review manifest 当前仍是 pending_human_review；它没有被写入成功案例集合的主 accepted manifest，也不包含 R1。

建议按以下顺序接手：

1. 先读本 handover，理解代码与证据边界。
2. 打开 Plan 07 总报告，并逐案检查案例根目录的 original、damaged、repaired IFC。
3. 从案例的 FILES.json、validation/ 和 evidence/README.md 回到 append-only machine authority。
4. 人工认可后，才讨论 Plan 07 review manifest 的 accepted 安装或状态更新。
5. R1 使用自己的 Proof 集合继续处理，不把两个集合的成功行拼接。

当前人读 Plan 07 集合包含 10 案：6 个离线确定性 restoration/atomicity 案，3 个 genuine Provider repaired 案，以及 1 个正确无输出的 unsupported guard。Genuine run ID 为 uat-20260903T095045509630Z，总 Provider calls 为 11。

## 2. 项目分层

| 层 | 主要位置 | 职责 |
|---|---|---|
| 规范与计划 | .planning/、docs/validation/ | Phase SPEC、冻结 Plan、验证合同、能力和 Proof 边界 |
| Prompt 与 Schema | prompts/、schemas/ | Stage 1/Stage 1.5/Stage 2 的版本化输入输出合同 |
| Repair 核心 | src/text2ifc_ifc_repair/ | IFC 索引、解析、澄清、ChangeSet、原子应用、评估和发布 |
| 属性知识 | src/text2ifc_knowledge/ | IFC2X3 PSD/project records、BGE/Qdrant 检索与运行时知识 |
| IFC 基础能力 | src/text2ifc_extractor/、src/text2ifc_compiler/ | IFC 读取、几何/关系抽取和通用编译辅助 |
| Operation 插件 | src/text2ifc_ifc_repair/operations/ | Window、Door、Opening、Beam、Column 等确定性操作 |
| 执行入口 | scripts/ifc_repair/ | 离线矩阵、live UAT、R1、Proof 安装与验证 |
| 回归测试 | tests/ifc_repair/、tests/knowledge/ | 阶段 seam、完整离线链路、安全门和证据布局 |
| 原始运行 | dataset/processed/ifc-repair-runs/ | Provider attempts、clarification、index、staging、terminal evidence |
| Proof | dataset/processed/proof/ | 人工检查视图和不可变机器权威 |

更完整的历史与架构说明见 [IFC Repair Pipeline 与 Roadmap](../architecture/ifc-repair-pipeline-status-and-roadmap.md)。

## 3. Repair Pipeline

一次生产 repair 的数据流如下：

    public request + damaged IFC
      -> input/schema check and source fingerprint
      -> IFC index
      -> Stage 1 RepairIntent
      -> target/type resolution or clarification
      -> property retrieval + Stage 1.5 + admissibility
      -> Production Evidence + Semantic Manifest
      -> Stage 2 ChangeSet Draft
      -> deterministic binder + audit
      -> one in-memory atomic apply to staging IFC
      -> reopen from disk
      -> L0/L1/L2 + preservation
      -> terminal publication or fail-closed evidence

### 3.1 输入、状态和 Stage 1

RepairAPI.start 是公共行为入口。它先校验 damaged IFC 为 IFC2X3、记录 source fingerprint 和 run 状态，再由 request_stage.generate_repair_intent 调用 Provider 生成 RepairIntent。模型只表达 operation、target query、尺寸、Type 或属性意图；模型不生成 STEP，也不直接获得写 IFC 的权限。

缺少参数或目标不唯一时，同一个 run 进入 clarification_required。继续请求必须同时绑定 clarification_id 和 state_version，过期回答会被拒绝。

### 3.2 IFC Index、Target 与属性

indexer.py 和 index_store.py 把 occurrence、Type、GlobalId、Name、Storey、host/opening/fill、几何摘要、Pset/Qto/material/classification 写入可查询索引。

target_query.resolve_target 组合 class、storey、name 和 geometry 等硬约束。候选身份只能从当前 offered candidate set 选择，不能靠历史 alias、手写 phrase table 或错误 LLM 输出映射绕过。

自然语言属性由 property_resolution_coordinator 组织：retrieval 先返回 authoritative Top-K，Stage 1.5 只能在这组候选中选择，property_admissibility 再复核 class、template、value type、unit、scope 和 decision binding。只有通过后才生成 ExactPropertyIntent。

### 3.3 Stage 2、绑定和审计

provider_stage.generate_bound_changeset 向 Stage 2 提供已解析 operation、有界实体证据与 semantic authority。Provider 返回的是 ChangeSet Draft。

changesets.bind_repair_changeset 将 Draft 绑定到 damaged IFC fingerprint、真实目标、已授权 Type 和 Semantic Manifest。registry.py 选择 operation handler；production_evidence.py 建立写入与 L2 共用的权威。任何越权引用、未提供身份、缺少 semantic authority 或 schema 不一致都必须 fail closed。

### 3.4 原子应用、重开和发布

apply.apply_changeset 在内存中执行整份 ChangeSet，并只向 staging 写候选 IFC。多个 operation 属于一个事务，任一失败都不能部分发布，源 damaged IFC 不得原地修改。

RepairOrchestrator.apply_and_evaluate 核对源 fingerprint、事务完整性和 source immutability，再从磁盘重开 candidate。evaluation.py 与 benchmark_evaluation.py 复核：

- L0：文件存在、IFC2X3、可重新打开及基本执行结果；
- L1：请求相关几何、placement、Storey、host/void/fill、修改范围与 preservation；
- L2：Type、property、material/classification/quantity 等适用的 semantic authority；
- 原子性：operation IDs、apply 与 audit 一致，无半事务；
- 保存性：非授权对象和关系没有意外变化。

run_artifacts.publish_terminal_artifacts 只有在 successful_artifact_publishable 为真时发布 successful/repaired.ifc。失败候选只能作为 diagnostic artifact；unsupported guard 必须零 mutation、零 publish。

## 4. 最关键代码入口

| 文件 | 接手时重点 |
|---|---|
| src/text2ifc_ifc_repair/api.py | 公共 start / continue / resume、状态转换、Provider 两阶段编排 |
| src/text2ifc_ifc_repair/run_store.py | durable run、state_version、clarification 与 terminal 状态 |
| src/text2ifc_ifc_repair/request_stage.py | Stage 1 Prompt、RepairIntent schema、公开上下文和 attempt 保存 |
| src/text2ifc_ifc_repair/indexer.py | damaged IFC 的 production-visible 索引事实 |
| src/text2ifc_ifc_repair/target_query.py | 目标硬约束、候选证据和 offered set |
| src/text2ifc_ifc_repair/resolution_flow.py | occurrence/type/property 解析与澄清分流 |
| src/text2ifc_ifc_repair/property_resolution_coordinator.py | retrieval、Stage 1.5、resume identity 的 durable 协调 |
| src/text2ifc_ifc_repair/property_admissibility.py | 属性身份、类型、单位、scope 与 offered-set 最终门 |
| src/text2ifc_ifc_repair/provider_stage.py | Stage 2 Draft 生成和 authority 输入边界 |
| src/text2ifc_ifc_repair/changesets.py | Draft 到 Bound ChangeSet 的确定性绑定 |
| src/text2ifc_ifc_repair/production_evidence.py | applicator 与 L2 共用 semantic authority |
| src/text2ifc_ifc_repair/operations/structural_member.py | Beam/Column placement、截面、Type 与 IFC authoring |
| src/text2ifc_ifc_repair/apply.py | 单事务 apply、staging、reopen 与失败回滚 |
| src/text2ifc_ifc_repair/orchestrator.py | apply、evaluation、terminal publication 的总门 |
| src/text2ifc_ifc_repair/evaluation.py | 独立 reopen、L1/L2、scope、source immutability 与 preservation |
| src/text2ifc_ifc_repair/run_artifacts.py | 成功 IFC、诊断候选和终端 manifest 的原子发布 |

常用脚本：

- scripts/ifc_repair/run_phase12_offline.py：Phase 12 离线矩阵和属性检索评估；
- scripts/ifc_repair/run_phase12_live_uat_v2.py：Plan 07 genuine UAT；
- scripts/ifc_repair/run_repair_milestone_r1.py：R1 连续 12 案；
- scripts/ifc_repair/install_plan07_human_proof.py：构建/验证当前人读 Plan 07 视图；
- scripts/ifc_repair/validate_human_proof_layout.py：检查必要文件、IFC 重开、角色与 authority path。

## 5. Plan 07 证据在哪里

人工入口：

- [Plan 07 总矩阵](../../dataset/processed/proof/ifc-repair-success-cases/PLAN07-REPORT.md)
- [Plan 07 review manifest](../../dataset/processed/proof/ifc-repair-success-cases/plan07-manifest.json)

代表性案例：

- [Live Beam + Column complete](../../dataset/processed/proof/ifc-repair-success-cases/structural/batch/phase12-plan07-live-beam-column-complete/REPORT.md)
- [Offline Beam restoration](../../dataset/processed/proof/ifc-repair-success-cases/structural/single/phase12-v2-vvo-beam-loadbearing-restoration/REPORT.md)
- [Unsupported program guard](../../dataset/processed/proof/ifc-repair-success-cases/guard/unsupported/phase12-plan07-live-structural-program-guard/REPORT.md)

成功案根目录直接放 01-original.ifc、02-damaged.ifc、03-repaired.ifc、REPORT.md 和 FILES.json。Guard 只有 02-damaged.ifc 与 NO-REPAIR.md，故意没有 repaired IFC。

离线 case 的 original 是运行前冻结的 damage truth，可用于相应 restoration comparison。Live case 的 original 只标为 physical_fixture_non_private_audit，不能事后冒充 case-specific private Gold；因此其 private IFCCompare 为 N/A，但 genuine execution、reopen 与 case-local L0/L1/L2 仍可独立检查。

完整 machine authority 继续保留在 dataset/processed/proof/ifc-repair-success-cases-v2-plan07-staging/ 和对应 raw run，不因人读视图而移动或改写。

## 6. 已发生的严重错误与通用修正

旧 Plan 07 Beam/Column 结果出现构件远离建筑的问题。定位结论是：错误在 repair 前的 fixture/request 层，不是 applicator 擅自移动。旧 runner 把约 100000 至 210000 mm 的远端占位坐标冻结进 operation；applicator 随后忠实执行了这些坐标。文件变大主要来自新增 IFC representation、placement、relationship 与序列化实体，文件大小本身不能证明恢复正确。

处理方式不是给某个 GlobalId 或坐标加特例，而是：

1. 撤销旧 offsite Proof 的有效性；
2. 改用 VVO 中能可靠重建的真实水平矩形 Beam 和竖直矩形 Column；
3. 从 source snapshot 提取 Storey-local axis、截面、方向与语义，生成 damage/request；
4. 新增 structural restoration audit，比较删除目标与 repaired occurrence；
5. 线性误差容差为 0.01 mm，方向容差为 0.1°；数百毫米或数百米错位仍必然失败；
6. 圆柱、映射表示或无法可靠反演 placement 的构件不勉强构造 repair fixture，应更换合法 IFC/目标。

完整记录见 [Plan 07 Structural Restoration Erratum](../validation/ifc2x3-changeset/phase12-plan07-structural-restoration-erratum-2026-09-03.md)。

## 7. 仍需注意的问题

### 7.1 Type 绑定不等于视觉一致

Beam/Column 精确复用现有 Type 时，当前 L1/L2 能证明 Type relationship、几何、Storey 与属性，但不自动证明 Viewer 中的颜色/材质外观一致。Type 的 IfcRelDefinesByType、RepresentationMap、Material association 和 StyledItem 是不同层。A1 暴露了新构件可能显示默认灰色的问题。

不要把视觉问题通过放宽 L1/L2、复制固定长度 geometry 或样例特判解决。后续应按 [Structural Type Visual Fidelity 计划](../validation/ifc2x3-changeset/phase12-structural-type-visual-fidelity-plan-2026-09-03.md) 增加 representation/style authority 和专门 visual fingerprint gate。

### 7.2 失败 run 与成功 Proof 分开

失败 genuine Provider attempt 不得进入成功 Proof，也不能被后续成功结果重标记。项目合同要求保留真实 attempt 供审计；可以把它标记为 superseded 或迁入有索引的冷归档，但不能直接抹除。离线 pytest、admission、preflight 缓存和逐文件相同的重复 proof 副本可以删除。

### 7.3 不要过度运行 curator

README、链接或纯人读报告更新只需路径与布局检查。只有安装/重新整理 accepted run、修改 curator/schema/evidence semantics，或冻结 release contract 明确要求时才跑 full curator。安全门、offered-set、admissibility、source immutability 和 preservation 不得因此弱化。

### 7.4 Truth boundary

Provider 只能看到 public request、damaged IFC 派生事实、当前候选和有限 Stage 2 authority。Pristine/original IFC、private Gold、mutation/deletion truth 和 benchmark expected labels 只能在 repair 后进入 evaluator。

## 8. 本次目录整理

已删除：

- 顶层 pytest/Python 临时缓存；
- 多组不含 Git 跟踪文件的旧离线 admission、background-preflight 与 preflight 工作目录；
- 与已提交 R1 curated 包逐路径、逐文件大小一致的 646 MiB 未跟踪重复副本；
- Plan 07 收尾过程中生成的 .test-tmp。

已保留：

- genuine Provider 成功与失败 attempts；
- 所有已提交 machine authority、repaired IFC 和 terminal evidence；
- .cache 中的本地检索模型/依赖；
- R1 原始 run 与 curated Proof。

一个 2026-08-20 的旧离线 preflight 内含错误 ACL 的 pytest 目录，当前账户即使是 owner 也不能递归删除。它不是真实 Provider run、未被 Git 跟踪，也不影响 Proof；需要在具有 Windows ACL 管理权限的终端中单独清理。不要为删除它而 reset 或 clean 仓库。

外部论文与 Matterport 条款从仓库根目录整理到 dataset/sources/PAPERS/ 和 dataset/sources/LICENSES/Matterport/，内容按 Git blob 精确一致处理。

## 9. 最小验证与后续动作

文档/布局收尾的最小命令：

    .venv\Scripts\python -m pytest tests\ifc_repair\test_plan07_human_proof_install.py -q
    .venv\Scripts\python scripts\ifc_repair\install_plan07_human_proof.py --validate-only
    .venv\Scripts\python -m compileall scripts\ifc_repair\install_plan07_human_proof.py
    git diff --check

这组验证只证明当前 Plan 07 人读视图、IFC 可发现性/重开和安装脚本没有回退；它不替代 R1 frozen Proof，也不构成新的模型能力评测。

后续接续点：

1. 用户检查 Plan 07 的 9 份 repaired IFC 和 1 个 NO-REPAIR guard；
2. 通过后，按冻结合同决定是否把 review manifest 安装为 accepted；
3. 单独复核 R1 的人读矩阵与 visual fidelity 限制，不把 Plan 07 结果拼入 R1；
4. 不启动 Phase 13，除非新的计划与授权明确允许。

## 10. Git 边界

本轮只提交 Plan 07 closeout 文档、Proof 导航、数据来源的精确移动和必要规范。未使用 reset、clean、restore 或 add -A。任何仍未跟踪的 raw run 都不是自动删除目标；任何与本任务无关的用户修改保持原状。
