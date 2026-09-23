# text2IFC Generation：Claims / Novelty 综合审核

> 日期：2026-09-16  
> 范围：只讨论 Generation；Repair 只在解释已有基础或迁移关系时出现，不用来补 Generation 的证据缺口。  
> 目标：整合当前仓库实现、generation-demo 文献卡和最直接原始论文，明确“现在真实能写什么”“哪些已经撞车”“还剩什么候选 novelty”。  
> 本文不设计新实验，不新增研究路线，不把未来 P1/P2/V1/L1 等尚未实现方向写成当前贡献。

---

## 1. 总结先行

当前仓库已经形成一套真实的 Text-to-IFC Generation 系统机制，而不是只有 Prompt workflow：

```text
Natural-language requirement
        ↓
Design Brief state
        ├─ needs_clarification → persistent human clarification → rerun
        └─ ready
        ↓
Expected Facts
        ↓
legacy_full / staged generation
        ↓
Candidate BIM JSON
        ↓
deterministic gates + IFC compilation / reopen
        ↓
structured Issue
        ↓
Change Scope
        ↓
revision-bound / issue-bound / scope-bound ChangeSet
        ↓
executor-enforced apply + preservation check
        ↓
IFC revalidation
```

但是，文献已经直接覆盖其中很多**宽泛思想**：Text-to-BIM、Multi-Agent、需求展开、任务特定检查、自验证闭环、IFC editing、反馈修订、层级/分步生成等都不能再单独称 novelty。

当前最值得保护的不是某一个原语，而是下面这个 **domain-method candidate**：

> **text2IFC 将 Text-to-IFC generation 的关键步骤组织为受控状态转换：生成前，需求必须通过可审计澄清从 Draft/needs_clarification 进入 Ready；生成后，验证问题不能直接授权任意整模重写，而是在绑定当前候选版本、来源 Issue 和允许实体/关系/字段范围的 ChangeSet 中执行，再对 IFC artifact 重新验证。**

当前判断：

```text
Direct exact collision in reviewed Text-to-BIM/IFC corpus: NOT FOUND
Primitive novelty: NO
System/domain-method distinction: REAL
Method novelty: PLAUSIBLE, NOT PROVEN
```

这比“首次 ChangeSet”“首次 clarification”“首次 self-verification”更准确。

---

# 2. 当前已经实现、可以安全描述的 Claim

## C-SYS1 — Fail-closed requirement-state clarification

### 仓库事实

`ClarificationController` 显式维护：

```text
awaiting_model
needs_clarification
ready
```

并保存：

- 原始用户请求；
- transcript turn；
- question IDs；
- Provider response ID；
- prompt template ID / hash；
- Design Brief；
- evidence catalog。

用户回答后不是直接修改最终模型，而是重新运行 Design Brief，并保留原始 request 和 turn provenance。

Generation 公共入口明确要求：

```text
stored_session.status == "ready"
```

否则 `_run_ready_session_to_ifc` 直接拒绝进入 IFC generation。

### 代码入口

- `src/text2ifc_agent/clarification.py`
- `src/text2ifc_agent/interactive_cli_flow.py:396` — clarification loop
- `src/text2ifc_agent/interactive_cli_flow.py:541` — Ready admission
- `tests/agent/test_clarification_resume_preservation.py`

### Novelty 状态

**系统区别：成立。**

**“clarification 本身是新算法”：不成立。** ClarifyGPT、Active Task Disambiguation、TiCoder、ProCAD 等已经研究需求澄清和基于执行差异的提问。

在当前已核实的直接 Text-to-BIM / IFC 核心工作中，尚未找到与以下组合完全同构的实现：

```text
missing/ambiguous requirement
→ fail closed
→ persistent clarification state
→ provenance-preserving rerun
→ Ready admission
→ generation allowed
```

Text2BIM 有 Product Owner 做 requirement refinement，也有 human feedback；但当前全文证据没有显示与 text2IFC 相同的“缺失事实必须阻断 generation + 持久化状态恢复”合同。

**结论：可作为整体 control protocol 的组成部分；是否单独作为 contribution，留给用户决定。**

---

## C-SYS2 — Requirement-derived Expected Facts

