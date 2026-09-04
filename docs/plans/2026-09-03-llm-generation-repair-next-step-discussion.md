# LLM Generation / IFC Repair 下一阶段执行计划（Discussion Draft）

> 首次记录：2026-09-03  
> 最近更新：2026-09-04（根据与老师讨论后的数据路线重新排序）  
> 状态：**Discussion Draft — 未经人工确认，不应作为执行授权。**  
> 目的：把“下一步怎么做”拆成可讨论的工作包。本文明确优先级、依赖、建议产物、人工审查点和待决策项；具体实现细节需要与用户讨论后再冻结。

## 1. 执行原则

当前优先级已经进一步明确：**近期先做 Generation Demo Paper，Repair 留作后续更大的文章。** 两条工作流需要分开推进，不再用同一个“先盘数据再做所有事情”的顺序。

### Generation 路线

当前已有 IFC 已经足够支撑 Generation Demo Paper，因此 Generation 不等待新数据收集，直接进入：

```text
已有 Generation 数据 / 场景
  -> scaling
  -> visual quality / color / material
  -> stability / repeated runs
  -> curated Demo Set
  -> Demo Paper 展示
```

### Repair / Post-training 路线

Repair 与后训练的数据规模仍然不足，需要持续扩大真实源 IFC 池：

```text
统计当前真实 Source IFC
  -> 收集更多公开真实 IFC
  -> license / schema / quality admission
  -> 构造约 40-case Repair Benchmark v1
  -> 加强 IFCCompare / IfcDiff 使用
  -> quantitative evaluation + Token / Context
  -> 继续扩充真实 IFC
  -> 若仍不足，再用 Generation 生成 IFC 补充
  -> Post-training data
```

这里的优先级原则是：**真实外部 IFC 优先，Generated IFC 兜底。** Generated IFC 不与真实来源混合统计，必须保留 provenance 标签。

Repair Loop 已明确不进入当前范围。

同时继续遵守当前工作模式：

- 小模块只做小模块级检查；
- 不因为文档或局部数据整理自动触发 repository-wide full preflight；
- 如果后续任务需要 full preflight、真实 Provider 大规模调用、正式 benchmark 重新验收，应先向用户请求批准；
- 文档和计划可以先形成讨论稿，但生产代码、正式 benchmark 合同和验收阈值应在讨论后再改。

---

# 2. P0 工作包

## WP0 — 冻结本阶段研究问题和论文实验边界

### 目标

在写新代码前，先明确下一阶段论文真正要回答什么，避免 Demo、benchmark、token、loop 同时无边界扩张。

### 建议冻结的研究问题

建议至少讨论以下 4 个主问题：

**RQ1 — Repair Reliability**  
Agentic Repair 在不同 IFC、不同实体类型和不同 damage 类型上，目标恢复、语义满足和 preservation 能做到什么程度？

**RQ2 — Safety / Evidence Isolation**  
在不向 Agent 暴露 Original / deleted identity / private Gold 的情况下，Repair 是否仍能有效完成？系统是否可以证明没有利用 benchmark oracle？

**RQ3 — Context Efficiency**  
Bounded structured evidence 相比更完整 context 能否显著减少 token / latency，同时保持 repair success、semantic accuracy 和 safety？

**RQ4 — Iterative Repair**  
Production-safe evaluator / audit issue 能否驱动第二轮局部修复，并提高 final success，而不引入更多 unintended edits？

### 建议产物

- 一页 `research-questions.md` 或论文实验设计说明；
- 明确每个 RQ 对应哪些数据、指标和 ablation；
- 明确 Demo 只负责展示，benchmark 才负责定量结论。

### 人工审查：必须

需要用户确认：

1. Demo Paper 是否只要求展示，还是需要同时承担完整定量实验？
2. Token efficiency 是否上升为主创新点，还是作为 ablation / efficiency section？
3. Repair Loop 是否进入当前论文，还是保留下一篇工作？
4. Generation 和 Repair 在论文中的比例：Repair 为主、Generation 为系统入口，还是二者并列？

