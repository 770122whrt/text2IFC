# Codex 跨对话上下文维护规则

> 适用目录：`docs/context-handoff/`  
> 目标：把 Codex 一次性侧边聊天中的高价值信息沉淀为可复用、可审计的仓库上下文，供后续 Codex 对话、网页端 GPT、人工审阅者继续使用。  
> 原则：**仓库事实优先，历史可追溯，当前状态与单次问题分离，不把 Codex 的判断直接当成事实。**

---

## 1. 为什么需要这个目录

Codex 的侧边聊天可以视为一次性工作会话。一次对话结束后，不应依赖该聊天本身继续承载项目背景。

需要长期保留的内容统一写入：

```text
docs/context-handoff/
```

该目录只保存“为了跨对话继续工作而有价值”的背景，不替代：

- 项目正式 SPEC；
- `AGENTS.md`；
- `.planning/`；
- 正式技术文档；
- 测试、Schema 和生产代码；
- Git 历史。

这里的文件是 **handoff / reviewer context**，作用是帮助新的 Codex 会话或网页端 GPT 快速理解：

1. 当前项目实际处于什么状态；
2. 哪些设计与合同是权威的；
3. 最近讨论过什么；
4. 当前问题为什么产生；
5. 哪些结论已经确认，哪些仍只是推测；
6. 下一次对话应该从哪里继续。

---

## 2. 目录中的四类文件

所有文件均放在同一个目录：

```text
docs/context-handoff/
├── CONTEXT-HANDOFF-RULES.md
├── PROJECT-CONTEXT-PACK.md
├── CHAT-SUMMARY__YYYY-MM-DD__<function>__<slug>.md
└── ISSUE-CONTEXT__YYYY-MM-DD__<slug>.md
```

不要为每次对话建立新的子目录。

---

# 3. `CONTEXT-HANDOFF-RULES.md`

## 3.1 作用

本文件就是当前规则文件。

任何需要生成、读取或维护跨对话背景的 Codex 会话，都应首先阅读本文件。

它负责规定：

- 文件类型；
- 命名方式；
- 什么内容应该记录；
- 什么内容不应该记录；
- 哪些文件可以原地更新；
- 哪些文件应该作为历史记录保留；
- 如何区分仓库事实、用户决定和 Codex 推测；
- 如何给下一次 Codex / 网页端 GPT 交接。

## 3.2 更新原则

只有当“上下文管理规则本身”需要变化时才更新本文件。

不要因为：

- 新增一个 Phase；
- 某个测试失败；
- 某个实现发生变化；

就修改本规则。

---

# 4. `PROJECT-CONTEXT-PACK.md`

## 4.1 作用

这是整个目录中最重要的 **长期维护快照**。

它回答：

> “如果一个新的技术审阅者现在第一次进入仓库，他至少需要知道哪些稳定背景，才能正确理解当前系统？”

它不是完整项目文档，也不是开发日志。

重点维护当前仍然有效的：

- 系统架构；
- 关键 pipeline；
- 组件职责；
- authoritative contracts；
- 测试分层；
- release / acceptance 规则；
- non-negotiable invariants；
- 当前 Phase / Roadmap 状态；
- 重要术语；
- 关键文件入口。

## 4.2 命名

固定：

```text
PROJECT-CONTEXT-PACK.md
```

不要每次更新生成：

```text
PROJECT-CONTEXT-PACK-v2.md
PROJECT-CONTEXT-PACK-final.md
PROJECT-CONTEXT-PACK-new.md
```

历史由 Git 保存。

## 4.3 文件顶部必须包含

```markdown
# Project Context Pack

- Last updated: YYYY-MM-DD
- Repository:
- Branch:
- Commit / HEAD:
- Maintainer: Codex-assisted
- Purpose: cross-conversation technical handoff
```

如果当前工作树未提交，可增加：

```markdown
- Worktree state: dirty
```

## 4.4 推荐结构