### 仓库事实

`build_expected_facts` 在 generation 前从 Ready Design Brief 动态投影：

- storeys；
- spaces；
- doors/windows/openings；
- stable IDs；
- semantic expectations；
- generation package manifest。

它不是从 candidate 反推，也不只是 fixture。

### 代码入口

- `src/text2ifc_agent/expected_facts.py`
- `src/text2ifc_agent/generation_packages.py`

### Novelty 状态

**C1 宽泛 novelty = RED。**

Self-Verification 已直接实现：

```text
Prompt
→ IDS specification
+ non-IDS specification
→ IFC
→ task-specific verification
→ feedback
→ refinement
```

而且 non-IDS 明确覆盖 geometry、topology、complex relations。

Self-Verification 同时承认：初始 specification 可能遗漏 requirement，遗漏会直接污染后续 verification/refinement。这一点与 text2IFC 的 Brief-derived Expected Facts 也存在同类风险。

因此 Expected Facts 是有价值的系统 contract，但不能单独声称“首次 requirement-derived verification contract”。

### Primary source

- Self-Verification EC³ 2026: https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf
- Code: https://github.com/Tsesterh/Text2BIM-Self-Verification

---

## C-SYS3 — Ownership-bounded staged generation

### 仓库事实

`build_generation_package_manifest` 为 Skeleton、storey-local、cross-storey、semantic-type packages 明确记录：

```text
owned_component_ids
owned_relationship_ids
allowed_reference_ids
```

Package Gate 检查：

- 当前操作必须是 add-oriented；
- target ID 不能已存在；
- target 必须属于 package ownership；
- package 声明的对象不能缺失；
- host/storey/opening/filling 等局部关系必须满足对应 Gate；
- 应用后已有 component hash 不允许漂移。

`staged_generation.py` 在 package apply 前后比较已有 component hashes，发现变化时返回：

```text
PACKAGE_FROZEN_COMPONENT_DRIFT
```

### 代码入口

- `src/text2ifc_agent/generation_packages.py`
- `src/text2ifc_agent/package_gates.py`
- `src/text2ifc_agent/staged_generation.py`

### 重要边界

不能写成“完整 reference allowlist / full read-write isolation”。

当前 Gate 使用：

```text
visible_ids = existing workspace IDs ∪ package IDs ∪ allowed_reference_ids
```

因此已有 workspace ID 并非严格按 `allowed_reference_ids` 白名单隔离。

另外，CLI 默认仍是 `legacy_full`；`staged` 是显式选择路径。

### Novelty 状态

**“分楼层 / staged / hierarchical generation” = RED。**

Text2MBL、Trestle-Bridge、SceneCraft/Graph-CAD 等已覆盖层级或阶段式生成/规划。

**“写入 ownership + 前序组件 drift 阻断” = 有真实实现区别，但通用 ownership/versioning 原语已有 MDE/BIM prior art。**

所以 C2 当前仍只能作为：

> **Text-to-IFC staged generation 的受控构造机制 / system contribution**

而不是“首次模型 ownership 算法”。

是否将 C2 单独作为论文 contribution，留给用户决定。

---

## C-SYS4 — Revision- and scope-bound ChangeSet correction

这是当前仓库中最具体、最强的受控修改机制。

### 4.1 Issue → stable target → Change Scope

`derive_change_scope` 不允许一个普通错误字符串直接授权修改。

Issue 必须能够绑定到稳定的：

```text
entity:<id>#<path>
relationship:<id>#<path>
```

然后 Scope 显式记录：

```text
base_revision_id
source_issue_ids
entity_ids
relationship_ids
allowed_paths
dependencies
forbidden_ids
```

对 host/opening/fill/containment 等关系，可以沿受支持依赖进行 scope 扩展。

### 4.2 ChangeSet 必须绑定当前 artifact state

当前 applicator 检查：

```text
base_revision_id
base_candidate_hash
expected_facts_hash
scope_id
source_issue_ids
target_component_hash
```

任何 stale candidate / stale target / scope mismatch 都 fail closed。

### 4.3 Executor 强制实体、关系与字段范围

Applicator 检查：

