# text2IFC

## What This Is

text2IFC converts Chinese-first natural-language building requirements into a
validated BIM JSON 2.0 semantic model and then deterministically compiles that
model to inspectable IFC2X3. Missing required facts remain Draft and may be
clarified over multiple turns instead of being silently invented.

## Core Value

Produce IFC models that are structurally valid, spatially checkable, and
traceable to explicit user requirements rather than generating fragile IFC
STEP text directly.

## Current State

**v1.0 Supported Text2IFC Baseline shipped on 2026-07-16.**

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

## History

- [v1.0 roadmap](milestones/v1.0-ROADMAP.md)
- [v1.0 requirements](milestones/v1.0-REQUIREMENTS.md)
- [v1.0 milestone audit](milestones/v1.0-MILESTONE-AUDIT.md)
- [milestone register](MILESTONES.md)

---
*Last updated: 2026-07-16 after v1.0 milestone archival*
