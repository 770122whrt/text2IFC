# Text-to-JSON RAG, Fine-tune, and Agent Decision

**Date:** 2026-06-14

## Decision

Do not start RAG, fine-tuning, or the multi-turn clarification Agent inside
Phase 3.

Phase 3 established the clean data path, structured-output boundary,
evaluation harness, and one E2E demo. The only measured baseline run is the
fake target-echo smoke run, so it proves pipeline correctness rather than real
model quality.

## Evidence

| evidence | result |
| --- | ---: |
| authorized BIMNet IFC2X3 files | 25 |
| formal BIM JSON 2.0 targets | 25 |
| Text/JSON pairs | 100 |
| validation fake baseline records | 20 |
| validation fake accepted predictions | 20 |
| validation fake invalid predictions | 0 |
| validation fake semantic_valid_rate | 1.00 |
| E2E demo compile/reopen | success |

The fake target-echo result is intentionally perfect and should not be used to
rank model approaches.

## Routing Rules

Future baseline errors should be routed by observed failure type:

| observed error | next owner |
| --- | --- |
| wrong IFC class, property name, attribute type, or relationship endpoint | RAG experiment over IFC2X3 class/property/relationship knowledge |
| good schema but poor coverage across paraphrases or styles | Phase 6 data expansion and fine-tuning comparison |
| missing required spatial facts or dimensions in user text | Phase 5 multi-turn clarification Agent |
| material, type reuse, connection topology, or complex geometry missing from target | Phase 4 high-fidelity IFC round trip |
| compiler rejects a valid formal target | immediate compiler/validator bug backlog |
| model emits raw IFC, STEP, or low-level IFC helper objects | prompt/provider boundary bug |

## RAG Recommendation

RAG is not justified before a real no-RAG baseline produces measured errors.

Prepare RAG only after file or live-provider runs show recurring knowledge
failures such as:

- class confusion between related IFC products;
- standard property-set/property name mistakes;
- invalid relationship endpoint attributes;
- repeated use of unsupported or extract-only classes.

The retrieval corpus should start from project-local generated IFC2X3
knowledge and capability files, not from unconstrained web text.

## Fine-tuning Recommendation

Fine-tuning remains Phase 6 work.

The current 100-pair dataset is useful for baseline evaluation and smoke
training experiments, but it is too small to claim deployable model quality.
Before fine-tuning, expand data with license-reviewed sources and preserve the
same scene-family or source-family split discipline.

## Multi-turn Agent Recommendation

The multi-turn Agent belongs in Phase 5.

Phase 3 formal predictions require complete BIM JSON 2.0. If a user request is
missing required placement, dimensions, storey membership, or relationships,
the system must ask targeted questions rather than invent values.

## Phase 4 Recommendation

Phase 4 should address source-fidelity gaps that are intentionally outside
Phase 3:

- materials and material layer sets from source data;
- type reuse;
- broader connection topology;
- arbitrary profiles, BReps, tessellations, and mapped geometry;
- broader product classes beyond the initial architectural generation profile.

## Next Step

The most honest next step is Phase 5 if the product priority is interactive
natural-language completion, or a Phase 6 provider/file-replay run if the
priority is measuring real model quality before Agent work.
