# text2IFC Generation Claim / Novelty Audit — 2026-09-14

用途：研究讨论与论文选题，不是新的实现规范或能力认证。以现有 Generation 为主，允许少量补强；本次不修改产品代码、不运行真实 Provider、不启动 Full Preflight。这里的 correction 指 Generation 内部对生成候选的纠错，不包含独立的 IFC Repair Pipeline。

**审核结论：C1 的宽泛新颖性主张为 RED；C2、C3 收窄后为 YELLOW。目前没有足够证据给任何一项 GREEN。最值得验证的是：Generation loop 的修改范围怎样影响纠错成功率、已有正确结果的保全与成本。**

## 1. Repository Ground Truth

### 1.1 审核依据与证据等级

- 当前检查分支：`codex/workflow-dataset-links`；HEAD：`ce3309bf3ac63ed8f47d793a32bc41ebf6bf0336`。判断以本次读取的工作区文件为准，不把 HEAD 当成整个工作区干净的证明。
- 当前权威入口：[接手指南](<E:/code for project/bimnet/docs/how-to/agent-takeover.md>)、[文档入口](<E:/code for project/bimnet/docs/README.md>)、[STATE](<E:/code for project/bimnet/.planning/STATE.md>)、[ROADMAP](<E:/code for project/bimnet/.planning/ROADMAP.md>)、[PROJECT](<E:/code for project/bimnet/.planning/PROJECT.md>)。
- 工作流说明：[Generation 工作流与数据流](<E:/code for project/bimnet/docs/architecture/current-workflow-and-data-flow.md>)；实验主张遵循 [Agent 能力评估协议](<E:/code for project/bimnet/docs/validation/agent-capability-evaluation.md>)。
- 实现存在、离线契约正确、真实运行可行、相对基线有效、研究新颖性，是五种不同结论。
- 本次运行七个相关 pytest 文件：**62 passed in 32.33s**。这不是 62 个独立建筑场景，也不是能力成功率。

### 1.2 Requirement contract：有动态生成前契约，但不是完整意图的独立真值

| 问题 | 当前结论 | 代码证据与边界 |
| --- | --- | --- |
| Expected Facts 是否先于 Generation？ | 是，所读公共交互流程先写入，再选择生成策略 | [interactive_cli_flow.py:578](<E:/code for project/bimnet/src/text2ifc_agent/interactive_cli_flow.py:578>) |
| 是否从 candidate 反推？ | `build_expected_facts` 的输入是 Design Brief；投影本身不消费 candidate | [expected_facts.py:30](<E:/code for project/bimnet/src/text2ifc_agent/expected_facts.py:30>) |
| 是否只是 fixture？ | 否；从 Brief 的楼层、空间、构件等事实动态构建，同时派生 package manifest | [expected_facts.py:275](<E:/code for project/bimnet/src/text2ifc_agent/expected_facts.py:275>) |
| 是否真正参与验证？ | 是；生成需求期望，再绑定候选目标，并检查编译后的 IFC | [live_pipeline.py:1755](<E:/code for project/bimnet/src/text2ifc_agent/live_pipeline.py:1755>)、[candidate gates](<E:/code for project/bimnet/src/text2ifc_agent/live_pipeline.py:1587>) |
| 能否称 executable generation contract？ | 可以，限于已支持、已表达且检查器覆盖的要求 | 不能扩大为任意自然语言需求的完整形式语义 |
| 是不是 candidate-independent oracle？ | 只能说期望的生成来源独立于 candidate；不能说它是独立于 Brief 的评测真值 | Brief 漏掉用户要求时，下游可能一致地遗漏；目标绑定也仍会读取 candidate |

Expected Facts 同时支持期望、身份分配与分包，是有用的系统设计。它不自动证明规范提取正确、约束完整、编译器语义完备或新颖性。部分几何检查还存在不同期望来源，实验必须报告各任务实际使用的来源，不能统称为完全独立的意图评估。

