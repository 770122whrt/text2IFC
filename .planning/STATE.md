# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-11)

**Core value:** Produce valid, inspectable IFC models from explicit user
requirements.

**Current focus:** Phase 6.5 immutable ChangeSet application and dependency scope

## Status

- Phase: 6.5
- Stage: Wave 0 contracts complete; Wave 1 in progress
- State: Phase 6.2-fix Waves 0-2 are implemented and automatically verified.
  Wave 3 real UAT
  produced useful live evidence and fixed defects 001/002, then exposed defect
  003: Audit accepted before final generated-IFC geometry feedback existed.
  Wave 4 is implemented and automatically verified. Generated-IFC gate evidence
  reaches decisive Audit, Audit override attempts block, true geometry failures
  can route to one bounded repair attempt, and repaired candidates rerun gates
  plus Audit before acceptance. Follow-up live session `d462b95089755d47`
  generated a real accepted IFC, but post-review exposed defect 004: geometry
  expectations can be derived from candidate wall placements rather than Design
  Brief/user facts, and unsupported explicit facts such as inward door opening
  can be silently lost. Wave 5 is now implemented and automatically verified:
  semantic geometry expectations, fact-level capability coverage,
  unsupported-fact Draft/block routing, report integration, Audit evidence, and
  final verifier hardening are in place. Final acceptance is still pending
  because the next live UAT exposed defect 005: parseable invalid Formal
  Generator output was preserved as `parsed-output.json`, but Repair only used
  validated `candidate.json` as a previous candidate and therefore blocked with
  `previous_candidate=None`. Wave 6 is now implemented and automatically
  verified: actionable invalid Formal output can enter bounded repair, invalid
  recovery source evidence is recorded, and Design Brief outside-boundary
  wording is normalized for semantic geometry gates. Final acceptance is still
  pending until a fresh human-terminal live Mimo run writes and verifies
  `final-acceptance.json`. A later complex multi-storey run was correctly
  blocked as `audit_blocked`, but exposed the next reliability gap: complex
  expected facts, Gate-Audit applicability, stage routing, and compact trace
  need a dedicated inserted Phase 6.3 before broader Phase 7 work. Phase 6.3
  SPEC, PLAN-OUTLINE, and seven wave plans are drafted for review. A
  follow-up cross-review strengthened the plan so non-two-storey coverage must
  reach dynamic gates and route decisions, Gate/Audit/Route evidence must bind
  through hashes, and compact non-accept traces must preserve recoverable
  failure evidence. Wave 0 is implemented with the complex two-storey
  fixture/no-false-accept baseline. Wave 1 is implemented with
  `gate-summary.json`, candidate/expected-facts hash binding, and decisive
  Audit prompt integration. Wave 2 is implemented with dynamic
  `expected-facts.json` extraction from Design Brief known facts, a reusable
  non-two-storey fixture, and REPL integration that binds Audit prompts to the
  expected-facts hash. Wave 3 is implemented with dynamic entity
  completeness, storey containment, host-wall, and opening/fill gates in the
  GateSummary bundle. The reusable three-storey fixture now reaches dynamic
  gate logic and fails on missing `storey-3` facts without hard-coded
  two-storey assumptions. Wave 4 is implemented with hash-bound
  `route-decision.json`, canonical route ownership, stale evidence blocking,
  bounded attempt/stall detection, and Audit-stage integration. Wave 5 is
  implemented with compact/debug/full trace-level policy, CLI propagation,
  stage-local compact `trace/` evidence, compact-aware report resolution, and
  root `trace-manifest.json` hashing actual run artifacts. Wave 6 is
  implemented with a repeatable complex-building matrix and final artifact
  verifier. The matrix covers the user's complex two-storey prompt as an
  honest blocked `generator_regeneration_required` route, a non-two-storey
  three-level dynamic gate/route case, and simple/two-room smoke regressions.
  Final verification reports `valid: true`, `false_accept_count: 0`,
  `hash_binding_valid: true`, `secret_finding_count: 0`, and
  non-two-storey gate/route coverage. This completes Phase 6.3 as a
  reliability/evidence-routing phase, but does not claim complex live provider
  generation already produces an accepted final IFC.
