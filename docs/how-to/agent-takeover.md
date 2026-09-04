# 首次接管 text2IFC 项目

本指南面向第一次进入仓库的 AI Agent 和开发者。目标是在 10–15 分钟内确认
当前项目状态、找到正确代码与证据入口，并在不覆盖他人工作、不夸大验证结论的
前提下开始任务。

项目和产品名称是 `text2IFC`。本地 checkout 目录可能被命名为 `bimnet`，但这个
目录名不应出现在项目标题、报告或对外说明中。`BIMNet` 在 dataset、source 或
manifest 语境中另指数据来源，也不代表本项目名称。

本文是操作指南，不是新的架构或验收权威。具体约束仍以仓库根目录的
[`AGENTS.md`](../../AGENTS.md)、适用的 Phase SPEC/PLAN/VALIDATION 和验证协议
为准。

## 1. 十分钟接管流程

### 第一步：确认仓库和工作树

在任何编辑、清理、运行实验或 Git 操作前执行：

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git log --oneline --decorate -5
```

确认当前目录确实属于 text2IFC Git 根目录。工作树已有修改时，默认它们属于用户或
其他并行任务；不要使用 `git reset --hard`、`git clean`、`git restore` 或
`git add -A` 处理它们。只读取和暂存本任务明确涉及的路径。若目标文件已经被修改，
先判断能否绕开；不能安全绕开时再向用户说明真实冲突。

### 第二步：建立权威阅读顺序

按以下顺序阅读：

1. [`AGENTS.md`](../../AGENTS.md)：仓库级行为、安全和证据合同。
2. [`docs/README.md`](../README.md)：文档总入口和放置规则。
3. [`.planning/STATE.md`](../../.planning/STATE.md)：当前执行位置和最近闭合状态。
4. [`.planning/ROADMAP.md`](../../.planning/ROADMAP.md)：milestone、phase 和依赖关系。
5. [`.planning/PROJECT.md`](../../.planning/PROJECT.md)：长期目标与稳定约束。
6. 当前任务所属 Phase 的 SPEC、active PLAN 和 VALIDATION。

`STATE.md` 回答“现在做到哪里”，`ROADMAP.md` 回答“阶段如何组织”，
`PROJECT.md` 回答“项目长期坚持什么”。历史报告、旧 handoff 和已完成计划可以
解释过去，但不能覆盖当前状态与适用合同。

### 第三步：给任务分类

先判断任务属于哪一种：

- 新模型生成（Text → BIM JSON → IFC）；
- 已有或 damaged IFC 的 repair；
- Agent/Prompt/Schema/Provider 行为；
- Dataset、manifest 或 provenance；
- Proof、验收或能力评估；
- 文档、发布或纯导航维护。

只加载该类别最小必要的代码和文档。不要为了熟悉仓库而默认扫描全部 dataset、
Proof、历史运行或 1000+ 测试。

## 2. 项目地图

text2IFC 的主产品目标是从自然语言生成新 IFC；仓库还包含一条对已有 IFC 做局部
修改的 repair 链路。二者共享部分证据原则，但输入、状态机和代码入口不同。

### 2.1 新模型生成链路

```text
自然语言 + 对话记录
  -> Design Brief Agent
  -> Draft 时定向澄清 / Ready 时继续
  -> 确定性 Expected Facts + stable entity IDs + Package Manifest
  -> generation strategy
       legacy_full（CLI 当前默认）: 一次生成完整 BIM JSON
       staged（显式选择）: Skeleton + 楼层包/跨楼层 ChangeSet
  -> Formal/Draft 分类 + BIM JSON 2.0 合同验证
  -> Semantic Coverage
  -> Candidate Gates: compile + reopen + relationship/geometry checks
  -> Audit Agent
  -> 必要时 Issue routing + 有界 BIM JSON ChangeSet 返工
  -> Final Acceptance: 重新 Gate + secret scan
  -> accepted output.ifc/report.md，或保留证据后阻断