### 当前建议

当前方向已确认：**这一篇 Demo Paper 以 Generation 为主，Repair 留作后续更大的文章；Token / Context Efficiency 可以暂定为潜在主贡献，但等受控实验后再最终冻结。Repair Loop 当前不进入。第一代 Repair benchmark 目标约 40 cases。**

---

## WP1 — 建立统一 IFC Dataset Inventory

### 目标

把目前分散的 raw manifest、授权 manifest、repair benchmark manifest、外部 corpus 和已处理 IFC 汇总成一份机器可读 inventory，并输出人读摘要。

Inventory 必须服务于两条不同目标，因此不能只给一个笼统的 `usable`：

- **Generation View**：回答哪些现有 IFC / generated scenes 已经足够用于 Demo、scaling reference、视觉质量比较。当前判断是 Generation 数据量已经够，重点是质量和稳定性，不以继续找更多 IFC 为前置。
- **Repair / Post-training View**：回答真实源 IFC 还缺多少、哪些可用于 Damage/Repair、哪些适合 property / retrieval、哪些来源允许后续训练或公开展示。该视图需要持续扩充。

建议每条记录至少增加：

- `data_origin`: `real_external | authorized_local | generated_internal | derived_repair_artifact`；
- `generation_role`；
- `repair_role`；
- `post_training_eligible`；
- `public_redistribution_status`；
- `source_family` / project family，用于 leakage control。

### 当前已经确认的数据池

本轮重新检查 `dataset/external` 后，上一版“正式 benchmark 都偏大，因此可能缺少小 IFC”的判断需要修正。

当前本地 source IFC 粗略统计为：

- `dataset/ifc/`：26 个已授权、已审计的 BIMNet IFC2X3；
- `dataset/external/bim-whale-ifc-samples/`：6 个 IFC，manifest 记录 6/6 为 IFC2X3 reopen-eligible；
- `dataset/external/ifc-bench/`：当前本地树中 50 个 IFC，manifest 记录其中 27 个为 IFC2X3 reopen-eligible；
- `dataset/external/buildingsmart-official/`：10 个 IFC，当前为 IFC4 / IFC4X3 样例。

因此当前本地可见 source IFC 总量约为 **92 个文件**，其中至少 **59 个已有 IFC2X3 可打开/可评估记录**。第一代约 40-case Repair benchmark 的主要问题不是文件数量不足，而是 suitability、任务覆盖、合法 Ground Truth 和 case diversity。

已经确认的小型真实候选包括：

- BIM Whale `SimpleWall.ifc`：IFC2X3，39,818 bytes，579 STEP lines；README 明确包含 1 Wall + 1 Door + `Custom_Pset`；
- `ManySimpleWalls.ifc`：IFC2X3，584,056 bytes，9,807 STEP lines；many Walls + many Doors + `Custom_Pset`；
- IFC-Bench West Riverside Hospital `fire_ifc2x3.ifc`：874 products；
- `str_ifc2x3.ifc`：2,915 products；
- `elec_ifc2x3.ifc`：6,305 products。

注意：STEP lines、Products 和 IfcOpenShell total entity count 不是同一个统计口径，正式 inventory 仍应统一重算。

### 建议实现方式

新增一个只读 inventory builder，不修改原 IFC：

```text
scripts/dataset/build_ifc_research_inventory.py
```

输出建议：

```text
dataset/manifests/ifc-research-inventory.jsonl
dataset/processed/review/ifc-research-inventory-summary.md
```

### 自动字段

建议程序自动计算：

- stable inventory id；
- local path；
- source corpus / source manifest id；
- SHA-256；
- bytes；
- IFC schema；
- IfcOpenShell open status；
- total entity count；
- IfcProject / Site / Building / BuildingStorey / Space 数量；
- Wall / Window / Door / Slab / Roof / Stair / Beam / Column 数量；
- valid Window-Opening-Wall chain count；
- valid Door-Opening-Wall chain count；
- property-bearing occurrence count；
- storey count；
- geometry generation success / sampled geometry status；
- current approved use / license metadata；
- duplicate SHA / scene-family group。

