# Text2IFC Workflow Language Policy and Feedback Routing Design

> 文档类型：架构专题设计；配套实施指令见同目录 `implementation-prompt.md`。

## 1. 文档目的

本文档用于记录 Text2IFC 项目下一阶段的 workflow 设计调整。

当前项目已经具备从自然语言建筑需求到 BIM JSON，再到 IFC2X3 文件的基础链路。单层建筑、简单房间、双房间、基础追问、BIM JSON schema validation、IFC compiler、deterministic gates、Audit Agent、report trace 等模块已经形成初步系统。

但是当项目进入复杂两层建筑、多空间、多构件、多楼层关系之后，当前 workflow 暴露出两个核心问题：

1. 当前流程仍然偏线性，能够判断成功或失败，但不能稳定根据失败结果回流到正确阶段；
2. 双层建筑的推进方式容易变成根据某一次失败 feedback 继续 TDD 补洞，而不是形成通用反馈归因与路由机制。

因此，下一阶段的重点不是继续盲目增强 prompt，也不是马上引入 RAG、fine-tuning 或大规模重构，而是建立一个清晰、可测试、可追踪的 feedback routing layer。

目标是把项目从：

```text
Generate -> Validate -> Gate -> Audit -> Accepted / Blocked
```

升级为：

```text
Generate -> Validate -> Gate -> Audit -> Normalize Issues -> Route Decision -> Feedback Target
```

---

## 2. 当前阶段判断

### 2.1 已经成立的部分

当前项目中以下能力可以视为阶段性成立：

- 单层建筑生成；
- 简单房间生成；
- 双房间基础 demo；
- 中文自然语言输入；
- 信息缺失时的追问；
- BIM JSON schema validation；
- BIM JSON 到 IFC2X3 的编译；
- IFC reopen 检查；
- 基础 deterministic gates；
- Audit Agent；
- report / trace 输出。

这些能力说明项目已经不只是一个概念 demo，而是具备基础 Text-to-BIM-to-IFC 链路。

### 2.2 尚未成立的部分

当前项目尚未稳定成立的是：

- 复杂两层建筑 accepted IFC；
- 多楼层空间、楼板、屋面、楼梯、门窗、空间关系的整体闭环；
- Gate / Audit feedback 自动或半自动回流；
- 对失败原因进行结构化归因；
- 根据失败归因决定回到 user、Design Brief、Generator、Repair、Schema、Compiler 或 Gate。

因此，当前最关键的问题不是“继续补一个双层建筑 case”，而是建立可以支撑复杂建筑推进的反馈闭环。

---

## 3. 语言策略

### 3.1 总原则

Text2IFC 项目采用：

```text
Engineering protocol in English.
Human-readable research documents in Chinese.
```

也就是说：

- 系统交互内容使用英文；
- Agent prompt 使用英文；
- 结构化数据字段使用英文；
- enum、route、issue type 使用英文；
- 代码、测试、日志、文件名尽量使用英文；
- 研究文档、阶段总结、人工阅读报告可以使用中文。

中文自然语言输入仍然需要被支持，因为 Text2IFC 的目标之一就是处理中文或自然语言建筑需求。但中文输入不应导致系统内部出现中文字段、中文 enum 或中文 route 名称。

### 3.2 推荐语言分层

```text
Layer 1: Raw User Input
  - Chinese or English are both allowed.
  - The original user request must be preserved as-is.

Layer 2: System Interaction
  - Use English by default.
  - CLI prompts, status messages, and route messages should use English.
  - Chinese UI can be added later as localization, but not mixed into core workflow logic.

Layer 3: Agent Prompts
  - System prompts, developer prompts, role prompts, and tool instructions should use English.
  - Prompts should explicitly instruct the model to preserve Chinese source facts when parsing Chinese building requirements.

Layer 4: Structured Artifacts
  - JSON keys, enum values, route decisions, issue types, status fields, severity fields, and validation codes must use English.
  - No Chinese keys or Chinese enum values should appear in machine-readable artifacts.

Layer 5: Reports and Documents
  - Research documents, architecture notes, experiment discussion, and human-readable project reports may use Chinese.
  - Chinese documents may quote English structured fields directly.
```