```markdown
# Project Context Pack

## 1. Current Scope

## 2. Current Architecture

## 3. Runtime / Data Flow

## 4. Major Components

## 5. Authoritative Contracts

## 6. Test Taxonomy

## 7. Acceptance / Release Gates

## 8. Non-Negotiable Invariants

## 9. Current Roadmap / Phase State

## 10. Important Repository Entry Points

## 11. Known Architectural Risks or Open Questions

## 12. Recent Material Changes

## 13. Reviewer Handoff
```

## 4.5 什么情况下更新

只有发生对“后续多个对话都有影响”的变化时才更新，例如：

- pipeline 架构变化；
- Stage 新增、删除或职责变化；
- authoritative contract 发生变化；
- acceptance / release gate 变化；
- Test taxonomy 发生变化；
- 关键 runtime 切换；
- Phase 状态发生实质变化；
- 某个旧架构被正式废弃。

不应因为单个测试失败就更新 Project Context Pack。

---

# 5. `CHAT-SUMMARY`

## 5.1 作用

`CHAT-SUMMARY` 是一次 Codex 对话结束后的 **历史摘要**。

它回答：

> “这次对话主要讨论或完成了什么？哪些信息以后可能需要继续使用？”

这是历史记录，不是当前系统唯一真相。

后续实现发生变化时，不要回头改写旧 Summary 让它看起来“始终正确”。

## 5.2 命名

统一使用：

```text
CHAT-SUMMARY__YYYY-MM-DD__<function>__<slug>.md
```

例如：

```text
CHAT-SUMMARY__2026-08-23__debug__stage15-bge-curator-tests.md
CHAT-SUMMARY__2026-08-24__design__repair-evaluation-contract.md
CHAT-SUMMARY__2026-08-25__review__door-repair-evidence.md
CHAT-SUMMARY__2026-08-26__planning__phase11-door-opening.md
```

### `<function>` 推荐值

优先使用有限的功能类型：

```text
debug
design
review
planning
implementation
evaluation
research
refactor
release
other
```

不要把具体模块名当作 function。

### `<slug>`

要求：

- 小写；
- 英文；
- 使用 `-` 分隔；
- 简短描述本次对话主题；
- 不写 `final`、`latest`、`new`。

---

## 5.3 每份 Summary 顶部必须包含

```markdown
# Conversation Summary

- Date: YYYY-MM-DD
- Function: debug / design / review / ...
- Topic:
- Repository:
- Branch:
- Commit / HEAD:
- Conversation purpose:
- Status: completed / partial / blocked
```

如果对话对应具体 Issue Context，可增加：

```markdown
- Related issue context: `ISSUE-CONTEXT__...md`
```

## 5.4 推荐结构

```markdown
# Conversation Summary

## 1. Why This Conversation Happened

## 2. Repository State Examined

## 3. Confirmed Repository Facts

## 4. Decisions Made

## 5. Changes Performed

## 6. Tests / Evidence

## 7. Codex Hypotheses or Interpretations

## 8. Unresolved Questions

## 9. What Should Be Carried Forward

## 10. Relevant Files / Symbols
```

---

# 6. `ISSUE-CONTEXT`

## 6.1 作用

`ISSUE-CONTEXT` 用于某一个具体复杂问题的技术取证和交接。

例如：

- Stage 1.5 BGE runtime 测试失败；
- Curator / Validator contract 疑似漂移；
- Door repair L1/L2 失败；
- 某个 production behavior 与 test expectation 不一致；
- Provider UAT 与 deterministic evaluation 不一致。

它回答：

> “在不急着修代码的情况下，一个外部 reviewer 需要看到哪些证据，才能独立判断 root cause 和正确修改方向？”

## 6.2 命名

```text
ISSUE-CONTEXT__YYYY-MM-DD__<slug>.md
```

例如：

```text
ISSUE-CONTEXT__2026-08-23__stage15-bge-curator-contract-failures.md
ISSUE-CONTEXT__2026-08-28__door-l2-topology-regression.md
```