### 1.3 Compositional generation：写入所有权与冻结存在，严格引用白名单不成立

| 机制 | 核实结果 |
| --- | --- |
| 稳定骨架 | `build_skeleton_workspace` 确定性创建空间骨架；后续通过 ID 引用。 |
| 动态分包 | `build_generation_package_manifest` 根据 Expected Facts 形成楼层局部包、跨楼层包及相关所有权记录；不是仅硬编码某栋示例建筑。 |
| entity / relationship 所有权 | 显式记录允许创建的 ID；包 Gate 检查目标所有权、重复创建、允许的 add 操作。 |
| 前序状态保护 | 包不能覆盖已存在的目标；应用后还比较前序组件 hash，出现漂移则失败。 |
| 包内失败 | 未通过的包不进入已接受 workspace；当前包有有界重试，已有包保留。 |
| 完整输出条件 | 分包 workspace 不等同于正式结果；仍需整体 formal 检查及后续 IFC 验证。 |
| 引用权限 | **不能声称是严格白名单。** `visible_ids = set(existing) | package_ids | allowed_refs`，已有 workspace ID 全部参与引用解析。 |
| 默认路径 | CLI 默认 `legacy_full`，`staged` 是可选策略。所读光庭验收案例采用 `legacy_full`。 |

证据：[generation_packages.py:13](<E:/code for project/bimnet/src/text2ifc_agent/generation_packages.py:13>)、[staged_generation.py:62](<E:/code for project/bimnet/src/text2ifc_agent/staged_generation.py:62>)、[package_gates.py:33](<E:/code for project/bimnet/src/text2ifc_agent/package_gates.py:33>)、[冻结检查](<E:/code for project/bimnet/src/text2ifc_agent/staged_generation.py:232>)、[CLI 默认策略](<E:/code for project/bimnet/scripts/agent/run_text2ifc_chat.py:56>)。

本次额外做了 Gate 层诊断：同一局部包声明只允许引用 `storey-1`；使用 Gate 识别的顶层 `relative_to` 字段时，引用已有但未列入白名单的 `storey-2` 仍通过；引用不存在的 `missing-storey` 被拒绝。该诊断只确认这个 Gate 的可见性规则，不代表相关输入通过最终 schema 或 IFC 编译。

诊断文件：[reference-boundary-probe-v2.json](<E:/code for project/bimnet/.tmp/claim-audit-20260914/reference-boundary-probe-v2.json>)。先前 v1 使用 Gate 不扫描的嵌套字段，无法区分“未授权但存在”和“不存在”；已保留并在 v2 标明，不能用 v1 支持白名单结论。这些 `.tmp` 文件是临时审核证据，未进入 accepted Proof。

因此，可以描述“按写入所有权约束、在追加阶段保留前序组件的组合生成”。不宜直接写成“严格 entity/reference permissions + immutable validated state”：引用边界比这宽；冻结期间局部检查通过，也不意味着所有全局关系已证明正确。

### 1.4 Verification-guided correction：特定路径是真实的受约束状态更新

| 核查项 | 结论 |
| --- | --- |
| 结构化 Issue 与路由 | 已实现，不只是错误字符串回传。 |
| ChangeSet 与作用范围 | ChangeSet 接受外部派生并验证的 scope；通过 ID、字段路径、操作类型等限制修改。不能说每种输出都内嵌相同 scope。 |
| 基础版本绑定 | 检查 revision、candidate hash、Expected Facts hash 和相关 component hash。 |
| 原子应用 | 在候选深拷贝上应用；结构或保全检查失败时不返回可提升的新候选。 |
| 范围外状态 | 应用后比较组件 hash，禁止未授权组件漂移。 |
| 重新验证 | `run_scoped_changeset_round` 本身不是完整 IFC 验证器；交互调用方随后运行 candidate gates，最终验收也重跑所配置的 Gate。 |
| 停止条件 | 有次数上限、未改善与重复问题循环停止规则。 |
| 收敛与语义保全 | 未证明全局收敛；未证明每一步都保持此前所有已满足语义/几何谓词。 |

