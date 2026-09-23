# IFC Repair 文献矩阵：WWW Demo Paper 专项

> **2026-09-21 接续说明：**本页保留为 09-18 调研快照。当前 Repair 专项已独立到 [Repair 文献矩阵](../repair-demo/repair-literature-matrix-20260921.md)和 [Claim 攻击审查](../repair-demo/archive/claim-novelty-audit-20260921.md)。新稿细化了保全检查的实际覆盖、补入 CAD/MDE 编辑表示先例，并将当前论文主线改为语义修复；不再以本页的安全/授权叙事作为现行 Claim。

> 更新：2026-09-18  
> 目的：为 text2IFC WWW Demo Paper 收紧 IFC Repair 的相关工作、冲突边界与可安全表述的系统差异。  
> 证据原则：优先正式论文/官方项目页/作者正文；“未看到”不等于“首次没有人做过”。

## 1. 结论先行

当前文献已经明确占据了以下宽泛表述：

- “自然语言直接编辑 IFC”不是空白；
- “LLM + IFC 工具调用 / 动态代码生成”不是空白；
- “BIM 生成后自动 verification -> correction loop”不是空白；
- “BIM 自动 repair / conflict resolution / component alteration”不是空白；
- “用几何、语义、拓扑与 preservation 评价 IFC 编辑”不是空白；
- “用 IDS / rule checking 验证 IFC”更不是空白。

因此，text2IFC Repair 不适合把 novelty 写成“首次实现 LLM-driven IFC repair”。

更稳妥的 Demo Paper 定位是：

> **A bounded and auditable IFC repair system that turns natural-language requests into deterministically authorized, atomic semantic ChangeSets, and publishes an IFC only after reopened-file validation and non-target preservation checks.**

这更接近“系统执行语义与可验证交互”的贡献，而不是抢一个过宽的方法首创。

---

## 2. 核心近邻矩阵

符号：

- **✓**：已明确覆盖；
- **△**：部分覆盖 / 目标不同；
- **?**：本轮证据不足，不能断言没有；
- **—**：不属于该工作的主要目标。

| Work | Existing BIM/IFC edit | Natural-language intent | Automatic mutation | Verification / feedback | Non-target preservation | Bounded authority / scope | Atomic multi-op / fail-closed | 与 text2IFC 的关系 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **Wu et al. 2026 — Automated building component alterations...** | ✓ | △：human-authored improvement strategies + issue text | ✓ | ✓：alterations re-evaluated for compliance | △：scope 由 designer strategy governance | ✓：预定义 component-level operations + topology | ? | **最强“repair/alteration”近邻**。已覆盖从 ACC violation 到可执行构件修改与方案探索；不能再 claim “verification 之后自动改 BIM” |
| **MCP4IFC, 2025/26** | ✓ | ✓ | ✓ | △：工具/代码执行反馈 | ? | △：predefined functions + dynamic code generation | ? | **最强通用 IFC manipulation 近邻**。证明 NL -> query/create/modify IFC 已存在；text2IFC 必须强调 deterministic binding、authority 和 release gate |
| **BIM-Edit, 2026** | ✓ | ✓ | benchmark | ✓：geometry + semantics + topology | ✓：论文明确把 preserving semantics/relations 作为核心难点 | — | — | **最强编辑评价近邻**。不能把多维 edit evaluation 或 preservation 本身称新 |
| **BIBIMBAP, 2026** | ✓ | ✓ | benchmark | ✓：test scripts | ✓：报告 constraint-preservation failures | — | — | 原子 CRUD / spatial / geometric / topological / numeric / conceptual benchmark；很适合做我们未来 benchmark 对照 |
| **Self-Verification, 2026** | △：主要 Text-to-BIM generation | ✓ | ✓：Modifier 继续改 IFC | ✓：IDS + LLM code checks -> feedback loop | ? | △：规格分解形成检查边界 | ? | **最强闭环近邻**。不能说“首次让 verifier 驱动 IFC 修正” |
| **Text2BIM, 2024-2026** | △：生成内 revision | ✓ | ✓ | ✓：外层通过 IFC/Solibri issue 继续修订 | ? | △：多 Agent / high-level tools | ? | 已有生成、审核、修订循环；text2IFC repair 不能仅靠“多 Agent + feedback”区分 |
| **Jiang et al. 2025 — RL BIM conflict resolution** | ✓ | — | ✓：移动/调整冲突构件 | ✓：rule-based checker real-time feedback | △：reward 包含 created conflicts | △：动作空间受 RL environment 控制 | ? | 已经是明确的 **automatic BIM repair/conflict resolution**；但目标主要是 geometric clashes，不是语言驱动 semantic repair |
| **Iversen & Huang 2026 — LLM BIM compliance checking** | —/△ | ✓：regulation interpretation | — | ✓ | — | △：structured checking workflow | — | 说明 LLM + BIM deterministic checking 也已成熟；它做“check”，不是 post-check mutation |
| **Closed-loop IFC validation & quality management, 2026** | — | — | — | ✓：rule matrices + issue tracking + dashboard | — | ✓：rule-based | — | “closed-loop IFC validation”术语已被使用，但并不等于自动修改；不要把 closed-loop 一词当 novelty |
| **Ma et al. 2024 — ontology-based BIM quality checking** | — | △：文本标准被 ontology 化 | — | ✓ | — | ✓：OWL/SWRL rules | — | 传统确定性 IFC compliance checking 基础；说明 deterministic validation 不是新点 |
| **Lee et al. 2016 — modularized rule-based MVD validation** | — | — | — | ✓ | — | ✓ | — | 更早的 IFC rule-validation 基础。我们的差异不能写成“首次确定性验证 IFC” |
| **buildingSMART IDS** | — | — | — | ✓：machine-interpretable IFC requirements | — | ✓：facet / applicability / requirement | — | 是验证规范基础，不是 repair engine |
| **text2IDS / LLM-Powered Structurer, WWW 2026 Demo** | — | ✓ | — | △：目标是 NL -> IDS 结构化要求 | — | ✓：输出落到 IDS schema | — | 是我们的前作与写作模板；它把用户语言变成 **verification specification**，Repair 则进一步把语言变成 **authorized model change** |
| **From Regulations to IDS, ICDM Workshop 2025** | — | ✓：regulation | — | ✓：IDS rule check | — | ✓ | — | 说明 NL/regulation -> IDS 也有其他先例；text2IDS 的具体 novelty 必须按其原文表述，不可泛化成“首次 text-to-IDS” |

