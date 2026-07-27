---
phase: 11-wall-opening-and-door-operations
plan: "04"
status: complete
completed: 2026-07-28
commits:
  - bced20c5
---

# Phase 11 Plan 04 Summary

## Delivered

- Semantic authoring now validates scopes against immutable Registry metadata.
  Unknown scopes and duplicate scope mappings fail closed.
- Door, Opening and Window assignments dispatch to their declared IFC
  occurrence role. Door Psets and Opening quantities were verified in one
  reopened LargeBuilding output.
- Explicit and deterministic occurrence geometry assignments now select
  Window, Door or Opening scope and use the correct `BaseQuantities` mapping.
- Added independent Door L1 authorization for topology, dimensions,
  containment, Type relation and the allowed root footprint.
- Door L2 selects the Door occurrence scope from the active operation
  definition. Required Type, host, Storey and Overall dimensions pass against
  facts re-extracted from the reopened IFC; a wrong width fails the dedicated
  `door.width` check.
- Added family-neutral occurrence comparison schema 0.2 with explicit IFC
  class, scope, role and related Opening identity. Historical Window
  comparison 0.1 remains compatible.
- Generated Type relations are now reported as created roots when newly
  authored and as modified roots only when extending an existing exact Type
  relation.

## Verification

- Focused semantic/evaluation regression: `218 passed`.
- Final Plan 11-04 Window/Door/Opening/benchmark matrix: `86 passed`.
- `compileall` and `git diff --check` passed.
- Real LargeBuilding candidate passed independent L1 and production L2 after
  IFC reopen; no private Ground Truth was used by the production evaluator.

## Deferred to Plan 11-05

- Source-bound Door damage fixtures and multi-model dataset matrix.
- Curated proof packages and independent proof validator integration.
- Complete and clarified real DeepSeek calls plus unsupported-operation early
  rejection evidence.
