# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 2.5 - BIM JSON 2.0 IFC Semantic Graph

## Status

- Phase: 2.5
- Stage: Wave 2 complete
- State: Ready to execute Wave 3
- Plans: 2 of 6 complete in 5 waves
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
- Official IFC2X3 acquisition is URL-allowlisted, bounded, and SHA-256
  verified before parsing.
- Generated IFC2X3 knowledge covers 980 declarations, 653 entities, 317
  property sets, 6 complex properties, and 1850 simple properties.
- Runtime knowledge loading is immutable, deterministic, and offline.
- Repository regression suite currently passes 171 tests.
- Formal BIM JSON 2.0 and separate Draft Envelope schemas are implemented.
- All 653 IFC2X3 entities have explicit project capability states.
- BIM JSON 1.0 migration preserves known facts in Draft, lists placement
  gaps, and records unknown space coverage without fabrication.
- Repository regression suite currently passes 194 tests.

## Current Decisions

- Phase 1 defines one BIM JSON 1.0 contract and validator.
- Phase 2 implements the minimum IFC2X3 compiler.
- Phase 2.5 establishes the breaking BIM JSON 2.0 IFC semantic graph before
  model training.
- Phase 3 consumes formal BIM JSON 2.0 and does not define a competing shape.
- IFC2X3 EXPRESS and official PSD definitions are the deterministic knowledge
  sources; bSDD is optional enrichment and not the IFC2X3 schema authority.
- The language model emits semantic IFC classes and values, while the compiler
  creates low-level IFC implementation objects.
- Formal documents are complete and compiler-ready; incomplete or unsupported
  content uses a separate Draft Envelope.
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
- Placement, semantic geometry, and relationship endpoint rules are not yet
  implemented in the BIM JSON 2.0 formal validator.
- Existing BIMNet train/test folders leak scene families (`7y3`, `e9z`, and
  `px4`) across file-level splits and must not be reused as model splits.
- IfcOpenShell 0.8.5 late-bound EXPRESS schema cleanup corrupts the Windows
  heap; registry generation isolates parsing in a hard-exit worker.
- The repository `.pytest-tmp` directory can acquire restrictive Windows ACLs;
  verification may need a unique `%TEMP%` basetemp.

## Next Action

Execute `02.5-03-PLAN.md`: parent-relative placement, bounded semantic
geometry, spaces, openings, and void/fill relationship validation.

## Accumulated Context

### Roadmap Evolution

- Phase 2.5 inserted after Phase 2 on 2026-06-11: BIM JSON 1.0 cannot represent
  the spatial ground truth required for Text-to-JSON training.

---
*Last activity: 2026-06-11 - completed Phase 2.5 Plan 02 BIM JSON 2.0 and Draft contracts*
