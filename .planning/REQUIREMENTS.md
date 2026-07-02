# Requirements: text2IFC

**Defined:** 2026-06-11
**Core Value:** Produce valid, inspectable IFC models from explicit structured
requirements.

## v1 Requirements

### BIM JSON Contract

- [x] **JSON-01**: The project defines one versioned BIM JSON contract for
  Phase 1 input.
- [x] **JSON-02**: Invalid BIM JSON is rejected with field-level errors before
  IFC generation.
- [x] **JSON-03**: The contract distinguishes required values from optional
  values without silently inventing missing required data.
- [x] **JSON-04**: The contract covers the supported project hierarchy,
  element families, basic dimensions, and selected common properties.
- [x] **JSON-05**: Existing project JSON artifacts can be converted to the
  versioned contract or rejected with an explicit incompatibility report.

### IFC Generation

- [x] **IFC-01**: Valid Phase 1 BIM JSON generates an IFC2X3 file that
  IfcOpenShell can reopen.
- [x] **IFC-02**: Generated IFC preserves the project, site, building, and
  storey hierarchy.
- [x] **IFC-03**: Generated IFC preserves supported element types and counts.
- [x] **IFC-04**: Generated IFC preserves Phase 1 basic dimensions.
- [x] **IFC-05**: Generated IFC preserves selected Phase 1 common properties.

### Verification

- [x] **VER-01**: Each Phase 1 compiler behavior is introduced with a failing
  automated test before implementation.
- [x] **VER-02**: Generated IFC is checked against IFC2X3 schema-level validity.
- [x] **VER-03**: A repeatable command runs the Phase 1 test suite.

### Documentation

- [x] **DOC-01**: The BIM JSON contract and supported IFC subset are documented
  from the same source used by validation.
- [x] **DOC-02**: Durable documentation is indexed from `docs/README.md`.

### IFC Semantic Graph, Knowledge, and Extraction

- [x] **JSON-06**: BIM JSON 2.0 is a separately versioned IFC2X3-aligned
  semantic entity graph, and BIM JSON 1.0 migrates deterministically to an
  explicit Draft Envelope rather than receiving invented spatial facts.
- [x] **KNOW-01**: A deterministic registry generated from official IFC2X3
  EXPRESS validates class names, inheritance, attributes, relationships,
  selects, and enumerations.
- [x] **KNOW-02**: A deterministic registry generated from official IFC2X3 PSD
  definitions validates standard property-set names, property names, types,
  applicability, and provenance.
- [x] **ENTITY-01**: BIM JSON 2.0 represents semantic IFC objects in
  `entities` with explicit `ifc_class`, stable identity, typed attributes, and
  source provenance.
- [x] **CAP-01**: Every recognized IFC2X3 entity has an explicit generation,
  extraction, compiler-only, or unsupported capability and no unsupported
  entity is silently emitted or dropped.
- [x] **GEO-01**: BIM JSON and generated IFC preserve hierarchical local
  placement and orientation for supported spatial objects.
- [x] **GEO-02**: BIM JSON and generated IFC preserve supported semantic
  geometry plus explicit opening, host-element, and filling-element
  relationships.
- [x] **SPACE-01**: BIM JSON represents supported rooms/spaces with stable
  identity, storey membership, placement, and geometry.
- [x] **DRAFT-01**: Incomplete, ambiguous, extract-only, or unsupported content
  uses a separate Draft Envelope that enumerates every missing fact, loss,
  provenance record, and future clarification target.
- [x] **EXTRACT-01**: Authorized IFC sources are deterministically normalized
  into valid BIM JSON 2.0 or an explicit Draft plus provenance and a complete
  machine-readable loss report.
- [x] **COMPAT-01**: The compiler accepts formal BIM JSON 2.0 within the
  architectural generation profile and preserves the
  Phase 2 guarantees while adding the supported spatial subset.

### Text-to-JSON Baseline

- [x] **TEXT-01**: The project can generate provenance-linked text and BIM JSON
  2.0 pairs from approved formal ground-truth records without split leakage.
- [x] **TEXT-02**: A structured-output baseline converts natural language into
  formal BIM JSON 2.0 without generating raw IFC text.
- [x] **TEXT-03**: Text-to-JSON output is evaluated with field-level,
  collection-level, and document-validity metrics.
- [x] **E2E-01**: At least one spatial natural-language request completes the
  validated Text-to-JSON-to-IFC pipeline.

