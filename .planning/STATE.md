# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 10 — Window L2 Semantic Fidelity Closure.

## Current Position

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 10
- Plan: not yet planned
- Status: Phase 9 complete; ready to discuss/plan Phase 10
- Progress: 3 / 7 phases complete
- Requirements: 8 pending, 14 complete, 22 mapped, 0 unmapped
- Last activity: 2026-07-20 — Phase 9 verified with 375 passed, 1 skipped;
  16/16 registered threats closed and code review clean

## Carried Context

- v1.0 shipped and remains archived with 722-test verification.
- Phase 7 supplies the deterministic SQLite index and bounded target context
  for Wall, Door, Window and contextual Space records; vector retrieval remains
  disabled behind an extension seam.
- Phase 8 supplies Evaluation 0.2 with independent mandatory L1/L2 gates,
  evaluator-only benchmark Gold and privacy-safe public projection.
- Phase 9 supplies one public IFC-plus-text API/CLI, versioned RepairIntent,
  resumable clarification, deterministic target resolution, bound unified
  ChangeSet generation, production semantic authority, all-or-nothing apply,
  and crash-recoverable terminal publication.
- The Phase 9 LargeBuilding offline path is intentionally L1 `passed`, L2
  `not_evaluable`, L3 `not_required`, non-publishable and diagnostic-only.
- The Phase 9 real DeepSeek attempt ended truthfully at Stage 1 as
  `provider_failed`; Stage 2 was not reached and no live success is claimed.
- Current DeepSeek input/output guards remain 65,536 tokens. The 128k
  experiment remains Phase 13.

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 authoring/identity exactness is deferred without a compatibility
  commitment.
- Automatic similarity/vector-based Prototype authorization is not enabled;
  Phase 9 permits only formal binding or explicit user authorization.

## Next Action

Discuss and plan Phase 10 Window L2 authoring closure: restore authorized
Psets, quantities, Material, Classification and `IsExternal`, then require the
LargeBuilding Window case to pass both L1 and L2 offline and in live UAT.

---
*Last updated: 2026-07-20 after Phase 9 completion*
