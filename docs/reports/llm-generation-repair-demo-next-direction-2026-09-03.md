# LLM Generation / IFC Repair / Demo Paper 后续方向记录

> 首次记录：2026-09-03  
> 最近更新：2026-09-04（根据与老师讨论后的方向重新冻结 Generation / Repair 数据边界）  
> 文档类型：研究方向与现状记录，不替代 `.planning/STATE.md`、Phase SPEC/PLAN/VALIDATION 或正式验收报告。  
> 目的：把当前论文讨论中的下一阶段方向，与仓库真实完成状态对齐，明确哪些工作已经具备基础、哪些仍需要补齐，并为后续执行计划讨论提供输入。

## 1. 研究方向概括

下一阶段需要明确拆成两个时间尺度，并且 **Generation 数据路线与 Repair / Post-training 数据路线必须分开管理**：

1. **近期：Generation Demo Paper。** 当前手头已有 IFC 数据已经足够支撑 Generation 部分，不把“继续找更多 IFC”作为 Generation Demo Paper 的前置条件。重点转向 generation scaling、构件完整性、可视化质量、颜色/材质表现和重复运行稳定性，形成更好看、更稳定、更有层次的 Demo。
2. **中期：Repair 主论文与 Post-training。** 现有 IFC 虽然足以启动第一代 Repair benchmark，但对于扩大 Repair 数据、自动 Damage/Repair Pair、trajectory/correction 数据以及后续训练仍然不够。因此 Repair 数据路线必须持续扩大真实源 IFC 池：**先系统统计已有数据，再优先从公开互联网、公开研究数据集、官方 sample repository 等来源收集真实 IFC；只有公开真实 IFC 仍不足时，才考虑使用 Generation Pipeline 生成的 IFC 作为补充。**

两类来源不能混为一谈：

```text
External / Real Source IFC
    -> Repair Benchmark 主数据源
    -> Post-training 优先数据源

Generated IFC
    -> Generation Demo 产物
    -> 必要时作为 Repair / Post-training 补充数据源
    -> 必须显式标注 synthetic/generated provenance
```

后续任何论文统计都应分别报告 real-source 与 generated-source 的数量、case 数量和结果，不能把生成数据伪装成独立真实建筑数据。

整体目标可以概括为：

```text
Generation Demo / Scaling
        +
IFC Dataset / Demo Set
        +
Stable Generation / Visual Quality
        +
Repair Dataset / IFCCompare
        +
Quantitative Evaluation
        +
Context / Token Efficiency
        +
Scalable Training Data
```

与论文主线的关系应优先突出 Agent / LLM Harness，而不是把研究包装成单纯的 BIM 工程工具：

1. **Generation Scaling / Stability**：从当前简单可运行的 Generation 链路出发，逐步提高房间、构件和楼层复杂度，同时保持 IFC 可打开、构件完整、门窗关系正确和多次运行稳定。
2. **Visual Demo Quality**：Demo Paper 优先选择建筑外观完整、Window / Door / Wall 易观察、材质/颜色和构件区分明显的案例，而不是追求大规模 Repair benchmark。
3. **可靠的 Agentic Repair**：作为后续大文章主线，LLM 负责理解和提出受约束的 RepairIntent / ChangeSet，确定性代码负责目标绑定、写回、验证和放行。
4. **Safety / Ground-Truth Isolation**：生产 Repair 只看到 damaged IFC、用户请求和当前 IFC 中可获得的证据；Original IFC、被删除实体身份和 private mutation mapping 只能在 repair 完成后进入 evaluator。
5. **IFCCompare / Deterministic Evaluation**：后续 Repair 论文应更系统地使用 IfcDiff / semantic fingerprint / mapped-element comparison，而不是重新开发一套 comparator。
6. **Context / Token Efficiency**：暂定为潜在主贡献，研究 Full Context、Structured Evidence、Compressed Evidence 对 token、latency、success 和 false authorization 的影响。
7. **Scalable Benchmark and Data**：第一代 Repair benchmark 目标约 40 cases；之后再扩展到几十乃至约 200 个 IFC，并沉淀为 retrieval、repair、trajectory 和 correction 数据。