## Later Requirements

### Geometric and Relational Fidelity

- **GEN-01**: Generated text-to-BIM-JSON-to-IFC demos preserve correct spatial
  relationships, user-visible content, supported attributes, IFC hierarchy,
  containment, and opening/filling relationships under automated checks.
- **GEN-02**: Text-to-BIM-JSON-to-IFC experiments record quantitative metrics,
  error classes, prompt/provider versions, repair iterations, and durable
  artifacts, including a generated human-readable `report.md` that exposes
  critical intermediate inputs and outputs, so reliability can improve through
  measured iteration.
- **GEO-03**: Preserve material assignments and layer details.
- **GEO-04**: Preserve supported topology and connection relationships.
- **GEO-05**: Preserve supported arbitrary profiles, BReps, tessellation, and
  reusable mapped geometry.
- **IFC-06**: Expand beyond the Phase 2.5 architectural generation profile
  with schema-aware support for selected structural, furnishing, and MEP
  classes.

### Natural-language Agent

- **AGENT-01**: Convert natural language into valid BIM JSON.
- **AGENT-02**: Ask targeted questions for missing required values.
- **AGENT-03**: Maintain multi-turn clarification state.
- **PROMPT-01**: Every provider-backed prompt run is rendered from a versioned
  prompt registry and records template ID, template hash, structured inputs,
  rendered prompt, raw output, parsed output, feedback, repair attempts,
  metrics, and artifact paths.
- **AGENT-04**: A Design Brief Agent converts raw user text into explicit known
  facts, missing facts, ambiguities, corrections, and clarification targets
  without outputting BIM JSON or IFC.
- **AGENT-05**: An Audit Agent reviews user intent coverage against the Design
  Brief, BIM JSON, validator diagnostics, generated IFC metrics, and artifacts,
  but cannot override deterministic failures.
- **REPAIR-01**: Failure handling distinguishes no-repair success, conditional
  repair attempts, Draft clarification, and blocking failures. Repair is not
  required for every successful run; when attempted, it uses validation and
  geometry feedback, records before/after issue deltas, and returns Draft
  questions instead of inventing missing facts.
- **OBS-01**: Prompt and Agent iteration uses an Observer Loop that records
  failure classes, metrics, prompt/provider versions, repair attempts, and
  experiment evidence before prompt changes are accepted. Each run must also
  produce a generated Markdown report that lets a human review the input,
  prompt, raw output, parsed BIM JSON or Draft, validation feedback, geometry
  feedback, audit result, metrics, and final artifacts from one file.
- **MODEL-01**: Evaluate fine-tuning against prompt-only and structured-output
  baselines.
- **MODEL-02**: Expand training data only from license-reviewed sources with
  provenance manifests.
- **DEPLOY-01**: Package the selected model and deterministic compiler behind
  a repeatable deployment interface.

### Live Mimo Multi-agent Acceptance

- [x] **LIVE-01**: Every Phase 6.1 acceptance role uses the configured real
  Mimo Anthropic API and preserves the exact response envelope, including
  provider response ID, model, `stop_reason`, content blocks, and usage.
- [x] **LIVE-02**: A real Mimo Design Brief Agent dynamically derives known,
  missing, ambiguous, unsupported, and corrected facts from the user request,
  conversation, BIM JSON schema, capability evidence, and relevant examples;
  it does not use a global hard-coded required/not-required field list.
- [x] **LIVE-03**: The Chinese-first live workflow asks one to three evidence-
  linked questions per clarification turn, preserves every user answer, and
  reruns the Design Brief Agent until it reports ready, Draft, or blocked.
- [x] **LIVE-04**: A real Mimo Generator receives both canonical Formal BIM
  JSON 2.0 and Draft Envelope contracts and returns exactly one contract-valid
  object; unknown versions and malformed envelopes are blocked explicitly.
- [x] **LIVE-05**: Repair is called through real Mimo only after deterministic
  validation feedback makes repair eligible, preserves before/after evidence,
  and never receives supervisor-authored facts or silent ambiguity removal.
- [x] **LIVE-06**: A real Mimo Audit Agent reviews intent coverage after all
  deterministic gates, cannot override failures, and an accepted live run
  produces a reopened, geometry-checked IFC2X3 file.