### 3.3 不推荐写法

```json
{
  "问题类型": "缺少实体",
  "建议路由": "重新生成",
  "严重程度": "阻塞"
}
```

### 3.4 推荐写法

```json
{
  "issue_type": "missing_entity",
  "suggested_route": "regenerate_json",
  "severity": "blocking"
}
```

如果需要中文解释，只能作为可选说明字段出现：

```json
{
  "source": "audit",
  "severity": "blocking",
  "owner": "generator",
  "issue_type": "missing_entity",
  "expected_entity": "IfcStair",
  "suggested_route": "regenerate_json",
  "message_zh": "用户要求两层建筑之间有楼梯，但当前候选 BIM JSON 缺少楼梯实体。"
}
```

---

## 4. 当前 workflow 的核心缺口

### 4.1 线性 workflow 的问题

当前 workflow 更接近：

```text
Input
  -> Design Brief
  -> BIM JSON Generation
  -> Validation
  -> Compilation
  -> Gate
  -> Audit
  -> Accepted / Blocked
```

这种流程可以判断结果是否失败，但不能稳定回答：

- 失败原因属于哪一层？
- 下一步应该回到哪里？
- 能否自动修复？
- 是否需要追问用户？
- 是否是 Schema 当前表达不了？
- 是否是 Compiler 当前不支持？
- 是否是 Gate 规则过严或漏判？
- 是否是 Provider 输出截断或格式错误？

### 4.2 理想 workflow

下一阶段应转向：

```text
Input
  -> Design Brief
  -> BIM JSON Generation
  -> Validation / Compilation / Gate / Audit
  -> Normalize Issues
  -> Route Decision
  -> Feedback Target
```

其中 feedback target 包括：

```text
ask_user
revise_design_brief
regenerate_json
repair_json
blocked_as_unsupported
gate_issue
provider_retry
runtime_blocked
accepted
```

---

## 5. Structured Issue 设计

下一阶段应将 schema validation、semantic validation、compiler、reopen check、geometry gate、deterministic gate、audit、provider、runtime 的失败统一转换为 `Issue` 对象。

### 5.1 Issue 示例

```json
{
  "issue_id": "issue_0001",
  "source": "audit",
  "severity": "blocking",
  "owner": "generator",
  "issue_type": "missing_entity",
  "expected_fact_ref": "expected_facts.storeys[1].vertical_connections.stair",
  "actual_ref": "candidate_bim_json.elements",
  "evidence": "The user requested a two-storey building with a stair, but the candidate BIM JSON does not contain any IfcStair or stair-like element.",
  "suggested_route": "regenerate_json",
  "retryable": true,
  "message_zh": "用户要求两层建筑之间有楼梯，但当前候选 BIM JSON 缺少楼梯实体。"
}
```

### 5.2 Issue 字段说明

| Field | Type | Required | Description |
|---|---:|---:|---|
| `issue_id` | string | yes | Unique issue identifier. |
| `source` | enum | yes | Where the issue comes from. |
| `severity` | enum | yes | Issue severity. |
| `owner` | enum | yes | Which module should handle this issue. |
| `issue_type` | enum | yes | Normalized issue category. |
| `expected_fact_ref` | string/null | no | Reference to expected facts. |
| `actual_ref` | string/null | no | Reference to candidate output or trace artifact. |
| `evidence` | string | yes | Short English evidence. |
| `suggested_route` | enum | yes | Recommended next route. |
| `retryable` | boolean | yes | Whether automatic retry is allowed. |
| `message_zh` | string/null | no | Optional Chinese explanation for reports. |

### 5.3 `source` enum

```text
schema_validation
semantic_validation
compiler
reopen_check
geometry_gate
deterministic_gate
audit
provider
runtime
```

### 5.4 `severity` enum

```text
info
warning
blocking
fatal
```

### 5.5 `owner` enum

```text
user
design_brief
generator
repair
schema
compiler
gate
audit
provider
runtime
```

### 5.6 `issue_type` enum