### 不建议自动判死的字段

以下字段建议机器生成候选值，但最终需要人工审查：

- `experiment_ready`；
- `demo_quality`；
- `generation_demo_suitability`；
- `repair_benchmark_suitability`；
- `property_retrieval_suitability`；
- `visual_quality`；
- `publication_screenshot_ok`。

### 建议四级状态

```text
raw
valid
experiment_ready
demo_quality
```

注意这四级应是不同 gate，而不是一个自由文本标签。

### 验证范围

本工作包是数据读取 / 报告类工作，不应触发 full Repair preflight。

建议最小验证：

- inventory builder focused tests；
- manifest path / SHA / schema consistency；
- 随机抽样 IFC reopen；
- 自动计数和已有 benchmark manifest 的交叉核对。

### 人工审查：必须

用户需要审查：

- 视觉质量；
- license / public screenshot 使用；
- borderline experiment-ready；
- 是否排除明显异常或过大的 IFC。

### 已冻结的扫描范围原则

第一轮真实 Source Inventory 扫：

```text
dataset/ifc/**.ifc
dataset/external/**.ifc
```

`dataset/processed/**.ifc` 不并入真实 Source Inventory，因为其中包含 generated / damaged / repaired / proof artifact。后续如需要统计这些产物，应建立独立的 Generated / Derived Artifact Inventory。

---

## WP1.5 — 公开 IFC Source Expansion（Repair / Post-training 专用）

### 目标

持续扩大 **真实源 IFC 数量**。这一工作包服务 Repair 和 Post-training，不是 Generation Demo Paper 的前置依赖。

### 收集优先级

按以下顺序执行：

```text
A. 已在本地但尚未完整 admission 的公开 IFC
   -> 先吃完现有 external 数据

B. 官方 / 学术 / 开源公开 IFC repository
   -> buildingSMART samples
   -> openBIM / university repositories
   -> GitHub / Hugging Face 等明确许可的数据集
   -> 论文附带数据或 benchmark repository

C. 其他可合法获得的真实 IFC
   -> 必须保留来源、revision、license 和使用边界

D. 如果真实公开 IFC 仍不足
   -> 使用 Generation Pipeline 生成补充 IFC
   -> 标记 generated_internal
   -> 不与 real-source 主结果混合
```

### 收集目标不是“凑文件数”

每增加一批源 IFC，都要统计它能带来多少后续可用产出：

```text
1 Source IFC
  -> N target entities
  -> N damage candidates
  -> N repair cases
  -> retrieval / property samples
  -> trajectory / correction samples
```

因此长期数据规模应同时报告：

- Source IFC count；
- unique source family count；
- admitted IFC2X3 count；
- repairable target count；
- generated Damage/Repair case count；
- training / post-training sample count。

### Admission 条件

公开收集来的 IFC 不自动进入 benchmark。至少检查：

- provenance / URL / repository / revision；
- license 和论文、训练、再分发边界；
- IFC schema；
- IfcOpenShell reopen；
- entity / target capability；
- geometry basic health；
- duplicate / near-duplicate source family；
- Repair / Property / Retrieval suitability。

### 人工审查：必须

- license / redistribution / training eligibility；
- 高价值数据源是否值得完整下载；
- source family 是否重复；
- 是否纳入真实 benchmark 主池。

### 2026-09-04 初步公开 Source Candidate Pool

本轮网络调研先确认以下高价值来源，后续应逐个做 download / license / schema / duplicate audit，而不是直接全部 admission：

1. **buildingSMART Community Sample Test Files**  
   GitHub: `buildingsmart-community/Community-Sample-Test-Files`。包含 IFC2X3 等多个 schema 的大量 sample/test files；贡献文件按仓库说明以 CC BY 4.0 发布，但仓库也明确提醒不少文件未必能通过完整 validity check，因此适合作为大候选池，不能无审查直接进 benchmark。