创建日期固定不变。

如果问题持续多天，在同一文件中维护：

```markdown
- Created: 2026-08-23
- Last updated: 2026-08-25
- Status: open / investigating / resolved / superseded
```

不要每天新建一个 Issue Context。

---

## 6.3 推荐结构

```markdown
# Issue Context

## 1. Problem Statement

## 2. Current Observed Failure

## 3. Relevant Runtime / Data Flow

## 4. Authoritative Contract

## 5. Production Implementation

## 6. Current Test Expectation

## 7. Three-Way Comparison

## 8. Relevant Fixtures / Mocks / Runtime Dependencies

## 9. Git / Change History

## 10. Confirmed Facts

## 11. Current Hypotheses

## 12. Unresolved Ambiguities

## 13. Candidate Fix Directions

## 14. Final Resolution

## 15. Regression Evidence

## 16. Reviewer Handoff
```

---

# 7. 三种信息必须明确区分

这是整个规则中最重要的要求之一。

Codex 在 Summary、Project Context Pack 和 Issue Context 中都不得把以下三类信息混在一起。

## 7.1 Confirmed Repository Fact

有直接仓库证据支持，例如：

- 代码；
- Schema；
- SPEC；
- 测试；
- Git commit；
- 实际运行结果；
- 用户明确确认的设计决定。

推荐写法：

```markdown
### Confirmed

`src/.../validator.py::validate_xxx()` currently requires ...
Evidence:
- `src/.../validator.py`
- `schemas/...json`
```

## 7.2 User / Project Decision

这是已经明确做出的设计选择，但不一定由当前生产代码证明。

例如：

```markdown
### Project Decision

Production repair must remain fail-closed.
Source:
- `.planning/...`
- user decision recorded on YYYY-MM-DD
```

## 7.3 Codex Hypothesis

任何 root cause 推断、设计建议、可能的解释，都必须明确标注。

例如：

```markdown
### Hypothesis

The failing fixture is probably stale because ...
This is not yet proven.
```

禁止把：

```text
production currently behaves this way
```

直接改写为：

```text
the system is intended to behave this way
```

---

# 8. Authoritative Source 优先级

不同问题可能有不同 authority，不应机械地只看一种文件。

Codex 应先定位当前问题的 authoritative source，并明确写出来。

通常可能包括：

1. 用户明确冻结的 task specification；
2. 正式 SPEC / contract；
3. JSON Schema / typed model；
4. acceptance / evaluation contract；
5. production implementation；
6. tests；
7. planning documents；
8.历史 Summary。

`CHAT-SUMMARY` 永远不是高于生产代码或正式合同的 authority。

如果来源之间冲突：

**必须记录冲突，不得自行消解。**

---

# 9. 侧边聊天开始时怎么做

当 Codex 收到“按跨对话上下文继续工作”的要求时，应：

1. 阅读：

```text
docs/context-handoff/CONTEXT-HANDOFF-RULES.md
```

2. 阅读：

```text
docs/context-handoff/PROJECT-CONTEXT-PACK.md
```

3. 根据当前主题搜索同目录下相关：

```text
CHAT-SUMMARY__*.md
ISSUE-CONTEXT__*.md
```

4. 再读取当前问题真正的 authoritative files：

- production code；
- tests；
- Schema；
- SPEC；
- planning；
- Git history。

5. 不得只依据历史 Summary 直接做修改。

---

# 10. 侧边聊天结束时怎么做

并不是每次对话都必须产生文件。

只有具有跨对话价值时才记录。

## 10.1 应创建 `CHAT-SUMMARY` 的情况

本次对话产生了至少一种：

- 重要设计讨论；
- architecture 理解；
- root cause 调查；
- 明确技术决定；
- 重要实现；
- 测试/评估结论；
- 下一次工作需要继续使用的信息。

## 10.2 不需要创建的情况

