---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Ready to execute
last_updated: "2026-07-20T15:53:08.568Z"
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 17
  completed_plans: 15
  percent: 88
---

# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 09.1 — IFC Type Evidence and Prototype Resolution Correction

## Current Position

Phase: 09.1 (IFC Type Evidence and Prototype Resolution Correction) — EXECUTING
Plan: 3 of 4

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 09.1
- Plan: 2 of 4 plans complete; Wave 2 in progress
- Status: TypeRecord index and human-readable Prototype resolution complete
- Progress: 3 / 8 phases complete
- Requirements: 11 pending, 14 complete, 25 mapped, 0 unmapped
- Last activity: 2026-07-20 — Phase 09.1 inserted after the post-Phase 9
  production-evidence diagnosis

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

- The first Phase 9 real DeepSeek attempt ended truthfully at Stage 1 as
  `provider_failed`. After the Stage 1 contract repair, complete-input and
  clarification-feedback UAT paths both reached Stage 2, application and L2;
  both remain non-publishable because the current index misclassifies
  occurrence `Constraints.Level` facts as inherited Window Style facts.

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

Execute Phase 09.1 Plan 03: build Production Evidence from direct TypeRecord
facts and remove occurrence-proxy Type aggregation without weakening L2.

---
*Last updated: 2026-07-20 after Phase 09.1 Plan 01 completion*
