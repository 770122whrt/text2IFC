---
phase: 12-beam-and-column-operations
plan: "07"
subsystem: beam-operation
tags: [ifc2x3, beam, registry, storey, resolution, application, tdd]

requires:
  - phase: 12-01
    provides: Frozen beam.add prompt profile
  - phase: 12-02
    provides: Structural occurrence and Type index
  - phase: 12-05
    provides: Straight rectangular member geometry
  - phase: 12-06
    provides: Structural Type and semantic binding
provides:
  - Default-registry add_beam operation through the common lifecycle
  - Storey target indexing and Storey-local exact Beam-axis reference resolution
  - Canonical structural scopes in current Phase 12 schemas
  - Reopened contained and typed Beam application proof
affects: [12-08, 12-09, 12-10, 12-11, 12-12]

tech-stack:
  added: []
  patterns:
    - OperationDefinition metadata drives request, resolution, audit, apply and semantics
    - Existing exact member-axis references authorize measured Storey-local endpoints only after unique identity resolution

key-files:
  created:
    - src/text2ifc_ifc_repair/structural_resolution.py
    - src/text2ifc_ifc_repair/operations/beam.py
    - tests/ifc_repair/test_beam_resolution.py
    - tests/ifc_repair/test_beam_application.py
  modified:
    - src/text2ifc_ifc_repair/operations/__init__.py
    - src/text2ifc_ifc_repair/index_adapters.py
    - src/text2ifc_ifc_repair/indexer.py
    - schemas/agent/ifc-repair-intent-0.5.schema.json
    - schemas/agent/ifc-repair-intent-body-0.5.schema.json
    - schemas/agent/ifc-repair-changeset-0.4.schema.json
    - schemas/agent/ifc-repair-semantic-manifest-0.3.schema.json
    - schemas/agent/ifc-occurrence-comparison-0.2.schema.json

key-decisions:
  - "Storey identity is indexed as a public structural placement target; raw IFC placement nodes remain compiler-owned."
  - "Exact member reference is resolved through a strict TargetQuery and converted to Storey-local center-axis points; ambiguous references clarify."
  - "Beam omission still generates one dedicated deterministic IfcBeamType and never selects nearby Types."

patterns-established:
  - "Latest Phase 12 schemas declare beam_occurrence and column_occurrence; historical schema versions remain unchanged."
  - "Existing and in-batch same-axis overlap is rejected before occurrence creation."

requirements-completed: [OPS-03]

duration: 14min
completed: 2026-08-06
---

# Phase 12 Plan 07: Registered Beam Operation Summary

**`add_beam` is now a default-registry operation that resolves, audits, applies and reopens one exact Storey-local horizontal rectangular Beam without common Beam dispatch branches.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-06T01:10:33+08:00
- **Completed:** 2026-08-06T01:24:04+08:00
- **Tasks:** 1 TDD feature
- **Files modified:** 15 including two RED test files

## Accomplishments

- Registered `add_beam` with `beam.add`, strict target/intent/canonical schemas, semantic role, deterministic Type factory and physical-only capability metadata.
- Added common structural resolution for explicit center axes and exact existing Beam-axis references.
- Indexed `IfcBuildingStorey` identities and robust Storey-local structural axes from the complete placement chain.
- Grouped missing endpoints and returned stable capability codes for inclined, curved/Grid, non-rectangular, scalar-extent, rotated and analysis requests.
- Published one reopened IFC2X3 Beam with one exact Storey containment and one generated `IfcBeamType` relation.
- Kept omitted material/Psets absent and verified common apply/provider source has no Beam-specific dispatcher branch.
- Rejected existing and in-batch same-axis overlap before new `IfcRoot` creation.

## TDD Gate Evidence

### RED

`6ce0fd1b` - `test(12-07): add failing beam operation tests`

- Command: `.\.venv\Scripts\python.exe -m pytest tests\ifc_repair\test_beam_resolution.py tests\ifc_repair\test_beam_application.py -q`
- Result: collection failed because the planned registered Beam module did not exist.

### GREEN

`27150930` - `feat(12-07): register deterministic beam operation`

- Plan verification: **5 passed in 10.44s**.
- Registry/profile/index/schema regressions: **40 passed in 16.77s**.
- Request/provider/general changeset/audit plus structural primitive regressions: **75 passed in 22.52s**.
- Focused compileall passed.
- `git diff --check` passed.

### REFACTOR

Beam-specific registration delegates geometry, Type binding and common resolution to shared structural modules ready for Plan 12-08; no common orchestration conditional was added.

## Deviations from Plan

### Auto-added: Storey target indexing and current structural scope enums

- **Found during:** real-index resolution and bound application GREEN.
- **Issue:** indexer 0.5 did not index `IfcBuildingStorey`, so the frozen Storey target could never resolve. Current schemas also omitted `beam_occurrence`/`column_occurrence`, so a canonical bound Beam assignment failed before audit.
- **Fix:** added the minimal Storey public adapter, Storey-local axis evidence, bumped extractor 0.6 and extended only the latest Phase 12 schema enums.
- **Why required:** without these two contract links the registered operation could not enter the existing common lifecycle. Storey policy and LLM-visible low-level placement exclusions remain unchanged.

## Issues Encountered

- Historical Wave-1 and Wave-2 tests still asserted that Beam was unregistered and extractor was exactly 0.5. They were updated to the current wave state; all other assertions remain intact.

## User Setup Required

None - no external service configuration required.

## Requirement Tracking Note

Plan 12-07 supplies the registered OPS-03 operation, but authoritative OPS-03 remains **Pending** until strict L0/L1/L2, real DeepSeek UAT and independent Plan 12-16 closure pass. OPS-04 remains unimplemented until Plan 12-08.

## Next Phase Readiness

- Plan 12-08 can reuse the family-neutral resolver and shared member primitive to register `add_column`.
- `add_column` is intentionally still absent from the default registry; Phase 13 has not started.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Default registry reopens one correct Beam with exact Type and Storey cardinality.
- Clarification and unsupported paths publish nothing.
- No `add_beam` or `IfcBeam` branch exists in common apply/provider orchestration.

---
*Phase: 12-beam-and-column-operations*
*Completed: 2026-08-06*