- Plans: Phase 6.2-fix Waves 0-2 complete; Wave 3 produced UAT defect evidence;
  Wave 4 implementation/regression complete; Wave 5 implementation/regression
  complete; Wave 6 implementation/regression complete; Phase 6.3 planned in
  seven waves; Waves 0-6 implemented and verified; Phase 6.4 Waves 0-6
  implemented and verified; Phase 6.4 Waves 7-8 complete with a real accepted
  two-storey DeepSeek IFC after two bounded Generator regenerations
- Branch: `multiagent-design` in C-drive worktree
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
- Phase 4 Wave 1 produced
  `dataset/processed/phase4/fidelity-inventory.json` for all 25 authorized
  BIMNet IFC2X3 files with scene-family split metadata and SHA-256 verification.
- Phase 4 Wave 1 measured 2554 material associations, 228 material layers,
  1012 type relationships, 4526 connection topology relationships, 1033 mapped
  geometry items, 2654 BRep-related items, 125 tessellation/face-based surface
  items, 845 openings, and 189 spaces across the authorized source set.
- Phase 4 Wave 2 added BIM JSON 2.0 `materials` support for selected
  `material_layer_set_usage` facts and compiler/extractor round-trip support
  for wall material layers.
- Regenerated BIMNet extraction accounting now reports 2554 material source
  facts, 1533 represented material facts, and 1021 remaining material losses.
- Phase 4 Wave 3 added selected wall type reuse support through `IfcWallType`
  and `IfcRelDefinesByType` while keeping unsupported type/style constructs as
  explicit losses.
- Regenerated BIMNet extraction accounting now reports 1012 type relationship
  source facts, 154 represented type relationships, and 858 remaining type
  relationship losses.
- Phase 4 Wave 4 added selected connection topology support through
  `IfcRelConnectsPathElements`.
- Regenerated BIMNet extraction accounting now reports 2263 connection source
  facts, 2263 represented connection facts, and 0 remaining connection losses.
- Phase 4 Wave 5 keeps mapped, BRep, tessellated, boolean, and surface-model
  geometry out of Formal BIM JSON until exact-enough round-trip support exists.
- Unsupported complex geometry losses now explicitly record the source IFC
  item class and `substitution: "none"` so downstream data and evaluation can
  distinguish honest unsupported geometry from fabricated proxy geometry.
- Phase 4 Wave 6 completed the broader class and all-25 audit closure. Common
  BIMNet architectural product classes already marked `generate` remain
  supported; extract-only classes such as `IfcBuildingElementProxy` and
  `IfcFurnishingElement` now receive explicit no-substitution class losses.
- Phase 4 final verification passed: 337 repository tests, 89 focused
  IFC-quality/Agent/compiler tests, compileall, generated IFC demo gates,
  direct generated IFC checks, all-25 audit accounting, fidelity inventory, and
  geometry-gate artifact secret scan.
- Phase 4 final metrics across 25 authorized BIMNet IFC2X3 files: entities
  4444/5308 represented, relationships 15046/16926 represented, properties
  17607/18758 represented, representations 4509/6382 represented, materials
  1533/2554 represented, types 154/1012 represented, and connections
  2263/2263 represented.
- Phase 6 is specified and planned with a Wave 0 prompt registry and
  multi-agent design contract before data expansion, fine-tuning, or
  deployment.
- Phase 6 records that `two-room-suite` is currently a deterministic
  geometry-gate artifact with a hard-coded candidate, not proof of unified live
  prompt orchestration.
- Phase 6 defines five logical roles: Design Brief Agent, BIM JSON Generator
  Agent, generator repair mode, Audit Agent, and Observer Loop.
- Phase 6 acceptance now has a phase-local single-entry report at
  `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-ACCEPTANCE-TRACE-REPORT.md`.
- Phase 6 Wave 4 now writes a formal fake-provider trace bundle with a real
  compiled/reopened IFC2X3 file and a generated `report.md`, plus a five-case
  controlled matrix covering success, Draft, repair routing, blocked invalid
  JSON, and semantic audit mismatch.