其中 Token / Context Efficiency 可以暂定为后续论文的潜在主贡献，但在形成受控 ablation 之前，不应提前把“节约 token”写成已验证贡献。

---

## 2. 状态判定说明

本文使用三种状态：

- **已完成（Done）**：仓库中已有实现，并存在足以支撑该能力的测试、真实运行或独立 Proof 证据。
- **部分完成（Partial）**：关键基础设施已有，但尚未形成本文希望的统一数据、系统化实验、Demo 或论文级指标。
- **未完成（Not Started / Not Formalized）**：尚无正式数据集、实验协议或稳定实现可以支撑该主张。

需要特别区分：

```text
“某项基础能力已经实现”
!=
“该能力已经被整理成论文 benchmark / demo / ablation”
```

---

# 3. 已经完成的部分

## 3.1 Generation 基础链路与已有 Demo —— 已完成基础能力

仓库已经具备 Natural Language → BIM JSON → IFC2X3 的生成主线，并存在简单房间、双房间、Mimo live、CLI 等历史 Demo 产物。

已完成的关键基础包括：

- BIM JSON 1.0 / 2.0 Schema 与 Draft 表达；
- IFC2X3 编译器；
- IfcOpenShell 写出与 reopen；
- Generated IFC correctness gates；
- Design Brief / Generator / Repair / Audit 等 Agent 模块；
- 多轮 Clarification；
- report / trace / gate / route evidence；
- 简单 Generation E2E Demo。

因此下一阶段不需要重新证明最小 `Text -> IFC` 可运行性，而应重点提高 **展示质量、复杂输入稳定性、Demo 选择与实验组织**。

### 当前仍存在的边界

复杂多楼层住宅的稳定 accepted generation 并没有被当前证据彻底解决。Generation Demo 可以使用已有稳定小案例，但如果论文要声称复杂完整建筑生成能力，需要单独建立新的受控验收。

---

## 3.2 Repair Pipeline 主体 —— 已完成

当前 Repair Milestone R1、Phase 12 和 Phase 12.1 已关闭。现有系统已经具备：

- IFC2X3 damaged-file 输入；
- Stage 1 RepairIntent；
- bounded target / type / property resolution；
- Stage 1.5 property retrieval / reranking；
- Stage 2 ChangeSet Draft；
- deterministic Binder / Audit；
- atomic IfcOpenShell apply；
- source IFC immutability；
- reopen；
- L0 / L1 / L2 evaluation；
- fail-closed publication；
- Window、Door、Opening、Wall property、Beam、Column 等多类操作；
- clarification / resume；
- unsupported atomic guard；
- multi-operation atomic repair。

2026-09-03 的 R1 accepted genuine run 已达到 12/12 frozen case contracts PASS，并具有独立 Proof 0.3。

因此“Repair 能否跑通”已经不是下一阶段的核心问题。近期工作应让位于 Generation Demo Paper；Repair 侧主要做 **数据扩充、约 40-case 第一代 benchmark、IFCCompare 深化使用、统一指标和 Token / Context Efficiency 实验准备**，为后续更大的文章积累数据。

---

## 3.3 Production / Private Benchmark 隔离 —— 已完成并应保持为核心研究边界

用户提出的以下原则当前已经落实在仓库设计和验收规则中：

```text
Production Repair 只能看到：
- Damaged IFC
- 用户自然语言请求
- 当前 IFC 中仍存在的事实
- 正式授权的结构化 evidence

Private Evaluator 才能看到：
- Original IFC
- Private mutation mapping
- 被删除实体身份
- Ground Truth correspondence
```

这部分不仅是工程安全规则，也应视为论文的重要 Agent Safety / Evaluation Integrity 设计。

后续新增 Damage / Repair Benchmark 时必须继续遵守：