2. **IFC-Bench**  
   Hugging Face / GitHub 数据集，22 个 BIM projects、约 51 个 IFC models，包含 architectural / structural / MEP / specialty 多专业模型。当前本地已经有一份副本，但仍应继续把它作为 model-family / license / task diversity 的正式来源管理。IFC 模型保留各项目自身 license，不能只按 QA 数据集的 CC BY 4.0 统一处理。

3. **BIMData R&D Open Models Index**  
   BIMData 整理了约 40 个 BIM models、100+ IFC files，来源覆盖 DURAARK、OpenIFC Model Repository、BIMcollab、Schependomlaan、NIBS 等；页面说明若未特别注明，多数为 IFC2X3 且经常是 architectural。它更适合作为“公开 IFC 来源索引”，实际 admission 时必须回到原始 source 核对 license 和下载内容。

4. **OpenIFC Model Repository / University of Auckland**  
   BIMData 索引和 IFC-Bench 均引用该来源，适合补充真实 multi-discipline / large-building IFC。优先检查 architectural、hospital、conference-center 等已有公开模型，并避免与 IFC-Bench 本地副本重复。

5. **BIMcollab Example Project**  
   BIMcollab 当前公开提供 example project IFC 下载；官方帮助页说明示例项目由 9 个 IFC models 组成，覆盖 architecture、structure、MEP 等专业。适合做跨专业 repair / property 候选，但需要单独确认使用与再分发条款。

6. **IfcOpenShell/files**  
   IfcOpenShell 官方组织维护的 public test files repository，包含大量 wall / beam / geometry / regression IFC。非常适合补充 edge-case、geometry robustness 和 regression slice，但其中不少文件本身就是 bug / invalid / known-error fixture，因此不应与正常真实建筑 benchmark 混合；license 也需要单独核实后再决定训练用途。

7. **KIT IFC Examples / IFC Wiki**  
   KIT 页面提供 FZK Haus、Office Building、Smiley West 等 example；页面明确这些 examples 可 unrestricted use 并要求出版时注明来源。当前页面主要列 IFC4/4x 系列，因此更适合后续 schema expansion 或 Generation reference，不是 IFC2X3 Repair 主池的第一优先级。

8. **STEP Tools IFC Sample Data**  
   提供 IFC2X3 / IFC4 混合 sample，例如小型 NIST steel examples，适合作为小型结构/几何补充候选；仍需逐文件核对来源和许可。

第一批实际扩充建议优先级：

```text
P0: buildingSMART Community Sample Test Files
    + BIMData R&D 所指向的原始 IFC2X3 source
    + OpenIFC Model Repository

P1: BIMcollab Example Project
    + IFC-Bench 中尚未重复 admission 的 families

P2: IfcOpenShell/files / STEP Tools / KIT
    -> edge-case / robustness / schema expansion
```

### Generated IFC 的兜底规则

只有在真实公开 IFC 扩充之后仍然无法满足 Repair / Post-training 的规模或任务覆盖时，才启动 Generation-based dataset expansion。

Generated IFC 必须：

- 与 Generation Demo 输出分开管理；
- 记录 generation prompt、model、pipeline version 和 hash；
- 标记 `generated_internal`；
- benchmark 表中单独形成 synthetic/generated slice；
- 不用于夸大“真实 IFC 数量”。

---

## WP2 — Generation Demo Set 筛选

### 目标

选 3–5 个 Demo IFC，形成真正面向论文和系统展示的 curated set。

### 推荐分工

这一篇 Demo Paper 只围绕 Generation 展示组织，不要求把 Repair Demo 塞进主展示集合。建议 3–5 个 Generation Demo 按复杂度和视觉表现分层，例如：

1. **Simple Stable**：单层、较少房间/构件，用来证明稳定最小闭环；
2. **Scaled Layout**：更多房间、更多 Wall / Window / Door；
3. **Multi-storey / Richer Composition**：有限多楼层或更复杂构件组合；
4. **Visual-quality Demo**：颜色、材质、构件区分明显，适合论文截图和现场展示；
5. **Optional Stress Demo**：在不牺牲稳定性的前提下展示更大规模。