- Phase 6.1 replaces fake-provider acceptance with real Mimo evidence. Waves
  0-3 verified streaming response envelopes, Design Brief v2.1, real Chinese
  clarification, and exact Formal/Draft Generator routing.
- Phase 6.1 Wave 4 records conditional repair truthfully: the canonical live
  Generator result needed no repair, so the repair stage wrote
  `no_repair_needed`, `provider_call_count: 0`, and
  `evidence_class: live-derived-no-call` linked to response
  `msg_99a7039ffef047d2815e0c4f`.
- Phase 6.1 Wave 5 ran a separate real Mimo Audit Agent and generated the
  single-entry live report. A fenced Audit response
  `msg_463225669d994c2390ccebf0` triggered a strict output-contract fix and
  prompt strengthening. The final Audit response
  `msg_7cbe7cb111df4758b0e78786` returned bare JSON with
  `recommendation: accept`, `blocking: false`, and zero validation issues.
  `report.md` is generated from sidecars and links Generator parsed output to
  `generator/candidate.json`.
- Phase 6.1 Wave 6 produced the final accepted live artifacts:
  `dataset/processed/agent-demo/phase6.1-mimo-live/output.ifc` and generated
  `dataset/processed/agent-demo/phase6.1-mimo-live/report.md`. The final
  acceptance metrics report `valid: true`, `compile_reopen_success: true`,
  `geometry_success: true`, and `secret_finding_count: 0`. The root artifact
  verifier reopened the IFC as IFC2X3 and passed.
- Phase 6.1 live matrix now includes a real unknown-answer Draft path. The
  Design Brief Agent first asked for wall thickness, then after the user
  answered `我不知道。`, real Mimo response `msg_f87c960adc6f4ec99172f658`
  terminated as `draft_required`, wrote no IFC, and preserved the missing wall
  thickness fact instead of repeating the same question.
- Phase 6.1 invalid-contract replay now blocks nonexistent Draft versions as
  `unknown_contract`, writes no IFC, and is explicitly
  `excluded_from_live_quality`, so replay evidence cannot inflate live Mimo
  quality claims.
- Phase 6.2 is planned as an inserted CLI-first phase. It turns Phase 6.1's
  scripted answer workflow into a Chinese-first interactive terminal session
  with a shared SQLite session DB, stable `session_id`/`session_hash`, query /
  resume / export interfaces, generated `report.md`, and final IFC artifacts
  linked from the accepted session.
- Phase 6.2 Wave 0 is a provider/framework research and compatibility
  checkpoint: OpenAI Agents SDK research must be written before live smoke
  interpretation, and the SDK is a candidate only if real Mimo Chat Completions
  compatibility and required trace metadata preservation pass. Otherwise the
  native orchestrator plus OpenAI Python SDK provider remains the implementation
  path.
- Phase 6.2 Wave 0 completed with real Mimo OpenAI-compatible evidence.
  The native OpenAI SDK Chat Completions path passed with `finish_reason: stop`,
  usage, response ID, raw content, and redacted request metadata. OpenAI Agents
  SDK was classified as `limited_sdk` because its Chat Completions final result
  lacks first-class `response_id` and `finish_reason`; it also required explicit
  AsyncOpenAI client cleanup to avoid a `.venv` process exit-code anomaly.
  The implementation route is
  `native_orchestrator_with_openai_sdk_provider`.
- Phase 6.2 Wave 1 completed the shared SQLite session DB and initial
  interactive CLI shell. The canonical dry-run session preserves Chinese input,
  stores turns/events/artifacts in
  `dataset/processed/agent-demo/phase6.2-interactive-cli/sessions.sqlite`,
  exports
  `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/a26e3365a3204b38/session-export.json`,
  and remains `incomplete` after user `quit` without fabricating Agent or IFC
  results.
- Phase 6.2 Wave 2 completed the DB-backed Mimo Design Brief loop. A real
  clarified-room session reached `ready` after Mimo asked for wall thickness
  and the user supplied `300mm`; Design Brief calls preserve prompt hashes,
  redacted requests, raw responses, parsed outputs, and usage metadata.
