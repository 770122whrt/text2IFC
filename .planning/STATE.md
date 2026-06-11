# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 1 - BIM JSON 1.0 Contract and Validator

## Status

- Phase: 1
- Stage: Planning complete
- State: Ready to execute
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

## Current Decisions

- Phase 1 defines one BIM JSON 1.0 contract and validator.
- Phase 2 implements the minimum IFC2X3 compiler.
- Phase 3 implements the Text-to-JSON data pipeline and baseline.
- High-fidelity placement and opening relationships are deferred to Phase 4.
- Phase specifications precede executable implementation plans.
- Implementation plans must use TDD tasks and explicit verification commands.

## Known Risks

- Current JSON structures are informal and inconsistent across scripts.
- Existing round-trip verification checks counts more than semantic fidelity.
- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.

## Next Action

Execute Phase 1 in wave order from
`.planning/phases/01-bim-json-1-0-contract-and-validator/01-01-PLAN.md`.

---
*Last activity: 2026-06-11 - completed Phase 1 specification, research, and plans*