```text
target ∈ authorized entity/relationship set
change_path ∈ allowed_paths
stable id / ifc_class immutable
remove must not create orphan relations
semantic-field permission does not imply whole-record delete permission
```

因此这不是“Prompt 要求 LLM 尽量少改”。

### 4.4 应用与保全

ChangeSet 在 candidate 副本上应用；失败时不返回可提升的新 candidate。

成功后记录：

- new revision；
- candidate hash；
- preservation report；
- changed IDs；
- forbidden drift IDs。

上层再重新执行 Candidate Gates / IFC compilation / reopen / acceptance。

### 代码入口

- `src/text2ifc_agent/change_scope.py`
- `src/text2ifc_agent/scoped_loop.py`
- `src/text2ifc_agent/changeset_apply.py`
- `tests/agent/test_phase6_5_changeset_apply.py`

### Novelty 状态

必须分四层说：

```text
partial update                               → NOT NOVEL
natural-language IFC editing                 → NOT NOVEL
structured patch / ChangeSet                 → NOT ENOUGH BY ITSELF
revision + issue + scope + path + hash
+ executor enforcement + preservation
inside Text-to-IFC generation               → STRONG DOMAIN-METHOD CANDIDATE
```

当前已核实的直接 IFC/Text-to-BIM 工作中，没有找到与这一整套执行约束完全同构的系统。

但：

- MDE 已有 fine-grained R/W access control；
- ChronoSphere 等已有 transaction/version/immutable committed state；
- IFC 标准本身已有 object-level revision/change concepts；
- program repair / CAD editing 已有 local patch 和 preservation。

因此不能声称这些 primitive 是 text2IFC 发明的。

**当前最合理 novelty 不是“新 ChangeSet 格式”，而是把 issue-derived modification authority 作为 Generation loop 的执行边界。**

---

## C-SYS5 — Deterministic IFC artifact verification

当前 Generation 不是以“LLM 返回合法 JSON”为成功条件。

系统还执行：

```text
BIM JSON contract
→ semantic coverage
→ deterministic compiler
→ IFC
→ reopen
→ relationship / storey / opening/fill / geometry checks
→ Audit
→ Final Acceptance
```

这是系统可信性的重要基础。

但：

- Text2BIM 已有 Solibri/rule-based checker + refinement；
- Self-Verification 已有 IDS + non-IDS checker；
- BIM-Edit 已系统评价 geometry / semantics / topology。

因此“artifact verification”本身不是 novelty，只能作为 text2IFC control protocol 的必要基础。

---

# 3. 与四个最直接工作的精确冲突

## 3.1 Text2BIM

### 已经占领

```text
Natural Language → BIM
Multi-Agent
requirement enhancement
structured building plan
high-level BIM tools
code execution + self-reflection
rule-based model checker
checker feedback → iterative revision
human feedback
whole-building generation
```

所以以上均不能作为 text2IFC 独立 novelty。

### 没有被它直接覆盖的 text2IFC 机制

当前全文与仓库证据中，Text2BIM correction 主要通过 Reviewer / Programmer 重新修改 modeling code，并利用 BCF/checker feedback；没有看到与 text2IFC 同构的：

```text
issue-derived Change Scope
candidate revision/hash binding
entity/relationship whitelist for write targets
field/path authorization
target component hash binding
scope-outside preservation enforcement
```

Text2BIM 反而提供了重要 motivation：论文报告 refinement 可能重构旧代码、产生 duplicate/conflict，甚至通过删已有构件减少 checker issue 而破坏建筑完整性。

### Source

- DOI: https://doi.org/10.1061/JCCEE5.CPENG-6386
- arXiv: https://arxiv.org/abs/2408.08054
- Code: https://github.com/dcy0577/Text2BIM

---

## 3.2 Self-Verification

### 与 text2IFC 高度重合

```text
request
→ task-specific specification
→ IFC generation/modification
→ verification
→ feedback
→ iterative refinement
```

其 Specifier 同时产生：

- IDS；
- non-IDS specification。

non-IDS 明确包含：

```text
geometric
topological
complex relational conditions
```

因此：

```text
requirement-derived checking
self-verification loop
task-specific checks
closed-loop IFC refinement
```

均不能再作为我们的独立 novelty。

### 没有直接覆盖

