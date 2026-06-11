# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 3 - Text-to-JSON Dataset and Baseline

## Status

- Phase: 3
- Stage: Specification
- State: Ready to specify
- Plans: Not yet planned
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
- Canonical BIM JSON 1.0 to IFC2X3 compiler and bounded file CLI implemented.
- Generated IFC preserves hierarchy, nine supported families, basic
  dimensions, selected properties, and deterministic source identity.
- Atomic output, normalized negative verification, path conflict handling,
  and strict finite-number parsing are covered by tests.
- Phase 2 Nyquist validation, deep code review, security verification, UAT,
  and all eight requirement checks passed.
- Repository regression suite currently passes 142 tests.

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

- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.
- Approved Text-to-JSON training/evaluation sources and their licenses have
  not yet been selected.
- Baseline model/provider choice must remain replaceable and reproducible.

## Next Action

Specify Phase 3 data provenance, deterministic text/JSON pair generation,
structured-output baseline, evaluation metrics, and first end-to-end request.

---
*Last activity: 2026-06-11 - Phase 2 verified complete with 142 passing tests*
