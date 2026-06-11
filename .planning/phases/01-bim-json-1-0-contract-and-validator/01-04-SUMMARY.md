---
phase: 01-bim-json-1-0-contract-and-validator
plan: 04
subsystem: contract-documentation
tags: [json-schema, markdown, drift-check, atomic-write, pytest, tdd]
requires:
  - 01-01
provides:
  - Deterministic BIM JSON 1.0 Markdown reference
  - Schema/reference drift checker
  - Atomic reference generation CLI
affects:
  - dataset-authoring
  - phase-02-ifc-compiler
  - phase-03-text-to-json
  - phase-05-clarification-agent
tech-stack:
  added: []
  patterns:
    - Documentation is rendered from the canonical JSON Schema
    - Generated files are replaced atomically
key-files:
  created:
    - src/text2ifc_contract/reference.py
    - scripts/bim_json/generate_reference.py
    - tests/contract/test_reference.py
    - docs/reference/bim-json-1.0.md
  modified:
    - docs/README.md
key-decisions:
  - "The renderer supports only the schema vocabulary used by BIM JSON 1.0."
  - "Element sections follow the kind order declared in the canonical schema."
  - "Drift checking never writes; generation uses a same-directory atomic replacement."
patterns-established:
  - "Generated references name their source and regeneration command."
  - "Checked-in generated content must exactly equal render_reference output."
requirements-completed: [DOC-01, DOC-02]
duration: 8min
completed: 2026-06-11
---

# Phase 1 Plan 04: Generated Contract Reference Summary

**Schema-derived BIM JSON documentation with deterministic drift enforcement**

## Performance

- **Duration:** 8 minutes
- **Tasks:** 1 TDD feature
- **Files modified:** 5

## Accomplishments

- Generated a durable reference for metadata, hierarchy, storeys, common
  element fields, nine element kinds, dimensions, properties, and constraints.
- Added an exact-content drift check tied directly to the canonical schema.
- Added a local CLI with read-only `--check` mode and atomic regeneration.
- Linked the generated contract from the durable documentation index.

## Task Commits

1. **RED: Generated-reference behavior and drift tests** - `649bb3e`
2. **GREEN: Renderer, CLI, checked reference, and index link** - `1a43a6f`
3. **REFACTOR:** Removed one unused local before the GREEN commit.

## Test Evidence

- RED: `python -m pytest tests/contract/test_reference.py -q` produced
  `8 failed` because the generator, CLI, reference, and index link were absent.
- GREEN: the same command produced `8 passed`.
- Contract regression: `python -m pytest tests/contract -q` produced
  `32 passed`.
- Repository regression: `python -m pytest tests -q` produced `35 passed`.
- `python scripts/bim_json/generate_reference.py --check` reported the
  reference current.
- Compile and whitespace checks passed.

## Files Created/Modified

- `src/text2ifc_contract/reference.py` - deterministic renderer, checker, and
  atomic writer.
- `scripts/bim_json/generate_reference.py` - generation and drift-check CLI.
- `tests/contract/test_reference.py` - content, determinism, drift, index, and
  CLI coverage.
- `docs/reference/bim-json-1.0.md` - generated human contract reference.
- `docs/README.md` - durable reference link.

## Decisions Made

- Traversed only local `#/$defs/` references and rejected any other reference
  form in the renderer.
- Derived kind dimensions and selected properties from the schema's `allOf`
  conditions instead of duplicating them in Python constants.
- Allowed `--output` for isolated generation tests and future release tooling.

## Deviations from Plan

Added the optional `--output` CLI argument so atomic generation can be tested
without rewriting the repository file. Default behavior and `--check` remain
as planned.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Wave 2 is complete.
- Plan 01-03 can use the canonical schema, semantic validator, and readable
  reference while auditing and migrating every legacy JSON artifact.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Generated content exactly matches the canonical schema rendering.
- Drift check, contract tests, and full repository tests pass.
- The documentation index exposes the reference.

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Completed: 2026-06-11*
