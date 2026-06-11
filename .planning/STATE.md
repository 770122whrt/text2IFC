# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 2 - Minimum BIM JSON to IFC2X3 Compiler

## Status

- Phase: 2
- Stage: Execution - Wave 3
- State: In progress
- Plans: 4 in 3 waves
- Branch: `main`
- Remote: `https://github.com/770122whrt/text2IFC`

## Completed Foundation

- Official IFC2X3 TC1 EXPRESS schema downloaded.
- All 25 source models identified as IFC2X3.
- IfcOpenShell can open all 25 models.
- Initial JSON-to-IFC round trip executes on three source models.
- Three TDD tests cover storey elevation, wall common properties, and
  door/window dimensions.
- Repository published with Git LFS.
- Durable documentation index and Git publishing guide established.
- BIM JSON 1.0 structural schema, validator, and bounded CLI implemented.
- Global ID uniqueness and storey-reference integrity checks implemented.
- Generated BIM JSON reference and schema drift check implemented.
- All 53 legacy JSON models classified by deterministic migration audit.
- Current migration yield is 0 converted and 53 explicitly rejected because
  required source facts are missing.
- Phase 1 Nyquist validation, deep code review, security verification, and
  requirement coverage checks passed.
- Contract and repository regression suite currently passes 97 tests.

## Current Decisions

- Phase 1 defines one BIM JSON 1.0 contract and validator.
- Phase 2 implements the minimum IFC2X3 compiler.
- Phase 3 implements the Text-to-JSON data pipeline and baseline.
- High-fidelity placement and opening relationships are deferred to Phase 4.
- Phase specifications precede executable implementation plans.
- Implementation plans must use TDD tasks and explicit verification commands.
- Phase 2 geometry APIs receive SI metres while direct IFC attributes remain
  in declared millimetre project units.
- Phase 2 uses dimension-preserving envelopes and deterministic synthetic
  placement; source placement fidelity remains Phase 4.

## Known Risks

- Current JSON structures are informal and inconsistent across scripts.
- Existing round-trip verification checks counts more than semantic fidelity.
- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.

## Next Action

Execute `02-04-PLAN.md`: write and commit RED tests for negative IFC
verification, the file CLI, and complete-fixture acceptance.

---
*Last activity: 2026-06-11 - completed Phase 2 Plan 02-03 with 125 passing tests*