- Phase 6.2 Wave 3/4 connected ready sessions to real Mimo Generator and Audit
  calls, deterministic repair routing, IFC compile/reopen, geometry gates,
  generated reports, session export, and a root `final-acceptance.json`.
- Phase 6.2 live prompt iteration found and fixed three real failures:
  `finish_reason=length` at the old 1024 token budget, Audit misunderstanding
  parent-relative centered openings, Generator duplicating wall rotation into
  `Representation.position`, and Mimo fenced JSON output before
  `response_format` was added.
- Phase 6.2 accepted live session `2063e6228b5f2f6d` is compiled. Its final
  metrics report `valid: true`, `compile_reopen_success: true`,
  `geometry_success: true`, `secret_finding_count: 0`, and
  `audit_evidence_class: live`. Acceptance artifacts are under
  `dataset/processed/agent-demo/phase6.2-interactive-cli/`.
- Phase 6.2 final accepted session is now `0fe9f14742b5c5d7`. It was generated
  with real Mimo calls, passes the Phase 6.2 artifact verifier, reopens as
  IFC2X3, passes geometry gates, has `audit_evidence_class: live`, and reports
  `secret_finding_count: 0`.
- Phase 6.2 report generation is now DB-backed. The accepted `report.md`
  includes original input, transcript, Design Brief sidecars, Generator
  sidecars, Repair route, Audit sidecars, deterministic gates, final artifacts,
  session export, events, and artifact index.
- Phase 6.2 query/resume/export commands are implemented and covered by tests.
  Read-only session queries no longer mutate `sessions.sqlite`.
- Real Mimo prompt iteration in Phase 6.2 found and fixed additional Design
  Brief issues: failed calls now preserve evidence before raising, and
  `design-brief.v2.1` now requires target-valid questions and exact transcript
  `source_turns`.
- Final Phase 6.2 verification passed 55 focused tests, 228 Agent/Service/
  Compiler regression tests, compileall, artifact verifier, and accepted-run
  secret scan.

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
- Complex source geometry is not box-substituted. Until a narrow mapped/BRep
  subset can be represented and reopened faithfully, complex geometry remains
  Draft/loss content with no-substitution metadata.
- Phase 6 may start only under the supported-scope boundary: formal targets
  must validate as BIM JSON 2.0, Draft/loss sidecars stay linked, generated IFC
  quality gates block deployment, and source-equivalent BIMNet geometry is not
  claimed until mapped/BRep/tessellated geometry has exact verified support.
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
- The preceding optional-live rules remain historical Phase 5/6 constraints.
  Phase 6.1 acceptance supersedes them: Design Brief, Generator, conditional
  Repair, and Audit evidence must come from real Mimo calls, while fake/file
  providers are unit/replay tools only.
- Phase 6.2 extends the live-evidence rule to the user-facing CLI: fake/file
  and replay providers remain test tools only and cannot satisfy live CLI
  acceptance.
- Phase 6.1 clarification necessity is derived per request from user text,
  transcript, canonical schemas, generation capability, and relevant examples;
  no global required/not-required field list is allowed.
- Phase 6.2 scripted stdin is allowed for deterministic tests only if it
  exercises the same CLI code path as a human terminal session; prewritten
  `answers.json` facts are not accepted as the interactive product path.
- Phase 6.2 uses a shared session database as the primary evidence container.
  Per-session directories under `runs/<session_hash>/` hold large artifacts and
  exported review bundles, but they are not independent truth stores.
- Phase 6.2 final acceptance requires a real-time CLI UAT where Codex acts as
  the user and Mimo acts as the Agent provider; scripted stdin remains
  regression support.
- Phase 6.2-fix Waves 0-2 implemented the missing real REPL product boundary.
  Focused tests now prove the assistant question is printed before answer
  input; `run_text2ifc_chat.py` can be run directly by file path; ready REPL
  sessions route through the existing BIM JSON, IFC, Audit, report, and export
  gates; and Phase 6.2-fix `final-acceptance.json` records
  `interaction_mode: "human_repl_live"` and `input_source: "terminal"`.
