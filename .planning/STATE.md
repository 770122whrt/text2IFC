---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Ready to execute
last_updated: "2026-07-21T08:23:52.858Z"
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 22
  completed_plans: 17
  percent: 77
---

# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 10 — Window L2 Semantic Fidelity Closure

## Current Position

Phase: 10 (Window L2 Semantic Fidelity Closure) — READY TO PLAN
Plan: 0 of 0

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 10
- Plan: Phase planning not started
- Status: Phase 09.1 complete; Window semantic authoring handoff ready
- Progress: 4 / 8 phases complete
- Requirements: 11 pending, 14 complete, 25 mapped, 0 unmapped
- Last activity: 2026-07-21 — Phase 09.1 completed with four-path real
  DeepSeek UAT and LargeBuilding Type evidence correction

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

- Phase 09.1 separates TypeRecord authority from occurrence-direct facts. The
  41-occurrence LargeBuilding Window Style no longer raises a false
  `PROTOTYPE_TYPE_FACT_CONFLICT`.

- Four real DeepSeek paths now reach Stage 2 and L2, including exact Type name
  without GUID and a one-candidate dimensions confirmation. All remain
  correctly non-publishable because genuine Window semantic authoring is still
  missing.

- Current DeepSeek input/output guards remain 65,536 tokens. The 128k
  experiment remains Phase 13.

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 authoring/identity exactness is deferred without a compatibility
  commitment.

- Automatic similarity/vector-based Prototype authorization is not enabled;
  Phase 9 permits only formal binding or explicit user authorization.

- IFC index/extractor v0.2 now stores referenced Types separately and treats
  duplicate or unreliable Type GlobalIds as diagnostic-only evidence.

## Next Action

Discuss and plan Phase 10 Window L2 semantic authoring for base quantities,
classification, width/height, host/instance and conditional material facts.

---
*Last updated: 2026-07-21 after Phase 09.1 completion*