- [x] **OBS-02**: A live run exposes stage progress through persisted stream
  events and generates one `report.md` from trace sidecars containing every
  material input/output, route, metric, and final artifact path while excluding
  credentials, authorization headers, and private provider URLs.

### Interactive CLI and OpenAI-Compatible Orchestration

- [ ] **CLI-01**: The project verifies Mimo OpenAI-compatible Chat Completions
  and OpenAI Agents SDK feasibility with redacted live evidence before any SDK
  adoption claim.
- [ ] **CLI-02**: A Chinese-first CLI accepts user request and answer turns from
  stdin, persists append-only session records in a shared SQLite database keyed
  by `session_id` and `session_hash`, and supports safe status/help/quit
  behavior.
- [ ] **CLI-03**: The interactive Design Brief loop asks one to three Chinese
  Agent-authored clarification questions per turn and records user answers as
  real transcript turns rather than prewritten `answers.json` facts.
- [ ] **CLI-04**: The CLI executes the role-isolated Design Brief, Generator,
  deterministic validation, IFC compile/reopen, geometry gates, conditional
  repair, and Audit route to a terminal Formal, Draft, or blocked outcome.
- [ ] **CLI-05**: Every CLI run generates a human-review `report.md` from
  session DB records and linked artifact references containing the original
  input, transcript, prompts, raw outputs, parsed outputs, gate feedback,
  route, metrics, audit result, and final artifact paths.
- [ ] **CLI-06**: Live CLI claims require real Mimo provider IDs, finish
  reasons, usage, raw output, artifact secret scan, and evidence-class labels;
  fake/file/replay output cannot satisfy live acceptance.
- [ ] **CLI-07**: The shared session store exposes query, resume, and export
  interfaces so users and later APIs can list sessions, inspect turns, inspect
  agent calls, inspect artifacts, resume incomplete sessions, and export one
  session's review bundle by `session_id` or `session_hash`.
- [ ] **CLI-08**: Final interactive CLI acceptance requires a true human-facing
  Chinese REPL run: the assistant question is visible before each user answer
  is read, the accepted session is marked as terminal/live interaction, and
  scripted stdin, prewritten answer files, fake providers, or replay evidence
  cannot satisfy final acceptance.
- [ ] **CLI-09**: Deterministic generated-IFC feedback is available to Audit
  before final acceptance. Audit can classify failed schema, compile, reopen,
  geometry, report, verifier, or secret-scan gates, but cannot override them;
  true candidate geometry failures route to bounded repair/generation, and
  gate disputes block for human/developer review. An Audit `accept` over failed
  deterministic gates is treated as `audit_override_attempt`, not acceptance.

### Scalable Gate-Audit and Complex-building Reliability

- [ ] **GEN-03**: Complex multi-storey natural-language requests must not be
  accepted merely because BIM JSON validates and IFC reopens. The system must
  either produce an accepted IFC whose applicable explicit facts are covered,
  or block with a precise route and evidence.
- [ ] **GATE-01**: Deterministic gates and Audit operate on one shared evidence
  bundle for the same candidate. Audit can classify, dispute applicability, or
  route failures, but cannot override failed applicable gates. The shared
  evidence must bind gate summary, Audit input, route decision, report, and
  manifest through matching candidate and evidence hashes.
- [ ] **GATE-02**: Expected facts and gate checks are dynamically derived from
  Design Brief and transcript evidence. Production logic must not hard-code
  storey count, room count, wall count, door/window count, or the two-storey
  benchmark shape, and non-two-storey coverage must exercise dynamic gates and
  route decisions rather than expected-fact extraction only.
- [ ] **GATE-03**: Formal acceptance checks dynamic completeness, storey/space
  containment, host-wall obligations, and door/window opening/fill
  relationships when those facts are explicit and currently supported.
- [ ] **ROUTE-01**: Failed Gate-Audit review records a route decision that
  identifies the owning next stage: Design Brief revision, Generator
  regeneration, local repair, Draft/clarification, gate dispute, or blocked
  failure. Bounded retry loops stop when issue counts do not improve, and
  stale/mismatched evidence hashes block acceptance.
- [ ] **TRACE-02**: Live REPL generation supports compact/debug/full trace
  levels. Compact is the default to reduce normal generation file writes and
  review noise, while debug/full preserves complete prompt/provider evidence
  for audits. Compact non-accept routes must preserve or link recoverable
  redacted evidence for the failed owning stage.

