# IFC-SemRepair：Claim 与 Novelty 攻击审查

> **历史审查快照，不再持续维护**： 保留当时的推导和来源；当前贡献措辞、novelty 状态及实验登记以 [Claim 与实验主文档](../claims-and-experiments.md)为准，新增原文核查进入 [literature](../repair-literature-matrix-20260921.md)。

> 日期：2026-09-21｜版本：讨论候选 v0.2
> 本轮范围：原文核查、仓库只读检查、研究文档更新。未运行新实验、真实 Provider 或生产代码修改。
> IFC-SemRepair 是 Repair 论文的暂定名称；不改变 text2IFC 仓库、Python 包、Schema 或历史 Proof 的身份。

## 1. 结论

**“Model-Bound Semantic ChangeSet”和“Semantic Round-Trip”可以描述系统，却还不能作为两项已经成立的独立方法创新。**前者受到模型变更图、CAD 编辑中间表示和形式化 mutation language 的直接挑战；后者实际上是修改后回读检查，不是可逆变换，也不能单独证明原始自然语言没有被误解。

这不等于 Repair 没有投稿价值。更合理的 WWW Demo 主张是：**面向已有 IFC2X3，把自然语言修改转成实例绑定的语义变更，并让用户核对实际写入的语义结果。**这是待通过演示和对照支撑的领域系统贡献，不冒充新检索算法、新编译理论或新的通用修复范式。

本轮把安全、权限、原子事务和 fail-closed 留在实现性质与边界检查中，不再作为论文主线。也不通过增加一个名字不同但内容重复的 IR 文件制造新颖性。

## 2. 先冻结被攻击的主张

| 编号 | 前一版候选 | 最强攻击 | 本轮判定 |
|---|---|---|---|
| C1 | 同时进行 Schema 与 Instance Grounding | SGSS、Query2Property 已有 schema/property 对齐；IFC-Agent、MCP4IFC 已在实际 IFC 上解析并执行操作 | 保留为任务能力；不能宣称首次把语言对齐到 schema 和实例 |
| C2 | Model-Bound Semantic ChangeSet 是新的编辑抽象 | RAMC 显式变更图、CADIR 编辑 IR、γμS mutation language 均已把变更从自由代码/完整模型中分离 | 现有代码可支撑领域化表示；尚未证明新的表示机制 |
| C3 | Semantic Round-Trip 是新的语义闭环 | ATLAS 共用规范化约束驱动生成与验证；Self-Verification 复用规格；CADIR/TraceCAD 检查实际修改效果 | 改称“修改后语义回读核验”；撤回可逆、完整语义保证及闭环首创暗示 |
| C4 | 多构件 ChangeSet 证明 compositional repair | 多操作列表与事务不等于推理操作依赖、顺序、副作用或学习组合规律 | 保留异构操作集成能力；不宣称一般组合推理创新 |

论文证据与访问级别见 [Repair 专项文献矩阵](../repair-literature-matrix-20260921.md)。

## 3. 攻击一：显式变更表示是否真的新？

### 3.1 RAMC：已有模型变更对象，不只生成完整模型

RAMC 在 ICSE 2025 的《Software Model Evolution with Large Language Models》中把新增、删除、保留及属性变化表示为 Simple Change Graph，序列化后让 LLM 补全，再解释为对具体模型的编辑。其输入主要是已有编辑上下文，不是我们的自然语言修复请求，但足以否定“把修改独立表示、绑定当前模型、再应用”这个宽泛思想的新颖性。[M1，§III–IV、附录 B/C]

**审稿问题：**我们的 ChangeSet 与这种变更图相比，新增了什么不可由已有节点、边、类型、属性前后值表达的语义？

**当前可答：**IFC 专属的 occurrence/Type 来源、Pset 身份、值类型、单位、宿主与填充关系，需要具体实现和检查。

**当前不能答：**这些字段的存在就构成通用 IR 方法创新。领域字段更丰富不等于新的表示机制。

### 3.2 CADIR：实体选择、编辑表示与实际效果验证已经同时出现

CADIR 将操作、参数、依赖和实体选择保存在可编辑构造表示中；其 post-reconstruction editing 要求目标唯一解析、修改正确、模型重算无错，且结果几何或特征状态体现所需变化。[M2，方法与 Post-reconstruction editing]

**剩余任务差异：**CAD 构造历史不等于来自不同软件的已有 IFC；IFC 中共享 Type、关系实体及属性来源有不同语义负担。但这只是需要实证的领域差异，不能改写成“CADIR 没有 model binding / effect verification”。

