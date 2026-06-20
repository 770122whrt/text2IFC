# Phase 6 验收与追踪报告

**日期:** 2026-06-20  
**分支:** `multiagent-design`  
**工作树:** `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`  
**当前状态:** Phase 6 已完成规划文档，尚未执行 Wave 0 代码实现。

## 一页结论

Phase 6 的最终目标已经明确：把当前 text2IFC 从“可以跑通 demo”推进到
“可追踪、可审核、可修复、可部署”的多 Agent 系统。

最终验收效果不是只看模型有没有返回 JSON，而是看完整链路是否成立：

```text
中文自然语言
  -> Design Brief Agent 提取意图
  -> BIM JSON Generator 生成 BIM JSON 2.0 或 Draft
  -> Repair Mode 根据验证失败修复或转 Draft
  -> Deterministic Gates 做硬检查
  -> Audit Agent 做语义审核
  -> 编译生成 IFC2X3
  -> 输出 trace bundle、metrics、report、output.ifc
```

Phase 6 完成时，最小最终验收产物是：

`dataset/processed/agent-demo/phase6-multiagent/output.ifc`

同时必须生成完整追踪包，包括输入、prompt、模型原始输出、解析后 JSON、验证反馈、
修复记录、审核报告、指标和 Markdown 报告。没有这些中间证据，即使 IFC 能打开，
也不能算 Phase 6 完成。

## 这份文档解决什么问题

之前 Phase 6 的内容分散在 `06-SPEC.md`、`06-AI-SPEC.md`、
`06-VALIDATION.md`、多个 `06-*-PLAN.md` 和架构说明里。这个文档把它们收束成
一个阅读入口，回答四个问题：

1. Phase 6 到底要做什么？
2. 每个 Agent 为什么存在？
3. 最终验收标准是什么？
4. 每一步的输入和输出应该长什么样？

本报告是规划和验收合同，不声称 Phase 6 代码已经实现。实际实现仍需按 Wave 0
到 Wave 6 执行。

## 系统边界

Phase 6 继续坚持项目核心边界：

- 模型不直接输出 IFC。
- 模型不输出 STEP 文本。
- 模型不输出 `IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory`、
  STEP ID 或 compiler-only 对象。
- BIM JSON Schema 仍然是 BIM JSON 的唯一结构真相。
- IFC 文件只能由 deterministic compiler 编译生成。
- 缺失事实必须进入 Draft 或追问，不能静默补默认值。

这条边界来自 Phase 2.5、Phase 3、Phase 4 和 Phase 5 的共同结论。

## Phase 6 最终验收标准

### 最终产物验收

Phase 6 完成时，必须存在并通过检查：

| 产物 | 路径 | 验收方式 |
|---|---|---|
| 最终 IFC | `dataset/processed/agent-demo/phase6-multiagent/output.ifc` | IfcOpenShell 可重新打开，且通过 generated IFC quality gate |
| 输入文本 | `dataset/processed/agent-demo/phase6-multiagent/input.txt` | 保存原始用户输入 |
| Design Brief | `design-brief.json` | 通过 Design Brief schema 验证 |
| Prompt 元数据 | `prompt-metadata.json` | 包含 template ID、hash、role、mode |
| 渲染后的 prompt | `prompt-rendered.md` | 能复现实际模型输入 |
| 原始模型输出 | `raw-response.txt` | 保存 provider 原始响应，不能包含 secret |
| 候选 BIM JSON 或 Draft | `candidate.json` 或 `draft.json` | Formal 走 BIM JSON 验证；不完整则保留 Draft |
| 验证反馈 | `validation-feedback.json` | 记录 schema/semantic validator 结果 |
| 几何反馈 | `geometry-feedback.json` | 记录 compiled IFC 几何质量检查 |
| 修复记录 | `repair-attempts.json` | 记录每次 repair 的输入问题和输出变化 |
| 审核报告 | `audit-report.json` | 记录 Audit Agent 的语义审核结果 |
| 指标 | `metrics.json` | 记录通过率、失败类别、repair 次数等 |
| 人读报告 | `report.md` | 汇总本次运行结果和失败原因 |

