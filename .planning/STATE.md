---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: IFC ChangeSet Repair Pipeline
status: Ready to execute
last_updated: "2026-07-23T18:00:00+08:00"
progress:
  total_phases: 10
  completed_phases: 5
  total_plans: 26
  completed_plans: 22
  percent: 50
---

# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 10.1 exact IFC property authoring is planned; Phase
10.2 property retrieval/RAG remains separate and deferred

## Current Position

Phase: 10.1 (Explicit IFC Property Authoring and Validation) — PLANNED
Plan: 0 of 4 executed

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 10.1
- Plan: 4 plans ready in 4 sequential waves
- Status: Ready to execute exact-property contract first
- Progress: 5 / 10 phases complete
- Requirements: 15 pending, 19 complete, 34 mapped, 0 unmapped
- Last activity: 2026-07-23 — split exact property authoring (10.1) from
  property knowledge retrieval/RAG (10.2) and wrote SPEC/CONTEXT/RESEARCH/
  VALIDATION plus four executable plans

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

- Phase 10 upgrades the LargeBuilding Window path to a bound ChangeSet 0.2,
  atomic semantic authoring, Production L1/L2 pass and successful publication.

- Phase 09.1 separates TypeRecord authority from occurrence-direct facts. The
  41-occurrence LargeBuilding Window Style no longer raises a false
  `PROTOTYPE_TYPE_FACT_CONFLICT`.

- Four real DeepSeek paths publish validated IFC results, including exact Type
  name without GUID and a one-candidate dimensions confirmation. All four pass
  Production and private benchmark L1/L2 with no synthetic fallback.

- Current DeepSeek input/output guards remain 65,536 tokens. The 128k
  experiment remains Phase 13.

- Phase 10.1 uses the existing checked-in IFC2X3 official property registry for
  case-sensitive exact lookup only. It does not implement aliases, embeddings,
  vector search or RAG.

- Exact property mutation is limited to the target occurrence. Existing
  authorized Type facts may be inherited, but Phase 10.1 does not modify shared
  Types; an explicit Type-mutation request fails closed and is deferred.

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

Review the three highlighted Phase 10.1 defaults with the user, then execute
plans 10.1-01 through 10.1-04. Phase 10.2 retrieval/RAG begins only after the
exact-property offline and real-Provider Window acceptance is evidenced.

---
*Last updated: 2026-07-23 after Phase 10.1 planning*
