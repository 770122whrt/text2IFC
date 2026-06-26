# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
创建一个长6米、宽4米、高3米的房间，南墙中间有一扇900mm宽、2100mm高的门，北墙中间有一扇1200mm宽、1500mm高、窗台900mm高的窗。
```

## Transcript

```json
[
  {
    "created_at": "2026-06-26T03:40:54+00:00",
    "role": "user",
    "text": "创建一个长6米、宽4米、高3米的房间，南墙中间有一扇900mm宽、2100mm高的门，北墙中间有一扇1200mm宽、1500mm高、窗台900mm高的窗。",
    "turn_index": 0
  },
  {
    "created_at": "2026-06-26T03:41:14+00:00",
    "role": "assistant",
    "text": "墙体厚度是多少？如果暂时不知道，可以直接告诉我不知道。",
    "turn_index": 1
  },
  {
    "created_at": "2026-06-26T03:41:28+00:00",
    "role": "user",
    "text": "墙体厚度为300mm。",
    "turn_index": 2
  }
]
```

## Design Brief Agent

- [design-brief/input.txt](design-brief/input.txt)
- [design-brief/conversation.json](design-brief/conversation.json)
- [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)
- [design-brief/request.redacted.json](design-brief/request.redacted.json)
- [design-brief/response.raw.json](design-brief/response.raw.json)
- [design-brief/model-text.txt](design-brief/model-text.txt)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)
- [design-brief/metrics.json](design-brief/metrics.json)

## BIM JSON Generator

- [generator/prompt-rendered.md](generator/prompt-rendered.md)
- [generator/request.redacted.json](generator/request.redacted.json)
- [generator/response.raw.json](generator/response.raw.json)
- [generator/model-text.txt](generator/model-text.txt)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [generator/metrics.json](generator/metrics.json)

## Repair Route

- [repair/route.json](repair/route.json)
- [repair/repair-attempts.json](repair/repair-attempts.json)
- [repair/source-validation.json](repair/source-validation.json)
- [repair/metrics.json](repair/metrics.json)

## Audit Agent

- [audit/prompt-rendered.md](audit/prompt-rendered.md)
- [audit/request.redacted.json](audit/request.redacted.json)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "0fe9f14742b5c5d7",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7\\output.ifc",
  "output_dir": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7",
  "report_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/0fe9f14742b5c5d7/session-export.json](runs/0fe9f14742b5c5d7/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-06-26T03:42:20+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "0fe9f14742b5c5d7",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/0fe9f14742b5c5d7/generator",
      "response_id": "1c1f88d0f4f04059a7058ff9c58b4fe8",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-06-26T03:42:20+00:00",
    "event_index": 1,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "0fe9f14742b5c5d7",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/0fe9f14742b5c5d7/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "1c1f88d0f4f04059a7058ff9c58b4fe8",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-06-26T03:42:27+00:00",
    "event_index": 2,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "0fe9f14742b5c5d7",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/0fe9f14742b5c5d7",
      "report_path": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/0fe9f14742b5c5d7/report.md",
      "response_id": "8043cad9894749f3901d33797ce7b4f6",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-06-26T03:42:29+00:00",
    "event_index": 3,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "0fe9f14742b5c5d7",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7",
      "report_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\0fe9f14742b5c5d7\\report.md",
      "secret_finding_count": 0,
      "stage": "final-acceptance",
      "valid": true
    }
  }
]
```

### Artifact Index

```json
[
  {
    "created_at": "2026-06-26T03:41:28+00:00",
    "kind": "design_brief",
    "path": "runs/0fe9f14742b5c5d7/design-brief.json"
  },
  {
    "created_at": "2026-06-26T03:42:20+00:00",
    "kind": "candidate",
    "path": "runs/0fe9f14742b5c5d7/candidate.json"
  },
  {
    "created_at": "2026-06-26T03:42:29+00:00",
    "kind": "ifc",
    "path": "runs/0fe9f14742b5c5d7/output.ifc"
  },
  {
    "created_at": "2026-06-26T03:42:29+00:00",
    "kind": "report",
    "path": "runs/0fe9f14742b5c5d7/report.md"
  },
  {
    "created_at": "2026-06-26T03:42:29+00:00",
    "kind": "session_export",
    "path": "runs/0fe9f14742b5c5d7/session-export.json"
  }
]
```
