# Agent Debug、能力评测与真实 LLM 准入协议

**状态：** 跨 Phase 规范性协议

**适用范围：** Agent/LLM 行为、Prompt、Schema、Router、Retriever、Compiler、
Applicator、Evaluator、Provider 接入及其能力声明

本文是 `AGENTS.md` 的渐进式披露详情。根目录只保留必须始终可见的门禁；本文
负责解释执行方法、证据合同和准入顺序。Phase SPEC、PLAN、VALIDATION 可以增加
更严格的测试和阈值，但不得降低本文要求。

## 1. 基本原则

单例失败适合用于发现和修复 Bug，但单例从红变绿只证明该 Bug 被修复。系统
能力提升必须证明修改对一个预先冻结、包含未知样本的任务分布产生净改善。

三个结论必须分开：

| 结论 | 最低证据 | 不足以证明它的证据 |
|---|---|---|
| Bug fixed | 原始症状可复现；根因和违反的不变量明确；原始复现与回归测试转绿 | 只看最终输出、只修改错误消息 |
| Failure-class robustness improved | 修复前冻结的同类案例族和未见 sibling 集整体改善 | 原案例或由原案例直接改写的一两个样本通过 |
| System capability improved | 冻结 Baseline/Candidate 全集配对比较、统计不确定性、关键切片无回退、安全门禁通过 | pytest 总数增加、成功 Proof 增加、一次真实 Provider 成功 |

Regression suite 回答“已知行为有没有坏”；Evaluation 0.2 等单次评估器回答
“这次输出是否正确”；成功 Proof 回答“这个成功结果是否可追溯”。它们都不是
系统能力提升的分母。

## 2. Agent Debug 协议

### 2.1 冻结观察，先建立反馈环

编辑实现、Prompt 或 Schema 前，先保存：

- 原始公共输入、环境、commit、模型/Provider 标识和配置；
- Prompt/profile/schema 的 ID、版本和 SHA-256；
- 每次真实响应、attempt、correction/retry 原因和中间产物；
- 预期行为、实际行为、失败阶段和终端状态；
- 可重复执行的最窄命令以及复现率。

反馈命令必须能命中用户观察到的具体症状，而不是只断言“没有崩溃”。确定性
问题应得到稳定的红/绿结果；随机问题应通过循环提高复现率，并把复现概率作为
Baseline，而不是挑选一次失败或成功。

### 2.2 先定位阶段，再讨论修复

按当前公共链路逐段定位，适用哪个路径就检查哪个路径：

```text
公共输入与 Truth Boundary
-> Prompt/Profile 选择与 Context 渲染
-> Stage 1 Intent / Design Brief
-> Clarification / Route
-> Index / Retrieval / Target Resolution
-> Stage 2 Formal Candidate / Provider ChangeSet Draft
-> Schema / Semantic Gate / Deterministic Binding
-> Compiler / Applicator / Transaction
-> IFC reopen / L0 / L1 / L2 / Preservation
-> Run Store / Resume / Terminal Publication
```

优先使用阶段替换和差分重放：

1. 冻结真实 Provider 输出，只重放确定性下游；
2. 用正确的 Stage 1 结果替换原结果，观察下游是否恢复；
3. 用正确的 Stage 2/ChangeSet 替换原结果，观察 Apply/Evaluation；
4. 把同一中间产物分别交给 Baseline 和 Candidate；
5. 对随机行为固定可固定的 seed/config，并重复运行。

只有在失败边界被定位后，才能修改相应层。最终失败不能自动归因于 Prompt。

### 2.3 分类根因

| 类型 | 典型判断 | 合适的修复目标 |
|---|---|---|
| 确定性实现 Bug | 冻结中间结果后仍稳定失败 | 算法、不变量、事务或边界实现 |
| Prompt/合同表达缺陷 | Schema 能表达正确答案，但不同任务反复误解同一约束 | Profile 渲染、指令结构或示例覆盖原则 |
| Schema 设计缺陷 | 合理结果无法表达，或多个权威字段冲突 | 新增版本和迁移合同；不得覆盖已发布版本 |
| Provider 随机失败 | 同输入、同配置产生不同有效性或语义结果 | 可靠性、重试/澄清策略和概率指标 |
| 能力范围外 | Registry/产品合同明确不支持 | fail-closed、清晰拒绝或新 Feature 规格 |
| Evaluator 缺陷 | 正确结果被拒或错误结果被放行 | 独立修复评分器，并重新评分 Baseline/Candidate |

