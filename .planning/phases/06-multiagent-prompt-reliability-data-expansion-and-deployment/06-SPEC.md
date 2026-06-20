# 06 SPEC: Multi-agent Prompt Reliability, Data Expansion, and Deployment

## Status

Specified on 2026-06-18 for the `multiagent-design` worktree branch.

## Objective

Phase 6 turns the current text2IFC pipeline into a measurable, traceable
multi-agent generation system and then uses that system to decide whether
prompt-only, RAG-assisted, or fine-tuned model deployment is justified.

The phase keeps the same hard product boundary:

Natural language -> validated semantic BIM JSON 2.0 -> deterministic IFC2X3.

The model layer still must not output raw IFC, STEP text, low-level IFC helper
entities, STEP IDs, compiler bookkeeping, or hidden defaults.

## Locked User Decisions

- All development for this conversation happens in the C-drive worktree:
  `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`.
- The E-drive working tree at `E:\code for project\bimnet` must not be edited
  by this conversation. Git metadata may still be shared by normal Git worktree
  mechanics.
- Phase 6 must explain every agent's job in plain terms: what it does and why
  it exists.
- The current `two-room-suite` geometry gate artifact is not proof of a
  unified prompt system. It is a deterministic generated-IFC gate with a
  hard-coded candidate.
- Phase 6 must introduce a unified prompt registry and traceable prompt input
  renderer before claiming prompt iteration capability.
- A Design Brief or expert-understanding step is allowed and recommended for
  weak natural-language inputs.
- Repair is conditional, not mandatory for every run. Successful generation may
  have zero repair attempts; failed generation must route to a safe repair
  attempt, Draft clarification, or blocking failure. If implemented, repair
  starts as a measured mode of the BIM JSON Generator, not as a separate
  physical agent.
- Audit should be separate from generation. Agent audit may review semantic
  coverage and human intent, but deterministic validators and IFC quality gates
  remain authoritative.

## Current State

- Phase 3 produced split-safe text/BIM JSON pairs, a structured-output
  baseline, an evaluator, and one text -> BIM JSON -> IFC demo.
- Phase 4 produced generated-IFC correctness gates and all-25 BIMNet fidelity
  accounting. It proved that valid and reopenable IFC can still be spatially
  wrong unless geometry gates check the compiled IFC.
- Phase 5 produced a Chinese-first clarification Agent state machine, fake/file
  providers, an optional Anthropic-compatible Mimo adapter, and a scripted
  simple-room IFC demo.
- Prompt files such as `prompts/agent/mimo-bim-json-v3.md` exist, but prompt
  rendering is not yet centralized.
- `scripts/agent/run_geometry_gate_demo.py` writes `prompt-used.md`, but its
  candidate BIM JSON is hard-coded. It is a quality gate demo, not a live
  multi-turn provider run.

## In Scope

- A versioned prompt registry with template IDs, hashes, allowed inputs, and
  rendered prompt artifact traces.
- A Design Brief Agent that converts raw Chinese natural language into explicit
  known facts, missing facts, ambiguities, and clarification targets.
- A BIM JSON Generator Agent that consumes the Design Brief, schema summary,
  capability profile, few-shot examples, and feedback to produce BIM JSON 2.0
  or Draft updates.
- Conditional failure routing inside the BIM JSON Generator: no repair needed,
  safe repair attempt, Draft clarification, or blocking failure. Repair uses
  validation and generated IFC quality feedback only when enough known facts
  exist.
- An Audit Agent that compares the original request, Design Brief, BIM JSON,
  deterministic diagnostics, and IFC metrics to produce an evidence-linked
  review report.
- An Observer or iteration loop that records prompt/provider versions, traces,
  failure classes, repair attempts, and metric changes before prompt updates
  are accepted.
- Dataset expansion only from license-reviewed sources with provenance,
  scene-family split integrity, and sidecar loss accounting.
- Prompt-only, RAG-assisted, and fine-tune comparison only after evaluation
  harnesses are in place.
- Deployable CLI/service packaging for the supported-scope text2IFC path.

## Out of Scope

- Raw IFC or STEP generation by any model.
- A separate standalone Repair Agent in the first Phase 6 implementation wave.
- Agent audit overriding deterministic schema, compiler, reopen, geometry, or
  secret-scan gates.