- Original / deleted GUID 不进入 Provider Prompt；
- private mutation manifest 不进入 target resolution；
- benchmark truth 必须在 repair 前固定；
- 不得在看到 repaired output 后再构造“Ground Truth”；
- private comparator 不能被误用为生产授权来源。

---

## 3.4 Deterministic Evaluation / Compare 基础设施 —— 已完成核心能力，论文整理部分尚未完成

当前已经具备：

- IFC reopen / validity；
- L0 / L1 / L2；
- target geometry / host / opening / fill / void / storey 等检查；
- property / Type / material / classification / quantity 的条件性语义检查；
- source immutability；
- non-target preservation；
- occurrence fidelity；
- IFCCompare / private triplet comparison；
- independent Proof recomputation。

现有 accepted truth-bearing collection 已经具有合法的 private triplets，并存在 12 个 truth-bearing triplet audits 可用于 comparator 验证。

因此 `Damaged IFC -> Repaired IFC -> Compare` 的机制不是从零开始。

但当前指标主要服务于工程验收和 Proof，还没有整理成一套专门用于论文表格、跨数据集统计和 ablation 的统一 **Repair Success Profile**。这一部分属于“基础已完成、研究指标未正式化”。

---

## 3.5 GUID / Entity Identity 原则 —— 已完成核心设计

当前系统已经明确区分：

### Production GUID

用于稳定定位 damaged IFC 中仍然存在的真实实体，例如 target Wall、Window、Door、Beam、Column 或 Type。

### Private Ground-Truth Identity

用于 mutation / benchmark correspondence，但不会进入 Provider 或 production target resolution。

当前系统也没有把：

```text
Repaired GlobalId == Original GlobalId
```

作为 L1/L2 修复成功条件。

重新创建 Window、Door、Opening、Beam、Column 等实体时产生新的合法 GlobalId 是允许的；STEP ID、序列化顺序、OwnerHistory 或其他 L3 authoring exactness 也不是当前主要 release condition。

因此后续 benchmark 应继续比较：

```text
Semantic / Structural Correspondence
```

而不是简单做 ID equality。

---

## 3.6 Bounded Evidence / Prompt Context 基础 —— 已部分完成

现有 Repair Pipeline 已经不是把整份 IFC 或整个历史 Trace 直接喂给 LLM，而是使用：

- deterministic IFC index；
- TargetQuery；
- bounded candidate context；
- Production Evidence；
- Semantic Manifest；
- property Top-K retrieval；
- exact typed facts；
- versioned prompt profiles / schemas。

这为后续“Context Compression / Token Efficiency”实验提供了很好的现成基线。

但当前尚未完成系统性的：

```text
Full Context
vs.
Structured Evidence
vs.
Compressed Evidence
```

受控对比，因此该方向目前属于 **Partial**。

---

## 3.7 Dataset Provenance / Manifest 基础 —— 已部分完成

当前已有多层数据管理基础：

- `dataset/manifests/raw-files.jsonl`：外部原始文件 provenance；
- `dataset/manifests/bimnet-ifc2x3.jsonl`：当前有 26 条授权本地 BIMNet IFC2X3 记录；
- `dataset/manifests/ifc-repair-benchmarks.jsonl`：当前有 4 个 Repair benchmark candidate；
- `dataset/manifests/ifc-repair-cases/*.private.json`：evaluator-only mutation identity；
- `dataset/processed/proof/`：accepted human-reviewable repair evidence；
- source / license / approved-use 信息的基础管理。

因此“数据 provenance 完全没有整理”并不准确。

真正缺少的是一个面向下一阶段研究问题的 **统一 IFC Dataset Inventory**，把 raw / valid / experiment-ready / demo-quality 等级与几何、实体数量、viewer 质量、repair suitability 和授权状态集中在同一张可审查清单中。

同时，Inventory 必须增加明确的 `data_origin` / provenance 分层：

