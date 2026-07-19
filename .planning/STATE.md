# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 9 — General IFC + Text Repair Orchestrator.

## Current Position

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 9
- Plan: 5 plans in 5 sequential waves
- Status: Ready to execute Phase 9
- Progress: 2 / 7 phases complete
- Requirements: 12 pending, 10 complete, 22 mapped, 0 unmapped
- Last activity: 2026-07-20 — Phase 9 planning passed requirement, decision, frontmatter, and Nyquist coverage checks

## Carried Context

- v1.0 shipped and remains archived with 722-test verification.
- One LargeBuilding Window repair has passed real DeepSeek L1 UAT.
- Direct original-vs-repaired comparison found L2 gaps in instance Psets,
  quantities, material/classification and `IsExternal`.
- L1 and L2 are mandatory for v1.1 repair success.
- L3 authoring/identity exactness is recorded but not supported in v1.1.
- GUID, Name/Tag/type, storey, direction, grid/space, relationships and geometry
  are complementary target evidence; `Name` is not a universal key.
- Current DeepSeek input/output guard remains 65,536 tokens; 128k is a later
  near-limit experiment, not a current capability claim.
- Phase 7 indexes Wall, Door, Window, and contextual Space records in SQLite;
  structured retrieval and bounded context are Provider-independent.
- Vector retrieval remains disabled behind an extension interface.
- Phase 8 defines Evaluation 0.2 with mandatory independent L1/L2 gates,
  evaluator-only benchmark Gold, public allowlist projection, and a fail-closed
  legacy Evaluation 0.1 boundary.
- Frozen LargeBuilding offline evidence is intentionally L1 `passed`, L2
  `failed`, L3 `not_required`, non-publishable, and zero-Provider; Window L2
  authoring closure remains Phase 10 work.

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 exactness is deferred without a compatibility commitment.

## Next Action

Execute Phase 9 Plan 09-01: implement the versioned RepairIntent and public
request-understanding contract using TDD, then advance through the five
dependency-ordered plans.

---
*Last updated: 2026-07-20 after planning Phase 9*