一个 Demo 可以承担多个角色，但最终展示最好不要所有案例都来自同一 prompt 模板或同一几何布局。

### 自动初筛规则

自动筛选 / generation acceptance 可考虑：

- IFC2X3；
- open / reopen success；
- expected Wall / Window / Door / Space / Storey 完整；
- hosted-opening relations 正确；
- geometry gate 通过；
- 颜色 / material assignment 可稳定生成或复用；
- 多次重复运行成功率可接受；
- 输出规模和 Viewer 加载时间适合 Demo。

### 人工 Viewer Review

机器无法决定 Demo 是否好看。建议生成一个人工 review 表：

| IFC | Viewer 可读性 | 构件可见性 | 颜色/材质 | Target 是否无遮挡 | Before/After 表现 | 推荐角色 | 结论 |
|---|---|---|---|---|---|---|---|

用户人工审查后给：

- `approve_demo`；
- `maybe`；
- `reject_demo`。

### 建议 Demo 产物目录

不建议立即复制 IFC；先冻结清单：

```text
dataset/manifests/demo-ifc-set.json
```

只有确认公开 / 展示角色后，再决定是否建立专门的 demo package。

### 人工审查：强制

这是本阶段最不能完全自动化的一项。

---

## WP3 — 小型 IFC2X3 Benchmark Set

### 目标

建立一个低成本、高可解释、适合 prompt / resolution / repair loop 的 benchmark。

### 推荐规模

当前不再假设“真实小 IFC 难找”。external 已经证明有真实小模型存在。

正式 Repair benchmark **优先使用真实 IFC**。程序生成 / deterministic fixture 继续作为内部 regression/debug fixture，但默认不计入论文约 40-case 主 benchmark。

第一轮建议从至少 10–20 个不同 source/model family 中选 admission candidates，再从其中构造约 40 cases。这里 **40 cases 不等于 40 个 IFC 文件**；一个 IFC 可以产生多个不同 damage task，但最终 split 必须按 source family / model group 隔离，避免同模型泄漏。

### Candidate admission gate

建议每个小 IFC 必须满足：

- IFC2X3；
- reopen；
- geometry basic pass；
- 至少 1 个可识别 Repair target；
- target relation chain 可解释；
- damage 可确定性构造；
- repair runtime 合理；
- source / license 明确。

### 人工审查：必须

- 是否真实；
- 是否过于 toy；
- 是否具有 benchmark 难度；
- 是否会因为 target 太明显而让结果失去意义。

### 已冻结的数据来源原则

正式约 40-case Repair benchmark 优先从真实 IFC 构造。只有在完成本地 inventory 和公开 IFC 扩充后，真实数据仍无法覆盖必要任务类型或规模时，才允许引入 Generation Pipeline 产生的 IFC 作为补充 slice。

程序化 deterministic fixture 继续用于 regression/debug，不默认计入论文 benchmark。Generated IFC 如果进入 benchmark，必须单独报告，不能与 real-source case 合并成一个不区分来源的数字。

---

## WP4 — 冻结 Original / Damaged / Repaired Benchmark Cases

### 目标

在看到模型输出之前冻结 Damage 和 private truth，形成可重复的 benchmark cases。

### Case package 建议

每个 case 至少分成 Public 与 Private：

```text
case-id/
  public/
    damaged.ifc
    request.txt
    case.json
  private/
    original.ifc
    mutation-manifest.json
    expected-correspondence.json
```

Repair run 只允许访问 `public/`。

Comparator 在 repair 完成后才访问 `private/`。

### 第一轮 case taxonomy 建议

第一代目标约 **40 cases**。建议先按 Window / Door / Property / Beam+Column / mixed / clarification / negative 做分层，具体比例等统一 inventory 统计出各数据源 capability 后再冻结。

- Window deletion / restoration；
- Door deletion / restoration；
- Opening / hosted relation restoration；
- Wall property repair；
- Window property repair；
- Door property repair；
- Beam / Column add or property；
- two-operation atomic repair；
- ambiguity requiring clarification；
- unsupported atomic negative case；
- preservation stress case。