## Out of Scope

| Feature | Reason |
|---|---|
| Raw language-model generation of STEP text | Too fragile and difficult to validate |
| IFC4/IFC4x3 output in Phases 1-3 | Current compiler target is IFC2X3 |
| Exact geometry reconstruction in Phase 2 | Deferred to the fidelity phase |
| Model fine-tuning in Phase 1 | Compiler and evaluation contracts must stabilize first |

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| JSON-01 | Phase 1 | Complete |
| JSON-02 | Phase 1 | Complete |
| JSON-03 | Phase 1 | Complete |
| JSON-04 | Phase 1 | Complete |
| JSON-05 | Phase 1 | Complete |
| DOC-01 | Phase 1 | Complete |
| DOC-02 | Phase 1 | Complete |
| IFC-01 | Phase 2 | Complete |
| IFC-02 | Phase 2 | Complete |
| IFC-03 | Phase 2 | Complete |
| IFC-04 | Phase 2 | Complete |
| IFC-05 | Phase 2 | Complete |
| VER-01 | Phase 2 | Complete |
| VER-02 | Phase 2 | Complete |
| VER-03 | Phase 2 | Complete |
| JSON-06 | Phase 2.5 | Complete |
| KNOW-01 | Phase 2.5 | Complete |
| KNOW-02 | Phase 2.5 | Complete |
| ENTITY-01 | Phase 2.5 | Complete |
| CAP-01 | Phase 2.5 | Complete |
| GEO-01 | Phase 2.5 | Complete |
| GEO-02 | Phase 2.5 | Complete |
| SPACE-01 | Phase 2.5 | Complete |
| DRAFT-01 | Phase 2.5 | Complete |
| EXTRACT-01 | Phase 2.5 | Complete |
| COMPAT-01 | Phase 2.5 | Complete |
| TEXT-01 | Phase 3 | Complete |
| TEXT-02 | Phase 3 | Complete |
| TEXT-03 | Phase 3 | Complete |
| E2E-01 | Phase 3 | Complete |
| GEN-01 | Phase 4 | Planned |
| GEN-02 | Phase 4 | Planned |
| GEO-03 | Phase 4 | Planned |
| GEO-04 | Phase 4 | Planned |
| GEO-05 | Phase 4 | Planned |
| IFC-06 | Phase 4 | Planned |
| AGENT-01 | Phase 5 | Complete |
| AGENT-02 | Phase 5 | Complete |
| AGENT-03 | Phase 5 | Complete |
| PROMPT-01 | Phase 6 | Complete |
| AGENT-04 | Phase 6 | Complete |
| AGENT-05 | Phase 6 | Complete |
| REPAIR-01 | Phase 6 | Complete |
| OBS-01 | Phase 6 | Complete |
| MODEL-01 | Phase 6 | Complete |
| MODEL-02 | Phase 6 | Complete |
| DEPLOY-01 | Phase 6 | Complete |
| LIVE-01 | Phase 6.1 | Complete |
| LIVE-02 | Phase 6.1 | Complete |
| LIVE-03 | Phase 6.1 | Complete |
| LIVE-04 | Phase 6.1 | Complete |
| LIVE-05 | Phase 6.1 | Complete |
| LIVE-06 | Phase 6.1 | Complete |
| OBS-02 | Phase 6.1 | Complete |
| CLI-01 | Phase 6.2 | Complete |
| CLI-02 | Phase 6.2-fix | Planned |
| CLI-03 | Phase 6.2-fix | Planned |
| CLI-04 | Phase 6.2-fix | Planned |
| CLI-05 | Phase 6.2-fix | Planned |
| CLI-06 | Phase 6.2-fix | Planned |
| CLI-07 | Phase 6.2-fix | Planned |
| CLI-08 | Phase 6.2-fix | Planned |
| CLI-09 | Phase 6.2-fix | Planned |
| GEN-03 | Phase 6.3 | Planned |
| GATE-01 | Phase 6.3 | Planned |
| GATE-02 | Phase 6.3 | Planned |
| GATE-03 | Phase 6.3 | Planned |
| ROUTE-01 | Phase 6.3 | Planned |
| TRACE-02 | Phase 6.3 | Planned |

**Coverage:**
- tracked requirements: 68 total
- Mapped to phases: 68
- Unmapped: 0

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-07-02 after Phase 6.3 Gate-Audit fusion planning*