### 3.3 γμS：不能因尚未取得全文就宣布没有形式化编辑语言

MODELS 2026 官方摘要已提出形式化 mutation language、MCP 校验、反馈及可执行建议，并应用于 SysML。[M5，官方摘要]

本轮未取得全文，因此不能判断其保全、执行粒度和修复选择的具体覆盖。这个缺口同时阻止两个结论：不能说它完全覆盖我们，也不能说它没有相应机制。

### 3.4 对代码的直接影响

**不建议现在新增 SemanticRepairIR 来“增强 novelty”。**先解释已有 RepairIntent、Semantic Manifest、Bound ChangeSet 分别负责什么。除非新表示能带来可检验的表达能力、语义保持、依赖处理或诊断增量，否则它只是另一个封装。

## 4. 攻击二：“语义往返”究竟证明了什么？

仓库 `orchestrator.py:216–225` 明确让 authoring 与 evaluation 使用相同 Manifest 重建的 expected facts；后续对写出的 IFC 进行重开和评估。这是有价值的**执行一致性检查**。

但请区分三件事：

```text
原始自然语言 R + 当前模型 M
           ↓ 解释/定位
       语义变更 C
           ↓ 应用
       新模型 M'
           ↓ 回读
       实际语义事实 F'
```

**A．意图对齐：**C 是否正确表达 R，并指向 M 中正确的对象？

**B．执行符合：**F' 是否满足 C 所要求的属性、关系和几何事实？

**C．非目标保持：**不属于此次变更的相关状态是否保持？

B 与 C 通过，并不逻辑蕴含 A 通过。共享合同主要减少“写入一套含义、检查另一套含义”的漂移；它无法自动修正上游共同采用的错误解释。

### 一个分析性反例，而不是本轮复现的生产 Bug

用户要求修改某根梁的 Pset Reference；若上游错误地把它解释成根属性 Tag，写入器与检查器又都按 Tag 工作，那么二者可以一致通过，而用户要求仍未被满足。

仓库历史中确实保留了相近失败：`r1-20260902T053023885207Z` 的 runtime 报告通过，但独立 Proof 因 M2 写入根 Tag 而不是冻结的 Pset 属性拒绝该次运行；最终 R1 的 M2 已纠正。这里引用的是历史证据，不是宣称当前仍有该 Bug。[K5]

### 先例进一步削弱“共享表示即新闭环”

ATLAS 的 ICM 已把规范化约束、来源及依赖用于生成期约束、生成后验证和修订。[M4，§3.3–3.6]

Self-Verification 已在初次请求后保留 IDS/非 IDS 规格供后续轮次使用，也明确承认初始规格可能漏掉需求。[G3，两页正文]

TraceCAD 已把请求特征、步骤、错误及候选结果绑定，并据执行、语义、保全和局部性证据决定是否接受修补；其保全主要基于视觉/shape-delta，不能等同精确 IFC 保全。[M3，方法]

因此，我们应使用 **post-edit semantic read-back validation（修改后语义回读核验）**。除非另外定义编码/解码或双向变换性质，否则不要用 round-trip 暗示可逆恢复；它也不是本仓库另一条 IFC→Text→IFC 重建实验。

## 5. 最接近的 IFC 工作：哪些差异确实有原文依据？

**IFC-Agent 是最重要的直接系统比较对象之一。**它已有 schema-guided reasoning、原生 IFC 字段修改与对话交互；但 §6.3 明确承认缺乏修改后模型一致性验证。这支持“我们重点实现并展示修改后的语义核验”的具体差异，不支持“只有我们验证 IFC”。[R1，PDF p18]

**Wu 2026 是实际自动修改的强近邻。**其输入包含 ACC 问题及设计人员的改进策略，LLM 形式化构件操作并重新评价候选。不能用“我们的输入是人类自然语言”轻易排除，因为对方也在形式化人类策略。其完整执行/检查合同本轮仍待全文核查。[R4]

**Design Healing 2025 更早已研究检查后的自动设计改正。**我们不能把“不从零生成，而是保留原设计进行修复”本身算成新颖点。[R5]

**BIBIMBAP 的保全有明确边界。**其 Limitations 写明 Update 不检查非几何属性保持，删除重建丢属性仍可能计作正确。旧矩阵笼统打勾应撤回；但检查几何、存在性和关系的价值仍应承认。[E2，PDF p8]

## 6. 仓库支持与不支持的主张