其公开论文/当前已审代码证据没有显示与 text2IFC 同构的 executor-level：

```text
revision/hash binding
issue-authorized mutation scope
entity/relationship/path enforcement
scope-outside preservation
```

其 case study 五轮后仍未修复 `IfcSpace → IfcBuildingStorey` 关系，并且作者明确承认 specification generation 无法保证完整覆盖需求。

### Source

- Paper: https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf
- Code: https://github.com/Tsesterh/Text2BIM-Self-Verification

---

## 3.3 BIM-Edit

BIM-Edit 是一个 **editing benchmark**，不是 Text-to-IFC generation system。

它覆盖：

```text
existing IFC + natural-language edit
→ modified IFC
```

并评价：

```text
geometry
semantics
topology
```

因此：

```text
natural-language IFC editing
partial IFC modification
semantic/topological edit evaluation
```

不是 text2IFC novelty。

但 BIM-Edit 不提供：

```text
requirement clarification state machine
whole-building generation pipeline
Expected Facts
revision-bound scoped generation correction
```

所以它主要是评价/编辑 prior work，而不是当前 Generation control protocol 的直接同构竞争者。

### Source

- Paper: https://arxiv.org/abs/2606.20146
- Dataset: https://huggingface.co/datasets/BIM-Edit/BIM-Edit
- Tasks: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks

---

## 3.4 MCP4IFC / IFC-Copilot

这条线已经明确覆盖：

```text
Natural Language → native IFC
IFC create/edit/query
high-level typed IFC tools
dynamic IfcOpenShell code
execution feedback
whole-structure generation demos
```

所以 “first Text-to-IFC” 不成立。

但其研究重点是：

> 给 LLM 什么 IFC action space / tools 才更可靠和高效。

当前已核实材料没有显示与 text2IFC 同构的 requirement-state gating 或 issue-derived revision/scope-bound patch protocol。

### Source

- MCP4IFC: https://arxiv.org/abs/2511.05533
- Project: https://show2instruct.github.io/mcp4ifc/
- IFC-Copilot: https://show2instruct.github.io/ifc-copilot/
- Code: https://github.com/Show2Instruct/ifc-bonsai-mcp

---

# 4. 已经明确撞车、建议删除的 Claim

下面这些不应再作为论文 novelty：

```text
First Text-to-BIM
First Text-to-IFC
Multi-Agent BIM generation
high-level IFC/BIM tools
structured intermediate representation
hierarchical / staged generation（宽泛版本）
requirement enhancement
requirement-derived verification specification
rule-based checking
self-verification loop
verification → feedback → correction
natural-language IFC editing
partial IFC modification
geometry + semantics + topology evaluation
clarification（作为通用 AI 原语）
ChangeSet / version / transaction / ownership（作为通用原语）
```

---

# 5. 当前 Novelty 应分为“已实现候选”和“未实现研究方向”

## 5.1 当前已经实现、最值得保护的候选

### N-A — Controlled State-Transition Text-to-IFC Generation

候选表述：

> **text2IFC constrains both requirement-state and artifact-state transitions in natural-language IFC generation. Missing or ambiguous requirements must be resolved through an auditable clarification state before generation is admitted, while post-generation corrections are applied through issue-derived, revision-bound and scope-enforced ChangeSets before the resulting IFC artifact is revalidated.**

中文：

> **text2IFC 对自然语言 IFC 生成中的需求状态和产物状态进行显式控制：缺失或歧义需求必须经过可审计澄清进入 Ready 后才能生成；生成后的验证问题则通过由 Issue 派生、绑定候选版本并由执行器强制范围的 ChangeSet 修改，随后重新验证 IFC artifact。**

为什么它比 “我们有 clarification / ChangeSet” 更合理：

```text
clarification     不是新原语
ChangeSet         不是新原语
versioning        不是新原语
verification      不是新原语

BUT

在 Text-to-IFC generation 中，
把“何时允许进入生成”与“何种修改允许进入下一 artifact revision”
都变成 fail-closed contract，
是当前系统最明确的完整区别。
```

### 当前状态