---

## 3. 逐篇重点

### 3.1 Automated building component alterations driven by LLM-formalized human strategies to achieve code compliance

**来源**

- Automation in Construction 190 (2026), 107148
- DOI: https://doi.org/10.1016/j.autcon.2026.107148
- Official page: https://www.sciencedirect.com/science/article/pii/S0926580526003894
- Code: https://github.com/Jaaaaabin/AutoComplianceWu

**它做了什么**

论文明确指出传统 Automated Compliance Checking 能发现 violation，却不能帮助 designer 自动解决。方法从 ACC / BCF issue 出发：

1. 用 LLM 把 issue 信息结构化；
2. 将 violation 与 IFC GUID、空间和拓扑相关构件关联；
3. 将 designer-authored improvement strategy 形式化为预定义 component-level operations；
4. 执行 CREATE / DELETE / MODIFY / SWAP 等 alteration；
5. 重新评价 altered model，寻找 feasible alterations / resolution clusters。

**对我们的直接冲突**

它已经做到了：

- compliance issue -> component-level executable alteration；
- LLM 用于语义形式化；
- mutation scope 由 designer strategy 约束；
- topology 被用于扩展可修改对象；
- 修改后重新评估。

所以以下表述应删除：

- “首个从 model checking 走向 automatic BIM repair 的系统”；
- “首次由 LLM 把人类意图转成受控 BIM 修改”；
- “首次利用拓扑上下文定位可修复构件”。

**仍可区分的地方**

text2IFC 当前重点不是合规方案搜索，而是一个自然语言 request 的受控修改事务：

- target occurrence / Type / Property authority 显式分层；
- semantic retrieval 不直接授权写回；
- Binder 重新建立 deterministic execution authority；
- 多 operation 是统一 atomic transaction；
- unsupported 子操作使整组 fail closed；
- repaired IFC 必须 reopen；
- L0/L1/L2 + preservation 决定 publish；
- ambiguous target/value 可以 clarification + resume。

这些是 system semantics 的差异，暂时不能在没有穷尽查重的情况下写“首次”。

---

### 3.2 MCP4IFC

**来源**

- arXiv: https://arxiv.org/abs/2511.05533
- Project: https://show2instruct.github.io/mcp4ifc/

它提供：

- IFC scene querying；
- predefined create / modify tools；
- dynamic IfcOpenShell code generation；
- RAG / in-context support；
- query、generation、existing IFC editing。

**冲突**

“LLM 可以通过工具直接操作 IFC”已经成立。我们的 Demo 不应把 MCP/IfcOpenShell/tool calling 当 novelty。