- Phase 6.2-fix UAT defect 001 was reproduced and fixed on 2026-06-27. The
  default live REPL path previously wrote Design Brief call traces under the
  output root instead of `runs/<session_hash>`, causing IFC generation to miss
  `design-brief/conversation.json`. The invoker is now constructed after
  session creation with the session run directory.
- Phase 6.2-fix UAT defect 002 was reproduced and fixed on 2026-06-27. A real
  run reached Generator `formal`, Repair `no_repair_needed`, real Audit
  `accepted`, and IFC reopen success, but final geometry gates failed with
  wall-orientation/enclosure issues. The REPL previously exited silently for
  `final_blocked`; it now prints stage summaries and paths to `output.ifc`,
  `report.md`, and `geometry-feedback.json` without claiming acceptance.
- Phase 6.2-fix UAT defect 003 was specified and planned on 2026-06-27. The
  same real run showed a stage-order contract mismatch: Audit reviewed only
  validation and repair-route evidence, while generated-IFC geometry feedback
  was produced later by final acceptance. The next Wave 4 fix requires
  generated-IFC gate evidence before decisive Audit, Audit classification
  without override authority, bounded repair/generation for true geometry
  failures, and gate-dispute blocking for uncertain gate results.
- Phase 6.2-fix Wave 4 was implemented and automatically verified on
  2026-06-27. The pipeline now writes candidate generated-IFC gate evidence
  before Audit, includes `geometry-feedback.json` in Audit prompt inputs,
  rejects Audit `accept` over failed deterministic gates as
  `AUDIT_OVERRIDE_ATTEMPT`, and routes Audit `revise` on true geometry failures
  through one bounded repair attempt followed by regenerated gates and a second
  Audit. Reports now link generated-IFC gate sidecars, repair attempts, and
  Audit validation.
- Phase 6.2-fix post-Wave-4 live UAT session `d462b95089755d47` produced real
  Mimo Design Brief/Generator/Audit evidence, compiled and reopened IFC2X3,
  and geometry-success output. Review then identified defect 004: the geometry
  expectation can be circular when derived from candidate wall placements, and
  explicit unsupported user facts such as `door.opening_direction:
  "into_space"` need Draft/blocking coverage instead of silent acceptance.
- Phase 6.2-fix Wave 5 is now specified and planned as a semantic fidelity
  gate and BIM JSON capability contract: Design-Brief-derived rectangular-room
  geometry expectations, fact-level support profile, unsupported-fact
  Draft-first routing, `semantic-coverage.json`, report integration, and final
  verifier hardening before final user-run UAT.
- Phase 6.2-fix Wave 5 was implemented and automatically verified on
  2026-06-27. The pipeline now writes `semantic-capabilities.json`,
  `semantic-coverage.json`, and `semantic-geometry-expectation.json`; blocks
  unwaived unsupported facts such as `/known_facts/door/opening_direction`;
  uses Design-Brief-derived wall expectations for supported rectangular rooms;
  exposes semantic coverage in generated reports and Audit inputs; and requires
  semantic coverage in the final artifact verifier.
- Phase 6.2-fix Wave 6 was implemented and automatically verified on
  2026-06-28. Parseable invalid Formal Generator output can now enter bounded
  repair as `invalid_formal` when diagnostics are actionable, route evidence
  records `invalid-candidate.json`, missing door semantic `Representation` and
  unsupported compiler relationship output are repair-eligible when facts are
  known, and Design Brief outside-boundary wording is normalized for semantic
  geometry gates.
- Phase 6.2 treats OpenAI Agents SDK as a conditional integration. A failed SDK
  compatibility checkpoint is not a product failure if the native OpenAI SDK
  provider path remains evidence-complete.
- Design Brief Agent is the only semantic owner of clarification questions.
  Deterministic clarification code validates count, mapping, evidence, and
  transcript state but does not author questions or facts.
- The Observer may diagnose, block, and report prompt/provider/routing failures,
  but cannot delete ambiguity or add semantic facts to force success.
- The simple-room demo reaches `formal_ready`, validates BIM JSON 2.0, asks
  three Chinese clarification questions, compiles IFC, and records transcript,
  state, candidate, diagnostics, metrics, report, and IFC artifacts.