证据：[issues.py:97](<E:/code for project/bimnet/src/text2ifc_agent/issues.py:97>)、[change_scope.py:26](<E:/code for project/bimnet/src/text2ifc_agent/change_scope.py:26>)、[changeset_apply.py:19](<E:/code for project/bimnet/src/text2ifc_agent/changeset_apply.py:19>)、[scoped_loop.py:58](<E:/code for project/bimnet/src/text2ifc_agent/scoped_loop.py:58>)、[调用后的 Gate](<E:/code for project/bimnet/src/text2ifc_agent/interactive_cli_flow.py:1715>)、[feedback_loop.py:17](<E:/code for project/bimnet/src/text2ifc_agent/feedback_loop.py:17>)。

在所审查的 ChangeSet 路径上，结论属于 **D：有代码执行约束的 bounded state transition**。但其保证首先位于 BIM JSON 操作与状态层；它不是所有 IFC 属性的形式化保全证明。

特别需要区分两件事：组件 JSON 没有变化，不代表该组件在所有上下文中的几何或语义性质不变。例如父级定位、宿主或关联上下文发生变化，可能影响最终解释。这是需要外部检查的风险假设，不是本次已经复现的编译器缺陷。

### 1.5 仍存在整文档输出的纠错路径

[live_pipeline.py 的 Generation 内部恢复分支](<E:/code for project/bimnet/src/text2ifc_agent/live_pipeline.py:988>)仍可要求 Provider 返回完整 BIM JSON。它随后使用 `allowed_change_paths`、证据与 `evaluate_repair_fact_delta` 检查变更边界。

所以，“整个 Generation 系统遇到失败都只输出局部 ChangeSet”不成立；反过来，将这条路径称为“无约束重写后门”也不准确。**输出粒度与允许修改的权限是两个变量，实验应分别控制。**

### 1.6 已有真实案例能支持多强的结论

[2026-09-12 光庭阅读馆报告](<E:/code for project/bimnet/dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/open-court-v2/REPORT.md>)记录真实 Brief → Generator → Audit → IFC，采用 `legacy_full`，没有 Provider 修复。报告记载 111 个实体网格成功、独立检查 545/545 通过，并保留评价修订及原失败。

这是该案例的可行性与人工验收证据。它不能证明 staged 优于 monolithic、纠错 loop 有收益，或 545 个检查等价于 545 个独立任务。报告中的三次成功 loop 也不能改写为三次纠错成功。

## 2. Candidate Claims

| Claim | 待审核的精确定义 | 不应混入的扩大表述 |
| --- | --- | --- |
| C1 Requirement-derived generation contract | 在候选生成前，从需求表示确定验收事实，并用于后续生成与实际 IFC 核验 | 首次从自然语言生成验证规范；完整独立真值；保证所有用户意图 |
| C2 Ownership-bounded compositional generation | 用显式写入所有权组织生成包，受控追加到已有状态，并在追加阶段检查前序组件保全 | 分楼层本身新颖；严格引用白名单已实现；局部通过保证全局正确 |
| C3 Verification-guided bounded state transitions | 将 Issue 转换为受限修改，在绑定版本上应用，验证边界与结果后继续流程 | 首次反馈纠错；所有路径均局部输出；全局最小修改；保证单调收敛 |

三个机制可以共同构成系统贡献，但目前不能按“三个已证明的新算法”书写。

## 3. Prior-work Collision Matrix

### 3.1 作者关联与版本去重

