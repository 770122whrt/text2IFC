---
phase: 01-bim-json-1-0-contract-and-validator
plan: 03
subsystem: legacy-migration
tags: [migration, audit, provenance, sha256, deterministic-json, pytest, tdd]
requires:
  - 01-01
  - 01-02
provides:
  - Pure legacy-model adapter with explicit rejection semantics
  - Complete deterministic audit of 53 existing JSON models
  - Source immutability and stale-output cleanup guarantees
affects:
  - dataset-quality
  - phase-02-ifc-compiler
  - phase-03-text-to-json
tech-stack:
  added: []
  patterns:
    - Whole-model rejection prevents partial element loss
    - Migration dimensions and properties follow canonical schema rules
    - Fixed-root audit outputs are deterministic and source-hash checked
key-files:
  created:
    - src/text2ifc_contract/migration.py
    - scripts/bim_json/migrate_existing.py
    - tests/contract/test_migration.py
    - dataset/processed/bim-json-1.0/migration-audit.json
    - dataset/processed/bim-json-1.0/migrated/.gitkeep
  modified: []
key-decisions:
  - "Known aliases are normalized, but required geometry is never inferred from names or fallback constants."
  - "Legacy millimetre units and generated IDs are recorded as provenance notes."
  - "Any incomplete supported element rejects the whole model rather than being dropped."
patterns-established:
  - "Audit record IDs and output filenames come from source category and ordinal, never source text."
  - "Each audit run hashes all source files before and after writing."
requirements-completed: [JSON-05]
duration: 18min
completed: 2026-06-11
---

# Phase 1 Plan 03: Legacy Migration Audit Summary

**Deterministic classification of all legacy JSON without invented geometry or silent element loss**

## Performance

- **Duration:** 18 minutes
- **Tasks:** 1 TDD feature plus 1 discovered-shape regression
- **Files modified:** 5

## Accomplishments

- Classified all 53 existing models: 25 basic, 25 enhanced, and 3 round-trip.
- Produced a provenance-rich audit with source selectors, SHA-256 hashes,
  diagnostics, omissions, element counts, and dispositions.
- Added pure conversion coverage proving known aliases and valid explicit
  dimensions can produce schema-valid BIM JSON.
- Preserved every source byte and made repeated audit output byte-identical.

## Migration Result

- **Converted:** 0
- **Rejected:** 53
- **Unclassified:** 0

All existing complete models lack at least one required Phase 1 fact. Basic and
enhanced records lack complete wall and slab dimensions. Round-trip records
contain arbitrary or missing profiles, incomplete slabs or columns, and
dimensionless stairs or stair flights. No fallback dimensions were inserted.

## Rejection Code Histogram

| Code | Count |
|---|---:|
| `MISSING_REQUIRED_DIMENSION` | 9300 |
| `MISSING_STOREY_REFERENCE` | 77 |
| `MISSING_REQUIRED_NAME` | 61 |
| `UNRESOLVED_STOREY_REFERENCE` | 16 |

## Omission Categories

| Category | Models |
|---|---:|
| `materials` | 53 |
| `openings` | 50 |
| `site_geolocation` | 28 |
| `building_metadata` | 28 |
| `storey_metadata` | 25 |
| `material_assignments` | 3 |
| `geometry_profiles` | 3 |

No source model contained a non-empty MEP collection, so no `mep` omission was
emitted in the real audit. Synthetic coverage verifies that MEP omissions are
recorded when present.

## Task Commits

1. **RED: Migration and full-audit behavior tests** - `7e593c0`
2. **GREEN: Pure adapter, fixed-root audit, CLI, and generated report** -
   `affe58f`
3. **REFACTOR:** Not required after the discovered legacy-shape fix.

## Test Evidence

- RED: `python -m pytest tests/contract/test_migration.py -q` produced
  `10 failed` because the migration API and audit did not exist.
- A discovered basic-parser shape test failed before the adapter accepted
  singleton name arrays.
- GREEN: the migration suite produced `11 passed`.
- Repository regression: `python -m pytest tests -q` produced `46 passed`.
- Two real audit runs produced SHA-256
  `30F6A8370828D54A450B20266C0DB8A4D7E7E296E501F733FB04BDAACA628906`.
- Source hash comparison reported `source_changes=0`.

## Files Created/Modified

- `src/text2ifc_contract/migration.py` - pure adapter, schema-derived family
  rules, provenance diagnostics, discovery, hashing, and deterministic writes.
- `scripts/bim_json/migrate_existing.py` - fixed-input migration CLI.
- `tests/contract/test_migration.py` - synthetic conversion and real inventory
  coverage.
- `dataset/processed/bim-json-1.0/migration-audit.json` - complete 53-record
  audit.
- `dataset/processed/bim-json-1.0/migrated/.gitkeep` - stable output root; no
  model currently qualifies for output.

## Decisions Made

- Assigned `MILLIMETRE` only with an explicit
  `UNIT_ASSIGNED_FROM_SOURCE_PIPELINE` provenance note.
- Accepted the basic parser's singleton string arrays as explicit hierarchy
  names while still rejecting empty names.
- Kept all field-level missing-dimension diagnostics in the audit so future
  data repair can identify exact source paths.

## Deviations from Plan

The planned audit anticipated an unknown conversion yield. Execution showed
that no existing full model satisfies the minimum contract. The plan was not
weakened; all 53 models were explicitly rejected and synthetic fixtures prove
the conversion path works when source facts are sufficient.

## Issues Encountered

The first real run showed 75 hierarchy-shape errors because the basic parser
stores hierarchy names as singleton string arrays. A RED regression test was
added, the adapter was extended for that known shape, and the full audit was
regenerated.

## User Setup Required

None.

## Next Phase Readiness

- Phase 1 implementation is complete.
- Phase-level verification must confirm requirement coverage, audit security,
  code quality, and generated artifact consistency before Phase 2 planning.
- The 0/53 conversion result is a concrete input-quality risk for later
  Text-to-JSON dataset work and should inform new data acquisition.

## Self-Check: PASSED

- All 53 records are classified with stable provenance.
- Converted-path tests validate against BIM JSON 1.0.
- Rejected models retain source element counts and actionable diagnostics.
- Repeated audits are byte-identical and source files remain unchanged.

---

*Phase: 01-bim-json-1-0-contract-and-validator*
*Completed: 2026-06-11*
