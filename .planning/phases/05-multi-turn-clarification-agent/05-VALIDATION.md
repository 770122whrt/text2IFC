# Phase 5: Multi-turn Clarification Agent - Validation Strategy

**Created:** 2026-06-15
**Status:** Ready for execution

## Validation Objective

Prove that Phase 5 can turn an incomplete Chinese building request into a
traceable multi-turn Draft, ask bounded Chinese clarification questions, merge
answers without fabrication, produce valid formal BIM JSON 2.0 when enough
facts exist, and compile a reopenable IFC2X3 file.

The final completion gate is the IFC artifact:

`dataset/processed/agent-demo/simple-room/output.ifc`

## Nyquist Dimensions

| Dimension | Minimum coverage |
|---|---|
| Agent state | original request, transcript, missing facts, accepted facts, status transitions |
| Chinese questions | Chinese user-facing text, no schema jargon, no low-level IFC helper terms |
| Question batching | exactly 1-3 questions per turn when facts are missing |
| Draft handling | unknown required facts remain Draft and do not compile |
| Answer merging | previous facts preserved; explicit corrections tracked |
| Formal validation | `validate_v2_document` required before compilation |
| Provider boundary | fake/file deterministic providers plus Mimo adapter diagnostics |
| Secret safety | no token/header/base URL values in artifacts |
| E2E demo | scripted simple-room request produces BIM JSON, IFC, transcript, diagnostics, metrics, report |

## Required Verification Commands

Focused commands:

```powershell
python -m pytest tests/agent -q
python scripts/agent/run_clarification_demo.py --check
python scripts/agent/run_mimo_smoke.py --check-config
python scripts/agent/scan_agent_artifacts.py --path dataset/processed/agent-demo
```

Regression commands:

```powershell
python -m pytest tests -q
python -m compileall -q src scripts
python scripts/text2json/run_e2e_demo.py --check
python scripts/ifc_knowledge/check_registry.py
```

Optional live smoke, only when the user explicitly provides runtime
environment variables:

```powershell
python scripts/agent/run_mimo_smoke.py --prompt-only
```

## Pass/Fail Gates

- **Pre-flight gate:** Existing BIM JSON 2.0 schema, Draft schema, validators,
  Phase 3 provider code, and compiler import successfully.
- **Revision gate:** Each TDD plan passes focused tests before dependent plans
  start.
- **Interaction gate:** Every user-facing clarification turn has 1-3 Chinese
  questions.
- **No-fabrication gate:** unknown required facts stay Draft and no IFC output
  is written.
- **Formal gate:** compilation is attempted only after formal BIM JSON 2.0
  validation passes.
- **IFC gate:** final demo writes `output.ifc` and reopened verification
  succeeds.
- **Security gate:** generated transcripts, diagnostics, raw provider logs, and
  reports contain no secret values.
- **Requirement gate:** AGENT-01, AGENT-02, and AGENT-03 are each covered by
  passing tests and the final summary.

## Manual Review Points

Manual review is required only if:

- live Mimo authentication or endpoint behavior is ambiguous;
- the user wants automatic template defaults despite the Phase 5 no-default
  boundary;
- the simple-room demo cannot produce a formal document without a product
  decision;
- a requested class or geometry requires Phase 4 fidelity support.