- `real_external`：公开互联网、官方 repository、研究数据集等真实来源 IFC；
- `authorized_local`：已有授权本地数据，例如 BIMNet；
- `generated_internal`：由本项目 Generation Pipeline 生成的 IFC；
- `derived_repair_artifact`：Damaged / Repaired / Proof 等运行衍生产物。

其中 Repair benchmark 与 Post-training 的主统计应优先来自前两类；`generated_internal` 只能作为补充，并且必须单独报告。

---

# 4. 尚未完成的部分

## 4.1 专门的 Demo IFC Set —— P0，未正式建立

### 目标

建立 3–5 个高质量、可稳定展示的 IFC Demo，而不是从全部实验数据中临时抽样。

Demo 应覆盖：

1. **Generation Demo**：自然语言生成完整 BIM / IFC；
2. **Repair Demo**：明显局部 damage 后自然语言恢复；
3. **Property / Semantic Demo**：实体查询、定位和属性修改。

### 当前缺口

仓库有历史 Demo 和 Repair Proof，但尚没有统一的“论文 / Demo Paper 专用 Demo Set”，也没有按 viewer 可视效果、遮挡、构件可辨识度、材质/颜色、操作稳定性进行正式筛选。

### 必须人工审查

- Viewer 中的视觉质量；
- 构件是否明显可见；
- Before / After 差异是否容易解释；
- 颜色 / 材质 / Type 是否满足展示需要；
- 授权是否允许论文截图、公开演示或分发；
- 是否真的适合作为主 Demo，而不是只适合作为工程测试。

---

## 4.2 统一 IFC Dataset Inventory —— P0，部分完成但需要重新汇总

### 目标

对当前全部 IFC 建立统一清单，至少记录：

- 文件名；
- source / provenance；
- license / approved use；
- IFC Schema；
- bytes；
- total entity count；
- major entity histogram；
- `IfcWall` / `IfcWindow` / `IfcDoor` / `IfcSpace`；
- storey count；
- IfcOpenShell reopen；
- geometry availability / geometry failure；
- repair target chain availability；
- Generation Demo suitability；
- Repair Benchmark suitability；
- Property / Retrieval suitability；
- visual / demo quality；
- notes / exclusion reason。

需要把 IFC 分类成：

```text
Raw IFC
  -> Valid IFC
  -> Experiment-ready IFC
  -> Demo-quality IFC
```

### 当前缺口

已有 manifest 分散解决 provenance、授权和部分 Repair capability，但没有一份统一 inventory 回答：

1. 当前到底有多少可用 IFC？
2. 哪些最适合 Demo？
3. 哪些可进入规模化实验？

### 必须人工审查

- Demo-quality；
- license / public-use interpretation；
- 自动几何检测无法判断的视觉问题；
- borderline model 是否纳入 experiment-ready。

---

## 4.3 小型 IFC2X3 Benchmark Set —— P0，未正式建立

### 目标

建立一个实体数以几百到几千为主、结构清晰、IfcOpenShell 稳定、易于构造 damage 的小型 IFC2X3 benchmark。

### 当前缺口

当前 `ifc-repair-benchmarks.jsonl` 中正式列出的最小主候选 `vvo.ifc` 约有 48,935 entities；其余候选达到约 501k、770k 和 1.0M entities。

这些模型适合真实兼容性、candidate volume 和 scalability，但不符合当前提出的“小型、快速、适合 Agent loop / prompt iteration”的基准定位。

### 必须人工审查

- 小模型是否仍具有足够真实 BIM 关系；
- 是否有 Wall / Window / Door / Space；
- Damage Case 是否自然；
- 是否把 deterministic synthetic fixture 与真实 IFC benchmark 混为一谈。

---

## 4.4 系统化 Original → Damaged → Repaired Triplet Dataset —— P0，部分完成

### 已有能力

- mutation；
- private mapping；
- damaged-only public repair；
- private comparator；
- truth-bearing accepted cases。

### 仍缺少

面向论文和扩展实验的一组统一、预先冻结、可批量运行的 triplet benchmark，覆盖：