- Full BIMNet source-equivalent reconstruction for mapped, BRep, tessellated,
  boolean, or surface geometry that Phase 4 still reports as loss-explicit.
- Training on unlicensed or unclear-license data.
- Silent defaults for missing user facts.
- Claiming production fine-tuning value before prompt-only, conditional repair,
  Draft, and blocking-failure routes are evaluated.

## Agent Roles

### 1. Design Brief Agent

What it does:

- Reads the user's original Chinese request.
- Extracts explicit building facts such as storeys, spaces, dimensions,
  openings, wall relationships, and user constraints.
- Marks missing or ambiguous facts instead of guessing.
- Produces a Design Brief JSON record, not BIM JSON and not IFC.

Why it exists:

- Weak user input often mixes intent, partial dimensions, and vague spatial
  language. Asking the BIM JSON Generator to solve understanding, schema
  construction, repair, and self-audit in one prompt makes failures harder to
  diagnose.
- A separate Design Brief gives the later generator a cleaner input and gives
  the Audit Agent a human-intent artifact to compare against.

### 2. BIM JSON Generator Agent

What it does:

- Consumes the Design Brief, BIM JSON schema summary, capability profile,
  few-shot examples, and prior validation feedback.
- Outputs formal BIM JSON 2.0 when facts are sufficient.
- Outputs a Draft update when required facts are missing.

Why it exists:

- BIM JSON 2.0 is the project contract between language and IFC.
- Keeping generation focused on semantic BIM JSON prevents the model from
  producing fragile STEP text or low-level IFC resource objects.

### 3. Conditional Repair Route

What it does:

- Runs only when a previous candidate failed and the known user facts are
  sufficient to attempt a safe correction.
- Re-runs the BIM JSON Generator with structured validator and IFC quality
  feedback, such as schema errors, wall orientation errors, room enclosure
  failures, opening host mismatches, or missing containment.
- Produces a repaired BIM JSON candidate, Draft questions, or a blocking
  failure record.

Why it starts as a mode, not a separate agent:

- Repair, when attempted, still has the same output contract as generation:
  BIM JSON 2.0 or Draft. Keeping it inside the generator avoids two competing
  prompt families while the failure taxonomy is still small.
- It can be split into a standalone Repair Agent later if measured experiments
  show a specialized repair prompt improves results.

### 4. Audit Agent

What it does:

- Reads the user request, Design Brief, candidate BIM JSON, validator results,
  IFC quality metrics, and compiled artifact references.
- Produces a semantic review that explains whether the output matches the
  user's request and where it differs.
- Flags coverage gaps, unsupported facts, suspicious assumptions, and evidence
  that needs human review.

Why it exists:

- Deterministic gates are excellent for schema, geometry, and relationship
  checks, but they do not fully answer "did this model satisfy what the user
  meant?" An Audit Agent can review intent coverage while still respecting the
  hard gates.

### 5. Observer Loop

What it does:

- Records every run's prompt version, rendered inputs, raw output, parsed
  output, validation feedback, repair attempts, audit result, metrics, and
  final artifact paths.
- Classifies failures before any prompt or agent contract change is accepted.
- Requires a failing test or experiment case before changing a production
  prompt.

Why it exists:

- The project needs continuous prompt improvement without losing provenance.
  A prompt change is not "better" unless the recorded metrics and failure
  classes improve under stable tests.

## Requirements

### 1. Prompt registry and traceability

- Current: Prompt files exist, but provider runs can still use ad hoc prompt
  text such as the geometry-gate `prompt-used.md`.
- Target: Every live or replayed provider run must declare the prompt template
  ID, template hash, renderer inputs, rendered prompt path, raw response path,
  parsed output path, and validation feedback path.
- Acceptance: A test rejects an Agent/provider run artifact that lacks prompt
  template ID or hash.

### 2. Design Brief contract

- Current: Natural language goes directly to baseline or provider prompt.
- Target: Phase 6 defines a Design Brief schema and validator for known facts,
  missing facts, ambiguities, user corrections, and provenance.
- Acceptance: Tests show complete, incomplete, and ambiguous Chinese requests
  become valid Design Brief records without generating BIM JSON or IFC.

### 3. Generator and failure-routing contract

- Current: `mimo-bim-json-v3.md` contains useful constraints, but the pipeline
  does not have a reusable prompt renderer and repair attempt contract.