### 必须通过的硬门槛

| Gate | 做什么 | 失败后如何处理 |
|---|---|---|
| Prompt trace gate | 检查 prompt 是否来自 registry，是否有 template ID 和 hash | 阻止进入正式实验结论 |
| Design Brief gate | 检查意图提取是否结构化、没有伪装成 BIM JSON | 返回 Draft 或报错 |
| BIM JSON gate | `validate_v2_document` 检查 Formal BIM JSON | 不编译 IFC |
| Draft honesty gate | 检查缺失事实是否明确保留 | 不能静默默认补全 |
| Repair gate | 检查 repair 是否减少错误，是否编造事实 | 无法修复则转 Draft 并报告 |
| IFC gate | 编译、重开、几何、关系、属性、结构检查 | 阻止部署验收 |
| Audit gate | 审核用户意图与输出是否一致 | 标记 mismatch，不能覆盖硬失败 |
| Data gate | license、provenance、split、sidecar 检查 | 阻止训练/评估导出 |
| Secret gate | 扫描 token、header、私有 URL | 阻止提交和发布 |

### 计划中的最终验证命令

Phase 6 完成前应至少通过：

```powershell
python -m pytest tests/agent tests/service tests/dataset
python scripts/service/run_text2ifc_service_demo.py --check
python -m compileall src scripts -q
```

预期结果：

- Agent、service、dataset 相关测试通过。
- demo 命令写出 `output.ifc`。
- `src` 和 `scripts` 可以编译。
- artifact secret scan 没有发现 token、header 或私有 URL 值。

## Agent 设计与目的

### Design Brief Agent

结论：Design Brief Agent 负责理解用户意图，不负责生成 BIM JSON。

它的输入是用户自然语言，输出是结构化的设计简报，包括：

- 已知事实
- 缺失事实
- 模糊表达
- 用户修正
- 需要追问的问题
- provenance

为什么要做：用户输入常常不完整。直接让 BIM JSON Generator 同时理解意图、
生成结构、处理 schema、修复几何和自我审核，会让错误难定位。Design Brief
把“用户想要什么”先单独固定下来。

### BIM JSON Generator Agent

结论：BIM JSON Generator 负责把 Design Brief 转成 BIM JSON 2.0 或 Draft。

它的输入包括：

- Design Brief
- BIM JSON schema summary
- IFC2X3 capability profile
- few-shot examples
- validation feedback
- geometry feedback

它的输出只能是：

- Formal BIM JSON 2.0
- Draft update

为什么要做：BIM JSON 是 text2IFC 的模型输出合同。这样 deterministic compiler
才能在写 IFC 前检查结构、语义、几何和关系。

### Repair Mode

结论：Repair 第一版不单独拆成物理 Agent，而是 BIM JSON Generator 的 repair mode。

它的输入包括：

- 上一版 candidate
- validator 反馈
- geometry gate 反馈
- 已知用户事实
- repair attempt number

它的输出仍然只能是：

- 修复后的 BIM JSON
- Draft update

为什么要这样：repair 的本质仍然是“生成更正确的 BIM JSON”。如果太早拆成独立
Repair Agent，会产生两套 prompt、两套责任边界和更多漂移风险。等 repair 数据
足够多，再根据指标判断是否值得拆分。

### Audit Agent

结论：Audit Agent 负责语义审核，但不能覆盖 deterministic gate。

它检查：

- 原始用户输入是否被满足
- Design Brief 是否被 BIM JSON 覆盖
- BIM JSON 是否和 validator / geometry 结果一致
- IFC artifact 是否有硬失败
- 是否存在可疑假设、unsupported facts 或需要人工确认的内容

为什么要做：确定性检查能判断 schema、IFC、几何、关系是否对，但不一定能判断
“是否符合用户真正意图”。Audit Agent 用来补这层语义检查。