### 2.4 提出可证伪假设

测试修复前列出 3–5 个排序假设。每个假设必须写明预测：如果它是真的，改变
哪个变量会让错误消失或加重。一次实验只改变一个主要变量，避免把 Prompt、
Schema、Parser 和 Evaluator 同时修改后无法归因。

### 2.5 修复前冻结 Failure Family

原始案例是复现入口，不是能力评测集。根据违反的不变量，在看到修复结果之前
建立并冻结同类案例：

- 同语义、不同措辞；
- 同措辞、不同目标和不同 scene family；
- 相邻正例、反例和边界值；
- single、batch、mixed 和冲突/回滚路径；
- complete、clarification、ambiguous、unsupported；
- 至少一个未参与调试的 sibling/holdout 子集。

同一 base IFC、mutation recipe、target identity 或 request template 的派生项必须
作为一组分配，不能跨 Development/Holdout 泄漏。若是必须立即修复的安全问题，
可以先修，但只能声明 Bug fixed；后续补齐独立案例族后才能扩大声明。

### 2.6 机制级修复

修复应恢复通用不变量，例如证据优先级、澄清策略、operation registry、事务
原子性、profile/schema 一致性或 Evaluator 独立性。下列修改默认视为定点兜底，
除非产品合同和跨案例证据另有证明：

- 根据一个模型输出直接增加 alias、字段搬迁或宽松解析；
- 把失败输入、scene 名称、实体 ID 或期望答案写入 Prompt/Few-shot/代码；
- 为通过案例放宽 L1/L2 tolerance 或 preservation 范围；
- 在修复 Candidate 的同时修改 Evaluator，却不重新评分 Baseline；
- 把已揭示的 Holdout 案例继续当作盲测证据。

## 3. 能力评测合同

### 3.1 数据集角色

- **Development：** 可查看错误和私有 Gold，用于诊断与实现。
- **Validation：** 用于选择候选方案；不得逐例加入特判。
- **Hidden Test：** 发布前受控运行；一旦揭示便降级为后续 regression 数据。
- **External Challenge：** 不同来源或建模分布，专门约束跨数据集声明。

任务 manifest 必须列出完整分母，包括成功、失败、澄清、拒绝、超时和不可评估
结果；成功 Proof 集不得替代它。至少按 `scene_family`、`mutation_family` 和
`request_template_family` 分组隔离。

### 3.2 能力矩阵

根据阶段范围分层覆盖：

- operation family：Window、Door、Beam、Column、Mixed；
- request state：Complete、Clarification、Ambiguous、Unsupported；
- target evidence：Name/Tag、Storey、Space/Grid、方向、几何、无 GUID；
- cardinality：Single、Batch、Mixed-family；
- semantic policy：Type 复用/创建、Material 有/无、Pset、Quantity；
- model distribution：已见 scene、未见 scene family、外部来源；
- scale：小、中、大 IFC；
- language：规范表达、同义改写、口语、冗余和轻微噪声；
- safety：冲突、重复目标、部分失败、原子回滚和越权修改。

不要求构造完整笛卡尔积，但必须预先说明抽样方法、每个关键切片的分母和未覆盖
区域。批量 operation 不能因为 operation 数量大而支配总体指标。

### 3.3 Baseline/Candidate 配对

比较必须绑定：

- 精确 commit、依赖、Prompt/Profile/Schema/Registry/Evaluator 版本和哈希；
- 相同任务、公共输入、Provider 模型、配置、token/retry budget；
- 相同评分器；若评分器改变，用新评分器同时重算两边保存的输出；
- 真实 Provider A/B 随机交错运行，降低服务端时间漂移；
- 所有 attempt 和失败保留，不得只挑选成功运行。

### 3.4 指标与声明门禁

端到端严格成功必须同时满足正确路由、合法意图和目标、合法 Candidate/
ChangeSet、Apply/Compile、IFC reopen、强制 L0/L1/L2、Preservation、无私有信息
泄漏、无 synthetic fallback，以及正确终端发布。