```text
missing_required_fact
ambiguous_user_requirement
changed_original_request
invalid_json
schema_mismatch
draft_unresolved_path
unsupported_schema_capability
compiler_unsupported_feature
compile_error
reopen_error
missing_entity
missing_relationship
missing_host
missing_storey_assignment
missing_space_boundary
missing_vertical_connection
geometry_invalid
semantic_mismatch
provider_truncation
provider_format_error
gate_false_positive
runtime_error
```

### 5.7 `suggested_route` enum

```text
accepted
ask_user
revise_design_brief
regenerate_json
repair_json
blocked_as_unsupported
gate_issue
provider_retry
runtime_blocked
```

---

## 6. RouteDecision 设计

所有 Issue 应被聚合为一个 `RouteDecision` 对象。

### 6.1 RouteDecision 示例

```json
{
  "final_status": "blocked",
  "route": "regenerate_json",
  "reason": "Audit found blocking missing entities required by expected facts.",
  "blocking_issue_ids": ["issue_0001", "issue_0002"],
  "retry_allowed": true,
  "target_stage": "generator",
  "max_feedback_rounds": 2,
  "current_feedback_round": 0,
  "human_review_required": false,
  "message_zh": "Audit 发现缺少用户需求中要求的关键实体，建议回到 Generator 重新生成 BIM JSON。"
}
```

### 6.2 RouteDecision 字段说明

| Field | Type | Required | Description |
|---|---:|---:|---|
| `final_status` | enum | yes | Current final status. |
| `route` | enum | yes | Next workflow route. |
| `reason` | string | yes | English reason for the route. |
| `blocking_issue_ids` | string[] | yes | Blocking issues used to make the decision. |
| `retry_allowed` | boolean | yes | Whether another generation or repair attempt is allowed. |
| `target_stage` | enum/null | yes | Stage to return to. |
| `max_feedback_rounds` | integer | yes | Max feedback loop count. |
| `current_feedback_round` | integer | yes | Current loop count. |
| `human_review_required` | boolean | yes | Whether manual review is needed. |
| `message_zh` | string/null | no | Optional Chinese explanation for reports. |

### 6.3 `final_status` enum

```text
accepted
draft
blocked
failed
```

### 6.4 `target_stage` enum

```text
user
design_brief
generator
repair
schema
compiler
gate
provider
runtime
none
```

---

## 7. Route Decision 规则

### 7.1 总体优先级

Route decision 应按以下优先级处理：

```text
fatal runtime/provider errors
  > schema/compiler unsupported
  > missing user facts
  > invalid JSON
  > missing required entities/relationships
  > geometry/semantic blocking issues
  > warnings
  > accepted
```

### 7.2 用户事实缺失

```text
if owner == "user" and issue_type == "missing_required_fact":
    route = "ask_user"
    target_stage = "user"
```

### 7.3 Design Brief 理解错误

```text
if owner == "design_brief" and issue_type in ["semantic_mismatch", "changed_original_request"]:
    route = "revise_design_brief"
    target_stage = "design_brief"
```

### 7.4 Generator 漏实体或漏关系

```text
if owner == "generator" and issue_type in [
    "missing_entity",
    "missing_relationship",
    "missing_host",
    "missing_storey_assignment",
    "missing_space_boundary",
    "missing_vertical_connection"
]:
    route = "regenerate_json"
    target_stage = "generator"
```

### 7.5 JSON 小错误

```text
if owner == "repair" and issue_type in ["invalid_json", "schema_mismatch"]:
    route = "repair_json"
    target_stage = "repair"
```

### 7.6 Schema 表达能力不足

```text
if owner == "schema" and issue_type == "unsupported_schema_capability":
    route = "blocked_as_unsupported"
    target_stage = "schema"
```

### 7.7 Compiler 不支持

```text
if owner == "compiler" and issue_type == "compiler_unsupported_feature":
    route = "blocked_as_unsupported"
    target_stage = "compiler"
```

### 7.8 Provider 输出截断

```text
if owner == "provider" and issue_type == "provider_truncation":
    route = "provider_retry"
    target_stage = "provider"
```

### 7.9 Gate 可能误判