- Phase 6 prompt/provider work must use versioned prompt templates, template
  hashes, structured renderer inputs, raw/parsed output traces, feedback,
  repair-attempt records, metrics, and artifact paths.
- The Design Brief Agent is allowed and recommended as a first step for weak
  natural-language input. It records intent, known facts, missing facts, and
  ambiguities without generating BIM JSON or IFC.
- The BIM JSON Generator Agent consumes Design Brief, schema/capability
  context, few-shot examples, and feedback to output formal BIM JSON 2.0 or
  Draft only.
- Repair is conditional rather than mandatory. Successful first-pass generation
  records `no_repair_needed`; failed generation routes to `repair_attempted`,
  `draft_required`, or `blocked_failure`.
- Audit Agent is separate from generation and cannot override deterministic
  schema, compiler, reopen, generated-IFC, split, or secret-scan gates.
- Fine-tuning in Phase 6 is a metric-backed decision after prompt-only and
  repair-mode baselines, not an assumed next action.
- This conversation's implementation work must stay in
  `C:\Users\rt do believe\.codex\worktrees\a542\bimnet`; do not edit the
  E-drive working tree files.

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

Execute Phase 6.5 Wave 1 with strict RED/GREEN TDD: stable-ID candidate index,
semantic component hashes, deterministic dependency closure, and immutable
ChangeSet application. Do not run real DeepSeek Phase 6.5 stability claims
until Waves 0-5 deterministic verification pass. Preserve all existing
terminal records and historical live artifacts.

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
- Phase 4 Wave 1 completed on 2026-06-15 with RED/GREEN commits `53f5b44`,
  `31cf2ea`, `1930f1f`, and `3148beb`; the inventory covers 25 / 25
  authorized files and provides the metric baseline for Waves 2-6.
- Phase 4 Wave 2 completed on 2026-06-15 with RED/GREEN commits `eca6a97`,
  `20cb5d0`, `1dfeeee`, and `94b3189`; selected wall material layer-set usage
  now round-trips and BIMNet extraction accounting was regenerated.
- Phase 4 Wave 3 completed on 2026-06-16 with RED/GREEN commits `0f7cfe4`,
  `adad41e`, `4d74825`, `fe65d8d`, `29c9997`, and `a3ade19`; selected wall
  type reuse now round-trips and unsupported type/style relationships remain
  loss-explicit.
- Phase 4 Wave 4 completed on 2026-06-16 with RED/GREEN commits `42edd7b`,
  `75010ee`, `5d58ae2`, and `0556563`; selected path element topology now
  round-trips and BIMNet connection accounting was regenerated.
- Phase 4 Wave 5 completed on 2026-06-16 with RED/GREEN commits `05517ed` and
  `ea832d2`; unsupported complex geometry losses now record no-substitution
  metadata instead of promoting unsafe mapped/BRep/tessellated geometry to
  Formal BIM JSON.
- Phase 4 Wave 6 completed on 2026-06-16 with RED/GREEN commits `1cd3021` and
  `12226f0`; regression stabilization commit `27941f7`; final documentation
  and artifact verification commit follows. The phase closes with all-25 audit
  accounting balanced and Phase 6 ready under supported-scope constraints.
- Phase 6 was specified and planned on 2026-06-18 with seven waves. Wave 0
  introduces prompt registry and multi-agent traceability; Wave 1 adds Design
  Brief; Wave 2 adds BIM JSON generation plus repair mode; Wave 3 adds Audit
  Agent; Wave 4 adds reliability experiments; Wave 5 handles data/model
  decision; Wave 6 packages the supported deployable demo.
- Phase 6 Wave 0 completed on 2026-06-21 with RED commits `4f355bf` and
  `3b69a9b`, GREEN commit `cf64af1`, and architecture commit `38937da`.
  Prompt registry, hash-verified rendering, trace validation, and five-role
  responsibility boundaries passed the full Agent regression and secret scan.
- Phase 6 Wave 1 completed on 2026-06-21 with RED commits `ecaf6c2` and
  `a5ed5b8`, GREEN commit `f80c2da`, and prompt commit `0e735a3`. The
  Design Brief contract, validator, and Chinese-first registered prompt passed
  46 Agent tests and the artifact secret scan.