本轮连接到 `E:\code for project\bimnet`，分支 `codex/bim2text-research`；工作树存在其他任务修改。下面是读取时的实现证据，不代表冻结发布版本或新测试通过。

| 证据 | 实际支持 | 不应推导 |
|---|---|---|
| K1 `src/text2ifc_ifc_repair/changesets.py:157–235` | Draft 绑定 source/model、Manifest、scope、operation 与 assignments，生成 Bound ChangeSet | 通用新编辑语言、最小补丁、完整依赖闭包 |
| K2 同文件 `:239–295` | 在提供 resolved_authority 的路径，比较操作集合、目标、参数和范围是否一致 | LLM 在第二阶段还承担了新的规划推理；该价值需要单独证明 |
| K3 `property_intent.py:31–42,143–168` | 精确属性意图可携带来源；构造路径使用标准记录、规范化值与 occurrence scope | 仅凭 ExactPropertyIntent 类实例就获得执行资格；类注释明确它本身是 claim |
| K4 `orchestrator.py:185–227`；`docs/how-to/agent-takeover.md:195–224` | Manifest 统一写入/评估预期，公共链包含 staging、reopen、生产评估和私有基准评估分离 | 自动证明原始自然语言意图正确，或完整 IFC 可逆往返 |
| K5 `docs/validation/repair-milestone-r1/repair-proof-matrix-2026-09-03.md:83–176` | 最终 R1 12 个冻结案例合同通过；其中 11 个输出模型、1 个正确无输出，历史失败保留 | 12 个修复产物、盲测 100% 成功率、可与别人的平均分直接比较 |
| K6 `.planning/STATE.md:1–19`、`.planning/ROADMAP.md:1–18` | R1/Phase12/12.1 历史关闭，Phase13 未启动，另有历史测试债务 | 当前工作树仓库级测试全绿或大模型规模泛化成立 |

当前 R1 的主要语义写入仍是受支持类的 occurrence 标量属性，以及受限梁柱新增。Door/Window/Opening 的注册实现与历史演示不自动获得本轮 R1 新资格。`OperationIntent` 中出现 quantity、reuse 等字段也不能直接当作整个功能已验收。

### 一个值得验证而非立即改动的代码问题

K2 表明目标、参数、操作集合等在 Stage 2 前已经可被确定。如果 Stage 2 主要复述这些已确定内容，**“确定性生成 Draft”应成为对照**。它检验第二次 LLM 调用究竟增加语义能力，还是只增加格式失败与费用。没有实验前，不判断该阶段冗余，更不删除生产实现。

## 7. 从前作 SGSS 继承什么？新增什么？

SGSS 的作者贡献叙事是拆开语言理解与 schema matching，并借助中间缓存组织 IDS 输出；具体内容见 [全文阅读](../sgss-fulltext-review-20260921.md)。这是一种任务化系统架构，不是全文已证明的新 embedding 算法。

我们应明确继承语义拆分、schema 检索/匹配及中间记录的思想。后续增量放在：**将需求规范化扩展到已有 IFC 的实例化变更，并核对真实产物的语义实现。**它是合理的前后作关系，但由于 RAMC、CADIR、IFC-Agent 等已覆盖相邻机制，仍不能直接推出独立方法首创。

可以仿其“问题—方法图—交互平台—案例”的写作组织；不能仿照缺少定量对照时仍直接宣称更高精度、更强多语言鲁棒性的写法。

## 8. 攻击后保留的论文主张

### 推荐标题（暂定）

**IFC-SemRepair: Schema-Grounded Repair of Existing IFC Models with Semantic ChangeSets**

相比前一版，标题不再让 Model-Bound 或 Round-Trip 两个词承担未证明的方法创新。

### 一句中文主张

**我们展示一个面向已有 IFC2X3 的自然语言语义修复系统，将用户要求解析为实例绑定的局部变更，并通过修改后回读检查其在真实 IFC 中的实现。**

### English contribution candidate

We demonstrate an interactive IFC2X3 repair system that connects natural-language change requests with schema-grounded, instance-bound semantic ChangeSets and post-edit read-back validation. The system exposes the interpreted target, property semantics, and resulting model changes for inspection, and reports conformance to the interpreted edit separately from the evidence supporting the original request.

最后一句的完整交互呈现属于论文目标；现有后端证据与统一 UI 的差距需要核查后补齐，不能据该句声称已部署完整界面。

### 三项支撑能力，而不是三项“首创算法”