例如：

- 很小的 typo；
- 单个变量重命名；
- 无长期价值的快速查询；
- 已经完整记录在某个 Issue Context 中且没有额外决策的小修复。

## 10.3 Project Context Pack 是否更新

结束对话时判断：

> “这次变化会不会影响未来多个不同问题的理解？”

如果不会：

不要更新。

如果会：

更新 `PROJECT-CONTEXT-PACK.md`。

## 10.4 Issue Context 是否更新

如果当前会话围绕现有 Issue：

更新原文件。

如果出现新的独立复杂问题：

创建新的：

```text
ISSUE-CONTEXT__YYYY-MM-DD__<slug>.md
```

---

# 11. 历史文件如何维护

## 11.1 CHAT-SUMMARY

创建后原则上不重写历史事实。

允许：

- 修 typo；
- 补缺失文件路径；
- 标记：

```markdown
> Superseded by: `...`
```

不允许把旧结论改成后来才知道的结论。

## 11.2 PROJECT-CONTEXT-PACK

这是 living document。

必须保持 **当前有效状态**。

旧状态由 Git 保存。

## 11.3 ISSUE-CONTEXT

问题未解决时可以持续更新。

问题解决后：

```markdown
Status: resolved
```

补充：

- final root cause；
- final fix；
- regression evidence；
- relevant commit。

之后原则上冻结。

如果未来出现“相似但不同”的问题，应新建 Issue Context，而不是重新开启旧文件。

---

# 12. 给网页端 GPT 的信息应该长什么样

网页端 GPT 不直接看到 Codex 当前工作区，因此交接信息应优先做到：

- 可以独立阅读；
- 不依赖聊天上下文；
- 关键结论有路径和 symbol；
- 包含必要错误信息；
- 能区分事实和推断；
- 不只给 Codex 自己的最终建议。

如果需要网页端 GPT 对一个具体问题进行独立判断，建议提供：

```text
1. PROJECT-CONTEXT-PACK.md
2. 对应 ISSUE-CONTEXT__*.md
3. 最近 1–3 个直接相关 CHAT-SUMMARY
4. 必要时补充具体源码 / diff / test output
```

不要一次上传整个 `docs/context-handoff/` 的所有历史 Summary。

---

# 13. `Reviewer Handoff` 统一格式

Project Context Pack 和 Issue Context 最后都应有：

```markdown
## Reviewer Handoff
```

只保留外部 reviewer 开始分析前必须知道的 10–20 个事实。

例如：

```markdown
## Reviewer Handoff

1. Production executor currently calls ...
2. Stage 1.5 authority is defined in ...
3. The failing test is ...
4. The test mocks ...
5. Real BGE-M3 is covered by ...
6. `property_authority_coverage` is defined in ...
7. Curator consumes it in ...
8. The current failure is not yet proven to be a stale fixture.
...
```

这里仍然要区分：

- confirmed；
- decision；
- hypothesis。

---

# 14. 测试失败类问题的特别规则

遇到测试失败，禁止直接：

```text
production changed
→ test failed
→ update fixture
```

必须先做：

```text
Authoritative Contract
        vs
Production Implementation
        vs
Current Test Expectation
```

然后再分类：

```text
A. stale test fixture
B. production regression
C. contract/spec drift
D. test architecture problem
E. environment/runtime dependency
F. other
```

如果无法证明：

写入 `Unresolved Ambiguities`。

不要为了让测试变绿而倒推设计。

---

# 15. Runtime / Mock / Fixture 问题的特别规则

当问题涉及：

- mock；
- monkeypatch；
- fake provider；
- fake runtime；
- fixture；
- transport；
- local model；
- HuggingFace model；
- provider endpoint；

Issue Context 必须明确写出：

```text
REAL:
- ...

MOCKED:
- ...

PATCHED:
- ...

EXTERNAL:
- ...

NOT COVERED BY THIS TEST:
- ...
```