### Damage 难度分层

建议后续可分：

```text
L1 Easy: 单实体、用户信息充分
L2 Medium: 需要 target resolution / relation reconstruction
L3 Hard: 多实体、歧义、property/type/evidence 组合
```

但第一版不必立即冻结 L1/L2/L3 名称；先把可测 case 做对。

### 人工审查：强制

每个 benchmark case 在首次 Provider run 前至少审：

- public request 是否自然；
- request 是否泄露 GUID / private truth；
- damage 是否合理；
- original role 是否合法预先建立；
- mutation manifest 是否 private；
- comparator 是否只在 post-repair 打开 truth。

### 重要规则

**绝对不能在模型修复后再根据 repaired output 反推 expected truth。**

---

## WP5 — Repair Evaluation Profile v1

### 目标

不重写底层 evaluator，先建立一个“论文指标投影层”，把现有 Proof / Evaluation 输出变成统一 table-ready metrics。

### 推荐实现

优先新增 projection / report，不改变当前 release semantics：

```text
Repair Evaluation 0.2 / Proof
      -> Research Metric Projection
      -> repair-evaluation-profile.json
```

这样论文实验不会反向影响现有生产放行规则。

### 建议 v1 指标

#### A. Validity

- `artifact_reopen_success`
- `schema_preserved`
- `source_immutable`

#### B. Target Recovery

- `target_semantic_success`
- `geometry_success`
- `relationship_success`
- `property_success`

#### C. Preservation

- `non_target_preservation_success`
- `unintended_root_additions`
- `unintended_root_deletions`
- `unintended_semantic_changes`

#### D. User Satisfaction

- `requested_predicate_success`
- `clarification_required`
- `unsupported_correctly_blocked`

#### E. Efficiency

- Stage 1 calls；
- Stage 1.5 calls；
- Stage 2 calls；
- input tokens；
- output tokens；
- total latency；
- repair rounds。

### 关于总分

用户已确认可以设置总分，但必须同时保留各维度比例，避免一个总分掩盖失败原因。

候选形式：

```text
Repair Score =
  w_validity * ValidityRatio
  + w_target * TargetRecoveryRatio
  + w_preservation * PreservationRatio
  + w_semantic * SemanticSatisfactionRatio
```

Efficiency（token / latency / Provider calls）建议先独立报告，不直接混入 correctness score。具体权重后续讨论。

### 人工审查：必须

用户需确认：

- headline metrics；
- success definition；
- 是否把 clarification 视作失败；
- negative case 如何计分；
- 是否需要 micro / macro averaging。

---

# 3. P1 工作包

## WP6 — Repair Loop（Deferred）

### 目标

用户已经明确当前不进入 Repair Loop。本节只保留历史设计备忘，不进入当前 Demo Paper 或第一代约 40-case Repair benchmark 的执行范围。

未来如果重启，可建立有限的：

```text
Repair -> Evaluate -> Issue -> Repair -> Evaluate
```

但不能让 private Gold 成为 oracle。

### 推荐 feedback source

允许回传：

- production L0/L1/L2 failure；
- deterministic apply/audit issue；
- public-safe semantic manifest mismatch；
- explicit user-request predicate mismatch；
- non-private Audit finding。

禁止回传：

- original deleted entity GUID；
- exact private Ground Truth geometry；
- private mutation mapping；
- comparator-only correspondence；
- “你应该创建和 original 一模一样的某实体”这种 oracle feedback。

### Issue Contract

建议先定义一个非常小的 public-safe issue schema，例如：

```text
issue_type
operation_id
target_public_identity
failed_predicate
observed_public_fact
expected_public_constraint
repairable: true/false
```

### 停止条件

建议默认：

- all public-safe evaluation pass；
- no repairable issue；
- current score / predicate set no improvement；
- new blocking regression；
- max rounds = 2 或 3。

### 第一轮实验

不建议一开始上所有 case。

先选 5–10 个已知 first-pass 有机会失败但可修的 controlled cases，测：

- first-pass success；
- final success；
- round count；
- new-error rate；
- token / latency overhead。

