# 05 SPEC: Multi-turn Clarification Agent

## Status

Specified on 2026-06-15.

## Objective

Build the first Chinese-first multi-turn clarification Agent for text2IFC.

The Agent turns incomplete Chinese natural-language building requests into
either:

- a valid formal BIM JSON 2.0 document that can compile to IFC2X3; or
- a Draft clarification state that explicitly lists missing required facts and
  asks the user targeted follow-up questions.

The Agent must not silently invent required building facts.

## Locked User Decisions

- First-version interaction language is Chinese.
- Each clarification turn asks 1-3 key questions.
- If the user does not know required information, the conversation remains in
  Draft; no default template is applied in this phase.
- The first demo is simple: a one-storey rectangular room with four walls, one
  door, and one window.
- Later complexity should be able to grow toward BIMNet-like building requests,
  but Phase 5 does not need to solve full BIMNet complexity in its first demo.
- Real model tests target Anthropic-compatible Mimo endpoints through
  environment variables. Secrets must not be committed or written to artifacts.

## Current State

- BIM JSON 2.0 formal schema, Draft Envelope schema, and validators exist.
- The compiler can turn valid formal BIM JSON 2.0 into reopenable IFC2X3.
- Phase 3 produced Text-to-BIM-JSON pairs, a structured-output baseline,
  provider-independent evaluator, and one E2E demo.
- Phase 3 baseline has fake/file provider modes but no multi-turn state,
  follow-up question planner, answer merger, or live Mimo provider adapter.
- Missing user facts currently cause invalid output or Draft rejection rather
  than a guided conversation.

## In Scope

- Chinese-first Agent state and transcript format.
- Missing-fact detection from BIM JSON schema, Draft Envelope state, and
  `validate_v2_document` diagnostics.
- User-facing question generation that translates schema/validator gaps into
  plain Chinese questions.
- Question batching with 1-3 questions per turn.
- Multi-turn answer merging without overwriting original user text.
- Draft state when required facts are still missing.
- Formal BIM JSON 2.0 generation only after required facts are available.
- A simple demo: one-storey rectangular room, four walls, one door, one window.
- Fake and file providers for deterministic TDD.
- Anthropic-compatible Mimo provider adapter using environment variables.
- Diagnostics and transcripts that show what was asked, answered, accepted,
  rejected, and compiled.

## Out of Scope

- Silent defaults or template filling when the user says they do not know.
- Raw IFC or STEP generation by the model.
- Asking users for low-level IFC implementation objects such as
  `IfcCartesianPoint`, `IfcDirection`, `IfcOwnerHistory`, STEP IDs, or IFC
  placement resource entities.
- Fine-tuning, dataset expansion, or deployable model packaging.
- RAG over IFC documentation unless a later real-model baseline shows recurring
  knowledge errors.
- Phase 4 fidelity work: material layers, type reuse, arbitrary BRep,
  tessellation, mapped geometry, broad topology, or broader product classes.
- Full BIMNet-complexity natural-language generation in the first demo.

## Requirements

### 1. Chinese-first interaction

- Current: Phase 3 prompts and pair text are English-oriented and one-shot.
- Target: Phase 5 Agent asks user-facing clarification questions in Chinese by
  default.
- Acceptance: A test with missing wall/room dimensions returns Chinese
  questions and no English schema jargon as the main user-facing text.

### 2. Bounded question batching

- Current: No clarification question planner exists.
- Target: Each Agent turn asks between 1 and 3 necessary questions.
- Acceptance: A test with more than 3 missing facts returns exactly the top
  1-3 questions and carries remaining missing facts forward in state.

### 3. Draft instead of defaults

- Current: The compiler rejects Drafts, and baseline rejects Draft-as-formal,
  but there is no conversational Draft flow.
- Target: If required facts are missing or the user says they do not know, the
  Agent keeps the conversation in Draft and does not compile IFC.
- Acceptance: A test where the user answers "I do not know" in Chinese leaves
  status as Draft, writes missing facts, and produces no IFC output.

### 4. Missing-fact diagnostics become user questions

- Current: Validator issues are machine-readable paths and codes.
- Target: Agent maps missing required BIM facts into understandable Chinese
  questions about storey, dimensions, placement, openings, or relationships.
- Acceptance: Removing required room size, wall height, or door placement from
  a request yields targeted Chinese questions about those facts.

### 5. Multi-turn answer merging

- Current: No persistent conversation state exists.
- Target: User answers are appended as new facts and merged into the candidate
  BIM JSON without losing the original request or previous answers.