- Window；
- Door；
- Opening；
- Wall / Window / Door property；
- Beam / Column；
- multi-operation；
- negative / unsupported / ambiguity；
- preservation stress。

所有 Ground Truth 必须在 repair 前建立并冻结，不能从 repaired output 反推。

### 必须人工审查

- Damage 是否具有研究意义而不是人为制造过于简单的答案；
- request 是否泄露目标 identity；
- private/public 文件边界；
- benchmark case 是否在 repair 前完成冻结。

---

## 4.5 论文级 Repair Quantitative Evaluation —— P0，部分完成

### 已有能力

已有 L0/L1/L2、occurrence fidelity、preservation、atomicity、proof recomputation 和 private comparator。

### 需要整理出的论文指标

建议首先保留独立维度，而不是立即定义一个线性加权总分：

#### Artifact Validity

- reopen success；
- schema preserved；
- invalid reference count；
- broken relationship count。

#### Target Recovery

- target class；
- target existence / correspondence；
- geometry tolerance；
- storey；
- host / opening / fill / void；
- requested property correctness。

#### Non-target Preservation

- deleted non-target roots；
- changed non-target semantic facts；
- changed non-target relations；
- unintended additions / edits。

#### Semantic Satisfaction

- user-requested predicates；
- correct target / host / orientation / scope；
- requested dimensions / properties；
- clarification outcome。

#### Agent / System Metrics

- first-pass success；
- clarification count；
- repair rounds；
- Provider calls；
- input/output tokens；
- latency；
- false authorization / unsafe mutation count。

### 必须人工审查

- 哪些指标属于主论文 headline；
- 哪些阈值可以跨实体类型共享；
- 是否需要一个总分；
- 如果需要总分，权重必须有解释，不能为了好看临时调权。

---

## 4.6 Compare / Audit → Issue → Repair Loop —— P1，未形成正式 Repair Benchmark Loop

现有 Generation Agent 中已有 feedback / route / scoped loop 类基础设施，Repair Pipeline 也已有 rich evaluation evidence，但目前尚没有正式完成一个 benchmark-grade：

```text
Repair
  -> Public-safe Evaluate / Audit
  -> Issue
  -> Local Repair
  -> Re-evaluate
```

的有限闭环实验。

### 关键研究边界

**Private Ground-Truth Comparator 不应直接驱动 benchmark repair。**

否则相当于测试时把答案通过 comparator feedback 注入 Agent，破坏 Ground-Truth isolation。

更合理的划分是：

```text
Production-safe L0/L1/L2 / Audit Issue
    -> 可以反馈给 Repair Agent

Private Original-vs-Repaired Comparator
    -> 只负责每一轮之后的 evaluator-only scoring
    -> 不作为 Repair Agent 的 oracle
```

这是后续计划中需要优先冻结的安全设计。

### 必须人工审查

- 哪些 issue 可以回传给 Agent；
- issue 是否包含 private truth；
- 最大 round；
- no-improvement 停止条件；
- 是否出现修复一个问题又引入新问题。

---

## 4.7 Prompt / Evidence Context Compression —— P1，未完成受控实验

### 目标

比较：

```text
Full Context
vs.
Structured Evidence
vs.
Compressed Evidence
```

在相同 model、case、temperature / decoding contract 和 evaluator 下对：

- input tokens；
- output tokens；
- total Provider calls；
- latency；
- first-pass success；
- final success；
- semantic accuracy；
- target resolution accuracy；
- false authorization；
- non-target preservation；
- clarification rate

的影响。

### 当前原则

Demo 阶段不应为了减少 token 破坏已经稳定的 evidence boundary。

Token Efficiency 只有在不降低 repair success / safety 的情况下才有研究价值。

### 必须人工审查

- 三个 context profile 的信息边界；
- 哪些字段允许压缩、哪些必须 exact；
- 是否把模型历史 CoT / trace 错误计入必要上下文；
- 是否存在 Ground Truth leakage；
- ablation 是否公平。

---

## 4.8 IFC 数据规模扩展 —— P2，尚未达到计划规模