### 人工审查：强制

Issue schema 在写代码前先让用户确认。

---

## WP7 — Context / Token Compression Ablation

### 目标

把“我们只让 LLM 看到什么信息”正式实验化。

### 推荐 3 个 profile

#### Profile A — Full-ish Operational Context

作为上界 / 高 context baseline。

包含更多 candidate/evidence 描述，但仍不能包含 private Gold。

#### Profile B — Current Structured Evidence

使用当前 bounded target context、semantic manifest、property candidate set 等，作为当前系统基线。

#### Profile C — Compressed Evidence

进一步删除冗余自然语言、历史 trace 和重复字段，只保留必要结构事实。

### 重要公平性

三个 profile 必须：

- 同一模型；
- 同一 benchmark；
- 同一 public evidence source；
- 同一 evaluator；
- 不改变 private/public boundary；
- 不改变 repair operation capability。

否则不能把结果解释为 context compression 的效果。

### 指标

至少：

- input token reduction；
- end-to-end token reduction；
- latency；
- first-pass success；
- final success；
- clarification rate；
- target-resolution correctness；
- false authorization；
- unintended edit；
- Provider malformed-output rate。

### 论文价值

如果 Structured / Compressed Evidence 可以显著减少 token，同时保持 repair 和 safety，则可以形成比“单纯 token 少”更强的论述：

> deterministic IFC retrieval + bounded evidence projection reduces agent context cost without exposing private benchmark truth or sacrificing repair fidelity.

### 人工审查：必须

先讨论 profile 字段，再实现。

---

# 4. P2 工作包

## WP8 — 扩展到几十个 IFC

### 目标

在 inventory 和 admission gate 稳定后，把 Experiment-ready IFC 扩展到几十个。

### 建议不要只按文件数扩展

应按 task coverage 扩：

- small / medium / large；
- simple / multi-storey；
- Window-heavy / Door-heavy / structural；
- property-rich；
- different source families；
- different candidate ambiguity levels。

### 自动化

这一阶段才值得将：

- inventory；
- damage generation；
- case validation；
- benchmark packaging；
- evaluation projection

串成批处理。

### 人工抽检

建议按 source family / task slice 抽样，不是只随机抽文件。

---

## WP9 — 扩展到约 200 IFC

### 前置条件

只有以下条件满足后再做：

- inventory 自动化稳定；
- license / provenance 不混乱；
- case builder 可重复；
- evaluator scalable；
- benchmark split 有 group isolation；
- 不会因为规模导致人工审查完全失效。

### 核心目标

200 IFC 的意义不是“数字大”，而是作为：

- retrieval corpus；
- case generation source；
- generalization benchmark；
- trajectory / correction source；
- post-training candidate source。

---

## WP10 — Post-training Feasibility

### 目标

只在数据达到足够规模和质量后做 Go / No-Go。

### 先做数据统计

至少统计：

- unique IFC family；
- unique repair case；
- target entity type distribution；
- successful / failed / clarification trajectory；
- correction pairs；
- human-reviewed fraction；
- leakage-safe split。

### 再决定训练对象

可能不是直接 fine-tune 整个 Agent。

优先比较：

1. Target Retrieval / ranking；
2. RepairIntent semantic parsing；
3. Stage 2 constrained changeset generation；
4. feedback-to-correction behavior。

哪一层错误贡献最大，就优先训练哪一层。

---

# 5. 建议的人工审查 Gate

为避免自动化推进过头，建议显式设 5 个 Human Gates。

## H-Gate 1 — Dataset Admission

人工确认：哪些 IFC 进入 Experiment-ready / Demo-quality。

## H-Gate 2 — Demo Selection

人工看 Viewer 后确认最终 3–5 个 Demo。

## H-Gate 3 — Benchmark Freeze

在第一次模型运行前确认 public/private case package 和 Damage。

## H-Gate 4 — Metric Definition

在跑大实验前确认论文主指标、成功定义和聚合方式。

## H-Gate 5 — Loop / Compression Contract