- Phase 6 Wave 2 completed on 2026-06-21 with RED commit `c4bdfeb` and GREEN
  commit `efd108c`. Registry-rendered Formal/Draft generation and four-route
  conditional failure handling passed 52 Agent tests and the secret scan.
- Phase 6 Wave 3 completed on 2026-06-21 with RED commit `fcdde3f` and GREEN
  commit `a486c17`. Evidence-linked Audit reports preserve deterministic gate
  failures and passed 55 Agent tests plus the secret scan.
- Phase 6 Wave 4 completed on 2026-06-21 with initial RED/GREEN commits
  `0df6d57`, `7228acd`, and `8a581a7`, followed by failure-path and durable
  matrix RED/GREEN commits `6b7c466`, `37f95a3`, `fd59d60`, and `29f5a67`.
  The formal run compiled and reopened IFC2X3; the five-case matrix covers all
  four failure routes and five outcome classes; Agent regression passed 62
  tests; artifact scans found zero secrets across both output sets.
- Phase 6 Wave 5 completed on 2026-06-21 with RED commits `69935a2` and
  `0d2c84d`, GREEN commit `cba91bc`, and model-decision commit `b5a533c`.
  The deterministic manifest links 100 pairs to 25 authorized IFC2X3 sources,
  19 isolated scene families, formal targets, hashes, licenses, and loss
  sidecars. Only 68 train records are training-eligible. Prompt-only plus
  deterministic gates was selected for deployment; RAG and fine-tuning remain
  deferred until real-provider and Chinese-first reviewed evidence exists.
- Phase 6 Wave 6 completed on 2026-06-21 with RED commit `ecb2481`, GREEN
  commit `c60bae5`, and Windows worktree stability fix `c3a559e`. The service
  acceptance path writes a complete trace bundle, generated `report.md`, and
  real IFC2X3 artifact. Phase 6 focused verification passed 72 tests, full
  repository regression passed 368 tests, compileall passed, and the final
  artifact scan found zero secrets.
- Phase 6.1 was inserted and planned on 2026-06-22 after real Mimo experiments
  showed that Phase 6 fake-provider acceptance did not verify live behavior.
  Seven waves now cover exact provider envelopes/streaming, evidence-grounded
  Design Brief v2, real Chinese clarification, exact Formal/Draft Generator
  contracts, conditional repair, real Audit/reporting, and final live IFC
  acceptance.
- Phase 6.1 Wave 0 completed on 2026-06-22 with four RED/GREEN cycles. The
  canonical real `mimo-v2.5-pro` smoke retained response ID
  `msg_2bc401bbfdaa455696937d1d`, `stop_reason=end_turn`, request
  `max_tokens=131072`, 15 ordered SSE events, complete usage, parsed bare JSON,
  and zero secret findings. Agent regression passed 76 tests.
- Phase 6.1 Wave 1 completed on 2026-06-22 with evidence-grounded Design Brief
  2.0, request-scoped schema/capability context, and immutable prompt versions.
  The first real v2 response was schema-valid but fenced and was retained as a
  failed-format experiment. Prompt v2.1 then produced bare JSON response
  `msg_164276907f364826bb9a625c`, `end_turn`, status `ready`, zero validation
  issues, zero normalization diagnostics, and zero secret findings.
- Phase 6.1 Wave 2 completed on 2026-06-22 with a real two-call Chinese
  clarification. Mimo response `msg_c4981c9c476443d2a929e240` asked only for
  wall thickness; the exact 300 mm user answer was appended; response
  `msg_d7c51fc05baf4f3eb82cc3f5` returned `ready`. Both calls were `end_turn`,
  strict bare JSON, schema/evidence valid, and the 40-file scan found no secrets.
- Phase 6.1 Wave 3 completed on 2026-06-22 with exact discriminator-first
  Formal/Draft routing and both full canonical schemas in Generator v2. Real
  Mimo response `msg_99a7039ffef047d2815e0c4f` returned strict Formal BIM JSON
  2.0 with 13 entities, 4 relationships, zero contract issues, and zero secret
  findings. No repair was invoked and no IFC was compiled in this wave.