至少报告：

- macro strict end-to-end success rate 和各能力切片；
- first-attempt success 与 bounded-retry success，不能只报告 pass@k；
- clarification 必要事实召回、无关提问率和完成轮数；
- unsupported/conflict 的正确拒绝率和 false-publish rate；
- Provider 调用数、token、成本、p50/p95 latency；
- paired delta、样本量和置信区间；随机 Provider 按任务重复运行。

改进阈值、关键切片非劣界限、统计方法和运行预算必须在看结果前冻结。只有总体
主指标达到预设改善、置信区间支持、关键切片无越界回退，并且 false publish、
private-Gold leakage、source mutation 等零容忍指标仍为零，才可声明系统能力
提升。否则只声明 Bug fixed、class robustness improved 或结果 inconclusive。

## 4. 真实 LLM 前的逐环节与全链路门禁

真实 LLM 是最后的 viability/reliability 层，不是 Debug 确定性代码的第一步。
任何真实 Provider transport 前，都必须由当前 Stage Admission 证明逐环节测试和离线全链路要求已经满足；阶段内普通修复只需补充与 changed scope 相匹配的验证，除非该修复使 Admission 失效。

### 4.1 每个环节的最低测试

| 环节 | 真实 LLM 前必须证明 |
|---|---|
| 公共输入/Truth Boundary | 输入 Schema、source hash、路径安全、source 不原地修改、Gold/mutation/deleted identity 不可达 |
| Prompt/Profile/Context | 只选择相关 profile/few-shot；版本/哈希固定；token 有界；无私有值；canonical 字段一致 |
| Provider adapter seam | fake/replay 的正常、认证失败、超时、截断、空响应、非 JSON、schema-invalid 和重试上限 |
| Stage 1 Intent/Design Brief | complete、missing、ambiguous、unsupported；必填事实不猜测；错误可定位 |
| Clarification/Resume | grouped question、answer 绑定、候选确认、过期/篡改 answer 拒绝、幂等恢复 |
| Retrieval/Target Resolution | matched/mismatched/unavailable、唯一/多候选/零候选、跨 Storey/方向/几何边界、无 Gold |
| Stage 2 Candidate/ChangeSet | operation 白名单、canonical schema、授权事实、未知字段、重复 ID、顺序和 cardinality |
| Deterministic Binding/Audit | damaged/source fingerprint、target binding、authority provenance、scope、Evaluator 不信任自报 aggregate |
| Compiler/Applicator | 正常 apply、failure injection、mixed atomic rollback、source immutability、无部分发布 |
| IFC/Evaluation | IFC2X3 reopen、L0/L1/L2、关系/几何/语义、global preservation、private/public projection |
| Run Store/Publication | crash/restart、resume、terminal idempotency、diagnostic 与 success 隔离、失败不可晋升 |

每个环节至少包含 positive、negative、boundary 和 failure-injection；如果某环节
无法在无网络条件下测试，应先增加 seam，不得直接用真实 Provider 代替测试。

### 4.2 离线完整链路

使用 deterministic fake Provider 或已冻结且诚实标记的 replay，通过生产公共
API/CLI 运行完整链路，而不是直接调用内部 helper。至少包括：

1. 完整请求成功并通过最终 reopen/L0/L1/L2/Preservation；
2. 信息不足后 clarification/resume 成功；
3. ambiguous/unsupported/conflict 正确 fail-closed，且无 Provider 后续调用或 IFC 发布；
4. malformed/truncated/schema-invalid Provider 输出按合同重试或终止；
5. batch/mixed 中途失败触发原子回滚；
6. source IFC、private Gold 和 evaluator-only mapping 的隔离；
7. crash/restart、run lineage、terminal publication 幂等；
8. 至少一个真实规模 IFC 的时间、内存和 context/token 边界。

全链路成功不能由 mock 某个被测下游阶段、手写成功报告或 aggregate
`success=true` 替代；最终评估必须重新打开产物并独立计算强制 Gate。

### 4.3 Preflight 与 Admission 证据

活动 Phase 的 VALIDATION 必须维护“环节 -> 测试文件/命令 -> 状态”映射，但验证频率分为三层，避免每次局部修改都升级成同一套大范围检查：