### Observer Loop

结论：Observer Loop 是监督和持续改进机制。

它记录：

- prompt template ID
- prompt hash
- rendered prompt
- renderer inputs
- raw output
- parsed output
- validation feedback
- geometry feedback
- repair attempts
- audit result
- metrics
- artifact paths

为什么要做：prompt 不能靠感觉改。每次 prompt 改动都要能回答：

- 原来哪里错了？
- 属于什么失败类别？
- 这次改动修复了哪个失败？
- 指标有没有变好？
- 有没有引入新的错误？

## 中间输入与输出合同

下面是 Phase 6 的合同样例。它们不是已经跑出的真实结果，而是实现时应生成的
artifact 形态。

### 1. 用户输入

文件：`input.txt`

```text
请创建一个单层两房间套间，总长 8 米、宽 4 米、高 3 米。中间在 x=4 米处有分隔墙，分隔墙中间有一扇门，东墙中间有一扇窗。
```

预期作用：这是唯一原始需求。后续 Design Brief、BIM JSON、IFC 和 Audit 都要能追溯
到这段输入。

### 2. Design Brief 输出

文件：`design-brief.json`

```json
{
  "schema_version": "text2ifc/design-brief/1.0",
  "language": "zh-CN",
  "original_request": "请创建一个单层两房间套间，总长 8 米、宽 4 米、高 3 米。中间在 x=4 米处有分隔墙，分隔墙中间有一扇门，东墙中间有一扇窗。",
  "known_facts": {
    "storey_count": 1,
    "overall_length_mm": 8000,
    "overall_width_mm": 4000,
    "height_mm": 3000,
    "spaces": [
      {"id": "space-west", "name": "West Room"},
      {"id": "space-east", "name": "East Room"}
    ],
    "partition_wall": {"x_mm": 4000},
    "openings": [
      {"kind": "door", "host": "partition_wall", "position": "center"},
      {"kind": "window", "host": "east_wall", "position": "center"}
    ]
  },
  "missing_facts": [],
  "ambiguities": [],
  "clarification_questions": [],
  "provenance": {"source": "user_request"}
}
```

预期作用：Design Brief 固定用户意图，但不直接生成 `entities` 和 `relationships`。

### 3. Prompt 渲染输入

文件：`prompt-render-input.json`

```json
{
  "template_id": "bim-json-generator.v1",
  "role": "bim_json_generator",
  "mode": "generate",
  "inputs": {
    "user_request_path": "input.txt",
    "design_brief_path": "design-brief.json",
    "schema_summary_path": "schemas/bim-json/2.0/schema.json",
    "capability_profile_path": "docs/reference/ifc2x3-generation-profile.md",
    "few_shots": ["simple-room", "two-room-suite"],
    "validation_feedback": [],
    "geometry_feedback": []
  }
}
```

预期作用：记录 prompt 是如何被构造的。后续如果输出异常，可以复现模型输入。

### 4. Prompt 元数据

文件：`prompt-metadata.json`

```json
{
  "template_id": "bim-json-generator.v1",
  "template_hash": "sha256:<computed>",
  "role": "bim_json_generator",
  "mode": "generate",
  "rendered_prompt_path": "prompt-rendered.md",
  "forbidden_outputs": [
    "raw IFC",
    "STEP text",
    "IfcCartesianPoint",
    "IfcDirection",
    "IfcOwnerHistory",
    "STEP IDs"
  ]
}
```

预期作用：如果没有 `template_id` 和 `template_hash`，这次模型调用不能进入正式
实验结论。

### 5. BIM JSON 候选输出

文件：`candidate.json`

