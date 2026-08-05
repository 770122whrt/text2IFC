---
phase: 12-beam-and-column-operations
plan: "02"
subsystem: ifc-index
tags: [ifc2x3, beam, column, sqlite, provenance, tdd]

requires:
  - phase: 12-01
    provides: Hash-bound reserved Beam/Column prompt profiles
provides:
  - Beam and Column occurrence adapters in the default IFC index registry
  - Separate IfcBeamType and IfcColumnType records with source provenance
  - Bounded structural axis, section and representation diagnostics
  - Fail-closed IFC index schema 0.5 cache behavior
affects: [12-03, structural-property-authoring, structural-resolution]

tech-stack:
  added: []
  patterns:
    - Structural geometry evidence is source-bound and diagnostic-only
    - Stale SQLite indexes reject by default and rebuild atomically

key-files:
  created:
    - tests/ifc_repair/test_structural_index.py
  modified:
    - src/text2ifc_ifc_repair/index_models.py
    - src/text2ifc_ifc_repair/index_adapters.py
    - src/text2ifc_ifc_repair/indexer.py
    - src/text2ifc_ifc_repair/index_store.py
    - tests/ifc_repair/test_indexer.py
    - tests/ifc_repair/test_index_store.py

key-decisions:
  - "Structural occurrence indexes expose exact identity, Storey, Type, material and property provenance while geometry and ranking remain diagnostic-only."
  - "The active rebuildable index contract advances from 0.4 to 0.5; opening a stale cache now fails without callers having to opt into the version check."

patterns-established:
  - "Structural adapter pattern: family-specific adapters share bounded evidence extraction without adding family branches to the common index loop."
  - "Authority pattern: measured axis/section facts retain explicit current-IFC provenance plus diagnostic_only authority labels."

requirements-completed: [OPS-03, OPS-04]

duration: 5min
completed: 2026-08-06
---

# Phase 12 Plan 02: Structural Occurrence and Type Index Summary

**Beam and Column occurrences, Types and bounded representation evidence now survive source-bound SQLite indexing without becoming write authority.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-06T00:08:22+08:00
- **Completed:** 2026-08-06T00:13:00+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 7

## Accomplishments

- Registered `BeamIndexAdapter` and `ColumnIndexAdapter` through the existing default adapter registry; the common index build loop remains family-neutral.
- Reopened SQLite indexes reproduce the frozen structural inventories: d7n has 10 Beams and 15 Columns; vvo has 6 Beams and 5 Columns.
- Indexed `IfcBeamType` and `IfcColumnType` separately, including unreferenced explicit Type enumeration, exact source provenance and representation summaries.
- Persisted exact Storey containment and `IfcRelDefinesByType` evidence alongside existing material/property associations.
- Advanced the rebuildable cache contract to IFC Index 0.5 and Extractor 0.5; stale 0.4 caches fail closed by default and a successful rebuild atomically replaces them.

## TDD Gate Evidence

### RED

`50a1a39c` - `test(12-02): add failing structural index tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_index.py -q`
- Result: **4 failed** for the intended missing behavior.
- Failure reasons: zero structural inventory, absent Beam/Column adapters, and no default stale-cache rejection.
- No import, syntax or fixture failure occurred.

### GREEN

`4f461b61` - `feat(12-02): index structural occurrences and types`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_structural_index.py tests\ifc_repair\test_indexer.py tests\ifc_repair\test_index_store.py -q`
- Result: **23 passed in 29.46s**.
- Compile check: `.\.venv\Scripts\python.exe -m compileall -q src\text2ifc_ifc_repair tests\ifc_repair\test_structural_index.py tests\ifc_repair\test_indexer.py tests\ifc_repair\test_index_store.py` passed.
- `git diff --check` passed.

### REFACTOR

No separate refactor commit was needed. The minimal GREEN implementation uses a private shared structural adapter while preserving Beam/Column family semantics and existing adapters unchanged.

## Files Created/Modified

- `tests/ifc_repair/test_structural_index.py` - Real d7n/vvo inventory, diagnostic-only synthetic evidence, SQLite round-trip and stale-cache rebuild tests.
- `src/text2ifc_ifc_repair/index_adapters.py` - Structural adapters and bounded explicit representation evidence extraction.
- `src/text2ifc_ifc_repair/indexer.py` - Structural Type enumeration, exact Type relationship evidence and Extractor 0.5.
- `src/text2ifc_ifc_repair/index_models.py` - IFC Index schema version 0.5.
- `src/text2ifc_ifc_repair/index_store.py` - Default active-version validation on reopen.
- `tests/ifc_repair/test_indexer.py` - Historical family regression expectation for Extractor 0.5.
- `tests/ifc_repair/test_index_store.py` - Historical repository regression expectation for Index 0.5.

## Decisions Made

- Axis and rectangular extrusion measurements are retained as current-IFC diagnostic evidence with explicit provenance; they are not direct mutation or similarity authority.
- Missing or non-unique explicit representation evidence remains `unavailable` with a stable diagnostic instead of being estimated from mesh bounds, names or nearby members.
- Existing Type and Storey relationships are persisted as exact relationship facts, but later deterministic resolution must still establish authorization.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The execution subagent quota became unavailable before RED work began. Per the execute-phase fallback protocol, the plan was completed sequentially in the main context with the same TDD and atomic-commit gates. No implementation scope changed.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

The plan frontmatter traces both OPS-03 and OPS-04, so they are copied into this Summary metadata as required by the execution protocol. Their authoritative project status remains **Pending** until Plan 12-16 independently proves complete Beam/Column creation, strict L0/L1/L2, real DeepSeek UAT and final closure.

## Next Phase Readiness

- Plan 12-03 can extend the generic occurrence-property and typed RAG authority path to the newly indexed structural families.
- No Beam/Column operation is executable yet; no frozen Door/Window policy changed and Phase 13 has not started.

## Self-Check: PASSED

- Created key file exists: `tests/ifc_repair/test_structural_index.py`.
- Structural adapter key file exists: `src/text2ifc_ifc_repair/index_adapters.py`.
- RED and GREEN commits are present in Git history.
- All plan verification and compile/diff checks pass.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