```text
Implementation support: STRONG
Direct exact Text-to-BIM/IFC collision: NOT FOUND
Primitive novelty: NO
Combination/domain-method novelty: PLAUSIBLE
Paper-level novelty: NOT YET LOCKED
```

不使用 `first`。

---

## 5.2 可以作为 N-A 技术核心的候选

### N-B — Issue-derived scoped correction

更窄的表述：

> **Verification issues are converted into explicit modification authority over a versioned BIM candidate, and the executor rejects stale, unrelated, or out-of-scope modifications before IFC revalidation.**

它强调的不是“local patch”，而是：

```text
verification evidence
→ authorization
→ executable state transition
```

这个是当前仓库里最具体的技术机制。

是否将 N-B 单列成论文 Claim，还是作为 N-A 的核心机制，**USER DECISION**。

---

## 5.3 当前实现存在、但建议先作为 supporting mechanism

### Staged package ownership / frozen drift checks

真实存在，但：

- staged 不是默认路径；
- reference allowlist 不严格；
- hierarchical/staged generation prior work 很多；
- 通用 ownership/freeze 原语已有先例。

所以当前更适合支撑 N-A/N-B，而不是单独占一个主要 Claim。

如果用户希望把它提升为独立 contribution，需要先决定是否值得进一步收紧 reference boundary；本文不替用户做这个决定。

---

## 5.4 Clarification 是否单列 contribution

当前实现明显强于“聊天时随便问一句”：它有持久化状态、question IDs、turn provenance、resume、Ready admission 和 fail-closed generation。

但：

- clarification / active disambiguation 本身已有大量 AI/Coding prior work；
- Text2BIM 也包含 human feedback 和 requirement refinement；
- 当前尚未找到直接 IFC 同构机制，不等于已证明 novelty。

因此本文只确认：

> **它是 N-A 的重要组成机制。**

是否把“fail-closed requirement clarification for Text-to-IFC”单独列为 contribution，**USER DECISION**。

---

# 6. 最新 P1 / P2 / V1 / L1 与“当前 Claim”的关系

[历史 research-shortlist](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/research-shortlist.md) / `broader-method-directions.md` 在 Self-Verification 之后又提出：

```text
P1  多步编辑效果与规划
P2  空间结构/几何联合分解
V1  学习有区分力的检查
L1  按迁移收益选择课程
```

这些是**未来研究问题池**，当前仓库没有实现对应方法，也没有实验结果。

因此：

> **它们不能进入“已有 Claim / novelty”。**

同理，较早 N01/N03/N06 也已经被最新文献复核进一步压低：

- N01 被 LearnAct、COS-PLAY、Bayesian-Agent 等强近邻压缩；
- N03 被 ExpeL / ACE / TraceCAD 等压缩；
- N06 被 ClarifyGPT / Active Task Disambiguation / ProCAD 等压缩。

它们可以继续作为研究备选，但不应与当前系统贡献混在一起。

---

# 7. 当前最干净的 Claim 结构

如果只根据**已经实现的代码 + 当前已核实文献**，不新增任何方法，我建议先保留下面的层级，而不是硬凑多个算法创新：

## Main system/domain-method candidate

### Controlled State-Transition Text-to-IFC Generation

核心：

```text
Requirement state:
needs_clarification
→ auditable clarification
→ ready
→ generation admitted

Artifact state:
revision R
→ issue evidence
→ authorized scope
→ bound ChangeSet
→ executor enforcement
→ revision R+1
→ IFC revalidation
```

## Supporting mechanisms

1. Requirement-derived Expected Facts；
2. ownership-bounded staged construction；
3. deterministic BIM JSON → IFC compilation；
4. artifact-level gates / reopen；
5. revision / hash / path / dependency preservation。

## Not current claims

P1 / P2 / V1 / L1 / skill-learning 等尚未实现方法。

---

# 8. 当前仍不能确定的两件事（需要用户决定，不由本文代替）

## USER DECISION 1

**Clarification 是否需要单独成为 contribution？**

两种合法组织方式：

```text
A. 作为 Controlled State-Transition 的 requirement-side mechanism
B. 单列“fail-closed requirement clarification for Text-to-IFC”系统贡献
```

本文不替用户选择。

## USER DECISION 2

**Staged/package ownership 是否需要单独成为 contribution？**

