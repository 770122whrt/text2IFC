# text2IFC

## What This Is

text2IFC converts Chinese-first natural-language building requirements into
validated semantic changes and deterministically compiles them to inspectable
IFC2X3. It supports both new-model generation through BIM JSON and the emerging
existing/damaged-IFC repair path through a unified semantic ChangeSet; missing
or ambiguous target facts must be clarified instead of silently invented.

## Core Value

Given an IFC file and an explicit user request, produce a traceable semantic
ChangeSet and an L1/L2-validated IFC result without model-authored STEP text.

## Current State

**v1.0 Supported Text2IFC Baseline shipped on 2026-07-16.**

**v1.1 IFC ChangeSet Repair Pipeline is in implementation; Phases 7 and 8 are
complete.**

The shipped supported-scope chain is:

```text
Chinese natural language
-> Design Brief / clarification state
-> Formal BIM JSON 2.0 or explicit Draft
-> deterministic validation and Gates
-> IFC2X3 compile/reopen
-> Audit, report, and review artifacts
```

The milestone contains 15 phases and 94 plans. Its final current-state
verification passed 722 focused regression tests, static compilation, seven
representative IFC2X3 reopen checks, a zero-finding planning secret scan, and
human review of all three frozen stability cases.

## Current Milestone: v1.1 IFC ChangeSet Repair Pipeline

**Goal:** A user can provide an existing or damaged IFC2X3 file plus a natural-
language modification request, run one program, and receive a validated
semantic ChangeSet, a repaired/modified IFC, and auditable evidence.

**Target features:**

- Deterministic IFC retrieval index and hybrid target resolution using GUID,
  Name/Tag/type aliases, storey, grid/space context, direction and geometry.
- Mandatory L1 geometry/relationship and L2 BIM semantic-fidelity evaluation.
- One public CLI/API orchestration path from IFC + text to ChangeSet + IFC.
- Window semantic-fidelity closure followed by Opening, Door, Beam and Column
  operation expansion.
- Large-IFC bounded context and a separate 128k near-limit experiment.

## Validated Capabilities

- One JSON Schema-backed BIM JSON contract with explicit Draft semantics.
- Official-source IFC2X3 schema/property knowledge and authorized IFC
  extraction with complete loss accounting.
- Scene-family-isolated Text/BIM JSON data and structured-output evaluation.
- Chinese multi-turn clarification, versioned prompts, provider traces, and
  bounded generation/repair routes.
- Gate-authoritative Audit, component-scoped ChangeSets, preservation checks,
  and multi-storey generation within the supported profile.
- Real-provider Easy/Medium/Difficult Text -> BIM JSON -> IFC2X3 cases with
  machine and human acceptance at 3/3.
- Deterministic IFC2X3 retrieval index and explainable target resolution for
  Wall, Door, Window and contextual Space records.
- Evaluation 0.2 with independent mandatory L1/L2 gates, conditional
  Material/Pset semantics, evaluator-only benchmark Gold, and privacy-safe
  public evidence projection.
- LargeBuilding offline acceptance with honest L1-pass/L2-fail diagnostic
  retention and zero Provider calls.

## Accepted Boundaries

- v1.0 does not claim general material, topology, BRep, tessellation,
  furnishing, structural, or MEP generation.
- A final successful true-human REPL acceptance remains technical debt; later
  successful live runs used adaptive/automated drivers.
- Three-case stability is coverage-oriented and is not a repeated-run success
  probability.
- Current stair-wall collision checks are bounded to the documented supported
  geometry subset; double-leaf door style semantics remain future work.

## Constraints

- IFC output remains IFC2X3 until a later milestone explicitly adopts another
  schema.
- JSON Schema is the only BIM JSON structural truth.
- IFC is generated through IfcOpenShell, never by model-authored STEP text.
- Required facts are not silently invented, overwritten, or discarded.
- Dataset training/evaluation splits remain isolated by scene family and
  linked to license/provenance evidence.
- New behavioral work follows TDD and deterministic acceptance Gates.
- L1 and L2 are mandatory repair gates; L3 authoring/identity exactness is
  recorded but excluded from the v1.1 compatibility target.

## Key Decisions

| Decision | Outcome |
|---|---|
| Natural language -> BIM JSON -> IFC | Validated; retained as the architecture |
| IFC2X3-first compiler | Validated against the authorized source set |
| Official schema knowledge before retrieval/model memory | Validated and offline-reproducible |
| Draft plus clarification for missing facts | Validated; no default template in v1.0 |
| Audit subordinate to deterministic Gates | Validated; override attempts block |
| Prompt-only structured generation before fine-tuning | Retained until larger reviewed data proves need |
| Component-scoped ChangeSets for corrections | Validated with preservation rate 1.0 |
| Coverage-based three-case stability | Accepted for v1.0; statistical reliability deferred |
| Hybrid target selectors | GUID, Name/Tag/type, storey, direction, grid/space and geometry contribute evidence; no single human-facing field is the universal key |
| Repair completion levels | L1 geometry/relationship and L2 semantic fidelity are required; L3 authoring exactness is deferred |
| Original IFC in benchmark evaluation | Private ground truth may score L2 after repair but must never enter Provider input |
| 128k context | Deferred until a dedicated near-limit Provider/tokenizer test; current repair default remains 64k input |

## Evolution

This document evolves at phase transitions and milestone boundaries.

After each phase, validated requirements move to completed traceability,
invalidated assumptions move out of scope with reasons, and new decisions are
recorded before implementation drifts. Milestone completion requires a full
review of scope, evidence and deferred L3 exactness.

## History

- [v1.0 roadmap](milestones/v1.0-ROADMAP.md)
- [v1.0 requirements](milestones/v1.0-REQUIREMENTS.md)
- [v1.0 milestone audit](milestones/v1.0-MILESTONE-AUDIT.md)
- [milestone register](MILESTONES.md)

---
*Last updated: 2026-07-20 after Phase 8 completion*
