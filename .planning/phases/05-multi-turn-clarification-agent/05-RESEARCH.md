# Phase 5: Multi-turn Clarification Agent - Research

**Created:** 2026-06-15
**Status:** Ready for execution planning

## Research Objective

Answer: what do we need to know to plan Phase 5 well?

Phase 5 should reuse the existing BIM JSON 2.0 validator, Draft validator,
compiler, Phase 3 provider boundary, and evaluation harness. The smallest
valuable Agent is not a production chatbot; it is a deterministic
clarification state machine that can ask Chinese questions, collect missing
facts, validate formal BIM JSON, and produce one IFC file.

## Existing Project Patterns

### Provider boundary

`src/text2ifc_text/baseline.py` already defines a provider protocol plus
deterministic `FakeProvider` and `FileProvider`. Phase 5 should mirror this:

- tests use fake/file providers only;
- live Mimo is an adapter, not a dependency of unit tests;
- raw provider responses stay separate from parsed/accepted state;
- invalid provider output becomes diagnostics, not accepted facts.

### Validation boundary

`validate_v2_document` is the formal BIM JSON gate. It should remain the last
structural and semantic check before the compiler. The Agent may use validator
diagnostics to produce missing-fact questions, but it may not create a second
independent BIM JSON data model.

### Draft boundary

`validate_draft` already represents incomplete or unsupported content. Phase 5
should add a conversational Draft state that points to missing facts and
questions. Draft state is useful and inspectable, but not compilable.

### Compiler boundary

`compile_document` already rejects Draft input and writes IFC atomically. Phase
5 should call it only after formal validation succeeds. The final acceptance
demo should also reopen the IFC through existing verification behavior.

## Recommended Architecture

Use a small in-repo state machine:

1. Intake: original Chinese natural-language request is stored unchanged.
2. Candidate generation: provider returns a semantic candidate or Draft update.
3. Diagnostics: validator/Draft/schema issues are normalized into missing
   facts.
4. Question planning: choose top 1-3 open missing facts and render Chinese
   questions.
5. Answer merge: append user answers as facts, preserving transcript and source.
6. Formal gate: build/validate formal BIM JSON only when required facts exist.
7. Compile gate: compile IFC only after formal validation passes.
8. Reporting: write transcript, state, candidate JSON, diagnostics, metrics,
   report, and final IFC.

This keeps the first Agent small enough for TDD while leaving room to add RAG,
fine-tuning, or LangGraph later.

## Live Provider Notes

Mimo should be treated as an Anthropic-compatible provider configured by
environment variables. The implementation should:

- read credential and base URL only at runtime;
- accept model name through CLI or environment;
- provide clear diagnostics when variables are missing;
- redact headers and credential values from artifacts;
- keep fake/file providers as the default verification path.

Official Anthropic documentation at
`https://docs.anthropic.com/en/api/client-sdks` describes Messages API SDKs and
compatibility-layer options. Phase 5 should keep the adapter narrow and avoid
locking the whole Agent to one provider.

## Validation Architecture

Phase 5 requires both deterministic tests and one demo-level E2E acceptance.

Core deterministic checks:

- Agent state serialization and transcript ordering.
- Missing-fact records from schema, validator, and Draft inputs.
- Chinese question rendering and 1-3 batching.
- unknown-answer flow stays Draft and compiles nothing.
- answer merge preserves previous facts.
- provider invalid output is diagnosed.
- formal validation is required before compilation.
- artifact redaction and secret scan.

E2E acceptance:

- start from incomplete Chinese request for a simple room;
- ask questions over at least two turns;
- merge scripted answers;
- produce valid formal BIM JSON 2.0;
- compile IFC2X3;
- reopen/check the IFC;
- write `dataset/processed/agent-demo/simple-room/output.ifc`.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Agent invents missing dimensions | Unknown answers keep Draft; no defaults in Phase 5 |
| Too many questions overwhelm user | hard 1-3 question cap per turn |
| User-facing text exposes schema jargon | tests assert Chinese question wording and forbidden terms |
| Live provider breaks deterministic tests | fake/file providers remain required and default |
| Secret values leak into artifacts | redaction plus repository/artifact scan |
| Demo passes JSON but not IFC | final gate compiles and reopens `output.ifc` |
| Scope drifts into Phase 4 fidelity | plans explicitly defer materials, type reuse, topology, arbitrary geometry |

## Open Decisions

No user-blocking product decisions remain for Phase 5 planning. Implementation
may ask the user only if:

- the live provider credentials fail in a way that cannot be diagnosed locally;
- a product conflict appears between Draft honesty and desired auto-completion;
- a requested class/geometry exceeds the Phase 2.5 generation profile.

---

*Phase: 05-multi-turn-clarification-agent*