1. **语义落地。**明确区分用户词语、标准属性、当前 occurrence、值/单位和来源，形成可执行修改。
2. **局部实现。**在已有模型上使用受支持操作构成 ChangeSet，而非为修一个属性重新生成整栋模型。
3. **结果核对。**回读实际 IFC 的目标事实与相关未修改状态，向用户展示改前、预期、改后及检查结果。

这些能力共同形成一个 Demo 系统贡献。是否比已有强工具 Agent 更有效，是待验证的效果问题；当前不写“首次”“无损”“通用”或“显著优于”。

## 9. 最值得补的证据：语义正确性，而不是安全压力测试

下一步建议先冻结一个小型、按原始模型分组的语义修复集合，数量由问题覆盖与成本决定；**36 个样本不是创新性或统计充分性的阈值**。

| 切片 | 核心问题 | 必须有的独立检查 |
|---|---|---|
| Property 与根 Attribute | Reference/Tag 等字段是否混淆 | 人工预先确认字段身份，回读实际字段而非只看名称 |
| Occurrence 与 Type | 改一个实例还是共享类型？ | 检查实际写入来源及其他实例；Type 修改不支持时应如实界定 |
| 值和单位 | 语义选对以后，值是否正确解释 | 类别、值类型、数值换算分别记录，不能仅记 schema valid |
| 目标定位 | 相同词语在不同模型中指谁？ | 预先确认目标或允许的候选集合，避免输出反推真值 |
| 构件补全 | 新构件是否连到正确宿主/楼层？ | 回读受支持的几何及关系，不以“文件能打开”替代 |
| 复合修改 | 多个要求是否全部实现？ | 每项语义都检查；不以事务成功推断操作交互推理能力 |

至少分开报告：意图解释正确、目标变更完成、相关非目标状态保持、澄清后的完成情况，以及总调用/耗时/成本。把只改了 FireRating 标签与实际达到防火工程要求分开；写入 LoadBearing=true 也不等于完成结构验算。

### 公平对照，而不是只移除最后一层门禁

**B0 同模型工具 Agent：**提供合理 IFC 查询/修改工具、同样可访问的 schema 资料和预算，不刻意弱化为一次性吐 STEP。

**B1 同操作能力的结构化直接输出：**使用同一受支持操作集合与确定性 applicator，隔离“中间语义拆分/对齐”的增量，避免把工具能力差异当方法差异。

**B2 完整链：**当前多阶段方案。另用确定性 Draft 替代 Stage 2 作为针对性消融，不增加新的表达能力。

所有方案用同一份独立冻结的意图与产物检查评分。新建评测可预先准备合法参考；不可给旧 R1 事后补造 private Gold。若系统把错误候选拦住但完成率下降，应同时报告，不将“没有输出”一律记成修复成功。

## 10. 本轮结论边界与下一步决策

本轮没有证明“世界上不存在完全相同系统”，也没有因局部先例多就否定领域系统价值。已经足以否定的是：**仅靠改名为 Semantic ChangeSet / Round-Trip，就宣布两个新方法成立。**

最有价值的继续方向是让语义链可观察、可独立核对，并用小规模公平对照回答：复杂的多阶段结构究竟在哪些真实 IFC 语义问题上减少错误、在哪些地方没有收益。

本轮新增研究资料，不改生产实现、不启动 Phase13、不新增训练路线，也不修改任何历史验收结论。

## 参考定位

[M1] RAMC，https://www.se.cs.uni-saarland.de/publications/docs/TWA%2B25.pdf ，§III–IV，Appendix B/C。

[M2] CADIR，https://arxiv.org/html/2608.00891v1 ，方法、Post-reconstruction editing。

[M3] TraceCAD，https://arxiv.org/pdf/2608.03062 ，方法、Algorithm 1。

[M4] ATLAS v3，https://arxiv.org/html/2510.25890v3 ，§3.3–3.6。

[M5] Well-Formed Executable Suggestions，https://conf.researchr.org/details/models-2026/models-2026-research-papers/7/Well-Formed-Executable-Suggestions-for-Continuous-Model-Driven-Engineering ，官方摘要。

[R1] IFC-Agent，https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf ，§6.3，PDF p18。

[R4] Wu 等 2026，https://portal.fis.tum.de/en/publications/automated-building-component-alterations-driven-by-llm-formalized/ ，作者机构摘要。

[R5] Design Healing 2025，https://portal.fis.tum.de/en/publications/design-healing-framework-for-automated-code-compliance/ ，作者机构摘要。

[G3] Self-Verification，https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf ，两页正文。

[E2] BIBIMBAP，https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf ，Benchmark、Evaluation Metrics、Limitations。