```json
{
  "schema_version": "bim-json/2.0",
  "ifc_schema": "IFC2X3",
  "units": {"length": "MILLIMETRE"},
  "entities": [
    {"id": "project-1", "ifc_class": "IfcProject", "attributes": {"Name": "Generated Project"}},
    {"id": "storey-1", "ifc_class": "IfcBuildingStorey", "attributes": {"Name": "Level 1"}},
    {"id": "space-west", "ifc_class": "IfcSpace", "attributes": {"Name": "West Room"}},
    {"id": "space-east", "ifc_class": "IfcSpace", "attributes": {"Name": "East Room"}},
    {"id": "wall-partition", "ifc_class": "IfcWall", "attributes": {"Name": "Partition Wall"}}
  ],
  "relationships": [
    {
      "id": "void-door-1",
      "ifc_class": "IfcRelVoidsElement",
      "attributes": {
        "RelatingBuildingElement": "wall-partition",
        "RelatedOpeningElement": "opening-door-1"
      }
    }
  ],
  "provenance": {"source": "phase6-multiagent-demo"}
}
```

预期作用：这里只展示形态，不是完整可编译样例。真实 Phase 6 输出必须包含完整
placement、representation、space、wall、door、window、void/fill 等必要字段，并通过
`validate_v2_document`。

### 6. 验证反馈

文件：`validation-feedback.json`

```json
{
  "formal_valid": false,
  "issues": [
    {
      "code": "REQUIRED_ATTRIBUTE_MISSING",
      "path": "entities[4].attributes.ObjectPlacement",
      "message": "IfcWall requires ObjectPlacement for generation."
    }
  ]
}
```

预期作用：如果 Formal BIM JSON 未通过验证，不能编译 IFC。该反馈进入 repair mode。

### 7. 修复记录

文件：`repair-attempts.json`

```json
[
  {
    "attempt_number": 1,
    "mode": "repair",
    "input_issue_codes": ["REQUIRED_ATTRIBUTE_MISSING"],
    "output_issue_codes": [],
    "fixed_issue_codes": ["REQUIRED_ATTRIBUTE_MISSING"],
    "remaining_issue_codes": [],
    "result": "formal_candidate"
  }
]
```

预期作用：repair 不能只说“修好了”，必须说明修复了什么、还剩什么、是否有编造风险。

### 8. 几何反馈

文件：`geometry-feedback.json`

```json
{
  "success": true,
  "issues": [],
  "metrics": {
    "room_enclosure_pass": true,
    "wall_orientation_pass": true,
    "opening_host_fit_pass": true,
    "compile_reopen_success": true
  }
}
```

预期作用：IFC 能打开不够，必须证明空间关系、墙方向、洞口宿主关系等也正确。

### 9. Audit Agent 输出

文件：`audit-report.json`

```json
{
  "deterministic_status": "passed",
  "blocking": false,
  "intent_coverage": {
    "storey_count": "covered",
    "two_rooms": "covered",
    "partition_wall": "covered",
    "east_wall_window": "covered"
  },
  "mismatches": [],
  "unsupported_facts": [],
  "recommendation": "accept"
}
```

预期作用：Audit 只负责审核和解释。若 deterministic status 是 `failed`，Audit 不允许
把结果改成通过。

### 10. 指标输出

文件：`metrics.json`

```json
{
  "parse_valid": true,
  "design_brief_valid": true,
  "bim_json_valid": true,
  "compile_reopen_success": true,
  "geometry_pass": true,
  "audit_pass": true,
  "repair_attempt_count": 1,
  "failure_class": null
}
```

预期作用：后续 prompt-only、repair-mode、RAG、fine-tune 的比较必须基于这些指标。

## 什么时候必须停止并向用户汇报

下面这些情况不能自动吞掉，也不能假装成功。

