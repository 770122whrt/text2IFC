# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 2.5 - BIM JSON 1.1 Spatial Ground Truth

## Status

- Phase: 2.5
- Stage: Discovery complete
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
- A 35-file IFC gap audit quantified placement, space, relationship, material,
  type, geometry, and product-class information absent from BIM JSON 1.0.
- The user confirmed Matterport3D/BIMNet authorization for local training.

## Current Decisions

- Phase 1 defines one BIM JSON 1.0 contract and validator.
- Phase 2 implements the minimum IFC2X3 compiler.
- Phase 2.5 establishes BIM JSON 1.1 spatial ground truth before model training.
- Phase 3 consumes BIM JSON 1.1 and does not define a competing data shape.
- Placement, spaces, and opening/filling relationships move to Phase 2.5.
- Materials, type reuse, complex geometry, connection topology, and broader
  product classes remain Phase 4.
- Phase specifications precede executable implementation plans.
- Implementation plans must use TDD tasks and explicit verification commands.
- Phase 2 geometry APIs receive SI metres while direct IFC attributes remain
  in declared millimetre project units.
- Phase 2 uses dimension-preserving envelopes and deterministic synthetic
  placement; Phase 2.5 adds source placement without changing Phase 2 history.
- IFC-to-BIM-JSON extraction is an offline dataset-label construction path,
  not part of runtime Natural Language to IFC inference.
- BIMNet dataset splits are grouped by Matterport scene family before text
  generation; buildingSMART data remains a separate cross-schema track.

## Known Risks

- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.
- Baseline model/provider choice must remain replaceable and reproducible.
- BIM JSON 1.1 field semantics and supported extraction-loss taxonomy are not
  yet locked.
- Existing BIMNet train/test folders leak scene families (`7y3`, `e9z`, and
  `px4`) across file-level splits and must not be reused as model splits.

## Next Action

Run Phase 2.5 specification to lock placement, spaces, openings/fills,
IFC extraction, loss reporting, migration, and compiler compatibility.

## Accumulated Context

### Roadmap Evolution

- Phase 2.5 inserted after Phase 2 on 2026-06-11: BIM JSON 1.0 cannot represent
  the spatial ground truth required for Text-to-JSON training.

---
*Last activity: 2026-06-11 - inserted Phase 2.5 after a 35-file IFC gap audit*
