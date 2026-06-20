# Phase 6 Multi-agent Design

**Date:** 2026-06-18
**Branch:** `multiagent-design`
**Worktree:** `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`

## Why This Exists

Phase 5 proved that text2IFC can ask Chinese clarification questions and write
a real IFC file after BIM JSON validation. Phase 4 proved that a generated IFC
can open successfully and still be spatially wrong unless a geometry gate checks
the compiled file.

The next problem is prompt and agent reliability. We need to know exactly what
prompt, input facts, feedback, failure route, optional repair attempt, and
audit result created each BIM JSON and IFC artifact.

## Current Reality

The current repository has useful pieces, but they are not yet one unified
multi-agent architecture.

- `prompts/agent/mimo-bim-json-v3.md` is the best current geometry-aware prompt.
- `src/text2ifc_agent/providers.py` can call fake/file providers and optional
  Anthropic-compatible Mimo.
- `src/text2ifc_agent/session.py` handles Phase 5 clarification state.
- `scripts/agent/run_geometry_gate_demo.py` writes the `two-room-suite`
  geometry-gate artifact, but the BIM JSON candidate is hard-coded. That case
  proves the quality gate, not live prompt orchestration.

## Design Brief Agent

What it does:

- Reads the user's original Chinese request.
- Extracts explicit building facts: storeys, rooms, dimensions, placements,
  openings, relationships, and user constraints.
- Records missing facts and ambiguities.
- Produces a Design Brief JSON object.

What it does not do:

- It does not output BIM JSON entities.
- It does not output IFC or STEP.
- It does not invent missing dimensions or spatial relationships.

Why it exists:

- Weak natural language is often incomplete. A Design Brief separates "what the
  user seems to want" from "how to build valid BIM JSON." This makes the BIM
  JSON Generator easier to control and gives the Audit Agent something to
  compare against.

## BIM JSON Generator Agent

What it does:

- Reads the Design Brief, BIM JSON schema summary, capability profile,
  few-shot examples, and validation feedback.
- Outputs formal BIM JSON 2.0 when facts are complete.
- Outputs a Draft update when facts are missing.

What it does not do:

- It does not output raw IFC.
- It does not output STEP text.
- It does not output `IfcCartesianPoint`, `IfcDirection`, `IfcOwnerHistory`,
  STEP IDs, or compiler-only objects.

Why it exists:

- BIM JSON is the project contract. Keeping the model at this semantic level
  lets validators and the deterministic compiler catch errors before IFC is
  written.

## Repair Is Conditional

What it does:

- Runs only after a candidate fails validation or generated IFC quality checks.
- Records the route as one of: no repair needed, repair attempted, Draft
  required, or blocked failure.
- When repair is safe, reuses the BIM JSON Generator with explicit validation
  and geometry feedback.
- Returns repaired BIM JSON, Draft questions, or a blocking failure report.

Why it is not a separate agent first:

- Successful first-pass generation should not require repair.
- When repair is attempted, it has the same output contract as generation. If
  we split it too early, we create two prompt systems before we have enough
  failure data. We can split it later if measured experiments show a
  specialized Repair Agent is better.

## Audit Agent

What it does:

- Reviews the original request, Design Brief, BIM JSON, validator results,
  generated IFC quality metrics, and artifact paths.
- Reports whether the output matches the user's intent.
- Flags mismatch, unsupported facts, suspicious assumptions, and human-review
  needs.

What it does not do:

- It does not generate BIM JSON.
- It does not repair BIM JSON.
- It does not pass a failed deterministic gate.

Why it exists:

- Deterministic gates measure hard facts such as schema validity, relationships,
  compiled geometry, and reopen success. The Audit Agent reviews semantic
  intent coverage, which is closer to how a human expert would inspect the
  result.

## Observer Loop

What it does:

- Records prompt template ID, template hash, rendered inputs, raw output,
  parsed output, validation feedback, geometry feedback, failure route,
  optional repair attempts, metrics, audit result, and final artifacts.
- Classifies failures before prompt changes are accepted.
- Requires a test or experiment case before production prompt updates.

Why it exists:

- Prompt iteration needs memory. Without a trace bundle and metrics, prompt
  updates become anecdotes. The Observer Loop turns prompt tuning into measured
  engineering work.

## Prompt Registry Requirement

Every provider-backed run should record:

- `template_id`
- `template_hash`
- role and mode
- renderer input JSON
- rendered prompt
- raw response
- parsed output
- validation feedback
- failure route
- repair attempts when attempted
- metrics
- artifact paths

This is the first Phase 6 wave because all later model comparison, conditional
repair, RAG, and fine-tuning decisions depend on it.

## Hard Boundary

Audit cannot override deterministic gates.

The system may say:

- "The model understood the user intent, but geometry failed."
- "The IFC opens, but the room is not spatially correct."
- "The user did not provide enough information, so this remains Draft."

The system must not say:

- "The audit agent thinks it is probably fine, so compile anyway."
- "The model guessed a wall placement, so treat it as user-provided."
- "The geometry is unsupported, so substitute a box and call it faithful."

## Phase 6 Execution Order

1. Prompt registry and trace bundle.
2. Design Brief Agent.
3. BIM JSON Generator and conditional failure routing.
4. Audit Agent.
5. Experiment harness and reliability metrics.
6. Data expansion and model decision.
7. Deployable CLI/service and final IFC demo.

---
*This document records the Phase 6 multi-agent design direction before
implementation.*
