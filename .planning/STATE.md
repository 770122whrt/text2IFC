# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 3 execution - Text-to-JSON Dataset and Baseline

## Status

- Phase: 3
- Stage: Executing
- State: Phase 3 Wave 2.5 complete; Wave 3 ready
- Plans: Phase 3 planned, 3 of 7 plans complete
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
- BIM JSON 2.0 validates bounded parent-relative placement and derives
  deterministic world transforms without mutating source documents.
- Formal geometry supports bounded rectangle and closed-polygon extrusions;
  unsupported geometry remains explicit Draft/loss content.
- `IfcSpace`, `IfcOpeningElement`, `IfcRelVoidsElement`, and
  `IfcRelFillsElement` are covered by the complete semantic fixture.
- Repository regression suite currently passes 219 tests.
- Authorized IFC2X3 files now extract deterministically into formal BIM JSON
  2.0 or a loss-explicit Draft Envelope.
- Exact `IfcWallStandardCase`, source GlobalIds, local placement, extrusion
  position, properties, and void/fill endpoints are preserved.
- Independent represented-plus-reported inventories balance for hxp, i5n,
  and vt2_1 representative files.
- Repository regression suite currently passes 231 tests.
- Formal BIM JSON 2.0 now compiles to schema-valid IFC2X3 with exact initial
  architectural profile classes and no proxy substitution.
- Exact `IfcWallStandardCase` receives the IFC2X3-required generated material
  layer usage while retaining its source semantic class.
- Parent-relative placement, rectangle/polygon extrusion, optional
  representation-local position, typed properties, and void/fill relations
  survive reopened verification.
- BIM JSON 1.0 compiler behavior remains compatible.
- Repository regression suite currently passes 238 tests.
- All 25 authorized BIMNet IFC2X3 files have hash-addressed provenance and
  deterministic represented-plus-reported extraction accounting.
- The 25 files map to 19 Matterport scene families; no Phase 3 split has been
  assigned.
- Phase 3 now has a deterministic BIMNet scene-family split manifest:
  13 train families / 17 files, 3 validation families / 5 files, and 3 test
  families / 3 files.
- The split builder rejects missing dataset/training authorization, disabled
  training eligibility, missing SHA-256 values, non-IFC2X3 records, and
  mutated family leakage before downstream dataset generation.
- Phase 3 Draft triage now preserves all 25 BIMNet Draft records, all 8,280
  original loss records, and per-record sidecars split by train/validation/test.
- Current formal gold target count is 0. All 25 Draft partial documents fail
  `validate_v2_document` because of missing representations, non-rectangular
  `IfcWallStandardCase` profiles, invalid IFC attribute/property value types,
  and non-generatable classes.
- Inserted Wave 2.5 resolves the zero-formal blocker with conservative
  supported-scope projection. Phase 3 now has 25 formal targets, 0
  `draft_clarification` records, and 5,325 projection omissions retained in
  sidecars.
- Generated BIM JSON 2.0 and IFC2X3 generation-profile references are
  drift-checked from canonical schemas and registries.
- Deep code review fixed three Formal/typed-identity gaps through recorded
  RED/GREEN commits.
- Phase 2.5 security verification closes all 23 threats with none open.
- All 11 Phase 2.5 requirements are verified.
- Repository regression suite currently passes 248 tests.

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
- `Representation.position` is geometry-local and independent from product
  `ObjectPlacement`; missing local position is compiler-derived from the
  semantic extrusion direction.
- Exact `IfcWallStandardCase` requires a compiler-generated anonymous
  `IfcMaterialLayerSetUsage` under IFC2X3. This is low-level schema
  bookkeeping, not a claim about source material composition.
- Phase 3 starts with data truth, not model tuning: scene-family splitting,
  Draft triage, formal supported-scope gold targets, text pairs, evaluation,
  baseline, then E2E demo.
- A Draft `partial_document` can become a Phase 3 formal target only when it
  validates as BIM JSON 2.0 and every omitted source fact remains in a sidecar.
- Structured-output baseline outputs formal BIM JSON 2.0 and forbids raw IFC
  STEP text or low-level compiler entities.
- RAG, fine-tuning, and runtime clarification are decided after baseline
  metrics; Phase 3 only produces the decision report and labeled Draft data.

## Known Risks

- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.
- Baseline model/provider choice must remain replaceable and reproducible.
- All 25 extraction labels are currently Drafts because material, type,
  connection, and complex-geometry losses are explicit. Phase 3 must define
  how Formal training targets are selected or completed.
- Projection removes invalid formal facts and records omissions, but it reduces
  IFC source fidelity. Phase 4 still owns high-fidelity material/type/topology
  and complex-geometry recovery.
- Existing BIMNet train/test folders leak scene families (`7y3`, `e9z`, and
  `px4`) across file-level splits and must not be reused as model splits;
  downstream Phase 3 code must consume `dataset/splits/bimnet-scene-splits.json`.
- IfcOpenShell 0.8.5 late-bound EXPRESS schema cleanup corrupts the Windows
  heap; registry generation isolates parsing in a hard-exit worker.
- The repository `.pytest-tmp` directory can acquire restrictive Windows ACLs;
  verification may need a unique `%TEMP%` basetemp.

## Next Action

Resolve the Phase 3 zero-formal-gold decision before Wave 3:

Execute Phase 3 Wave 3 (`03-03-PLAN.md`): generate deterministic
provenance-linked Text/JSON pairs from formal targets without mentioning
sidecar-only omissions as formal facts.

## Accumulated Context

### Roadmap Evolution

- Phase 2.5 inserted after Phase 2 on 2026-06-11: BIM JSON 1.0 cannot represent
  the spatial ground truth required for Text-to-JSON training.
- Phase 3 specified and planned on 2026-06-14 with six waves: split,
  gold-set construction, pair generation, evaluation harness, structured-output
  baseline, and E2E/decision report.
- Phase 3 Wave 1 completed on 2026-06-14 with RED/GREEN commits `687cebe` and
  `9576753`; focused split tests, split drift check, and full regression passed.
- Phase 3 Wave 2 completed on 2026-06-14 with RED/GREEN commits `b186531` and
  `f201553`; all 25 records are triaged as `draft_clarification`, with zero
  formal gold targets.
- Phase 3 Wave 2.5 inserted on 2026-06-14 after GSD SDK was unavailable in
  this runtime. The insertion resolves the zero-formal-gold finding by adding a
  no-fabrication supported-scope projection before pair generation.
- Phase 3 Wave 2.5 completed on 2026-06-14 with RED/GREEN commits `1026482`,
  `1181217`, `6f3f76f`, and `f01220a`; all 25 formal targets validate.

---
*Last activity: 2026-06-14 - completed Phase 3 Wave 2.5 projection*