```

#### 当前运行入口和策略

公开交互入口是
[`scripts/agent/run_text2ifc_chat.py`](../../scripts/agent/run_text2ifc_chat.py)，随后进入
[`repl_chat.py`](../../src/text2ifc_agent/repl_chat.py) 和
[`run_ready_session_to_ifc`](../../src/text2ifc_agent/interactive_cli_flow.py)。会话、
消息、Provider 调用和产物引用由 SQLite `SessionStore` 持久化；Design Brief 未达到
`ready` 时不得进入 IFC generation。

当前实现保留两种明确策略：

| 策略 | 当前行为 | 适用理解 |
|---|---|---|
| `legacy_full` | CLI 默认；Generator 一次输出完整 Formal BIM JSON 2.0 或 Draft | 简单请求或既有兼容路径 |
| `staged` | 需传 `--generation-strategy staged`；先建确定性 Skeleton，再逐包生成 | 复杂、多楼层、需要清楚 ownership 的请求 |

`staged` 不是当前自动默认，也不存在按建筑复杂度自动切换。接管者不得只根据架构
图假设实际运行已经走分包生成；应检查命令、`generation-strategy.json` 和对应
run 的 `generator/`、`generator-staged/` 证据。

#### 为什么先有 Design Brief 和 Expected Facts

Design Brief 保存用户已经表达的事实、缺失项、歧义和问题来源；它只允许进入
Ready 或 Draft，不直接创建 BIM 实体。Ready Brief 随后由确定性代码投影为
Expected Facts。Expected Facts 不是第二套 BIM 模型，而是：

- Gate 用来核对用户需求是否被覆盖的验收投影；
- Generator 必须遵守的稳定实体 ID 合同；
- staged 路径划分 Skeleton、楼层本地包和跨楼层包的依据。

缺少阻断事实时，Package Manifest 必须保持 `draft_required`，不能让 Generator
猜测楼层、宿主、尺寸或跨层关系。

#### 两种 BIM JSON 生成方式

`legacy_full` 由 Generator Agent 在一次调用中生成完整文档。输出会被严格区分为
`bim-json/2.0` Formal、`bim-json-draft/1.0` Draft 或非法输出；只有结构、语义和
严格 Provider 输出合同都通过的 Formal 文档才是 Candidate。

`staged` 先确定性创建 `IfcProject`、`IfcSite`、`IfcBuilding` 和全部
`IfcBuildingStorey` 的 Skeleton，再根据 Expected Facts 生成：

1. 每层自己的空间、墙、门、窗、洞口和 containment 包；
2. 楼梯、层间楼板、屋面等跨楼层包；
3. 每包绑定 owned IDs、允许引用和当前 revision 的 ChangeSet。

每个 package 最多尝试三次，并在合入 workspace 前检查 ChangeSet 合同、包 ownership、
引用、几何表示、完整 BIM JSON Schema，以及已经接受的冻结构件是否发生漂移。中间
workspace 只是 `partial_not_formal`，不能提前编译或当作最终模型；所有包通过后才会
产生一个 Formal Candidate。

#### Candidate Gate、Audit 与返工

Formal Candidate 先做 fact-level Semantic Coverage，再由确定性 Gate 编译 IFC、用
IfcOpenShell 重开，并检查 Schema、关系、楼层归属、void/fill、数量和几何。Audit
Agent 只判断结果是否忠实表达用户意图；它不能修改 BIM JSON，也不能覆盖确定性
失败。

失败会规范化为带 owner、evidence 和 route 的 Issue。允许返工时，Change Scope
先限定实体、依赖和 JSON 路径，再让 Provider 生成绑定 base revision、candidate
hash、Expected Facts hash 和来源 Issue 的 ChangeSet；Applicator 在副本上原子应用，
并验证范围外构件未漂移。随后重新执行 coverage、Gate、Audit 和 Final Acceptance。

这里的 `run_repair_stage` 修的是“本轮生成的 BIM JSON Candidate/Draft”，不是
2.2 节的“对已有 damaged IFC 做 repair”。两类 repair 不得共用状态或把证据互相
替代。

Candidate Gate 为检查目的可能已经在 run 目录写出 `output.ifc`。只有最终 session
状态为 `compiled`，且 Final Acceptance 确认此前 Audit 为 non-blocking accept、
strict output contract 有效，并重跑 Candidate Gates 与 secret scan 后仍为 valid，
这个 IFC 才能称为 accepted；存在文件不等于已经放行。

#### 关键代码和合同入口

| 职责 | 入口 |
|---|---|
| 人机 REPL 与会话入口 | [`scripts/agent/run_text2ifc_chat.py`](../../scripts/agent/run_text2ifc_chat.py)、[`repl_chat.py`](../../src/text2ifc_agent/repl_chat.py) |
| 总编排与持久化 | [`interactive_cli_flow.py`](../../src/text2ifc_agent/interactive_cli_flow.py)、[`session_store.py`](../../src/text2ifc_agent/session_store.py) |
| Design Brief 与澄清 | [`clarification.py`](../../src/text2ifc_agent/clarification.py)、[`design_brief.py`](../../src/text2ifc_agent/design_brief.py)、[`schemas/agent/design-brief/2.0/`](../../schemas/agent/design-brief/2.0/) |
| Expected Facts 与分包 | [`expected_facts.py`](../../src/text2ifc_agent/expected_facts.py)、[`generation_packages.py`](../../src/text2ifc_agent/generation_packages.py) |
| 完整文档与 staged generation | [`generator.py`](../../src/text2ifc_agent/generator.py)、[`staged_generation.py`](../../src/text2ifc_agent/staged_generation.py)、[`changeset_stage.py`](../../src/text2ifc_agent/changeset_stage.py) |
| Package、coverage 和 revision Gates | [`package_gates.py`](../../src/text2ifc_agent/package_gates.py)、[`semantic_coverage.py`](../../src/text2ifc_agent/semantic_coverage.py)、[`dynamic_gates.py`](../../src/text2ifc_agent/dynamic_gates.py)、[`revision_gates.py`](../../src/text2ifc_agent/revision_gates.py) |
| Issue 路由与局部返工 | [`route_decision.py`](../../src/text2ifc_agent/route_decision.py)、[`scoped_loop.py`](../../src/text2ifc_agent/scoped_loop.py)、[`changeset_apply.py`](../../src/text2ifc_agent/changeset_apply.py) |
| Provider stages、Audit 与最终验收 | [`live_pipeline.py`](../../src/text2ifc_agent/live_pipeline.py)、[`audit.py`](../../src/text2ifc_agent/audit.py)、[`run_report.py`](../../src/text2ifc_agent/run_report.py) |
| BIM JSON Schema 与确定性合同实现 | [`schemas/bim-json/2.0/`](../../schemas/bim-json/2.0/)、[`schemas/bim-json/draft/1.0/`](../../schemas/bim-json/draft/1.0/)、[`src/text2ifc_contract/`](../../src/text2ifc_contract/) |
| IFC2X3 编译与重开 | [`src/text2ifc_compiler/`](../../src/text2ifc_compiler/)、[`src/text2ifc_quality/`](../../src/text2ifc_quality/) |
| Prompt 与版本注册 | [`prompts/agent/`](../../prompts/agent/)、[`prompts/agent/registry.json`](../../prompts/agent/registry.json) |

进一步阅读：

- [`text2IFC Generation 工作流与数据流（截至 Phase 6.5）`](../architecture/current-workflow-and-data-flow.md)：完整对象和失败路由；
- [`主工作流代码审计快照（2026-07-16）`](../architecture/main-workflow-code-audit-2026-07-16.md)：历史基线的代码核对，不能替代当前代码或 `STATE.md`；
- [`BIM JSON 2.0 Contract`](../reference/bim-json-2.0.md)：正式中间表示。

该链路中，模型不能直接编写 IFC STEP。BIM JSON、Gate、Compiler 和 Final
Acceptance 的职责不能被 Prompt 或 Audit 自我报告替代。

### 2.2 IFC repair 链路

```text
public request + damaged IFC
  -> source fingerprint / IFC index
  -> Stage 1 RepairIntent
  -> target/type resolution 或 clarification
  -> property retrieval / Stage 1.5 / admissibility
  -> Stage 2 ChangeSet Draft
  -> deterministic bind and audit
  -> atomic staging apply
  -> reopen + L0/L1/L2 + preservation
  -> publish repaired IFC 或 fail closed