- Phase 6.1 Wave 4 completed on 2026-06-22 with RED/GREEN commits `3b2145f`,
  `87a508e`, `c0b3c8a`, `65a0651`, `a11e850`, and `d6ba0d8`, followed by
  this documentation/artifact commit. The canonical repair stage preserved
  `no_repair_needed` and zero provider calls for the real Formal Generator
  result. Controlled eligible repair is covered as unit/replay evidence only,
  not live quality evidence. Focused tests passed 45 checks; the Agent suite
  passed 125 checks; service/IFC gate slice passed 6 checks; compileall passed.
  Full `python -m pytest -q` was attempted twice and timed out at 120s and
  300s without failure output; collection found 431 tests.
- Phase 6.1 Wave 5 completed on 2026-06-22 with RED/GREEN commits `b8af624`,
  `0b579ca`, `3d3855f`, `f85779d`, `1b60898`, `fa0ad2e`, `12dba94`,
  `bfdf5dc`, and `884e44e`, followed by this documentation/artifact commit.
  The first real Audit response `msg_463225669d994c2390ccebf0` exposed a
  strict output-contract gap by using an outer Markdown fence. After the gate
  and prompt fix, real Audit response `msg_7cbe7cb111df4758b0e78786` was
  `end_turn`, strict bare JSON, valid Audit v2, `recommendation: accept`, and
  `blocking: false`. The generated `report.md` is sidecar-derived and links
  the Generator parsed output to `generator/candidate.json`. Agent regression
  passed 129 tests and compileall passed.
- Phase 6.1 Wave 6 completed on 2026-06-23 with final acceptance commits and
  generated root artifacts. The live finalize command passed, artifact verifier
  passed, 25 focused live-report tests passed, the Agent suite passed 134 tests,
  service/compiler/dataset passed 56 tests, compileall passed, and the final
  artifact secret scan found zero sensitive strings.
- Phase 6.1 MiMo API compatibility was re-verified on 2026-06-23 after the
  official Anthropic-compatible MiMo API reference was captured. The provider
  now accepts `API_KEY` / `MIMO_API_KEY` and sends the documented `api-key`
  header. Live smoke response `msg_db85c7ecd9cf4ff79823ffa0` returned
  `stop_reason: end_turn`. The clarified-room matrix then produced a live
  Formal Generator response `msg_4190b4fc62c04a839d1a48ee`, live Audit response
  `msg_33bcfd37905c45bfbf3d4e67`, `no_repair_needed` routing, and an
  independently verified IFC artifact at
  `dataset/processed/agent-demo/phase6.1-mimo-live/clarified-room-final/output.ifc`.
- Phase 6.1 prompt hardening on 2026-06-23 fixed the real unknown-answer
  failure where MiMo recognized `不知道` but repeated the same clarification
  question. `design-brief.v2.1` now requires `draft_required` when a current
  blocking fact cannot be supplied by the user, and the rerun passed with real
  MiMo evidence.
- Phase 6.2 was specified and planned on 2026-06-23 after the user prioritized
  CLI clarification over public API/service work. Seven waves now cover
  OpenAI-compatible Mimo and Agents SDK checkpointing, durable CLI sessions,
  interactive Design Brief questions, Generator and IFC gates,
  Audit/repair/report integration, acceptance matrix, and final verification.
- Phase 6.2 planning was revised on 2026-06-23 so the session architecture is a
  shared SQLite DB for all conversations rather than one DB per run. Each
  conversation has a stable `session_id` and `session_hash`; CLI interfaces must
  support listing, showing, resuming, and exporting sessions. Final acceptance
  also now requires Codex-as-user real-time CLI UAT with Mimo-backed Agent
  responses.

---
*Last activity: 2026-07-12 - completed Phase 6.5 Wave 0 ChangeSet, immutable
revision, and allowed-scope contracts through RED/GREEN TDD. The focused and
compatibility regression set reports 52 passed. No candidate mutation,
provider prompt, live model call, IFC5 dependency, or existing-IFC edit path
was added. Wave 1 is the next implementation boundary.*