- Acceptance: A two-turn test records original request, question, answer, and
  updated candidate state; previous facts remain unchanged unless explicitly
  corrected.

### 6. Formal-only IFC compilation

- Current: `compile_document` already rejects invalid/Draft input.
- Target: The Agent calls IFC compilation only after the candidate document
  passes formal BIM JSON 2.0 validation.
- Acceptance: Tests prove invalid, Draft, and missing-fact states do not create
  or overwrite IFC output; valid formal state compiles and reopens.

### 7. Simple room demo

- Current: Phase 3 E2E demo uses a validation data pair, not an interactive
  user clarification flow.
- Target: A command runs an interactive-scripted demo for a one-storey
  rectangular room with four walls, one door, and one window.
- Acceptance: The demo starts from an intentionally incomplete Chinese request,
  asks follow-up questions, merges scripted answers, validates formal BIM JSON
  2.0, compiles IFC2X3, and writes transcript, JSON, diagnostics, metrics, IFC,
  and report artifacts.

### 8. Provider abstraction remains replaceable

- Current: Phase 3 baseline has fake/file providers but no live Mimo adapter.
- Target: Phase 5 adds a provider boundary that can run fake/file in tests and
  Anthropic-compatible Mimo models in live smoke tests.
- Acceptance: Tests use fake/file providers without network; a live smoke CLI
  reads `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, and a model name from the
  environment and fails with a clear diagnostic if they are missing.

### 9. Secret safety

- Current: No Phase 5 live provider artifacts exist.
- Target: Tokens, API headers, and full credential values are never written to
  repo files, diagnostics, transcripts, or git history.
- Acceptance: Tests and a repository scan prove generated artifacts contain
  environment variable names at most, not secret values.

### 10. Evaluation of Agent outcomes

- Current: Phase 3 evaluator scores one-shot prediction records.
- Target: Agent runs produce machine-readable outcome metrics: turn count,
  asked question count, draft/formal status, validation status, compile status,
  and failure category.
- Acceptance: The demo writes `metrics.json` and `report.md` summarizing those
  outcomes.

## Acceptance Checklist

- [ ] Agent asks Chinese clarification questions by default.
- [ ] Every clarification turn asks 1-3 key questions.
- [ ] Unknown required facts keep the state as Draft and do not compile IFC.
- [ ] Missing facts are represented explicitly and are not silently filled.
- [ ] Multi-turn answers are appended and merged without overwriting original
      user facts.
- [ ] Formal BIM JSON 2.0 is compiled only after `validate_v2_document` passes.
- [ ] Simple room demo produces BIM JSON, IFC2X3, transcript, diagnostics,
      metrics, and report.
- [ ] Fake/file provider tests pass without network or credentials.
- [ ] Mimo live adapter is available behind environment variables and does not
      persist secrets.
- [ ] Phase 5 final summary distinguishes Agent gaps from Phase 4 fidelity,
      RAG, fine-tuning, and deployment work.

## Ambiguity Report

| Dimension | Score | Minimum | Status | Notes |
| --- | ---: | ---: | --- | --- |
| Goal Clarity | 0.92 | 0.75 | Met | Chinese multi-turn clarification to formal BIM JSON or Draft is explicit |
| Boundary Clarity | 0.90 | 0.70 | Met | Phase 4 fidelity, RAG, fine-tuning, defaults, and raw IFC are out of scope |
| Constraint Clarity | 0.86 | 0.65 | Met | 1-3 questions, Chinese-first, no defaults, Mimo env-only, no secrets |
| Acceptance Criteria | 0.84 | 0.70 | Met | Demo, tests, validation, compile gates, and artifact checks are testable |

Ambiguity: 0.13. Gate passed.

## Interview Notes

| Round | Perspective | Question | Decision |
| --- | --- | --- | --- |
| 1 | Researcher | What exists today? | Phase 3 has one-shot Text-to-JSON, evaluator, and E2E; no multi-turn Agent |
| 2 | Simplifier | What is the smallest useful Agent? | Chinese simple room demo with missing facts and 1-3 questions per turn |
| 3 | Boundary Keeper | What if the user does not know? | Stay Draft; no default template in Phase 5 |
| 4 | Failure Analyst | What would make this unsafe? | Silent defaults, raw IFC output, secret persistence, compiling Draft/invalid JSON |
| 5 | Seed Closer | Where does real model testing fit? | Add Mimo adapter via env vars; keep fake/file for deterministic TDD |

---
*Phase: 05-multi-turn-clarification-agent*
