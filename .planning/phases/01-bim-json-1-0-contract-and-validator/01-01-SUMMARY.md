---
phase: 01-bim-json-1-0-contract-and-validator
plan: 01
subsystem: contract-validation
tags: [json-schema, jsonschema, pytest, cli, tdd]
requires: []
provides:
  - Canonical BIM JSON 1.0 Draft 2020-12 schema
  - Deterministic structural validation diagnostics
  - Bounded local JSON validation CLI
affects:
  - phase-01-semantic-validation
  - phase-01-contract-reference
  - phase-01-migration
  - phase-02-ifc-compiler
tech-stack:
  added: [jsonschema]
  patterns:
    - JSON Schema is the only structural source of truth
    - ValidationIssue exposes code, path, and message
key-files:
  created:
    - schemas/bim-json/1.0/schema.json
    - src/text2ifc_contract/schema.py
    - src/text2ifc_contract/validation.py
    - scripts/bim_json/validate.py
    - tests/contract/test_schema_validation.py
    - tests/contract/fixtures/complete.json
  modified: []
key-decisions:
  - "Element families share one discriminated elements array."
  - "Selected properties live in an explicit optional properties object; family dimensions remain required."
  - "Validation rejects remote $ref values and never imports IfcOpenShell."
patterns-established:
  - "Schema errors are normalized and sorted by path, code, and message."
  - "CLI operational failures use exit 2; contract failures use exit 1."
requirements-completed: [JSON-01, JSON-02, JSON-03, JSON-04]
duration: 8min
completed: 2026-06-11
---

# Phase 1 Plan 01: BIM JSON Structural Validation Summary

**Draft 2020-12 BIM JSON contract with deterministic field diagnostics and a bounded local validation CLI**

## Performance

- **Duration:** 8 minutes
- **Tasks:** 1 TDD feature
- **Files modified:** 8

## Accomplishments

- Defined `bim-json/1.0` for IFC2X3, millimetres, hierarchy, storeys, and all
  nine supported element families.
- Added immutable `ValidationIssue(code, path, message)` results with stable
  required/type/enum/range/unsupported-field codes.
- Added a UTF-8 CLI with 10 MiB input and 1000-error output limits.
- Kept validation independent from IfcOpenShell and remote schema resolution.

## Task Commits

1. **RED: Contract behavior tests and complete fixture** - `46b5574`
2. **GREEN: Schema, validator, and CLI** - `a4921cd`
3. **REFACTOR:** Not required; the minimal implementation remained clear.

## Test Evidence

- RED: `python -m pytest tests/contract/test_schema_validation.py -q`
  produced `16 failed` because the contract package and CLI did not exist.
- GREEN: the same command produced `16 passed`.
- Regression: `python -m pytest tests -q` produced `19 passed`.
- `python -m compileall -q src/text2ifc_contract scripts/bim_json` passed.
- The valid CLI fixture returned `{"errors": [], "valid": true}`.

## Files Created/Modified

- `schemas/bim-json/1.0/schema.json` - canonical machine contract.
- `src/text2ifc_contract/schema.py` - local-only schema loader and schema check.
- `src/text2ifc_contract/validation.py` - structural validator and diagnostics.
- `scripts/bim_json/validate.py` - file validation CLI and resource bounds.
- `tests/contract/test_schema_validation.py` - 16 contract and CLI tests.
- `tests/contract/fixtures/complete.json` - all-family valid example.
- `pyproject.toml` - package metadata and pytest import paths.

## Decisions Made

- Used conditional family constraints within one element schema instead of
  maintaining nine separate Python models.
- Kept `properties` optional because the selected IFC common properties are
  not universally available, while dimensions required by each family remain
  mandatory.
- Returned one diagnostic per unexpected field rather than a combined
  `additionalProperties` message so future agents can correct fields directly.

## Deviations from Plan

None. The implementation follows the planned API, limits, schema version, and
diagnostic codes.

## Issues Encountered

The initial source scan command contained a malformed regular expression. It
was replaced by separate literal checks and did not affect implementation.

## User Setup Required

None.

## Next Phase Readiness

- Plan 01-02 can add global ID uniqueness and storey-reference checks behind
  the structural gate.
- Plan 01-04 can render documentation directly from the checked schema.

## Self-Check: PASSED

- All listed files exist.
- RED and GREEN commits exist in order.
- Contract tests and full repository tests pass.
- No unresolved deviation or user setup remains.

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Completed: 2026-06-11*
