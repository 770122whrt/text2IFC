# Phase 5 Summary: Multi-turn Clarification Agent

**Status:** Complete - verified 2026-06-15

## What Phase 5 Delivered

Phase 5 added the first Chinese-first clarification Agent for text2IFC. The
Agent starts from an incomplete Chinese natural-language request, asks bounded
follow-up questions, records the conversation, keeps unknown required facts as
Draft, and compiles IFC only after the candidate passes formal BIM JSON 2.0
validation.

The phase acceptance artifact is:

`dataset/processed/agent-demo/simple-room/output.ifc`

The final demo compiles this IFC2X3 file and reports successful reopen
verification.

## Implemented Capabilities

| Area | Result |
|---|---|
| Agent state | `AgentState` records original request, transcript, missing facts, accepted facts, candidate JSON, and status |
| Chinese questions | Missing facts are rendered as Chinese user-facing questions |
| Question batching | Each turn asks at most 3 questions |
| Draft behavior | Unknown required facts keep the state as Draft and do not compile |
| Answer merge | Answers append to transcript and accepted facts; corrections are explicit |
| Provider boundary | Fake/file providers are deterministic; Mimo adapter is optional and env-configured |
| Guardrails | Raw IFC/STEP and low-level IFC helper output are rejected before merge |
| Demo | Scripted simple-room flow writes transcript, state, candidate, diagnostics, metrics, report, and IFC |
| Secret scan | Agent demo text artifacts scan clean with zero findings |

## Demo Flow

The scripted demo starts from an incomplete Chinese request for a one-storey
rectangular room with four walls, one door, and one window.

The Agent asks 3 Chinese clarification questions in one turn:

- room length, width, and height;
- door host wall and placement;
- window host wall, sill height, and dimensions.

Scripted answers are merged into Agent state. The final candidate validates as
formal BIM JSON 2.0 and compiles to IFC2X3.

## Final Artifacts

| Artifact | Purpose |
|---|---|
| `dataset/processed/agent-demo/simple-room/transcript.json` | Conversation transcript |
| `dataset/processed/agent-demo/simple-room/state.json` | Final Agent state |
| `dataset/processed/agent-demo/simple-room/candidate.json` | Formal BIM JSON 2.0 candidate |
| `dataset/processed/agent-demo/simple-room/diagnostics.json` | Validation and compile diagnostics |
| `dataset/processed/agent-demo/simple-room/metrics.json` | Turn, question, validation, and compile metrics |
| `dataset/processed/agent-demo/simple-room/report.md` | Human-readable demo report |
| `dataset/processed/agent-demo/simple-room/output.ifc` | Final IFC2X3 acceptance artifact |

## Verification

| Command | Result |
|---|---|
| `python -m pytest tests/agent -q` | 30 passed |
| `python scripts/agent/run_clarification_demo.py --check` | `{"success": true}` |
| `python scripts/agent/run_mimo_smoke.py --check-config` | passed, currently not configured |
| `python scripts/agent/scan_agent_artifacts.py --path dataset/processed/agent-demo` | 0 findings |
| `python -m pytest tests -q --tb=short` | 311 passed |
| `python -m compileall -q src scripts` | passed |
| `python scripts/text2json/run_e2e_demo.py --check` | passed |
| `python scripts/ifc_knowledge/check_registry.py` | passed |

## Requirement Coverage

- **AGENT-01:** Covered for the Phase 5 simple-room scope. Natural language
  plus answers reaches valid formal BIM JSON 2.0.
- **AGENT-02:** Covered. Missing facts become targeted Chinese questions with
  a 1-3 question cap.
- **AGENT-03:** Covered. Multi-turn state preserves original request,
  transcript, missing facts, accepted facts, diagnostics, and final status.

## Security and Code Review

Focused review checked:

- compilation gate bypass;
- Draft or invalid IFC output writing;
- state overwrite;
- provider secret leakage;
- raw IFC/STEP acceptance;
- unbounded question generation;
- live-provider dependency in tests.

No blocking issues were found.

The optional Mimo live smoke was not run because the current shell does not
have all required environment variables configured. This is non-blocking:
fake/file providers cover deterministic tests, and `--check-config` reports
only environment variable names.

## Remaining Boundaries

Phase 5 does not solve Phase 4 fidelity. Materials, type reuse, arbitrary BRep,
tessellation, mapped geometry, richer topology, and broader product classes
remain outside this Agent phase.

Phase 5 also does not fine-tune or deploy a production model. Those belong to
Phase 6 after the high-fidelity IFC path is addressed.

## Recommended Next Step

Proceed to Phase 4: High-fidelity IFC Round Trip. This closes the major IFC
fidelity gap before Phase 6 data expansion, fine-tuning, and deployment.