并说明真实 dependency 由哪一层测试负责覆盖。

禁止把“真实 executor + fake runtime”称为完整 production E2E。

---

# 16. 代码定位要求

高价值技术结论尽量给：

```text
file path
+ class/function/symbol
+ test name
```

例如：

```text
src/repair/executor.py::RepairExecutor.execute
tests/.../test_live_executor.py::test_xxx
```

如果 Git history 与判断有关，再给：

```text
commit hash
+ changed files
+ behavioral effect
```

不要复制大量无关源码。

---

# 17. 不应写入这些文件的内容

禁止保存：

- API Key；
- Token；
- 密码；
- 私有 Provider URL；
- 不必要的用户个人信息；
- 大段完整日志；
- 大量 generated artifacts；
- 整个 Git diff；
- 可以从代码直接查到、但对交接没有价值的琐碎实现细节。

必要错误日志只保留最小相关片段。

---

# 18. 推荐的标准工作流

```text
Codex Side Chat Starts
        ↓
Read CONTEXT-HANDOFF-RULES.md
        ↓
Read PROJECT-CONTEXT-PACK.md
        ↓
Read relevant CHAT-SUMMARY / ISSUE-CONTEXT
        ↓
Inspect authoritative repository evidence
        ↓
Perform current task
        ↓
Decide whether cross-conversation knowledge was produced
        ↓
Update existing ISSUE-CONTEXT if needed
        ↓
Create CHAT-SUMMARY if worthwhile
        ↓
Update PROJECT-CONTEXT-PACK only for durable project-wide changes
        ↓
Future Codex / Web GPT can continue from repository context
```

---

# 19. Codex 侧边聊天的标准入口提示词

后续无需每次重新解释本规则。

可以直接对 Codex 说：

```text
Read and follow:

docs/context-handoff/CONTEXT-HANDOFF-RULES.md

Then load the current Project Context Pack and only the conversation summaries /
issue contexts relevant to this task.

After that, inspect the authoritative repository code/spec/tests for the current
problem rather than treating the handoff documents as ground truth.

Perform the requested task.

Before finishing, follow the maintenance rules in CONTEXT-HANDOFF-RULES.md:
update the existing Issue Context if applicable, create a dated/function-tagged
Chat Summary only if this conversation produced reusable cross-conversation
knowledge, and update PROJECT-CONTEXT-PACK.md only if durable project-wide
architecture/contracts changed.
```

---

# 20. 给网页端 GPT 的标准说明

当把这些文件交给网页端 GPT 时，可以说明：

```text
These files are repository handoff context generated and maintained by Codex.

Treat PROJECT-CONTEXT-PACK.md as the current high-level snapshot, not as a
replacement for authoritative specifications or source code.

Treat CHAT-SUMMARY files as historical conversation records.

Treat ISSUE-CONTEXT files as issue-specific evidence packages.

When there is a conflict, distinguish:
1. authoritative contract,
2. production behavior,
3. test expectation,
4. historical summary,
5. Codex hypothesis.

Do not assume Codex's previous conclusion was correct merely because it appears
in a handoff document.
```

---

# 21. 最小原则

最终只记住以下几点即可：

1. **侧边聊天是临时的，仓库文件才承担跨对话记忆。**
2. **Project Context Pack 记录当前长期背景。**
3. **Chat Summary 记录一次有价值的历史对话。**
4. **Issue Context 记录一个复杂问题的证据链。**
5. **所有文件放在同一个 `docs/context-handoff/` 目录。**
6. **历史 Summary 不冒充当前真相。**
7. **重要判断区分 repository fact / project decision / Codex hypothesis。**
8. **测试失败必须比较 contract / production / test，不能直接迎合当前实现改测试。**
9. **网页端 GPT 应优先拿 Project Pack + 当前 Issue Pack，而不是整包历史记录。**
10. **这些 handoff 文件帮助理解仓库，但永远不替代 authoritative code/spec/schema/test。**
