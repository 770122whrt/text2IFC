# Milestones

## v1.0: Supported Text2IFC Baseline

**Shipped:** 2026-07-16
**Phases:** 15
**Plans:** 94
**Requirement outcomes:** 71 validated, 4 deferred later-scope, 1 accepted
technical debt

### Delivered

- Versioned BIM JSON 1.0 and IFC2X3-aligned BIM JSON 2.0 contracts with
  explicit Draft/loss semantics.
- Deterministic IFC2X3 compilation, reopen verification, spatial/relationship
  Gates, and official-source IFC knowledge.
- Provenance-linked and scene-family-isolated Text/BIM JSON dataset plus a
  structured-output baseline and evaluation harness.
- Chinese-first multi-turn clarification and role-isolated Design Brief,
  Generator, Repair, Audit, and Observer workflow.
- Hash-bound Gate/Audit routing, component-scoped ChangeSets, multi-storey
  support, and unrelated-component preservation at 1.0.
- Real-provider Easy/Medium/Difficult acceptance with machine 3/3 and human
  3/3 IFC review.

### Final Verification

- 722 focused regression tests passed.
- Static compilation passed.
- 7 representative IFC2X3 files reopened successfully.
- Planning artifact secret scan found 0 issues across 292 files.
- Milestone audit passed with zero orphaned requirements.

### Accepted Boundaries

- `CLI-08` successful final true-human REPL UAT is deferred.
- `GEO-03`, `GEO-04`, `GEO-05`, and `IFC-06` remain later scope.
- Three-case acceptance is not a repeated-run statistical claim.
- Generalized stair collision and double-leaf door semantics remain future
  work.

### Archives

- [Roadmap](milestones/v1.0-ROADMAP.md)
- [Requirements](milestones/v1.0-REQUIREMENTS.md)
- [Audit](milestones/v1.0-MILESTONE-AUDIT.md)

**Git tag:** `v1.0`