两种合法组织方式：

```text
A. 作为 N-A/N-B 的 generation-side supporting mechanism
B. 进一步收紧 reference policy 后单列 compositional generation contribution
```

本文不替用户选择。

---

# 9. 当前结论

截至本轮交叉审核，不能说 text2IFC “没有创新”。

更准确的是：

1. **大量宽泛方法已经被 prior work 占领。** Self-Verification 尤其直接撞掉了 requirement-derived checking + verify/refine loop；Text2BIM 撞掉了 multi-agent whole-BIM generation + checker refinement；MCP4IFC 撞掉了 native Text-to-IFC；BIM-Edit 撞掉了自然语言 IFC editing 和 geometry/semantics/topology evaluation。
2. **当前仓库仍有一套没有在这些直接工作中找到同构实现的受控 Generation protocol。** 它的区别不在“有 ChangeSet”，而在 requirement admission 和 artifact correction 都通过可验证状态合同限制 Agent 权限。
3. **最具体的技术核心是 scoped ChangeSet correction。** 当前代码已经做到 Issue→Scope→revision/hash/path/target enforcement→preservation→revalidation。
4. **这仍然不是已经证明的 paper-level novelty。** 通用 access control、versioning、transactions、clarification、local repair 都有 prior art；需要把贡献限定为 Text-to-IFC generation 中的具体控制问题，而不能声称发明这些原语。
5. **最新 P1/P2/V1/L1 是未来候选，不属于当前已有 novelty。**

当前最保守且仍有内容的表述是：

> **text2IFC is a verifiable Text-to-IFC generation system that governs requirement admission and post-generation model revision as explicit, auditable state transitions. Its correction path binds verification issues to authorized edits on a specific BIM candidate revision, enforces entity/relationship/field scope deterministically, and revalidates the resulting IFC artifact.**

这句话目前与代码一致，也没有把通用原语夸成首次。

---

# 10. 核心来源

## Direct BIM / IFC

- Text2BIM: https://doi.org/10.1061/JCCEE5.CPENG-6386
- Text2BIM arXiv: https://arxiv.org/abs/2408.08054
- Text2BIM code: https://github.com/dcy0577/Text2BIM
- Self-Verification: https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf
- Self-Verification code: https://github.com/Tsesterh/Text2BIM-Self-Verification
- MCP4IFC: https://arxiv.org/abs/2511.05533
- IFC-Copilot: https://show2instruct.github.io/ifc-copilot/
- IFC-Copilot/MCP code: https://github.com/Show2Instruct/ifc-bonsai-mcp
- BIM-Edit: https://arxiv.org/abs/2606.20146
- BIM-Edit tasks: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks

## Clarification / ambiguity near-neighbors

- ClarifyGPT: https://linshi-website.github.io/paper/ClarifyGPT.pdf
- Active Task Disambiguation: https://arxiv.org/abs/2502.04485
- ProCAD: https://arxiv.org/abs/2602.03045
- TiCoder: https://arxiv.org/abs/2404.10100

## Generic primitive prior art

- Fine-grained collaborative-model access control: https://link.springer.com/article/10.1007/s10270-017-0631-8
- ChronoSphere: https://link.springer.com/article/10.1007/s10270-019-00725-0
- buildingSMART IFC revision control: https://standards.buildingsmart.org/IFC/DEV/IFC4_3/HTML/concepts/Object_Attributes/Revision_Control/content.html

---

## Evidence boundary

本文依据：

- 当前本地仓库实现与 tests；
- [历史 paper-matrix](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/paper-matrix.md)；
- `novelty-literature-addendum.md`；
- `broader-method-directions.md`；
- [历史 research-shortlist](https://github.com/770122whrt/text2IFC/blob/09e8e9311f0b8c3ffc022dc42a12a48165ed7aa1/docs/reports/generation-demo/research-shortlist.md) / `research-shortlist-evidence.md`；
- `Text2IFC-Generation-Claim-Novelty-Audit-2026-09-14.md`；
- 直接原始论文 / 官方项目页。

没有运行新的 Provider 实验，没有改 Generation 产品代码，也没有把“未找到同构工作”升级为 first-of-kind 声明。