BIM-Edit 的作者群与 MCP4IFC / IFC-Copilot、BIBIMBAP、Self-Verification 有明显交集。应研究这一条工作线，不能只将 BIM-Edit 视为孤立 benchmark。作者所属实验室也将工具调用与 IFC 项目列在同一研究方向：[MDS Lab](https://www.mds-lab.de/research/tool-use-in-llms/)。

MCP4IFC 与 IFC-Copilot 属于同一项目演进线，不能当作两个完全独立的系统重复计算基线数量。其新版 [bonsai-mcp](https://github.com/Show2Instruct/bonsai-mcp) README 说明从原有仓库简化为更多依靠代码生成的实现；复现实验应冻结仓库与版本，不能把旧论文配置、新项目页和新代码的能力混成一个系统。BIBIMBAP 与 BIM-Edit 作者重叠不等于已经证明两个数据集完全同源或完全无重叠。

### 3.2 覆盖关系

“未核实某机制”不等于“该工作不存在该机制”；下面只依据所读原始材料判断碰撞。

| 工作与原始来源 | 已核实的相关内容 | 对本项目的攻击点 | 来源读取边界 |
| --- | --- | --- | --- |
| [MCP4IFC](https://arxiv.org/abs/2511.05533) | 通过 MCP 提供 IFC 操作工具 | NL→IFC、工具调用、标准 IFC 操作不能独立主张新颖 | 预印本摘要、当前官方项目资料 |
| [IFC-Copilot](https://show2instruct.github.io/ifc-copilot/) | 参数工具、动态代码、RAG、结构化返回与多轮设计；与 MCP4IFC 同一项目线 | typed tools、确定性领域工具、观察后纠错已经存在 | 官方项目页与公开仓库说明；项目页 Paper 链接本次未成功打开，不声称已精读新版全文 |
| [BIBIMBAP](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf) | 100 个原子 CRUD 任务、细分推理类别、可执行评估；不评完整多步设计目标 | 原子操作与几何/关系检查已被系统评测；不能将其描述成纯查询 benchmark | EC3 2026 原始 PDF，方法和局限章节；局限中明确非几何属性保全未覆盖 |
| [Self-Verification](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf) | 生成前 IDS 与非 IDS 规范、Modifier、双路验证、合并反馈、多轮更新 | **直接覆盖 C1 宽泛叙事；也覆盖普通 C3 闭环** | EC3 2026 两页论文全文，以及公开 README、orchestrator、merge、modifier 源码 |
| [Text2BIM](https://arxiv.org/html/2408.08054v2) | 多 Agent、规则检查、带构件身份的 BCF 反馈、局部记忆、多次代码修订与停止条件 | Agent loop、构件定位反馈、有限重试均非空白；论文还报告纠错产生新碰撞 | 原文方法 §4.4、算法 1、实验 §6.3 等；不是只读摘要 |
| [BIM-Edit](https://arxiv.org/html/2606.20146v3) | 324 个 IFC 编辑任务，11 个真实建筑与 36 个合成场景；几何、语义、拓扑指标；允许多次工具调用 | 语义拓扑编辑与工具轨迹并非未被研究；其差分评测不能简化为“仅看外观” | 原文方法 §3.2、实验 §4.1；最终 IFC 评分不等于逐轮谓词保全评估 |
| [Building-Diffusion](https://openaccess.thecvf.com/content/CVPR2026W/CV4AEC/html/Sehaba_Building-Diffusion_Graph_Discrete_Diffusion_Model_For_Architectural_Volumetric_Design_Generation_CVPRW_2026_paper.html) | 对建筑体量/布局进行图离散扩散建模 | 结构化建筑生成已有研究；但输出与任务不同，不应强作完整 IFC loop 直接基线 | CVPR 2026 Workshop 官方论文页与摘要；未审核实现 |
| [PRISM](https://arxiv.org/html/2510.25890v1) | 结构与语义分层约束、可验证产物、证据定位的局部修补、修补后区域重验 | 对“可验证生成 + 证据包 + 局部纠错”的一般 CS 新颖性形成强碰撞；不能仅凭更换领域认定首次 | 预印本原文 §3.6 及 AUTOSAR 方法段落；未复现其实现或核验定理 |
| [RADIANT](https://arxiv.org/html/2607.16708v1) | 需求到模型的可执行追踪、hash 识别变化、影响分析、反例驱动修复循环 | requirement trace、版本变化定位、跨阶段闭环也已有近邻 | 预印本原文方法与评测设计；未复现 |

本次在相关 `docs` / `.planning` 范围未定位到以上论文的本地全文副本。按参考审核提示，对“本地论文副本已审核”的统一状态为 **NOT VERIFIED FROM LOCAL PRIMARY SOURCE**；这不否定表中已从作者仓库、出版方 PDF 或 arXiv 原文完成的在线核查，也不代表搜索了整个磁盘。

### 3.3 最直接近邻的代码对照

Self-Verification 的 [orchestrator.py](https://github.com/Tsesterh/Text2BIM-Self-Verification/blob/main/src/orchestrator.py) 在循环前运行 Specifier，循环中将上轮 IFC 和合并的 patch plan 传给 Modifier，再汇合验证结果并判断结束。[merge.py](https://github.com/Tsesterh/Text2BIM-Self-Verification/blob/main/src/merge.py) 已包含 requirement ID、优先级、来源与证据字段。不能把“反馈结构化”当成我们的剩余区分点。

其所读 [modifier.py](https://github.com/Tsesterh/Text2BIM-Self-Verification/blob/main/src/modifier.py) 通过提示要求避免无关修改，工具 handler 按函数名派发；在这个本地 backend 文件中没有看到与本项目同构的 scope/hash 应用检查。这支持做“提示约束 vs 执行约束”的实验，不足以断言该系统所有 backend 都没有任何保护。

本次读取的 Git blob：orchestrator `dbf306b6d3834c6473640f63a3c51f78dfb58476`；merge `a29e172c8dbcfe017cd64e7d761a8bc78d4be1b3`；modifier `399ab9de35d4c62d5e9da8fe949b7dd233f4211f`。这些是文件 blob，不是整仓库 commit。

## 4. Novelty Attack

### C1：规范提取加生成后检查，为什么不是已有 Self-Verification？

这一攻击成立。Expected Facts 采用确定性投影、参与 ID 和分包可以说明系统设计，但若没有独有语义、机制比较或可测收益，就不能通过改名保留“生成前契约”这一大 Claim。需要单独测 Brief 对原始需求的漏提取，否则契约和产物可能一起漏掉同一要求。

**C1 SHOULD NOT BE CLAIMED AS NOVEL**，特指目前这个宽泛主张，而非否定模块价值。

### C2：所有权与冻结是否只是分块生成加常规状态管理？

当前比“逐层多调用几次 LLM”更具体，因为写入边界、前序组件 hash 与拒绝应用由代码执行。但以下问题没有答案：收益来自更短输出、更多推理预算，还是所有权与冻结？前序包已经选错布局时，冻结是否造成不可恢复？跨楼层包是否需要修改先前组件？为什么显式的引用列表没有成为严格白名单？

在没有消融前，只能确认实现区别。还需对照组件级生成、增量模型变换等邻近方法；PRISM 已有组件生成与验证，不能把“组合”二字视为天然区分。

### C3：受限修补是否只是普通事务与验证循环的领域应用？

版本绑定、范围检查与原子应用是实际机制；它们并不因用于 LLM 就自动成为算法创新。Text2BIM / Self-Verification 已有问题驱动闭环，PRISM 已提出证据定位与局部修补。

目前仍值得验证的区别是**执行器强制的修改范围如何影响整个迭代轨迹**。需要同时证明：没有把原来正确的要求改坏，也没有靠拒绝所有困难修改来获得漂亮的保全率。局部 hash 保全、实际 IFC 性质保全与全任务成功必须分别测量。

## 5. Claim Verdict

| Claim | Verdict | 理由与可保留部分 |
| --- | --- | --- |
| C1 | **RED** | 宽泛思路被直接近邻覆盖；可作为系统基础设计，不能单独承担创新性。 |
| C2 | **YELLOW** | 动态所有权与前序状态保护确有实现；严格引用权限表述过强，且没有隔离各机制收益。 |
| C3 | **YELLOW** | ChangeSet 路径有受约束状态更新；普通 loop 与局部修补已撞车，尚缺相对强基线的轨迹和完成率证据。若写成“首次验证后纠错”，则为 RED。 |

YELLOW 表示值得检验的候选贡献，不表示已有充分的新颖性或论文录用依据。没有 GREEN 是本次证据判断，不是对项目最终研究价值的结论。

## 6. Minimal Defensible Claims

以下可写入系统介绍，但不附带“首次”“显著优于”或未验证的保证：

1. **生成前需求投影。** text2IFC 将受支持的 Design Brief 事实投影为独立于生成候选来源的期望表示，用于身份分配、分包与后续产物检查。
2. **受所有权约束的组合生成。** 在 staged 策略中，生成包通过受限追加操作构建 BIM JSON；执行器检查写入所有权，并验证前序组件在追加阶段保持不变。
3. **基于版本的受限纠错。** 在 scoped correction 路径中，系统将验证问题映射为授权范围，对绑定候选版本的 ChangeSet 进行原子应用与保全检查，调用方再验证编译后的 IFC。

适合当前系统的英文描述草稿：

> text2IFC combines requirement-derived expectations with ownership-bounded staged generation and revision-bound correction. Its executor enforces authorized changes to BIM JSON candidates, while downstream checks assess the compiled IFC artifacts.

这句话描述组合与实现，不承诺这些基本概念均为本项目原创。

如果后续写三个论文贡献，建议围绕一个研究问题组织为“问题与评估定义、具体 loop 方法、系统与实验发现”。三项贡献不需要伪装成三个独立算法创新。第三项只有做完实验才能写结果。

## 7. Missing Evidence

| 类别 | 当前缺口 | 为什么影响结论 |
| --- | --- | --- |
| Code evidence | 严格 reference allowlist 并非当前行为；未建立所有路径都只用 ChangeSet 的统一保证 | 阻止过强的 C2/C3 表述；修掉边界问题本身也不等于新方法 |
| Semantic preservation | 没有本次核实过的逐轮、跨编译的已满足谓词保全实验 | 组件 bytes 不变与模型行为/几何性质不变不能等同 |
| Literature evidence | IFC-Copilot 新版全文、其他 backend、增量模型变换与程序修复的精确机制比较尚未完成 | 当前只是有针对性的近邻审核，不能作穷尽性首创证明 |
| Benchmark | 缺冻结的未见完整 Generation 任务及自然失败轨迹池 | accepted 案例不能作为能力总体分母；原子 CRUD benchmark 不能替代整栋生成 |
| Independent evaluator | 需独立于 Brief 的原始需求标注，并在最终 IFC 上检查 | 防止规范遗漏、候选遗漏、检查遗漏相互掩盖 |
| Baseline | 缺同模型同任务的强工具 loop / specification-verification loop 对比 | 与 one-shot 比较不足以支持 loop 创新 |
| Ablation | 缺输出粒度、作用权限、分包、预算各因素的拆解 | 无法归因机制收益 |
| Reliability | 缺重复运行、任务族分组隔离、失败分母和不确定性 | 无法把个案提升为系统能力 |

## 8. Recommended Experiments

### 8.1 优先验证的核心问题

**在模型、反馈与预算可比时，执行器强制的修改范围，能否降低迭代中对已有正确结果的破坏，并维持或提高完整 Generation 成功率？如果固定范围过窄，基于验证证据的有限范围扩展是否有价值？**

“迭代会产生新错误”已有文献观察；本项目应贡献明确的控制机制与因果实验。不能仅重复观察便称首次发现。

### 8.2 E1：同一失败候选上的 loop 机制比较 — 最优先

建立两套互补材料：自然生成失败的冻结候选用于能力实验；人工扰动与确定性反例用于机制诊断。两类结果分开报告。所有组从相同候选、相同公开需求及首轮反馈开始；后续反馈由同一固定检查器根据各自候选产生。

| 组别 | 输出/更新方式 | 修改边界 |
| --- | --- | --- |
| A | 整候选修订的普通 verify–refine loop | 有同等领域与 schema 检查，局部性只靠提示 |
| B | 局部 patch / 相同 ChangeSet 表达 | 局部性只靠提示，保留其余共同检查 |
| C | 与 B 相同表达 | 启用当前执行器的 scope、版本和保全检查 |
| D（可选新增） | 与 C 相同表达 | 根据验证证据有限扩展 scope，并比较修改前后的已满足要求 |

B→C 用于隔离“执行约束”；A→B 用于观察输出粒度影响。不能把项目现有的整文档 fact-delta 受限路径标成“无约束 baseline”。不应在生产路径关闭保护；需要对比时使用隔离的实验实现。

必须包含：局部可修复、宿主—洞口—填充耦合、跨楼层依赖、初始定位错误、需要联合修改、不可满足或证据不足的任务。记录失败和拒绝，不筛选只适合局部修改的例子。

主指标：**完整任务成功率 + 新引入回退的任务比例**。辅指标：每轮 true→false 的要求数、范围外组件变化、世界坐标几何变化、语义/拓扑结果、错误定位质量、循环与无效尝试、token、成本及延迟。任务分母、step 分母与 element 分母分别报告。

不能只报“99% 元素保持”：大模型中改坏一个关键楼梯也可能被大量无关元素稀释。也不能把“始终拒绝修改”产生的零回退当成更强能力。

### 8.3 E2：完整需求到 IFC 的端到端比较 — 必做

以相同原始需求分别运行强 baseline 与 text2IFC；将 Brief 提取失败、生成失败、纠错失败、预算耗尽和错误发布都计入分母。首选对照 Self-Verification 风格规范验证闭环，以及冻结版本的 IFC-Copilot / bonsai-mcp。改写了工具或 representation 的版本应标为受该工作启发的适配基线，不能当作原系统精确复现。

评估同时回答三个不同问题：

- 原始要求是否完整进入 Brief / Expected Facts？
- 最终 IFC 是否满足这些原始要求及必要几何、语义、拓扑条件？
- 增加 loop 后的收益是否抵得上增加的 token、延迟和失败机会？

内部 Gate 只作系统反馈；独立评测依据应预先冻结，不能运行后为 candidate 修改。对所有组保持相同领域信息、模型版本和资源上限；无法完全相同的工具表示差异应公开。报告成功率随预算变化的曲线，避免仅比较一次调用与多次调用。

### 8.4 E3：分包的增益究竟来自哪里 — C2 要当主贡献时必做

比较 Monolithic、Staged、Staged + Package Checks、Staged + Ownership + Freeze。实验开始前逐项定义开关；“分包边界”与“所有权”的语义不能重复，以免只是四个名称对应两种行为。所有实验组保留相同最终验证。

用共享的、在生成前冻结的 Brief / Expected Facts 隔离 Generation 本身。按楼层数量、构件数、跨包依赖密度与需求复杂度分层；同源建筑变体不能分散进开发集和未见集。比较预算匹配条件及预算曲线，专门纳入“前序局部合法、全局不合适”的冻结反例。

若收益只来自输出变短，应如实形成系统效率结论；若所有权与冻结对成功率没有增益或损害恢复，不应强保留 C2 为核心研究点。

### 8.5 E4：检查器与保全定义的反例评估 — 成本低，必须配套

在受支持要求上构造受控漏项、错误 host、错层、错误类型、几何定位与关系破坏；确认独立评测能检测它们。分别测假阴性与假阳性。关键反例包括：JSON 未变但上下文改变导致性质变化；错误期望让错误产物通过；把要求删掉而使违规数下降。

这些是验证器诊断材料，不能冒充自然分布性能或真实 Provider 能力。已通过的 62 项测试只支持所测软件行为。

### 8.6 少量补强应该补什么

先补逐轮“要求状态变化”的记录和独立评分，再决定是否改 loop。这样可以用现有实现发现收益究竟来自哪里，避免先堆新 Agent。

如果 E1 显示当前固定 scope 明显阻碍本可完成的任务，再原型化以下机制：依据失败要求与已知 IFC 依赖，选择一个有限的修改集合；尝试修改并重验；若需要扩大，记录具体证据和新增依赖后再扩大；无法解释的扩大或预算耗尽则停止。候选集合可覆盖目标、宿主/洞口/填充、相关楼层及几何邻接，但必须按实际 schema 与编译行为定义。

**这套自适应 scope 选择目前是研究建议，尚未实现，也尚未证明新颖。** 需要与固定依赖闭包、普通局部 patch、PRISM 风格证据局部修补等相邻机制区别。不能把“依据证据局部修改”本身再申报为新概念。

另外，零回退规则可能过于保守：某些任务需要联合修改或暂时经过中间不满足状态。应区分内部暂存状态与对外提交状态，测量严格保全的成功率损失；不要承诺任意任务单调收敛。

### 8.7 规模与执行顺序

建议先用约 12–20 个开发任务做诊断，覆盖至少四类失败机制。这是发现信号的 pilot，不作为最终未见集。确认指标和可比较性后，再冻结独立测试集。Demo 可从约 30–50 个分层任务、关键组多次重复的方案估算成本；正式规模取决于 pilot 的方差、任务族数量与可接受区间宽度，没有通用“够发表”的样本数。

至少在另一个骨干模型上复核关键消融，才考虑跨模型结论。按建筑/任务族分组计算配对差异与置信区间；相同建筑的多 prompt、多 seed 不能伪装成独立建筑。若只有一个模型，只作单模型结论。

执行顺序：E4 与轨迹记录 → E1 pilot → E2 held-out 对比 → 仅在 C2 有必要时做 E3 → 根据证据决定是否实现 D。真实 Provider 实验另须满足项目当前执行阶段的 admission；本次 62 项 focused tests 不替代该准入。

### 8.8 论文方向与 Generation + Repair 的关系

推荐的工作题目：**text2IFC: Scope-Controlled Agent Loops for Verifiable BIM Generation**。题目只是研究方向标签，不声明已经证明收益。

对 WWW Demo，可以围绕已实现的交互、生成、反馈定位、受限修改、版本与实际 IFC 对照组织系统展示；还必须说明 Web 场景价值。不能只因有网页界面便认定符合 Web 研究定位。正式 research paper 则需要 E1/E2 的方法或实证贡献；MODELS 的模型生成、变换、一致性与验证主题更自然。ICSE/ASE 需要明确软件工程研究问题，不能靠行业应用名词替代。

参考官方范围：[WWW 2027 Demo](https://www2027.thewebconf.org/demos/)、[MODELS 2026 research scope](https://conf.researchr.org/track/models-2026/models-2026-research-papers)、[ICSE 2027 Demonstrations](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations)。MODELS 2026 仅作范围参照，不代表仍可投稿或已经核实下一届 CFP。

若之后联合独立的 Repair Pipeline，合理主线是“结构化工程产物的受约束状态修改与验证”。需要在 Generation 自有状态和外部已有 IFC 上分别给出实现映射、失败类型、共享机制消融与收益。**两块功能放进一个系统并不自动产生新的方法贡献；本次没有重新审核 Repair，也不将其能力用于补足 Generation 的证据缺口。**

---

**当前最强 Claim：** scoped ChangeSet 路径在版本绑定与修改范围下进行受约束更新；目前是最值得测的候选贡献。

**当前最危险 Claim：** 首次从需求生成验证契约，以及“冻结状态保证全局正确/loop 必然收敛”。

**已经明显撞车的部分：** Agent loop、生成前验证规范、结构化问题反馈、工具执行、生成后检查与一般性局部修补。

**最值得下一步验证的研究假设：** 代码强制的修改范围是否在保持任务完成能力的同时减少迭代回退；如果存在过度约束，验证证据驱动的有限范围扩展能否改善这一取舍。