**可比较问题**

MCP4IFC 更强调操作能力和工具覆盖；text2IFC R1 更强调：

```text
request
-> resolve identity
-> authorize semantics
-> bind ChangeSet
-> atomic mutation
-> reopen
-> verify + preserve
-> publish / no output
```

论文需要展示这个 contract 改变了哪些失败行为，而不只是多了一层 JSON。

---

### 3.3 BIM-Edit

**来源**

- https://arxiv.org/abs/2606.20146
- https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks

公开描述：

- 324 natural-language editing tasks；
- 11 realistic building models + 36 synthetic scenes；
- create / update / delete；
- direct / spatial / topological；
- geometry / semantic / topology 三维评价；
- best model average 约 49.5/100；
- fully solves 不超过 3.4%。

**对我们的意义**

这是未来 Repair benchmark 最重要的直接对照之一。

它也直接否定两种宽泛 claim：

- “IFC editing benchmark 只看 geometry”；
- “还没有工作同时评价 geometry / semantics / topology”。

我们可以新增的评价维度应更加具体，例如：

- exact requested-property correctness；
- non-target preservation；
- atomic all-or-nothing；
- clarification correctness；
- correct refusal / no-output；
- private-gold isolation；
- successful artifact reopen。

---

### 3.4 BIBIMBAP

**来源**

- EC³ 2026: https://ec-3.org/publication/ec32026_271/

公开描述：

- 100 curated tasks；
- CRUD；
- spatial / geometric / topological / numeric / conceptual；
- prompt + IFC + expected structured outputs + tests；
- best baseline 50.2%；
- failure 包括 constraint preservation 与 spatial reasoning。

它的价值不是作为“repair method”，而是帮助我们设计 **atomic capability slices**。

如果 WWW Demo Paper 只需要小实验，可以用类似 BIBIMBAP 的 task slicing 展示：

```text
Property update
Target ambiguity
Invalid value
Beam/Column add
Cross-family atomic edit
Unsupported mixed request
```

这比只展示几个“漂亮成功 IFC”更有说服力。

---

### 3.5 Self-Verification Framework

**来源**

- EC³ 2026: https://ec-3.org/publication/ec32026_444/

流程大意：

```text
prompt
-> requirements
-> IDS + non-IDS verification
-> Modifier creates/modifies IFC
-> deterministic/LLM-based checks
-> feedback
-> another modification round
```

已明确覆盖 verification-driven iterative correction，因此我们不能用：

> “audit 后反馈给 agent 再修改”

作为独立创新。

真正能区分的是：

- 它的重点是 generation self-verification；
- 我们的 R1 是 existing/damaged IFC 的 bounded repair；
- 我们不是让 verifier 的自由文本直接推动无限修改，而是重新走 target/property authority、Binder 与 atomic ChangeSet。

---

### 3.6 Towards Automated BIM Conflict Resolution Using Reinforcement Learning

**来源**

- EG-ICE 2025
- https://doi.org/10.17868/strath.00093289
- Full text: https://mediatum.ub.tum.de/doc/1781883/1781883.pdf
- Code: https://github.com/YuyeJ48/Towards-Automated-BIM-Conflict-Resolution-Using-Reinforcement-Learning

它使用 PPO，在 BIM environment 中让 agent 根据 rule-based checker 的实时反馈移动冲突构件，优化冲突数量与严重度，并显式记录新产生的 conflicts。

**意义**

BIM “检测 -> 自动修复”至少在几何 clash resolution 上已经存在。

但是这也提示 text2IFC 的 preservation 评价可以更严：

- target problem 是否解决；
- 新错误数量；
- non-target mutation；
- 若失败是否回滚；
- 一个 operation 的修复是否破坏另一个已经正确的 operation。

---

## 4. Verification-only 近邻为什么仍然重要

### 4.1 Leveraging LLMs for BIM-based automated compliance checking

Automation in Construction 182 (2026), 106707：

https://www.sciencedirect.com/science/article/pii/S0926580525007472

该工作让 LLM 解释 regulation、选择 BIM data extraction tools、执行 checks 并生成报告，说明：

> “LLM reasoning + deterministic/structured BIM checking”

本身已经不是新故事。

### 4.2 Toward robust and quantifiable automated IFC quality validation

早期 IFC quality 研究已经把 IFC completeness / correctness 转成可自动执行的质量规则：

https://www.sciencedirect.com/science/article/abs/pii/S1474034615000725

### 4.3 Modularized rule-based validation of a BIM model pertaining to model views

