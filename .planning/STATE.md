# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Given an IFC file and an explicit user request, produce a
traceable semantic ChangeSet and an L1/L2-validated IFC result.

**Current focus:** Phase 8 — L1/L2 Evaluation Contract.

## Current Position

- Milestone: v1.1 IFC ChangeSet Repair Pipeline
- Phase: 8 (not planned yet)
- Plan: —
- Status: Phase 7 verified; ready for Phase 8 discussion/planning
- Progress: 1 / 7 phases complete
- Requirements: 17 pending, 5 complete, 22 mapped, 0 unmapped
- Last activity: 2026-07-19 — Phase 7 retrieval index and target resolution verified

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

## Accepted Debt / Deferred

- `CLI-08` final true-human REPL acceptance from v1.0 remains carried debt.
- Curved/free-form wall repair is deferred.
- L3 exactness is deferred without a compatibility commitment.

## Next Action

Run `$gsd-discuss-phase 8` to freeze the L1/L2 evaluation contract before
writing Phase 8 plans.

---
*Last updated: 2026-07-19 after completing Phase 7*
