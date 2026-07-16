# Project State

## Project Reference

See `.planning/PROJECT.md`.

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements through validated BIM JSON rather than raw STEP generation.

**Current focus:** Planning the milestone after v1.0.

## Status

- Milestone: v1.0 Supported Text2IFC Baseline
- State: shipped and archived on 2026-07-16
- Phases: 15 / 15 complete
- Plans: 94 / 94 complete
- Audit: passed
- Requirement outcomes: 71 validated, 4 deferred later-scope, 1 accepted
  technical debt, 0 orphaned
- Verification: 722 tests passed; compileall passed; 7/7 IFC2X3 files reopened;
  planning secret scan 0/292 findings
- Branch at archival: `codex/workflow-dataset-links`

## Accepted Debt

- `CLI-08`: no final successful true-human REPL acceptance bundle.
- `GEO-03`, `GEO-04`, `GEO-05`, `IFC-06`: future high-fidelity and capability
  expansion.
- Repeated-run statistical reliability, generalized stair collision, and
  double-leaf door semantics remain future candidates.

## Next Action

Run `$gsd-new-milestone` to choose the next version, define fresh requirements,
and create a roadmap beginning with Phase 7. Do not infer that the candidate
scope in ROADMAP is already committed.

---
*Last activity: 2026-07-16 - archived v1.0 after passed milestone audit.*