- Target: BIM JSON generation uses registry-backed templates and records the
  failure route for every run: no repair needed, repair attempted, Draft
  clarification, or blocked failure.
- Acceptance: A successful first-pass generation records zero repair attempts.
  A validation or geometry failure records its route; if repair is attempted,
  the trace records before/after candidates and error deltas.

### 4. Agent audit contract

- Current: Generated IFC gates produce deterministic metrics and reports, but
  no separate agent reviews human intent coverage.
- Target: Audit Agent reports compare user request, Design Brief, BIM JSON, and
  deterministic metrics. Audit cannot pass a run that deterministic gates fail.
- Acceptance: Tests prove that an audit report flags semantic mismatch and
  preserves deterministic failure status.

### 5. Data and model decision

- Current: Phase 3 has 100 deterministic text/BIM JSON pairs and Phase 4 has
  all-25 fidelity accounting.
- Target: Phase 6 expands only approved data, preserves scene-family split
  separation, and compares prompt-only, conditional repair, optional RAG, and
  optional fine-tune baselines before choosing deployment.
- Acceptance: A decision report states whether fine-tuning is justified and
  cites metrics, data counts, split integrity, and known unsupported facts.

### 6. Deployment package

- Current: Demo scripts exist, but no deployable service boundary is selected.
- Target: A repeatable CLI or service runs the supported-scope path:
  request -> Design Brief -> questions or BIM JSON -> validation -> IFC ->
  audit report.
- Acceptance: The final Phase 6 demo writes a real IFC file plus trace,
  metrics, and audit artifacts under a phase-specific output directory.

## Acceptance Checklist

- [ ] Phase 6 prompt registry exists and every provider run uses it.
- [ ] Prompt traces include template ID, template hash, rendered inputs, raw
      output, parsed output, feedback, repair iteration, metrics, and artifact
      paths.
- [ ] Design Brief Agent outputs validated structured briefs, not BIM JSON.
- [ ] BIM JSON Generator outputs only formal BIM JSON 2.0 or Draft updates.
- [ ] Failure routing records zero-repair success, conditional repair attempts,
      Draft clarification, and blocking failures. Any repair attempt records
      measured error deltas.
- [ ] Audit Agent is separate from generation and cannot override deterministic
      gates.
- [ ] Dataset expansion preserves licensing, provenance, sidecars, and
      scene-family split separation.
- [ ] Model decision compares prompt-only, conditional repair, optional RAG,
      and optional fine-tune baselines.
- [ ] Deployment demo produces a real IFC2X3 file and a complete trace bundle.
- [ ] No secret values, provider headers, or private URLs are written to
      artifacts or commits.

## Ambiguity Report

| Dimension | Score | Minimum | Status | Notes |
| --- | ---: | ---: | --- | --- |
| Goal Clarity | 0.84 | 0.75 | Met | Multi-agent reliability and deployment are now explicit. |
| Boundary Clarity | 0.83 | 0.70 | Met | Raw IFC, standalone repair agent, and deterministic-gate override are out. |
| Constraint Clarity | 0.82 | 0.65 | Met | C-worktree, prompt registry, traceability, and no-secret rules are locked. |
| Acceptance Criteria | 0.80 | 0.70 | Met | Prompt traces, brief validation, failure routes, optional repair deltas, audit, metrics, and IFC demo are measurable. |

Ambiguity: 0.18. Gate passed for planning, with model-provider and deployment
interface details to be resolved by Phase 6 execution evidence.

## Interview Notes

| Round | Perspective | Question | Decision |
| --- | --- | --- | --- |
| 1 | Reality check | Does `two-room-suite` prove unified prompt control? | No. It is a deterministic gate with a hard-coded candidate. |
| 2 | System designer | What must exist before prompt iteration can be trusted? | Versioned prompt registry, renderer, trace bundle, metrics, and failure taxonomy. |
| 3 | Product boundary | Should weak input be polished first? | Yes. Use a Design Brief Agent before BIM JSON generation. |
| 4 | Failure analyst | Is repair always mandatory? | No. Successful runs should record zero repairs; failed runs route to conditional repair, Draft, or blocking failure. |
| 5 | Safety reviewer | Can Agent audit approve invalid output? | No. It may explain and flag issues, but deterministic gates remain authoritative. |

---
*Phase: 06-multiagent-prompt-reliability-data-expansion-and-deployment*
