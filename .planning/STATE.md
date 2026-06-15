# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 4 Wave 1 fidelity inventory and metric harness

## Status

- Phase: 4
- Stage: In progress
- State: Phase 4 Wave 0 generated-IFC correctness gate complete; Wave 1 is next
- Plans: Phase 4 planned, 1 of 7 plans complete
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
- Phase 3 now has 100 deterministic Text-to-BIM-JSON pair records generated
  from 25 formal targets: 68 train, 20 validation, and 12 test records across
  concise, enumerated, spatial, and property-focused styles.
- Phase 3 now has a provider-independent evaluation harness with parse,
  schema, semantic, class, property, relationship, placement, geometry,
  compile, reopen, and split/source error-bucket metrics.
- The deterministic evaluation fixture contains 4 records: parse success 0.75,
  schema valid 0.50, semantic valid 0.25, and one compile/reopen-checked
  valid prediction with both rates at 1.00.
- Phase 3 now has a structured-output baseline runner with fake/file provider
  modes, a prompt contract forbidding raw IFC/STEP and low-level IFC helper
  entities, raw/parsed prediction separation, Draft rejection, diagnostics, and
  evaluator integration.
- The validation fake baseline smoke run produced 20 accepted formal
  predictions, 0 invalid predictions, and 1.00 parse/schema/semantic validity.
- Phase 3 E2E demo selected validation spatial record
  `bimnet-ifc2x3-i5n:spatial:09fcea3d6d138620`, validated the predicted BIM
  JSON 2.0, compiled IFC2X3, and reopened with no compiler issues.
- Phase 3 summary and RAG/fine-tune/Agent decision reports are written under
  `docs/architecture/`.
- Phase 5 is specified and planned as a Chinese-first multi-turn clarification
  Agent with a final simple-room IFC acceptance artifact.
- Phase 5 Wave 1 implemented deterministic Agent state primitives:
  original-request preservation, transcript turns, missing facts, accepted
  facts, candidate document storage, deterministic JSON serialization, and
  metadata redaction.
- Phase 5 Wave 2 implemented missing-fact question planning: validator and
  Draft diagnostics normalize into open Agent missing facts, rank the simple
  room-critical gaps first, and return at most three Chinese user-facing
  questions per turn.
- Phase 5 Wave 3 implemented answer parsing, transcript-preserving answer
  merge, unknown-answer Draft behavior, explicit correction facts, and
  validation-gated `formal_ready` session transitions.
- Phase 5 Wave 4 implemented fake/file Agent providers, provider JSON
  diagnostics, redacted Mimo runtime config checks, optional live Mimo adapter,
  and raw IFC/STEP plus low-level helper output guardrails.
- Phase 5 Wave 5 implemented the scripted Chinese clarification demo and wrote
  `dataset/processed/agent-demo/simple-room/output.ifc`, a reopenable IFC2X3
  file tracked through Git LFS.
- Phase 5 Wave 6 completed final verification: 30 Agent tests passed, full
  regression passed 311 tests, compileall passed, Phase 3 E2E regression
  passed, IFC2X3 registry check passed, and Agent artifact secret scan reported
  zero findings.
- Generated BIM JSON 2.0 and IFC2X3 generation-profile references are
  drift-checked from canonical schemas and registries.
- Deep code review fixed three Formal/typed-identity gaps through recorded
  RED/GREEN commits.
- Phase 2.5 security verification closes all 23 threats with none open.
- All 11 Phase 2.5 requirements are verified.
- Phase 3 final verification passes 281 tests plus split, gold, pair,
  evaluation, E2E, registry, accounting, and compileall gates.
- Phase 4 is specified and planned with Wave 0 as a generated-IFC correctness
  gate before high-fidelity source round-trip expansion.
- Wave 0 requires `simple-room-fixed` and `two-room-suite` to pass automated
  parse, BIM JSON validation, compile, reopen, spatial topology, attribute,
  relationship, IFC-structure, metrics, report, and artifact secret-scan gates.
- Phase 4 planning adds quantitative experiment records so prompt/provider,
  Agent, schema, compiler, and fidelity changes can be evaluated by error
  classes and metrics rather than visual inspection alone.
- Phase 4 Wave 0 now rejects the known disconnected live simple-room IFC with
  stable `WALL_ORIENTATION_MISMATCH` and `ROOM_ENCLOSURE_OPEN` diagnostics.
- Phase 4 Wave 0 generated `simple-room-fixed` and `two-room-suite` audit
  artifacts under `dataset/processed/agent-demo/geometry-gate/`; both cases
  pass parse, BIM JSON validation, compile/reopen, geometry, attributes,
  relationships, IFC structure, and artifact secret-scan gates.
- `mimo-bim-json-v3.md` records the rectangle profile center-origin and wall
  orientation rules learned from the live geometry failure.

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
- Generated IFC correctness now precedes Phase 4 high-fidelity source work:
  text-json-ifc demos must prove spatial relationships, content, attributes,
  relationships, and IFC structure under automated checks.