| 情况 | 为什么要汇报 | 正确处理 |
|---|---|---|
| API token 过期或 provider 无法连通 | 可能需要用户更新凭据或确认服务状态 | 停止 live provider 路径，保留 fake/file 测试，向用户报告 |
| provider 返回 raw IFC、STEP 或低层 IFC helper | 违反系统边界 | 拒绝输出，记录 provider boundary failure |
| prompt 没有 template ID 或 hash | 无法复现和审计 | 阻止进入正式实验结论 |
| demo 使用 hard-coded JSON 却标成 live model 输出 | 属于证据污染 | 立即制止，报告为 artifact provenance 问题 |
| repair 静默补充用户没给的数据 | 会制造虚假 BIM | 停止 repair，转 Draft 或追问 |
| Audit Agent 想覆盖 deterministic gate 失败 | 会把错误 IFC 包装成成功 | 强制保留失败状态 |
| 训练数据 license 不明确 | 可能违法或污染训练集 | 不纳入训练，标记待确认 |
| train/validation/test scene family 泄漏 | 评估结果失真 | 阻止导出和训练 |
| artifact 出现 token、header、私有 URL 值 | 安全风险 | 阻止提交和推送 |

## Phase 6 Wave 内容总表

| Wave | Plan | 做什么 | 为什么做 | 主要输出 |
|---:|---|---|---|---|
| 0 | `06-00` | Prompt registry 和 multi-agent design contract | 没有 prompt 追踪就无法可信迭代 | registry、renderer、设计文档 |
| 1 | `06-01` | Design Brief Agent | 把理解用户意图和生成 BIM JSON 分开 | `design-brief.json`、schema、测试 |
| 2 | `06-02` | BIM JSON Generator 和 repair mode | 让生成和修复都在同一 BIM JSON 合同内 | generator、repair、repair trace |
| 3 | `06-03` | Audit Agent | 检查语义覆盖，但不覆盖硬失败 | `audit-report.json`、审核测试 |
| 4 | `06-04` | Experiment harness | 用指标比较 prompt/repair/audit | experiment records、metrics、report |
| 5 | `06-05` | 数据扩展和模型决策 | 微调前先确认数据和指标是否支持 | training manifest、model decision |
| 6 | `06-06` | 部署服务和最终 IFC demo | 形成可重复运行的 text2IFC 服务入口 | `output.ifc`、trace bundle、service demo |

## 文件地图

Phase 6 的详细规划仍保留在 GSD 结构中。本报告是阅读入口。

| 文件 | 用途 |
|---|---|
| `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-SPEC.md` | Phase 6 范围、边界、验收标准 |
| `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-AI-SPEC.md` | 多 Agent / prompt / repair / audit 设计合同 |
| `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-VALIDATION.md` | 验证策略和最终 demo 要求 |
| `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-PLAN-OUTLINE.md` | Wave 顺序和计划索引 |
| `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-00-PLAN.md` 到 `06-06-PLAN.md` | 具体执行计划 |
| `docs/architecture/phase-6-multiagent-design.md` | 多 Agent 架构说明 |
| `docs/architecture/phase-6-acceptance-and-trace-report.md` | 当前这份单入口报告 |

## 已知限制与待确认项

- Provider API 可用性待实际执行时确认。若 Mimo token、base URL、model name 失效，
  必须向用户汇报。
- 最终 demo 的精确自然语言案例可以在 Wave 6 前再确认。当前规划要求它必须输出
  `dataset/processed/agent-demo/phase6-multiagent/output.ifc`。
- RAG 和 fine-tune 不是默认实施项。它们要等 Wave 4 实验指标和 Wave 5 数据审查后
  再决定。
- 当前文档中的 JSON 是合同样例，不是已经生成的真实 Phase 6 artifact。

## 判断 Phase 6 是否真的完成

可以用一句话判断：

> 给一个中文建筑需求，系统能保存完整输入，结构化理解意图，生成或追问 BIM JSON，
> 通过验证后编译出 IFC，审核其是否符合用户意图，并留下足够证据让我们复现、
> 修复、比较和部署。

如果只有 `output.ifc`，没有 trace bundle，不算完成。  
如果有 trace bundle，但 IFC 没通过 deterministic gates，不算完成。  
如果 deterministic gates 通过，但 Audit 发现用户意图明显不匹配，不应该进入部署验收。  
如果 prompt 或数据来源无法追踪，不应该进入模型结论。

---
*本报告整合 Phase 6 规划事实，用于后续执行、验收和用户审阅。*
