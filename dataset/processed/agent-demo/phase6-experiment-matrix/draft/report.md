# Phase 6 Multi-agent Run Report

## Original Input

Source: [input.txt](input.txt)

```text
创建一个房间，但我不知道宽度。
```

## Design Brief

Source: [design-brief.json](design-brief.json)

```json
{
  "ambiguities": [],
  "clarification_questions": [],
  "known_facts": {
    "door": {
      "host": "south_wall",
      "position": "center"
    },
    "room": {
      "height_mm": 3000,
      "length_mm": 6000
    },
    "storey_count": 1,
    "walls": {
      "count": 4,
      "enclosure": "closed"
    },
    "window": {
      "host": "north_wall",
      "position": "center"
    }
  },
  "language": "zh-CN",
  "missing_facts": [
    {
      "code": "ROOM_WIDTH_MISSING",
      "id": "room-width",
      "message": "缺少房间宽度。",
      "path": "/room/width_mm",
      "source": "user_request"
    }
  ],
  "original_request": "创建一个房间，但我不知道宽度。",
  "provenance": {
    "source": "user_request"
  },
  "schema_version": "text2ifc/design-brief/1.0",
  "user_corrections": []
}
```

## Rendered Prompt

Source: [prompt-rendered.md](prompt-rendered.md)

```text
# text2IFC BIM JSON Generator v1

你是 text2IFC 的 BIM JSON 2.0 生成专家。你只根据经过验证的 Design Brief 和提供的项目合同生成语义 BIM JSON。

## Inputs

- Design Brief：`{"ambiguities": [], "clarification_questions": [], "known_facts": {"door": {"host": "south_wall", "position": "center"}, "room": {"height_mm": 3000, "length_mm": 6000}, "storey_count": 1, "walls": {"count": 4, "enclosure": "closed"}, "window": {"host": "north_wall", "position": "center"}}, "language": "zh-CN", "missing_facts": [{"code": "ROOM_WIDTH_MISSING", "id": "room-width", "message": "缺少房间宽度。", "path": "/room/width_mm", "source": "user_request"}], "original_request": "创建一个房间，但我不知道宽度。", "provenance": {"source": "user_request"}, "schema_version": "text2ifc/design-brief/1.0", "user_corrections": []}`
- BIM JSON Schema 摘要：`{"ifc_schema": "IFC2X3", "schema_version": "bim-json/2.0"}`
- 当前可生成能力：`{"ifc_schema": "IFC2X3", "profile": "architectural-generation"}`
- 命名 few-shot 示例：`[]`
- BIM JSON 验证反馈：`[]`
- IFC 几何质量反馈：`[]`

## Output Contract

- 信息完整时，只输出 Formal BIM JSON 2.0 JSON 对象。
- 必要信息缺失或存在不能消解的歧义时，只输出 BIM JSON Draft Envelope。
- 不要输出 Markdown、解释文字或代码块标记。
- 不要输出 raw IFC、STEP 文本、STEP ID、`IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory` 或编译器内部对象。
- 不要新增 Design Brief 中没有的尺寸、位置、方向、楼层、空间、洞口、关系或属性。

## Generation Rules

- BIM JSON Schema 是结构真相，使用 `schema_version: "bim-json/2.0"` 和 `ifc_schema: "IFC2X3"`。
- 使用语义 `ifc_class`，如 `IfcProject`、`IfcBuildingStorey`、`IfcSpace`、`IfcWall`、`IfcDoor`、`IfcWindow` 和 `IfcOpeningElement`。
- 用户语义关系放入 BIM JSON；低层 IFC 实体和编译器关系由确定性编译器生成。
- 所有构件位置必须相对明确的父对象表达；门窗洞口必须相对宿主墙表达。
- 修复模式只能使用反馈和已知事实。无法从已知事实修复时返回 Draft，并提出 1-3 个中文追问。
```

## Model Raw Output

Source: [raw-response.txt](raw-response.txt)

