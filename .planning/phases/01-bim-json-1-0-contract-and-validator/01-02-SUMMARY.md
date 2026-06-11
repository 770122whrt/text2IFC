---
phase: 01-bim-json-1-0-contract-and-validator
plan: 02
subsystem: contract-validation
tags: [semantic-validation, identity, references, pytest, tdd]
requires:
  - 01-01
provides:
  - Global BIM JSON object ID uniqueness checks
  - Storey-reference integrity checks
  - Deterministic semantic diagnostics behind the structural gate
affects:
  - phase-01-migration
  - phase-02-ifc-compiler
  - phase-05-clarification-agent
tech-stack:
  added: []
  patterns:
    - Structural validation gates semantic validation
    - Semantic issues use the shared ValidationIssue contract
key-files:
  created:
    - tests/contract/test_semantic_validation.py
  modified:
    - src/text2ifc_contract/validation.py
key-decisions:
  - "IDs are globally unique across project, site, building, storeys, and elements."
  - "Duplicate diagnostics point to the later occurrence and identify the first path."
  - "Semantic checks do not run on structurally invalid documents."
patterns-established:
  - "All validation issues are sorted by path, code, and message."
  - "References resolve only against explicitly declared storeys."
requirements-completed: [JSON-02, JSON-03]
duration: 5min
completed: 2026-06-11
---

# Phase 1 Plan 02: BIM JSON Semantic Validation Summary

**Global identity and storey-reference validation with deterministic diagnostics**

## Performance

- **Duration:** 5 minutes
- **Tasks:** 1 TDD feature
- **Files modified:** 2

## Accomplishments

- Enforced global ID uniqueness across hierarchy objects, storeys, and elements.
- Rejected element `storey_id` values that do not name a declared storey.
- Kept semantic checks behind the structural gate so malformed documents do
  not produce speculative reference errors.
- Preserved the input document and returned stable, path-addressable issues.

## Task Commits

1. **RED: Semantic identity and reference tests** - `bc7f97b`
2. **GREEN: Semantic validation implementation** - `a3101fd`
3. **REFACTOR:** Not required; shared sorting was extracted during GREEN.

## Test Evidence

- RED: `python -m pytest tests/contract/test_semantic_validation.py -q`
  produced `6 failed, 2 passed` because semantic checks were absent.
- GREEN: the same command produced `8 passed`.
- Regression: `python -m pytest tests -q` produced `27 passed`.
- `git diff --check` reported no whitespace errors.

## Files Created/Modified

- `tests/contract/test_semantic_validation.py` - duplicate, unresolved
  reference, ordering, gating, and immutability tests.
- `src/text2ifc_contract/validation.py` - structural gate and semantic checks.

## Decisions Made

- Treated IDs as one global namespace because later compiler and agent stages
  need unambiguous object references.
- Reported a duplicate at each later occurrence while retaining the first
  declaration as the canonical diagnostic reference.
- Did not infer, create, or rewrite storeys when a reference is unresolved.

## Deviations from Plan

None. The implementation follows the planned error codes, ordering, and
structural-gating behavior.

## Issues Encountered

One initial RED ordering assertion contradicted the documented
path/code/message sort order. The assertion was corrected while the suite was
still RED and before implementation began.

## User Setup Required

None.

## Next Phase Readiness

- Plan 01-04 can generate human-readable reference material from the canonical
  schema.
- Plan 01-03 can use semantic diagnostics when auditing legacy JSON artifacts.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- The plan-specific and complete repository suites pass.
- Structural errors suppress semantic diagnostics.
- No input mutation, inferred storey, or silent correction was introduced.

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Completed: 2026-06-11*
