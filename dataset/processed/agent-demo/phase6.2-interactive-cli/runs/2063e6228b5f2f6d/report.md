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
    "created_at": "2026-06-25T15:25:53+00:00",
    "role": "user",
    "text": "创建一个长6米、宽4米、高3米的房间，南墙中间有一扇900mm宽、2100mm高的门，北墙中间有一扇1200mm宽、1500mm高、窗台900mm高的窗。",
    "turn_index": 0
  },
  {
    "created_at": "2026-06-25T15:26:19+00:00",
    "role": "assistant",
    "text": "墙体厚度是多少？如果暂时不知道，可以直接告诉我不知道。",
    "turn_index": 1
  },
  {
    "created_at": "2026-06-25T15:26:30+00:00",
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
  "ifc_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d\\output.ifc",
  "output_dir": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d",
  "report_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d\\report.md",
  "stage": "final-acceptance",
  "valid": true
}
```

## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/2063e6228b5f2f6d/session-export.json](runs/2063e6228b5f2f6d/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-06-25T15:27:19+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "2063e6228b5f2f6d",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d/generator",
      "response_id": "9cca772b67744412a0eb1061556ff84f",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-06-25T15:27:19+00:00",
    "event_index": 1,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "2063e6228b5f2f6d",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "9cca772b67744412a0eb1061556ff84f",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-06-25T15:27:26+00:00",
    "event_index": 2,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "2063e6228b5f2f6d",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d",
      "report_path": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d/report.md",
      "response_id": "d00ea640a9c9465c9d1e384196135706",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-06-25T15:27:30+00:00",
    "event_index": 3,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "2063e6228b5f2f6d",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d",
      "report_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d\\report.md",
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
    "created_at": "2026-06-25T15:26:30+00:00",
    "kind": "design_brief",
    "path": "runs/2063e6228b5f2f6d/design-brief.json"
  },
  {
    "created_at": "2026-06-25T15:27:19+00:00",
    "kind": "candidate",
    "path": "runs/2063e6228b5f2f6d/candidate.json"
  },
  {
    "created_at": "2026-06-25T15:27:30+00:00",
    "kind": "ifc",
    "path": "runs/2063e6228b5f2f6d/output.ifc"
  },
  {
    "created_at": "2026-06-25T15:27:30+00:00",
    "kind": "report",
    "path": "runs/2063e6228b5f2f6d/report.md"
  },
  {
    "created_at": "2026-06-25T15:27:30+00:00",
    "kind": "session_export",
    "path": "runs/2063e6228b5f2f6d/session-export.json"
  }
]
```
