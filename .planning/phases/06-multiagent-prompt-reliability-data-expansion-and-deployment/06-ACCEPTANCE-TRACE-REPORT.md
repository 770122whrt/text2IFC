# 06 Acceptance and Trace Report

**中文名:** Phase 6 验收与追踪报告  
**日期:** 2026-06-20  
**分支:** `multiagent-design`  
**工作树:** `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`  
**状态:** Phase 6 已完成 SPEC/PLAN/VALIDATION 文档规划，尚未执行 Wave 0 代码实现。

## 1. 最终验收效果

Phase 6 完成时，系统应能把中文自然语言请求转换为可验证 BIM JSON 2.0，并在通过
确定性检查后生成真实 IFC2X3 文件。

最终验收文件：

`dataset/processed/agent-demo/phase6-multiagent/output.ifc`

但只有 IFC 文件不够。Phase 6 的核心验收是完整证据链：

```text
input.txt
  -> design-brief.json
  -> prompt-render-input.json
  -> prompt-metadata.json
  -> prompt-rendered.md
  -> raw-response.txt
  -> candidate.json 或 draft.json
  -> validation-feedback.json
  -> geometry-feedback.json
  -> repair-attempts.json
  -> audit-report.json
  -> metrics.json
  -> report.md
  -> output.ifc
```

如果只有 `output.ifc`，没有这些中间证据，不算 Phase 6 完成。

## 2. 核心链路

```text
中文自然语言
  -> Design Brief Agent
  -> BIM JSON Generator Agent
  -> Failure Routing
       -> no_repair_needed
       -> repair_attempted
       -> draft_required
       -> blocked_failure
  -> Deterministic Gates
  -> Audit Agent
  -> IFC2X3 output
```

## 3. Repair 是否必须

结论：repair 不是每次必须。

必需的是 failure routing，也就是系统必须明确记录失败后走了哪条路径：

| 路由 | 什么时候出现 | 是否编译 IFC |
|---|---|---|
| `no_repair_needed` | 首次生成已经通过验证和几何检查 | 可以继续编译 |
| `repair_attempted` | 有明确 validator/geometry 失败，且已知用户事实足够修复 | 修复后再验证 |
| `draft_required` | 失败原因是缺用户事实或语义不明确 | 不编译，追问用户 |
| `blocked_failure` | 出现边界违规、证据污染、secret、不可恢复错误 | 不编译，向用户汇报 |

因此，成功路径的 `repair_attempt_count` 应该是 `0`。repair 只有在失败且可安全修复时
才使用。

## 4. 必须停止并汇报的情况

| 情况 | 正确处理 |
|---|---|
| API token 过期、provider 失败、Mimo 无法连通 | 停止 live provider 路径，保留 fake/file 测试，向用户汇报 |
| prompt 没有 template ID 或 hash | 阻止进入正式实验结论 |
| provider 返回 raw IFC、STEP 或低层 IFC helper | 拒绝输出，记录 provider boundary failure |
| hard-coded JSON 被标成 live model 输出 | 立即制止，报告 artifact provenance 问题 |
| repair 静默补用户没给的数据 | 停止 repair，转 Draft 或追问 |
| Audit Agent 想覆盖 deterministic gate 失败 | 保留失败状态，不能通过验收 |
| 数据 license 不明确 | 不纳入训练，标记待确认 |
| train/validation/test scene family 泄漏 | 阻止导出和训练 |
| artifact 出现 token、header、私有 URL 值 | 阻止提交和发布 |

## 5. 中间输入/输出合同样例

这些是 Phase 6 的合同样例，不是已经跑出的真实 artifact。

### 5.1 `input.txt`

```text
请创建一个单层两房间套间，总长 8 米、宽 4 米、高 3 米。中间在 x=4 米处有分隔墙，分隔墙中间有一扇门，东墙中间有一扇窗。
```

### 5.2 `design-brief.json`

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

### 5.3 `prompt-metadata.json`

```json
{
  "template_id": "bim-json-generator.v1",
  "template_hash": "sha256:<computed>",
  "role": "bim_json_generator",
  "mode": "generate",
  "rendered_prompt_path": "prompt-rendered.md"
}
```

### 5.4 `validation-feedback.json`

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

### 5.5 `repair-attempts.json`

成功首轮生成时：

```json
{
  "failure_route": "no_repair_needed",
  "repair_attempts": []
}
```

需要 repair 时：

```json
{
  "failure_route": "repair_attempted",
  "repair_attempts": [
    {
      "attempt_number": 1,
      "input_issue_codes": ["REQUIRED_ATTRIBUTE_MISSING"],
      "output_issue_codes": [],
      "fixed_issue_codes": ["REQUIRED_ATTRIBUTE_MISSING"],
      "remaining_issue_codes": []
    }
  ]
}
```

缺用户事实时：

```json
{
  "failure_route": "draft_required",
  "repair_attempts": [],
  "questions": [
    "请确认两间房间是左右相邻还是前后相邻？"
  ]
}
```

### 5.6 `audit-report.json`

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

### 5.7 `metrics.json`

```json
{
  "parse_valid": true,
  "design_brief_valid": true,
  "bim_json_valid": true,
  "compile_reopen_success": true,
  "geometry_pass": true,
  "audit_pass": true,
  "failure_route": "no_repair_needed",
  "repair_attempt_count": 0,
  "failure_class": null
}
```

## 6. Phase 6 Wave 总表

| Wave | Plan | 内容 | 验收重点 |
|---:|---|---|---|
| 0 | `06-00` | Prompt registry 和 multi-agent design contract | prompt 有 ID/hash/trace |
| 1 | `06-01` | Design Brief Agent | 输入被结构化理解，不生成 BIM JSON |
| 2 | `06-02` | BIM JSON Generator 和 failure routing | 成功、repair、Draft、blocking 都可追踪 |
| 3 | `06-03` | Audit Agent | 审核语义覆盖，但不能覆盖硬失败 |
| 4 | `06-04` | Experiment harness | 用指标比较 prompt/repair/audit |
| 5 | `06-05` | 数据扩展和模型决策 | license、provenance、split 安全 |
| 6 | `06-06` | 部署服务和最终 IFC demo | 写出 `output.ifc` 和完整 trace bundle |

## 7. 相关文件

| 文件 | 用途 |
|---|---|
| `06-SPEC.md` | Phase 6 做什么、边界、验收 |
| `06-AI-SPEC.md` | Agent、prompt、audit、failure routing 合同 |
| `06-VALIDATION.md` | 验证策略 |
| `06-00-PLAN.md` 到 `06-06-PLAN.md` | 具体执行计划 |
| `docs/architecture/phase-6-acceptance-and-trace-report.md` | 架构文档区的同主题长报告 |

## 8. Report Boundary

本文件是 Phase 6 的规划和验收说明，不是运行时产物。Phase 6 要实现的是每次
text2IFC 运行都自动生成自己的 `report.md`，把本次运行的中间输入输出汇总到一个
Markdown 审核入口里。

---
*本文件是 Phase 6 文件夹内的单入口验收报告，方便直接审阅。*