```

主要入口：

- [`src/text2ifc_ifc_repair/api.py`](../../src/text2ifc_ifc_repair/api.py)：公共 start/continue/resume；
- [`src/text2ifc_ifc_repair/indexer.py`](../../src/text2ifc_ifc_repair/indexer.py)：damaged IFC 索引；
- [`src/text2ifc_ifc_repair/target_query.py`](../../src/text2ifc_ifc_repair/target_query.py)：目标解析和 offered candidate set；
- [`src/text2ifc_ifc_repair/property_resolution_coordinator.py`](../../src/text2ifc_ifc_repair/property_resolution_coordinator.py)：属性检索与 Stage 1.5；
- [`src/text2ifc_ifc_repair/property_admissibility.py`](../../src/text2ifc_ifc_repair/property_admissibility.py)：属性身份、类型、单位与 scope 门；
- [`src/text2ifc_ifc_repair/changesets.py`](../../src/text2ifc_ifc_repair/changesets.py)：Draft 到 Bound ChangeSet；
- [`src/text2ifc_ifc_repair/apply.py`](../../src/text2ifc_ifc_repair/apply.py)：原子应用和 staging；
- [`src/text2ifc_ifc_repair/evaluation.py`](../../src/text2ifc_ifc_repair/evaluation.py)：reopen、L1/L2 和 preservation；
- [`src/text2ifc_ifc_repair/operations/`](../../src/text2ifc_ifc_repair/operations/)：Window、Door、Opening、Beam、Column 等 operation；
- [`scripts/ifc_repair/`](../../scripts/ifc_repair/)：离线矩阵、live UAT、milestone 和 Proof 工具。

完整解释见
[`IFC Repair Pipeline 与 Roadmap`](../architecture/ifc-repair-pipeline-status-and-roadmap.md)。

## 3. 按任务选择必读材料

| 任务 | 额外必读内容 |
|---|---|
| 修改生成链路或 BIM JSON | 当前 Phase SPEC/PLAN/VALIDATION、BIM JSON 2.0 reference、Generation 工作流、实际 strategy 入口 |
| 修改 IFC repair 行为 | Repair Pipeline 架构、适用 Phase 合同、对应 operation 与测试 |
| 修改 Agent、Prompt 或 Schema | [`Agent 能力评测与真实 LLM 准入协议`](../validation/agent-capability-evaluation.md)，以及版本 registry |
| 运行真实 Provider | 同上；必须先完成适用 seam 和完整离线 preflight |
| 检查或发布 Proof | [`IFC Repair Proof 人类可读收纳规范`](../validation/ifc-repair-proof-format.md) 和具体集合报告 |
| 修改 Dataset 或 manifest | [`dataset/data_organization.md`](../../dataset/data_organization.md)、[`dataset/manifests/README.md`](../../dataset/manifests/README.md) 和来源 catalog |
| 发布 GitHub | [`publish-to-github.md`](publish-to-github.md) |

Phase 12/12.1 或 Plan 07 的专项维护还可阅读
[`Phase 12 Plan 07 技术 handover`](../handoffs/phase12-plan07-closeout-handover-2026-09-03.md)。
它是专项接续材料，不是整个项目当前状态的替代品。

## 4. 必须分开的状态与证据

接管者最容易把以下概念混在一起：

| 概念 | 回答的问题 |
|---|---|
| Phase status | 计划阶段是否按其冻结合同闭合 |
| Collection status | 某个 Proof 集合是 accepted、pending review 还是 historical |
| Run status | 某一次运行是 succeeded、clarification、unsupported 还是 failed |
| Human view | 人工查看 request、IFC、报告和结论的入口 |
| Machine authority | Provider attempts、runtime、ChangeSet、terminal 和独立复算的完整权威 |

一个 Phase 可以由某份 accepted Proof 闭合，同时另一个展示集合仍是
`pending_human_review`。一次 genuine Provider 运行成功也不自动等于能力提升；
离线、fake、replay、live、accepted 和 capability evidence 必须按实际等级报告。

IFC repair Proof 的人读入口通常直接展示：

```text
REPORT.md
request.txt
01-original.ifc     # 仅角色合法时
02-damaged.ifc
03-repaired.ifc     # 成功案
NO-REPAIR.md        # 正确无输出案，与 03-repaired.ifc 互斥
evidence/README.md  # 回链机器权威
```

`original.ifc`、private Gold、mutation/deletion truth 不得进入 Provider 输入。没有
运行前冻结的 case-specific private truth 时，IFCCompare 应明确为 N/A，不能事后
挑选文件补造 Ground Truth。

## 5. 修改前的最小调查

开始编码前应能回答：

1. 用户要求的是诊断、修改、验证、报告，还是 live run？
2. 哪个 SPEC/PLAN/VALIDATION 是当前权威？
3. 失败发生在哪个阶段，违反了什么 invariant？
4. 哪些文件属于本任务，哪些是已有用户修改？
5. 最小可复现测试是什么？
6. 最终允许声称的是 bug fixed、offline pass、live viability，还是 accepted Proof？

搜索优先使用 `rg` 和 `rg --files`，并从相关包、测试或文档开始。只有现有证据
不足时才扩大范围。

## 6. 验证强度如何选择

验证应匹配本次变更可能引入的真实失败：

| 变化 | 起步验证 |
|---|---|
| README、报告或链接 | 路径、链接、声明和格式检查 |
| 新增人读 Proof 视图 | 必需文件、角色、authority link、IFC reopen、repair/no-output 互斥 |
| 普通行为修复 | 先写聚焦失败测试，再运行相关回归 |
| Agent/Prompt/Schema 行为 | failure family、stage seam、完整离线链路和适用协议 |
| 新 genuine Provider run | 所有适用 preflight 通过后才允许 live；保留每次真实 attempt |
| accepted collection 或 evidence semantics | 对应 Proof validator；只有合同要求时运行 curator |

不要用 curator 代替定位，也不要因为只改导航就普遍重跑 curator。反过来，
source mutation、unoffered identity、inadmissible property、missing repaired IFC、
no-output 案出现 repaired IFC、broken authority link 或适用 Proof gate 失败仍必须
fail closed。

## 7. Agent 与确定性代码的边界

Agent 可以理解请求、提出澄清、在有界候选中给出语义建议，但不能：

- 直接生成或修改 IFC STEP；
- 越过当前 offered candidate set 绑定目标；
- 通过别名表、案例文本或错误输出兼容映射绕过 admissibility；
- 覆盖确定性 Gate 的失败；
- 把 private Gold、pristine IFC 或 mutation truth 放入 Provider Prompt；
- 把一次成功 live run 描述为系统级能力提升。

确定性代码负责 identity binding、scope、transaction、IFC apply、reopen、L0/L1/L2、
preservation 和 publish gate。涉及真实 LLM 前，完整要求见
[`agent-capability-evaluation.md`](../validation/agent-capability-evaluation.md)。

## 8. 常用验证入口

优先使用仓库 `.venv`，Python 版本须满足
[`pyproject.toml`](../../pyproject.toml) 的要求。示例命令仅表示入口；实际范围仍由
适用 Phase 合同决定。

```powershell
# 聚焦测试
.venv\Scripts\python -m pytest <relevant-test> -q