- Prompt/provider iterations for geometry-sensitive generation are durable
  artifacts and must record metrics, repair iterations, and failure classes.
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
- Phase 5 asks 1-3 Chinese clarification questions per turn, keeps unknown
  required facts as Draft, and compiles IFC only after formal BIM JSON 2.0
  validation passes.
- The final Phase 5 acceptance artifact is
  `dataset/processed/agent-demo/simple-room/output.ifc`.
- Live Mimo provider work is optional smoke-test behavior behind environment
  variables; fake/file providers remain required for deterministic tests.
- Agent state is independent from BIM JSON structure; it can hold candidate
  BIM JSON as plain JSON but does not define a second BIM JSON model.
- Question planning never fills missing facts and avoids low-level IFC helper
  terms in user-facing text.
- Unknown user answers keep Agent state as Draft. Invalid candidates produce
  new open missing facts rather than defaults.
- Provider tests remain deterministic without network or credentials. Mimo live
  smoke is optional; config checks report env var names only.
- The simple-room demo reaches `formal_ready`, validates BIM JSON 2.0, asks
  three Chinese clarification questions, compiles IFC, and records transcript,
  state, candidate, diagnostics, metrics, report, and IFC artifacts.

## Known Risks

- Existing source files include text encoding problems.
- Project-local dependency handling is not yet standardized for new machines.
- Baseline model/provider choice must remain replaceable and reproducible.
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

Execute Phase 4 Wave 1: Fidelity inventory and metric harness. Phase 6 remains
deferred until Phase 4 and Phase 5 are both complete.

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
- Phase 3 Wave 3 completed on 2026-06-14 with RED/GREEN commits `faeec4a` and
  `9dac1de`; 100 deterministic split-aware pair records were generated.
- Phase 3 Wave 4 completed on 2026-06-14 with RED/GREEN commits `ed7719a` and
  `bcd6c12`; the provider-independent evaluation harness and fixture reports
  passed focused checks and full regression.
- Phase 3 Wave 5 completed on 2026-06-14 with RED/GREEN commits `aaf46e4` and
  `d06693f`; the structured-output fake/file baseline runner produced a
  validation fake smoke run and passed full regression.
- Phase 3 Wave 6 completed on 2026-06-14 with RED/GREEN commits `f1d5bcf` and
  `8cba218`; stabilization commit `0cfcb83` kept check commands clean, and the
  final gates passed.
- Phase 5 was specified and planned on 2026-06-15 with six waves: Agent state,
  missing-fact questions, answer merge, provider/Mimo adapter, simple-room
  Agent demo to IFC, and final verification/summary.
- Phase 5 Wave 1 completed on 2026-06-15 with RED commit `c53712e` and GREEN
  commit `d5ca58a`; `tests/agent/test_agent_state.py` passed and the
  `tests/contract_v2 tests/compiler` regression slice passed.
- Phase 5 Wave 2 completed on 2026-06-15 with RED commit `ba69e37` and GREEN
  commit `0b9fc84`; `tests/agent/test_question_planner.py` and
  `tests/agent` passed.
- Phase 5 Wave 3 completed on 2026-06-15 with RED commit `114e735` and GREEN
  commit `97fce76`; `tests/agent/test_answer_merge.py` and `tests/agent`
  passed.
- Phase 5 Wave 4 completed on 2026-06-15 with RED commit `0d14a22` and GREEN
  commit `e521c68`; provider tests, `run_mimo_smoke.py --check-config`, and
  `tests/agent` passed.
- Phase 5 Wave 5 completed on 2026-06-15 with RED commit `b10a574` and GREEN
  commit `5a812dd`; `tests/agent/test_clarification_demo.py`,
  `scripts/agent/run_clarification_demo.py --check`, and `tests/agent`
  passed.
- Phase 5 Wave 6 completed on 2026-06-15 with RED commit `d90e9c1`, GREEN
  commit `a421fd3`, and this final documentation/verification commit; final
  gates passed and `dataset/processed/agent-demo/simple-room/output.ifc` is the
  Phase 5 acceptance artifact.
- Phase 4 was specified and planned on 2026-06-15 with seven waves. Wave 0 is
  a new generated-IFC correctness gate for `simple-room-fixed` and
  `two-room-suite`; Waves 1-6 expand source fidelity through inventory,
  materials, type reuse, topology, complex/mapped geometry, broader classes,
  all-25 audit, and Phase 6 readiness.
- Phase 4 Wave 0 completed on 2026-06-15 with RED/GREEN commits `768596d`,
  `4b25802`, `fcf276b`, `d2af026`, `cc600b5`, `9ab2275`, `a796c90`,
  `d96fc00`, `11a8dbe`, and `b55cf63`; focused quality/demo tests, prompt
  tests, compileall, demo commands, and artifact secret scan passed.

---
*Last activity: 2026-06-15 - completed Phase 4 Wave 0 generated IFC correctness gate*