```text
if owner == "gate" and issue_type == "gate_false_positive":
    route = "gate_issue"
    target_stage = "gate"
```

### 7.10 Audit blocking 不能 accepted

```text
if any issue has source == "audit" and severity in ["blocking", "fatal"]:
    final_status must not be "accepted"
```

### 7.11 Gate blocking 不能 accepted

```text
if any deterministic gate has blocking or fatal failure:
    final_status must not be "accepted"
```

---

## 8. Feedback Loop 策略

### 8.1 不建议一开始做无限自动循环

当前阶段不应直接做无限 feedback loop。复杂两层建筑仍处于定位瓶颈阶段，如果直接允许 Agent 自我循环，可能出现：

- 无限重试；
- trace 膨胀；
- 错误归因混乱；
- provider 成本增加；
- prompt 越补越乱；
- case-specific hack 增多。

### 8.2 推荐做 bounded feedback loop

建议先实现最多 1-2 轮的 bounded feedback loop：

```text
max_feedback_rounds = 2
```

第一阶段即使不自动重跑，也必须输出清楚的 route decision。

推荐流程：

```text
Round 0:
  Generate initial BIM JSON

Validation:
  Run schema validation, compiler, reopen check, gates, audit

Issue normalization:
  Convert all failures into Issue objects

Route decision:
  Generate RouteDecision

Feedback:
  if route == ask_user:
      stop and ask user
  if route == revise_design_brief:
      revise design brief and continue if round < max
  if route == regenerate_json:
      regenerate BIM JSON with issues as feedback if round < max
  if route == repair_json:
      run repair agent if round < max
  if route == blocked_as_unsupported:
      stop
  if route == accepted:
      accept
```

---

## 9. TDD 使用边界

### 9.1 TDD 应该继续使用

TDD 适合用于：

```text
schema validation
issue normalization
route decision
expected facts coverage
gate checks
audit output contract
compiler capability checks
regression tests for known failures
```

### 9.2 不推荐的 TDD 方式

不应继续采用：

```text
A two-storey case fails
  -> manually inspect feedback
  -> hard-code a special rule
  -> rerun the same case
  -> add another special rule
```

这种方式容易导致 case-specific hack，无法支撑研究结论。

### 9.3 推荐的 TDD 方式

应将每次失败抽象成通用测试：

```text
missing IfcSpace should not be accepted
missing IfcDoor should not be accepted when expected facts require doors
missing IfcWindow should not be accepted when expected facts require windows
missing IfcSlab should not be accepted for multi-storey buildings
missing IfcStair should not be accepted when vertical connection is required
Draft unresolved paths should route to ask_user or blocked_as_unsupported
Gate pass + Audit blocking should not produce accepted final status
Provider truncation should block acceptance
```

---

## 10. Two-storey Benchmark 推进方式

复杂两层建筑不应只用一个自然语言输入反复测试。建议拆成三个 benchmark case。

### 10.1 Controlled Two-storey Case

信息全部明确，包括：

- 两层；
- 每层高度；
- 每层有哪些空间；
- 每个空间尺寸；
- 每个空间位置；
- 外墙、内墙；
- 门窗位置；
- 楼梯位置、宽度、踏步、连接楼层；
- 楼板；
- 屋面。

目标：验证系统在信息充分时能否生成 accepted IFC。

如果失败，问题主要可能在：

```text
generator
schema
compiler
gate
audit
```

而不是用户追问。

### 10.2 Clarification Two-storey Case

故意缺少部分关键事实，例如：

- 墙厚；
- 楼梯尺寸；
- 门窗位置；
- 空间位置；
- 楼板厚度；
- 层高。

目标：验证系统是否能正确进入 `ask_user` route。

如果系统直接生成 Formal BIM JSON 或 IFC，则说明 clarification workflow 存在问题。

### 10.3 Ambiguous Two-storey Case

输入自然、模糊，例如：

```text
Create a two-storey small house. The first floor has a living room, a kitchen, and a bathroom. The second floor has two bedrooms and a bathroom. There should be a stair, doors, windows, slabs, and a roof.
```

目标：验证系统是否能进入 Draft、ask_user 或 blocked_as_unsupported，而不是静默编造。