在修改 prompt/evidence behavior 前确认：

- Agent 能看到哪些字段；
- feedback 能看到哪些 issue；
- private comparator 永远不能反馈什么。

这些 gate 不一定都需要复杂流程，但应该有明确的人类批准记录。

---

# 6. 当前建议的实际执行顺序

当前应按两条路线并行，但不要互相阻塞。

## Route A — Generation Demo Paper（当前主线）

```text
Step G1
冻结 3–5 个 Generation 展示目标

Step G2
强化 scaling / multi-room / limited multi-storey

Step G3
强化颜色、材质、构件视觉区分

Step G4
做 repeated-run stability / acceptance

Step G5
人工 Viewer Review，确定最终 Demo Set
```

这条路线 **不等待新 IFC 数据收集完成**。

## Route B — Repair / Post-training Data（并行基础设施）

```text
Step R1
统一统计现有真实 Source IFC

Step R2
吃完当前 external 尚未 admission 的候选

Step R3
从公开互联网持续扩充真实 IFC source pool

Step R4
完成 license / schema / duplicate / capability admission

Step R5
从真实 IFC 构造约 40-case Repair Benchmark v1

Step R6
加强 IFCCompare / IfcDiff + Research Metric Projection

Step R7
进行 Token / Context Efficiency 实验

Step R8
继续扩充真实 Source IFC，为 post-training 准备

Step R9
若真实 IFC 仍不足，再启动 Generation-based dataset expansion
```

Repair Loop 当前不进入。Post-training 也不是近期执行项，但数据收集从现在开始就要为它保留 provenance、split 和 training eligibility。

---

# 7. 已冻结与仍待讨论的决策

## 已冻结

1. 当前 Demo Paper **Generation 为主**；Repair 留作后续更大的文章。
2. Generation 现有数据 **已经足够启动**，不等待新增 IFC。
3. Repair / Post-training **继续扩充真实 IFC**；公开真实来源优先，Generation 产物兜底。
4. Real-source 与 generated-source 必须分开统计、分开 provenance。
5. 第一代 Repair Benchmark 目标约 **40 cases**。
6. Repair Loop **当前不进入**。
7. Repair Evaluation **允许设置总分**，同时必须保留分维度比例；Efficiency 不混入 correctness score。
8. Token / Context Efficiency **暂定潜在主贡献**，最终由受控实验决定。
9. 程序化 deterministic fixture 默认只用于 regression/debug，不计入论文主 benchmark。

## 仍待讨论

1. Generation Demo 最终是 3 个还是 5 个，以及各复杂度档位。
2. 40-case Repair benchmark 各 task family 的具体比例。
3. Repair Score 中 Validity / Target / Preservation / Semantic 的具体权重。
4. Clarification case 在主 success rate 中如何计分。
5. 哪些公开来源允许 training、论文截图、artifact redistribution。
6. Token / Context Efficiency 最终是否上升为正式主 contribution。

---

# 8. 当前默认执行方案

```text
近期主线：Generation Demo Paper
  -> scaling
  -> 更好看
  -> 更稳定

并行数据线：Real IFC Source Expansion
  -> inventory
  -> online collection
  -> admission
  -> ~40 Repair cases
  -> IFCCompare / IfcDiff
  -> Repair Score
  -> Token / Context
  -> more real IFC
  -> generated IFC fallback only if needed
  -> post-training later
```

当前最重要的数据原则不是“尽快造很多 case”，而是 **持续增加独立真实 Source IFC family**。源文件越多，后续可以合法、可控地派生出的 Damage / Repair / Retrieval / Property / Trajectory 数据才会真正扩大。

---

# 9. 与方向记录的关系

研究现状、已完成/未完成和总体优先级见：

`docs/reports/llm-generation-repair-demo-next-direction-2026-09-03.md`

本文仅负责“怎么做”的讨论框架。

**下一步应先和用户讨论第 7、8 节，再把确认后的内容转成正式实施 PLAN；在此之前，不自动开始修改 Repair Pipeline、Prompt、Schema 或正式 benchmark contract。**