近期目标应先形成几十个稳定、高质量 IFC，用于：

- Demo；
- Repair Benchmark；
- Retrieval；
- Property；
- Agent Evaluation。

在数据质量和自动 audit 稳定后，再逐步扩展到约 200 个 IFC。

“200 IFC”不是当前 Demo Paper 的门槛，而是后续数据基础设施目标。

### 必须人工审查

- provenance / license；
- duplicate / near-duplicate scene；
- train / validation / test leakage；
- 自动 suitability 标签抽样复核；
- 是否真正增加任务多样性，而不是只增加文件数量。

---

## 4.9 Post-training 数据 —— P2，尚未进入正式构造阶段

后续可形成：

```text
Natural Language + IFC Context
-> Target Entity
```

```text
Natural Language + Retrieved Evidence
-> RepairIntent
```

```text
Damaged IFC State + User Request
-> ChangeSet
```

```text
Failed Repair + Public-safe Evaluation Issue
-> Corrected Repair
```

潜在用途：

- retrieval training；
- semantic parsing；
- repair instruction tuning；
- agent trajectories；
- preference / correction data。

当前优先级仍低于 Demo、Benchmark、Compare 和量化指标。

### 必须人工审查

- training label 是否来自真实、合法 authority；
- private Gold 是否错误进入训练输入；
- split leakage；
- failed trajectory 是否真的标注了正确失败原因；
- 是否已经有足够规模和人工审核质量支持 post-training。

---

# 5. 当前优先级记录

## P0：论文 / Demo 下一步最优先

1. 建立统一 Dataset Inventory；
2. 选出 3–5 个高质量 Demo IFC；
3. 建立小型 IFC2X3 Benchmark Set；
4. 固定一批合法的 Original / Damaged / Repaired benchmark cases；
5. 把现有 comparator / L0/L1/L2 / preservation 统一投影成论文级 quantitative profile；
6. 形成至少一组可直接用于 Demo Paper 的可视化 Before / Damage / Repair / Compare 案例。

## P1：在 P0 稳定后推进

7. 扩展 Window / Door / Wall / Beam / Column / property / mixed cases；
8. 建立 production-safe Evaluate → Issue → Repair loop；
9. 进行 Full / Structured / Compressed Context ablation；
10. 将 token、latency、Provider calls 与 repair/safety metrics 联合统计。

## P2：规模化阶段

11. 扩展至几十个稳定 IFC；
12. 自动化构造 Damage / Repair Cases；
13. 扩展到约 200 个 IFC；
14. 形成 retrieval / repair / trajectory / correction 数据；
15. 再评估 Target Retrieval、RepairIntent 或 Agent Repair 是否值得 Post-training。

---

# 6. 当前最需要保留的论文主张边界

在进入下一阶段之前，应保持以下主张不被后续 Demo 优化破坏：

1. **LLM 不直接拥有 IFC 写权限。**
2. **LLM 只看到 bounded production evidence。**
3. **Ground Truth 与 deleted identity 不进入 production repair。**
4. **成功由 deterministic evaluator / proof 决定，而不是由 LLM 自评。**
5. **Non-target preservation 与 source immutability 是成功条件。**
6. **新生成 GUID 合法，不要求与原始 deleted GUID 相同。**
7. **Token reduction 不能以安全、语义或 repair success 退化为代价。**
8. **Private comparator 是 evaluator，不是 test-time repair oracle。**

这些边界既是系统工程约束，也是后续面向 Agent / LLM 论文时最有价值的研究叙事之一。

---

# 7. 下一份文档

具体“怎么做”不在本文直接冻结。

执行顺序、数据格式、自动扫描脚本、Demo Set 选取规则、小型 benchmark 来源、Repair Loop feedback contract、context compression profile 和人工审查 gate 将单独写入：

`docs/plans/2026-09-03-llm-generation-repair-next-step-discussion.md`

该文件当前只作为 **Discussion Draft**，必须经过人工讨论和确认后才能升级为正式实施计划。