Automation in Construction 63 (2016)：

https://www.sciencedirect.com/science/article/abs/pii/S0926580515002319

说明 IFC / MVD rule validation 有成熟历史。

### 4.4 buildingSMART IDS

https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/

IDS 1.0 自 2024-06-01 成为 buildingSMART official standard，用 computer-interpretable requirements 自动检查 IFC。

因此 text2IFC 的确定性 gate 应被写成 **可靠系统基础**，而不是 novelty。

---

## 5. 与 text2IDS 的关系

text2IDS 的公开出版信息：

- **LLM-Powered Structurer: Normalizing Natural Language to Information Delivery Specification for Industrial Data Exchange**
- Jiqian Yang, Sujie Yan, Zhi Li, Mingyu Liu, Yousheng Wang, Wei He
- The Web Conference 2026, **Demo Track**
- Companion Proceedings, pp. 212–215
- DOI: https://doi.org/10.1145/3774905.3793139
- Official accepted demos: https://www2026.thewebconf.org/accepted/demo.html

从研究链条上，最自然的前后关系是：

```text
text2IDS
natural-language requirement
    -> normalized machine-checkable IDS

text2IFC Repair
natural-language modification
    -> bounded executable ChangeSet
    -> modified IFC
    -> independent verification
```

这不是说 text2IFC 必须依赖 text2IDS 才能执行；而是对 WWW Demo 叙事而言，两者共同体现：

> 把人类语言放到开放标准的结构化执行边界里，而不是让 LLM 直接生成最终工程文件。

---

## 6. 当前可以写、不能写的 Claim

### 6.1 不建议写

- First LLM system to edit IFC.
- First automated IFC/BIM repair system.
- First verification-driven BIM correction loop.
- First preservation-aware IFC editing benchmark/system.
- First system to use LLM + deterministic BIM validation.
- First natural-language-to-IDS system（除非 text2IDS 原文确实这样声明，且重新查重后仍成立）。

### 6.2 Demo Paper 中更安全的表述

#### 系统定位

> We demonstrate a bounded IFC2X3 repair workflow in which LLMs interpret user intent but cannot directly authorize model mutations.

#### 执行语义

> The system resolves target and property authority deterministically, binds all requested modifications into one atomic ChangeSet, and applies them only to a staging IFC.

#### 发布语义

> A modified IFC is published only after the artifact is reopened and independently checked for requested semantics and non-target preservation; ambiguous, incompatible, or partially unsupported requests fail closed or trigger clarification.

#### Demo 价值

> The demonstration exposes not only successful edits, but also clarification, invalid-value recovery, cross-family atomic edits, and a correct no-output guard.

这四句是当前证据最扎实、也最适合 Demo Track 的故事。

---

## 7. Demo 实验/展示建议

WWW Demo 不需要把它伪装成一篇大规模 benchmark paper。最值得展示的是“系统行为是可观察的”。

建议现场固定六个场景：

1. **Property edit**：Window `IsExternal=true`；
2. **Semantic type guard**：Door `FireRating=true` -> reject -> user clarifies `EI60`；
3. **Ambiguous target**：多个 Window -> bounded candidate list -> resume；
4. **Structural add**：Beam / Column + generated or exact existing Type；
5. **Cross-family atomic edit**：Beam + Window 或 Door + Wall；
6. **Correct no-output**：supported edit + unsupported structural analysis -> entire ChangeSet rejected, source unchanged。

每个场景都显示：

```text
request
-> resolved intent
-> target/property authority
-> Bound ChangeSet
-> IFC mutation
-> reopen facts
-> L0/L1/L2/preservation
-> publish / no-output
```

这会比只展示 IFC viewer 前后截图更能体现系统研究价值。

---

## 8. 当前最重要的新结论

截至 2026-09-18 的专项补查，**Wu et al. 2026** 是必须加入现有 literature-review-full 的直接近邻。它把研究边界进一步推进到了：

```text
compliance issue
-> human improvement strategy
-> LLM formalization
-> component operations
-> BIM alterations
-> re-evaluation
```

因此，text2IFC Repair 的论文价值不能再建立在“自动修改”本身。

更合理的核心故事是：

> **LLM interpretation is useful, but it is not sufficient authority for engineering-model mutation; text2IFC turns interpretation into a bounded, atomic and independently verifiable IFC repair transaction.**

这仍然需要在正式论文前继续查重“bounded/atomic/fail-closed/preservation-aware editing”是否存在完全相同系统，但目前比“首个 IFC repair”安全得多。