1. **Scoped Validation（默认）**：阶段内普通开发只验证本次修改及其直接上下游风险，记录 changed scope、命令、结果和与当前 Stage Admission 的关系。
2. **Stage Preflight（阶段首次进入或 Admission 失效时）**：第一次进入一个真实执行阶段，或者基础合同变化使既有 Stage Admission 失效时，必须重新覆盖逐环节 seam 与生产公共 API/CLI 的离线完整链路，并生成机器可读 Stage Admission。
3. **Full / Repository-wide Preflight（单独升级）**：只有在跨阶段、仓库级发布/验收或其他明确需要全局重新证明的情况下才运行。执行前 Agent 必须先说明原因、范围和预计门禁，并获得用户明确批准；缺失、过期或无效 Admission 不能自动触发 Full Preflight，只能 fail-closed。

Stage Preflight / Admission 至少记录：

- commit/worktree 状态、Python/依赖和平台；
- 每条命令、开始/结束时间、退出码、timeout、skip 和日志哈希；
- 阶段测试、离线全链路、该阶段公共路径需要的 regression、`compileall` 和 `git diff --check`；
- 离线矩阵、Proof/manifest/evaluator 的版本、路径和 SHA-256；
- admission scope、创建时间、适用 stage，以及会使其失效的基础合同边界；
- `network_transport_attempted: false` 直到所有 blocking gate 通过。

默认 Stage Preflight 命令形态如下，精确测试集合由活动 VALIDATION 根据公共入口实际经过的模块列出：

```powershell
.\.venv\Scripts\python.exe -m pytest <stage-specific tests> -q
.\.venv\Scripts\python.exe -m pytest <all suites reached by the stage public path> -q
.\.venv\Scripts\python.exe -m compileall -q src tests scripts
git diff --check
```

阶段内后续普通修复不得因为“当前没有新 preflight 目录”就重跑 Stage Preflight；应优先复用仍有效的 Stage Admission，并针对 changed scope 运行最窄充分验证。若修改触及公共 API/CLI 入口、核心 schema/version、Provider transport contract、private-Gold/truth boundary、source immutability/transaction rule 或 Admission/validation contract 本身，应将 Admission 视为可能失效并重新判断是否需要 Stage Preflight。

任何适用检查失败、timeout、unexpected skip、证据替代或 admission 验证失败都必须 fail-closed。配置了 API key 不是绕过 Admission 的理由。

## 5. 真实 LLM 执行和失败回流

Admission 通过后，真实运行仍须记录原始 attempt、模型标识、Prompt/Profile/
Schema hash、实际 Stage 调用次数、correction、token/latency、fallback 状态和终端
结果。Synthetic、cached、prerecorded、hand-authored 或 deterministic replay 只能
作为离线证据，不能标记为 live。

真实运行发现失败时：

1. 原样保留失败，不覆盖、不改名为成功；
2. 分类到具体阶段和不变量；
3. 回到离线最小复现与 Failure Family；
4. 在 Development 数据修复并完成与改动风险相匹配的 scoped validation；若改动使 Stage Admission 失效，再重新执行 Stage Preflight；
5. 已揭示案例只能作为 regression，不再作为 blind improvement evidence；
6. 新的真实验收使用冻结的 sibling/holdout 或明确声明为同案例重试可靠性证据。

一次真实成功只能证明该配置在该任务上的可行性。系统能力提升仍由第 3 节的
冻结 Baseline/Candidate 评测决定。

## 6. 每次变更的最小记录

```text
Observed failure / goal:
Reproduction command and rate:
Failing stage and violated invariant:
Ranked hypotheses:
Pre-fix failure-family manifest/hash:
Baseline commit/config/metrics:
Candidate change and why it is mechanism-level:
Original-case result:
Sibling/hidden-set paired delta:
Global capability-slice delta and uncertainty:
Safety/cost/latency regressions:
Offline scoped validation / Stage Admission evidence:
Real Provider evidence, if authorized:
Allowed claim: bug fixed | class robustness improved | system capability improved | inconclusive
```

没有相应证据的字段必须标记为未执行或未知，不得从其他测试结果推断。