---

## 11. 推荐产物

下一阶段建议新增或稳定以下产物：

```text
issues.json
route-decision.json
feedback-rounds.json
case-result.json
report.md
```

### 11.1 `issues.json`

保存所有标准化问题。

### 11.2 `route-decision.json`

保存最终路由判断。

### 11.3 `feedback-rounds.json`

保存每一轮 feedback 的输入、输出、issues 和 route。

### 11.4 `case-result.json`

用于实验矩阵统计。

推荐结构：

```json
{
  "case_id": "controlled_two_storey_001",
  "input_language": "zh",
  "workflow_language": "en",
  "prompt_language": "en",
  "document_language": "zh",
  "clarification_count": 0,
  "output_type": "formal_bim_json",
  "schema_pass": true,
  "compiler_pass": true,
  "reopen_pass": true,
  "gate_pass": false,
  "audit_pass": false,
  "final_status": "blocked",
  "route": "regenerate_json",
  "failure_owner": "generator",
  "blocking_issue_count": 2,
  "evidence_paths": {
    "issues": "issues.json",
    "route_decision": "route-decision.json",
    "report": "report.md"
  }
}
```

---

## 12. Report 要求

`report.md` 可以使用中文书写，但结构化字段名和 route 名称应保持英文。

报告至少应包含：

- Original user input；
- Input language；
- Workflow language；
- Prompt language；
- Design Brief；
- Candidate BIM JSON or Draft summary；
- Validation result；
- Compiler result；
- Gate result；
- Audit result；
- Normalized issues；
- Route decision；
- Feedback rounds；
- Final status；
- Evidence paths。

报告的目标是让人工审阅者不用打开大量 JSON 文件，也能判断：

1. 用户原本想要什么；
2. 系统生成了什么；
3. 为什么 accepted / draft / blocked / failed；
4. 下一步应该回到哪里。

---

## 13. 建议实施顺序

建议按以下顺序推进：

1. 统一语言策略：prompts、system interaction、JSON keys、enums、routes、tests 使用英文；
2. 定义 Issue schema；
3. 定义 RouteDecision schema；
4. 将 schema/compiler/gate/audit/provider failures 转换为 Issue；
5. 生成 `issues.json`；
6. 生成 `route-decision.json`；
7. 更新 `report.md`，展示 issues、route decision 和 feedback rounds；
8. 用已有 two-storey 失败记录补 regression tests；
9. 准备 controlled two-storey benchmark；
10. 再准备 clarification two-storey benchmark；
11. 最后准备 ambiguous two-storey benchmark；
12. 暂时不引入 RAG、fine-tuning 或 deployment 变更。

---

## 14. 成功标准

这一阶段完成后，应满足：

1. 系统 prompt 和 workflow message 使用英文；
2. 结构化 artifact 使用英文 key 和 enum；
3. 中文不作为机器可读控制字段；
4. validation/gate/audit/compiler/provider failures 能被标准化为 Issue；
5. Issue 能被聚合为 RouteDecision；
6. Audit blocking findings 不能被 accepted 覆盖；
7. Gate blocking findings 不能被 accepted 覆盖；
8. Draft unresolved paths 不能被静默 accepted；
9. two-storey 的失败被抽象成通用 regression tests；
10. `report.md` 能清楚解释 final status 和 next route；
11. 项目从线性 workflow 走向 feedback-capable workflow。

---

## 15. 最终结论

当前项目不应该继续只做线性生成，也不应该继续只靠手工 TDD 修某个双层案例。

下一阶段的关键目标应该是：

```text
Build a language-consistent, issue-driven, route-based feedback workflow.
```

也就是：

```text
Generate
  -> Validate
  -> Gate
  -> Audit
  -> Normalize Issues
  -> Route Decision
  -> Feedback Target
```

语言策略上，应采用：

```text
English for system workflow.
English for prompts.
English for structured artifacts.
Chinese for research documents and human-readable project discussion.
```

这会让 Text2IFC 从“能跑 demo 的系统”进一步变成“能解释失败、能路由修复、能支撑实验分析的研究型 workflow”。