# Python 静态编译检查
.venv\Scripts\python -m compileall <changed-python-path>

# Plan 07 人读视图
.venv\Scripts\python scripts\ifc_repair\install_plan07_human_proof.py --validate-only

# R1 人读布局
.venv\Scripts\python scripts\ifc_repair\validate_human_proof_layout.py `
  --root dataset\processed\proof\repair-milestone-r1 --json

# Git 格式边界
git diff --check
```

Windows 下 pytest 临时目录权限异常时，使用仓库内明确的 `--basetemp`。不要将
跳过、超时、替代验证或较窄的检查描述为完整通过。

## 9. Dataset、run 与 Proof 的清理边界

- `dataset/processed/ifc-repair-runs/` 保存原始运行、Provider attempts 和终端材料；
- `dataset/processed/proof/` 保存冻结 Proof、人读视图或机器权威；
- pytest cache、离线 preflight 临时目录和已确认完全重复的未跟踪副本可以清理；
- genuine Provider 的成功或失败 attempts、accepted authority、repaired IFC 和独立
  evaluation 不得因为“已经修好”而直接删除。

删除前先解析准确路径并确认它位于预期仓库子树；再用 `git ls-files` 判断是否已被
跟踪。不要对 dataset 根目录、仓库根目录或未解析变量执行递归删除。

## 10. 完成任务时如何交接

最终报告至少说明：

1. 结论和实际证据等级；
2. 根因或实现选择；
3. 修改过的 production、test、schema、prompt、docs 或 dataset 文件；
4. 精确运行的验证及结果，包括任何 skip、timeout 或未运行项；
5. live run ID、Provider calls 和关键产物路径（如果适用）；
6. Git commit、push、PR 或未提交状态；
7. 未解决问题、数据边界和需要用户决策的事项；
8. 保留下来的无关工作树修改。

不要只写“测试通过”或“已经完成”。让下一位接管者可以从报告中的路径和命令继续
验证，而不必重新猜测本轮做了什么。

## 11. 开始工作前检查表

- [ ] 已确认 Git root、branch 和工作树状态；
- [ ] 已阅读 `AGENTS.md`、`docs/README.md`、`STATE.md` 和 `ROADMAP.md`；
- [ ] 已定位适用 SPEC、PLAN、VALIDATION；
- [ ] 已区分当前状态与历史报告；
- [ ] 已识别 production input 与 private evaluator-only 数据边界；
- [ ] 已确定最小复现和最小必要验证；
- [ ] 已说明可支持的完成声明；
- [ ] 已避免覆盖或吸收无关用户修改。
