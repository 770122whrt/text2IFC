# Retrospective

## Milestone: v1.0 - Supported Text2IFC Baseline

**Shipped:** 2026-07-16
**Phases:** 15
**Plans:** 94

### What Was Built

An evidence-linked Chinese Text2IFC chain from natural language and
clarification through BIM JSON 2.0, deterministic IFC2X3 compilation, Gates,
Audit, generated reports, and human-inspectable IFC artifacts.

### What Worked

- JSON Schema as the single structural truth prevented Agent/compiler drift.
- Explicit Draft and loss sidecars kept missing or unsupported facts visible.
- TDD and deterministic Gates exposed spatial errors that schema/reopen alone
  could not detect.
- Retaining failed live runs made prompt, routing, and geometry improvements
  evidence-based.
- Component-scoped ChangeSets reduced regressions in already-passing building
  components.

### What Was Inefficient

- Historical phases did not consistently create final `VERIFICATION.md`, so
  Phase 6.7 had to backfill milestone evidence.
- Full-document model regeneration repeatedly damaged unrelated components
  before scoped ChangeSets were introduced.
- Requirement counts drifted between 59, 68, and the true 76 unique IDs.
- Automated/adaptive UAT and true-human REPL UAT were not named distinctly
  enough in early acceptance records.

### Patterns Established

- Separate semantic Agent decisions from deterministic acceptance authority.
- Bind candidate, expected facts, Gate evidence, Audit, and route decisions by
  identity/hash.
- Record every live failure as immutable evidence before changing prompts.
- Treat coverage acceptance and statistical reliability as separate metrics.

### Key Lessons

- IFC reopen success is necessary but not evidence of correct geometry.
- Prompt examples help class coverage, but capability registries and generic
  Gates are required to scale beyond one component at a time.
- Human visual review remains valuable after deterministic checks, especially
  for spatial intent and viewer-specific presentation issues.
- Milestone verification should be written during each phase rather than
  reconstructed at release time.

## Cross-Milestone Trends

| Milestone | Phases | Plans | Current regression | Accepted debt |
|---|---:|---:|---:|---:|
| v1.0 | 15 | 94 | 722 passed | 5 requirements |
