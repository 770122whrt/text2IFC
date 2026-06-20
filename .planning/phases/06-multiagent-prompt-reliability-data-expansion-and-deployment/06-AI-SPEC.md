# Phase 6: Multi-agent Prompt Reliability - AI Design Contract

**Created:** 2026-06-18
**Status:** Ready for planning

## 1. System Classification

Phase 6 is a structured multi-agent generation and evaluation system. It is
not a free-form chatbot, not a raw IFC generator, and not a fine-tuning project
until prompt-only and repair-mode baselines have been measured.

The AI system has five logical roles:

1. Design Brief Agent
2. BIM JSON Generator Agent
3. BIM JSON Generator repair mode
4. Audit Agent
5. Observer Loop

The deterministic system remains responsible for:

- BIM JSON schema validation
- semantic validation
- IFC compilation
- IfcOpenShell reopen checks
- generated IFC geometry checks
- artifact secret scans
- split/provenance checks

## 2. Selected Framework

Selected approach: lightweight in-repo orchestrator, prompt registry, and
provider adapter.

Rationale:

- Phase 5 already has a working in-repo Agent state machine and provider
  boundary.
- The immediate missing piece is traceability and prompt control, not a
  heavyweight runtime framework.
- A project-local registry and trace bundle can be tested deterministically
  with fake/file providers before any live Mimo run.
- LangGraph or a similar framework can be revisited after the project has
  stable role contracts, trace schemas, and evaluation metrics.

## 3. Prompt Input Contract

Every model call should be rendered from a versioned template.

Required metadata:

```json
{
  "template_id": "bim-json-generator.v1",
  "template_hash": "sha256:...",
  "role": "bim_json_generator",
  "mode": "generate",
  "inputs": {
    "user_request": "...",
    "agent_state": {},
    "design_brief": {},
    "schema_summary": {},
    "capability_profile": {},
    "few_shots": [],
    "validation_feedback": [],
    "geometry_feedback": []
  }
}
```

The provider receives the rendered prompt. Artifacts preserve both the rendered
prompt and the structured renderer inputs. This makes prompt debugging possible
without relying on memory or screenshots.

## 4. Agent Output Contracts

### Design Brief Agent output

The Design Brief Agent outputs a JSON object with:

- original request reference
- known facts
- missing facts
- ambiguities
- user corrections
- clarification questions
- provenance

It must not output BIM JSON entities or IFC content.

### BIM JSON Generator output

The generator outputs one of:

- formal BIM JSON 2.0
- Draft update with missing facts and questions

It must not output:

- raw IFC or STEP text
- `IfcCartesianPoint`
- `IfcDirection`
- `IfcOwnerHistory`
- STEP IDs
- compiler-only objects
- hidden default facts

### Repair mode output

Repair mode has the same output contract as BIM JSON generation, plus trace
metadata:

- previous candidate artifact path
- feedback codes
- repair attempt number
- fixed issue count
- remaining issue count
- whether the run became Draft

### Audit Agent output

The Audit Agent outputs a report object with:

- deterministic gate status
- user intent coverage
- Design Brief coverage
- BIM JSON coverage
- IFC artifact coverage
- mismatches
- unsupported facts
- human-review notes
- final recommendation

It cannot turn a deterministic failure into a pass.

## 5. Evaluation Strategy

| Dimension | Metric | Gate |
|---|---|---|
| Prompt traceability | template ID/hash and renderer inputs present | required |
| Design Brief validity | brief schema passes | required |
| BIM JSON validity | `validate_v2_document` passes for Formal | required |
| Draft honesty | missing facts remain Draft, no hidden defaults | required |
| Repair usefulness | issue count decreases or converts to Draft | required for repair success |
| IFC output | compile and reopen success | required for Formal demos |
| Generated geometry | Phase 4 quality gate passes | required for deployment demos |
| Agent audit | report exists and deterministic failure is blocking | required |
| Split safety | no train/validation/test scene-family leakage | required for data/model work |
| Secret safety | artifact scan finds no token/header/private URL values | required |

## 6. Guardrails

- Provider guardrail: reject raw IFC, STEP, and low-level helper terms.
- Renderer guardrail: reject prompt calls without template ID or template hash.
- Compiler guardrail: compile only after formal BIM JSON 2.0 validation.
- Audit guardrail: audit cannot override deterministic failures.
- Repair guardrail: repair may not invent missing facts; it must return Draft
  questions when feedback cannot be resolved from known facts.
- Data guardrail: training exports require provenance, split assignment, and
  license status.
- Secret guardrail: never write token values, headers, or full provider URLs to
  artifacts, docs, commits, or reports.

## 7. Tracing and Artifacts

Each Phase 6 run should write a trace bundle:

- `input.txt`
- `design-brief.json`
- `prompt-render-input.json`
- `prompt-rendered.md`
- `prompt-metadata.json`
- `raw-response.txt`
- `candidate.json` or `draft.json`
- `validation-feedback.json`
- `geometry-feedback.json`
- `repair-attempts.json`
- `audit-report.json`
- `metrics.json`
- `report.md`
- `output.ifc` when Formal compilation succeeds

## 8. Checklist

- [x] Multi-agent roles defined.
- [x] Prompt registry and renderer selected as the Phase 6 entry point.
- [x] Repair starts as generator repair mode.
- [x] Audit is separate and subordinate to deterministic gates.
- [x] Fine-tuning is deferred until prompt/repair evaluation exists.
- [x] Trace bundle requirements defined.

---
*Phase: 06-multiagent-prompt-reliability-data-expansion-and-deployment*
