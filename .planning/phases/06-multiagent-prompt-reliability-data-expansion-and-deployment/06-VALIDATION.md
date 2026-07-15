# Phase 6 Validation Strategy

**Created:** 2026-06-18

## Validation Goals

Phase 6 is valid only if the system can prove:

- which prompt produced each model output;
- which agent role produced each intermediate artifact;
- whether missing facts stayed Draft;
- whether failure routing correctly chose no repair, conditional repair, Draft,
  or blocking failure;
- whether the Audit Agent caught semantic mismatch without overriding hard
  deterministic failures;
- whether expanded data and model evaluation preserve licensing, provenance,
  and split integrity;
- whether the deployable path produces a real, reopenable IFC2X3 file;
- whether each run writes a generated Markdown `report.md` that exposes the
  critical intermediate inputs and outputs for human review without requiring
  the reviewer to manually open every JSON sidecar.

## Required Gates

| Gate | Evidence | Blocking |
|---|---|---|
| Prompt trace gate | template ID, hash, rendered prompt, renderer input | yes |
| Design Brief gate | Design Brief schema validation | yes |
| BIM JSON gate | `validate_v2_document` for Formal | yes |
| Draft honesty gate | missing facts explicit, no hidden defaults | yes |
| Failure-route gate | no-repair success, repair attempt, Draft, or block recorded | yes |
| Repair gate | before/after issues and no invented facts | yes only for repair claims |
| IFC gate | compile, reopen, generated IFC quality | yes for Formal demos |
| Audit gate | audit report with deterministic status preserved | yes |
| Run report gate | `report.md` contains original input, Design Brief, prompt, raw output, parsed BIM JSON or Draft, validation, geometry, failure route, audit, metrics, and final artifacts | yes |
| Data gate | license, provenance, split, sidecars | yes for model work |
| Secret gate | artifact scan | yes |

## Minimum Phase 6 Demo

The final Phase 6 acceptance demo should write:

`dataset/processed/agent-demo/phase6-multiagent/output.ifc`

The demo must also write a trace bundle with:

- `input.txt`
- `design-brief.json`
- `prompt-metadata.json`
- `prompt-rendered.md`
- `raw-response.txt`
- `candidate.json` or `draft.json`
- `validation-feedback.json`
- `geometry-feedback.json`
- `repair-attempts.json` or an empty repair-attempt list when no repair was
  needed
- `audit-report.json`
- `metrics.json`
- `report.md`

`report.md` is not a loose summary. It is the human-review entry point generated
from the same trace artifacts above. It must include or link each critical
intermediate input/output, name the final IFC artifact when compilation
succeeds, and state the secret-redaction status.

## Review Checks Before Phase Completion

- Agent tests pass.
- Prompt registry tests pass.
- Design Brief tests pass.
- Failure-routing tests pass, including zero-repair success and repair-attempt
  cases.
- Audit Agent tests pass.
- Full regression passes.
- `python -m compileall src scripts -q` passes.
- Demo command writes and reopens `output.ifc`.
- Demo command writes `report.md` with all required intermediate
  input/output sections.
- Artifact secret scan passes.
- Data split and provenance checks pass if data/model artifacts are generated.
- Requirement coverage checks include all Phase 6 requirements.

---
*Phase: 06-multiagent-prompt-reliability-data-expansion-and-deployment*