```text
{"draft_version": "bim-json-draft/1.0", "target_schema_version": "bim-json/2.0", "partial_document": {"room": {}}, "missing_facts": [{"entity_id": "space-1", "path": "/room/width_mm", "code": "ROOM_WIDTH_MISSING", "message": "缺少房间宽度。"}], "losses": [], "clarification_targets": [{"entity_id": "space-1", "path": "/room/width_mm", "question": "房间宽度是多少？"}], "provenance": {"source": "provider"}}
```

## Parsed BIM JSON or Draft

Source: [draft.json](draft.json)

```json
{
  "clarification_targets": [
    {
      "entity_id": "space-1",
      "path": "/room/width_mm",
      "question": "房间宽度是多少？"
    }
  ],
  "draft_version": "bim-json-draft/1.0",
  "losses": [],
  "missing_facts": [
    {
      "code": "ROOM_WIDTH_MISSING",
      "entity_id": "space-1",
      "message": "缺少房间宽度。",
      "path": "/room/width_mm"
    }
  ],
  "partial_document": {
    "room": {}
  },
  "provenance": {
    "source": "provider"
  },
  "target_schema_version": "bim-json/2.0"
}
```

## Validation Feedback

Source: [validation-feedback.json](validation-feedback.json)

```json
{
  "issues": []
}
```

## Geometry Feedback

Source: [geometry-feedback.json](geometry-feedback.json)

```json
{
  "attempted": false,
  "issues": [],
  "metrics": {},
  "success": false
}
```

## Failure Route

Source: [repair-attempts.json](repair-attempts.json)

```json
{
  "missing_fact_paths": [
    "/room/width_mm"
  ],
  "questions": [
    "房间宽度是多少？"
  ],
  "repair_attempts": [],
  "route": "draft_required"
}
```

## Audit Result

Source: [audit-report.json](audit-report.json)

```json
{
  "blocking": true,
  "deterministic_gates": {
    "bim_json": false,
    "compile_reopen": false,
    "design_brief": true,
    "geometry": false
  },
  "deterministic_status": "failed",
  "diagnostics": [],
  "evidence": {
    "candidate": "draft.json",
    "design_brief": "design-brief.json",
    "geometry": "geometry-feedback.json",
    "input": "input.txt",
    "raw_response": "raw-response.txt",
    "validation": "validation-feedback.json"
  },
  "failed_gates": [
    "bim_json",
    "compile_reopen",
    "geometry"
  ],
  "intent_coverage": {
    "requested_geometry": "unverified"
  },
  "mismatches": [],
  "narrative_recommendation": null,
  "recommendation": "reject",
  "unsupported_facts": []
}
```

## Metrics

Source: [metrics.json](metrics.json)

```json
{
  "audit_pass": false,
  "bim_json_status": "draft",
  "compile_reopen_success": false,
  "failure_class": "draft",
  "failure_route": "draft_required",
  "geometry_pass": false,
  "provider_mode": "fake",
  "repair_attempt_count": 0,
  "success": false
}
```

## Final Artifacts

Source: [artifact-manifest.json](artifact-manifest.json)

```json
{
  "artifacts": {
    "artifact_manifest": "artifact-manifest.json",
    "audit": "audit-report.json",
    "candidate": "candidate.json",
    "design_brief": "design-brief.json",
    "draft": "draft.json",
    "experiment_record": "experiment-record.json",
    "geometry_feedback": "geometry-feedback.json",
    "ifc": "output.ifc",
    "input": "input.txt",
    "metrics": "metrics.json",
    "parsed_response": "parsed-response.json",
    "prompt_metadata": "prompt-metadata.json",
    "prompt_render_input": "prompt-render-input.json",
    "prompt_rendered": "prompt-rendered.md",
    "raw_response": "raw-response.txt",
    "repair_attempts": "repair-attempts.json",
    "report": "report.md",
    "secret_scan": "secret-scan.json",
    "validation_feedback": "validation-feedback.json"
  },
  "secret_redaction_status": "passed",
  "secret_scan": {
    "finding_count": 0,
    "scanned_file_count": 16
  }
}
```
