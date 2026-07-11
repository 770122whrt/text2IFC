# Roadmap: text2IFC

## Phase 1: BIM JSON 1.0 Contract and Validator

**Goal:** Define one versioned BIM JSON contract, validate it with field-level
errors, and migrate or explicitly reject existing project JSON artifacts.

**Requirements:** JSON-01, JSON-02, JSON-03, JSON-04, JSON-05, DOC-01, DOC-02

**Explicit boundary:** This phase defines data meaning and validation. It does
not expand IFC generation behavior.

**Plans:** 4 plans in 3 waves

**Wave 1**

- [x] `01-01-PLAN.md` - Canonical structural contract, validator, and CLI

**Wave 2** *(blocked on Wave 1 completion)*

- [x] `01-02-PLAN.md` - Semantic identity and storey-reference validation
- [x] `01-04-PLAN.md` - Generated contract reference and drift check

**Wave 3** *(blocked on Wave 2 semantic validation)*

- [x] `01-03-PLAN.md` - Complete legacy migration audit

**Cross-cutting constraints:**

- JSON Schema Draft 2020-12 remains the single structural source of truth.
- Validation and migration are deterministic and never invent required data.
- Validation performs no IFC I/O and no remote schema resolution.

**Status:** Complete - verified 2026-06-11

## Phase 2: Minimum BIM JSON to IFC2X3 Compiler

**Goal:** Compile valid BIM JSON 1.0 into reopenable IFC2X3 with correct
hierarchy, supported element counts, basic dimensions, and selected properties.

**Requirements:** IFC-01, IFC-02, IFC-03, IFC-04, IFC-05, VER-01, VER-02,
VER-03

**Depends on:** Phase 1

**Plans:** 4 plans in 3 waves

**Wave 1**

- [x] `02-01-PLAN.md` - Validated compiler boundary, hierarchy, identity, and
  atomic IFC2X3 output

**Wave 2** *(blocked on Wave 1 completion)*

- [x] `02-02-PLAN.md` - Deterministic all-family geometry and dimensions
- [x] `02-03-PLAN.md` - Selected property and predefined-type fidelity

**Wave 3** *(blocked on Wave 2 completion)*

- [x] `02-04-PLAN.md` - Verifier proof, CLI, complete acceptance, and docs

**Cross-cutting constraints:**

- BIM JSON 1.0 validation runs before any IFC output path is touched.
- Tests inspect serialized and reopened IFC instead of compiler bookkeeping.
- Output replacement occurs only after in-memory and reopened verification.
- Every behavior follows a recorded RED-GREEN TDD cycle.

**Status:** Complete - verified 2026-06-11

**Post-verification discovery:** BIM JSON 1.0 intentionally contains no
source placement. A 35-file IFC audit confirmed that this prevents spatial
training and motivated the inserted Phase 2.5 without invalidating Phase 2's
minimum-compiler acceptance criteria.

## Phase 2.5: BIM JSON 2.0 IFC Semantic Graph (INSERTED)

**Goal:** Define and validate an IFC2X3-aligned BIM JSON 2.0 semantic entity
graph, build deterministic knowledge registries from official buildingSMART
sources, extract authorized IFC ground truth without silent loss, and extend
the compiler for the initial BIMNet architectural generation profile.

**Requirements:** JSON-06, KNOW-01, KNOW-02, ENTITY-01, CAP-01, GEO-01,
GEO-02, SPACE-01, DRAFT-01, EXTRACT-01, COMPAT-01

**Depends on:** Phase 1, Phase 2

**Evidence:** `02.5-IFC-GAP-AUDIT.md` audits 25 BIMNet IFC2X3 and 10
buildingSMART IFC4/IFC4X3 files.

**Canonical refs:**

- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-SPEC.md`
- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-CONTEXT.md`
- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-IFC-GAP-AUDIT.md`
- `docs/reference/ifc2x3-knowledge-sources.md`

**Explicit boundary:** This phase establishes official IFC2X3 knowledge,
IFC-class semantic truth, parent-relative placement, bounded semantic
geometry, Draft/loss accounting, and the BIMNet architectural generation
profile. Arbitrary BRep/tessellation, materials, type reuse, broad connection
topology, furnishing/MEP generation, and IFC4/IFC4X3 output remain Phase 4.

**Plans:** 6 plans in 5 waves

**Wave 1**

- [x] `02.5-01-PLAN.md` - Official IFC2X3 source manifest, safe acquisition,
  declaration registry, and PSD property registry

**Wave 2** *(blocked on Wave 1 completion)*

- [x] `02.5-02-PLAN.md` - Formal BIM JSON 2.0, Draft Envelope, capability
  overlay, registry validation, and 1.0 Draft migration

**Wave 3** *(blocked on Wave 2 completion)*

- [x] `02.5-03-PLAN.md` - Parent-relative placement, semantic geometry,
  spaces, openings, and void/fill relationship validation

**Wave 4** *(blocked on Wave 3 completion)*

- [x] `02.5-04-PLAN.md` - Deterministic IFC2X3 extraction and complete loss
  accounting
- [x] `02.5-05-PLAN.md` - BIM JSON 2.0 architectural compiler profile and
  reopened IFC verification

**Wave 5** *(blocked on both Wave 4 plans)*

- [x] `02.5-06-PLAN.md` - All-25 BIMNet audit, provenance, generated
  references, reviews, and phase acceptance

**Cross-cutting constraints:**

- Official-source schema/property facts and project-authored capability
  decisions remain separate.
- Normal validation and compilation are offline; network access is restricted
  to an explicit hash-verified acquisition command.
- Formal input is complete and compiler-ready; incomplete or unsupported
  content remains a Draft and never reaches IFC output.
- No source class, relation, property, geometry, or migration fact is silently
  dropped, substituted, or invented.
- Every implementation behavior follows recorded RED-GREEN TDD before full
  regression.

**Status:** Complete - verified 2026-06-12

## Phase 3: Text-to-JSON Dataset and Baseline

**Goal:** Use canonical formal BIM JSON 2.0 ground truth to build provenance-linked
text/JSON pairs, establish a structured-output Text-to-JSON baseline, evaluate
it, and demonstrate the first spatial Text-to-JSON-to-IFC request.

**Requirements:** TEXT-01, TEXT-02, TEXT-03, E2E-01

**Depends on:** Phase 1, Phase 2, Phase 2.5

**Canonical refs:**

- `.planning/phases/03-text-to-json-dataset-and-baseline/03-SPEC.md`
- `.planning/phases/03-text-to-json-dataset-and-baseline/03-CONTEXT.md`
- `.planning/phases/03-text-to-json-dataset-and-baseline/03-RESEARCH.md`
- `.planning/phases/03-text-to-json-dataset-and-baseline/03-VALIDATION.md`
- `.planning/phases/03-text-to-json-dataset-and-baseline/03-GOAL-PROMPT.md`

**Data boundary:**

- BIMNet is the primary authorized IFC2X3 source.
- Train, validation, and test split by Matterport scene family before any
  text generation or augmentation.
- buildingSMART samples remain a separate cross-schema and relationship track.
- IFC-to-BIM-JSON is an offline label-construction step; runtime inference
  remains Natural Language to formal BIM JSON 2.0 to IFC.

**Explicit boundary:** This phase builds the data and evaluation loop for
Text-to-JSON. It does not fine-tune a production model, does not implement the
runtime multi-turn clarification Agent, and does not expand source IFC fidelity
beyond the Phase 2.5 formal generation profile.

**Plans:** 7 plans in 7 waves

**Wave 1**

- [x] `03-01-PLAN.md` - Scene-family split manifest and provenance gate

**Wave 2** *(blocked on Wave 1 completion)*

- [x] `03-02-PLAN.md` - Draft triage and formal supported-scope gold set

**Wave 2.5** *(INSERTED; blocked on Wave 2 zero-formal finding)*

- [x] `03-02.5-PLAN.md` - Supported-scope projection for formal
  Text-to-JSON targets

**Wave 3** *(blocked on Wave 2.5 completion)*

- [x] `03-03-PLAN.md` - Deterministic Text/JSON pair generation

**Wave 4** *(blocked on Wave 3 completion)*

- [x] `03-04-PLAN.md` - Provider-independent evaluation harness

**Wave 5** *(blocked on Wave 4 completion)*

- [x] `03-05-PLAN.md` - Structured-output Text-to-JSON baseline

**Wave 6** *(blocked on Wave 5 completion)*

- [x] `03-06-PLAN.md` - End-to-end demo, summary, and RAG/fine-tune decision
  report

**Cross-cutting constraints:**

- Scene-family split assignment happens before any text generation,
  augmentation, baseline run, or fine-tuning export.
- Formal baseline targets are supported-scope BIM JSON 2.0 documents; source
  losses remain in sidecars and are not invented into the target.
- Draft/clarification records remain separate from formal baseline records.
- The model layer outputs BIM JSON 2.0 only; raw IFC STEP and low-level IFC
  implementation objects remain compiler output.
- Evaluation reports invalid JSON/BIM JSON as first-class failures before
  semantic field scoring.
- Every implementation behavior with defined inputs and outputs follows a
  recorded RED-GREEN TDD cycle.

**Status:** Complete - verified 2026-06-14

## Phase 4: High-fidelity IFC Round Trip

**Goal:** Improve the full text-to-BIM-JSON-to-IFC path so generated IFC is
spatially and semantically correct under automated checks, then preserve
material/type fidelity, complex source geometry, supported connection topology,
and broader product classes while reporting every unsupported loss.

**Requirements:** GEN-01, GEN-02, GEO-03, GEO-04, GEO-05, IFC-06

**Depends on:** Phase 2.5, Phase 3, Phase 5

**Canonical refs:**

- `.planning/phases/04-high-fidelity-ifc-round-trip/04-SPEC.md`
- `.planning/phases/04-high-fidelity-ifc-round-trip/04-CONTEXT.md`
- `.planning/phases/04-high-fidelity-ifc-round-trip/04-VALIDATION.md`
- `.planning/phases/04-high-fidelity-ifc-round-trip/04-GOAL-PROMPT.md`

**Explicit boundary:** Phase 4 starts with a generated-IFC correctness gate for
the text -> BIM JSON -> IFC path. It does not proceed to high-fidelity source
round-trip work until `simple-room-fixed` and `two-room-suite` pass automated
spatial, attribute, relationship, and IFC-structure checks. Unsupported source
facts remain explicit Draft/loss content and are never replaced with fabricated
boxes or proxies.

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `04-00-PLAN.md` - Generated IFC correctness gate for simple-room-fixed
  and two-room-suite

**Wave 1** *(blocked on Wave 0 generated-IFC gate)*

- [x] `04-01-PLAN.md` - Fidelity inventory and metric harness

**Wave 2** *(blocked on Wave 1 inventory)*

- [x] `04-02-PLAN.md` - Material and layer fidelity

**Wave 3** *(blocked on Wave 2 material support)*

- [x] `04-03-PLAN.md` - Type reuse fidelity

**Wave 4** *(blocked on Wave 3 type support)*

- [x] `04-04-PLAN.md` - Connection topology fidelity

**Wave 5** *(blocked on Wave 4 topology support)*

- [x] `04-05-PLAN.md` - Complex and mapped geometry fidelity

**Wave 6** *(blocked on Wave 5 geometry support)*

- [x] `04-06-PLAN.md` - Broader classes, all-25 audit, and Phase 6 readiness

**Cross-cutting constraints:**

- Generated IFC acceptance requires spatial topology, attribute correctness,
  relationship correctness, IFC hierarchy/containment correctness, compile,
  reopen, and artifact secret-scan checks.
- Prompt and provider iterations must be versioned and tied to machine-readable
  experiment records.
- The model layer outputs BIM JSON 2.0 semantics only; raw IFC STEP and
  low-level helper objects remain compiler output.
- Unsupported material, type, topology, product-class, BRep, mapped geometry,
  and tessellation facts must be explicitly represented as losses or Draft
  content.
- Phase 3 scene-family splits and provenance remain binding for any BIMNet
  benchmark or training-related artifact.
- Every implementation behavior with defined inputs and outputs follows a
  recorded RED-GREEN TDD cycle.

**Status:** Complete - verified 2026-06-16

## Phase 5: Multi-turn Clarification Agent

**Goal:** Turn incomplete Chinese natural-language requests into explicit Draft
clarification state or valid formal BIM JSON 2.0, then compile the completed
simple-room Agent demo to a reopenable IFC2X3 file.

**Requirements:** AGENT-01, AGENT-02, AGENT-03

**Depends on:** Phase 1, Phase 2.5, Phase 3

**Canonical refs:**

- `.planning/phases/05-multi-turn-clarification-agent/05-SPEC.md`
- `.planning/phases/05-multi-turn-clarification-agent/05-CONTEXT.md`
- `.planning/phases/05-multi-turn-clarification-agent/05-AI-SPEC.md`
- `.planning/phases/05-multi-turn-clarification-agent/05-RESEARCH.md`
- `.planning/phases/05-multi-turn-clarification-agent/05-VALIDATION.md`
- `.planning/phases/05-multi-turn-clarification-agent/05-GOAL-PROMPT.md`

**Explicit boundary:** Phase 5 builds the runtime clarification Agent, not
Phase 4 fidelity and not Phase 6 fine-tuning/deployment. The Agent asks Chinese
questions, keeps unknown required facts as Draft, and compiles IFC only after
formal BIM JSON 2.0 validation. The model/provider layer must not output raw
IFC, STEP text, low-level IFC helper entities, or compiler bookkeeping.

**Final acceptance artifact:**
`dataset/processed/agent-demo/simple-room/output.ifc`

**Plans:** 6 plans in 6 waves

**Wave 1**

- [x] `05-01-PLAN.md` - Agent state contract, transcript, missing facts, and
  redaction primitives

**Wave 2** *(blocked on Wave 1 completion)*

- [x] `05-02-PLAN.md` - Missing-fact diagnostics to bounded Chinese questions

**Wave 3** *(blocked on Wave 2 completion)*

- [x] `05-03-PLAN.md` - Answer merge and Draft/Formal transitions

**Wave 4** *(blocked on Wave 3 completion)*

- [x] `05-04-PLAN.md` - Fake/file providers and optional Anthropic-compatible
  Mimo adapter

**Wave 5** *(blocked on Wave 4 completion)*

- [x] `05-05-PLAN.md` - Scripted Chinese clarification demo to IFC

**Wave 6** *(blocked on Wave 5 completion)*

- [x] `05-06-PLAN.md` - Final verification, summary, security review, and
  roadmap/state update

**Cross-cutting constraints:**

- Chinese-first interaction with 1-3 user-facing questions per turn.
- No silent defaults when required facts are unknown.
- Draft state is explicit and never compiled.
- Formal BIM JSON 2.0 validation gates IFC compilation.
- Fake/file providers are deterministic; live Mimo smoke is optional and
  secret-safe.
- The final phase gate is a generated, reopenable IFC file.

**Status:** Complete - verified 2026-06-15

## Phase 6: Multi-agent Prompt Reliability, Data Expansion, Fine-tuning, and Deployment

**Goal:** Build a traceable multi-agent prompt and audit architecture, expand
approved training data only after reliability metrics exist, compare prompt-only,
conditional repair, optional RAG, and fine-tune approaches, then package the
supported text2IFC service.

**Requirements:** PROMPT-01, AGENT-04, AGENT-05, REPAIR-01, OBS-01, MODEL-01,
MODEL-02, DEPLOY-01

**Depends on:** Phase 3, Phase 4, Phase 5

**Canonical refs:**

- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-SPEC.md`
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-CONTEXT.md`
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-AI-SPEC.md`
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-RESEARCH.md`
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-VALIDATION.md`
- `.planning/phases/06-multiagent-prompt-reliability-data-expansion-and-deployment/06-ACCEPTANCE-TRACE-REPORT.md`
- `docs/architecture/phase-6-multiagent-design.md`

**Explicit boundary:** Phase 6 starts with prompt registry, traceability, and
multi-agent responsibility separation before data expansion or fine-tuning.
Design Brief captures user intent; BIM JSON Generator emits BIM JSON 2.0 or
Draft; failure routing decides whether no repair is needed, a conditional
repair attempt is safe, Draft clarification is required, or the run must block;
Audit Agent reviews semantic coverage but cannot override deterministic
validation, compile, reopen, generated-IFC, run-report, split, or secret-scan
gates.

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `06-00-PLAN.md` - Prompt registry and multi-agent design contract

**Wave 1** *(blocked on Wave 0 prompt traceability)*

- [x] `06-01-PLAN.md` - Design Brief Agent contract

**Wave 2** *(blocked on Wave 1 Design Brief contract)*

- [x] `06-02-PLAN.md` - BIM JSON Generator orchestration and conditional
  failure routing

**Wave 3** *(blocked on Wave 2 generation and failure-routing traceability)*

- [x] `06-03-PLAN.md` - Audit Agent and deterministic gate integration

**Wave 4** *(blocked on Wave 3 audit integration)*

- [x] `06-04-PLAN.md` - Experiment harness and reliability metrics

**Wave 5** *(blocked on Wave 4 experiment harness)*

- [x] `06-05-PLAN.md` - Data expansion and model decision

**Wave 6** *(blocked on Wave 5 model decision)*

- [x] `06-06-PLAN.md` - Deployable service and final multi-agent IFC demo

**Cross-cutting constraints:**

- All provider-backed prompt calls must use a versioned prompt template,
  template hash, structured renderer inputs, and durable trace artifacts.
- BIM JSON Schema remains the only BIM JSON structural truth.
- The model layer outputs Design Brief, BIM JSON 2.0, Draft updates, or audit
  reports only; raw IFC, STEP text, STEP IDs, and low-level helper entities
  remain forbidden.
- Repair is not required for successful runs. Failure routing must record
  whether no repair was needed, repair was attempted, Draft clarification was
  required, or the run blocked. Any repair attempt may not invent missing user
  facts and must return Draft questions when feedback cannot be resolved from
  known facts.
- Audit Agent cannot pass failed deterministic gates.
- Every Phase 6 run must write a generated `report.md` as the human-review
  entry point. The report must expose the original input, Design Brief,
  rendered prompt, raw output, parsed BIM JSON or Draft, validation feedback,
  geometry feedback, failure/repair route, audit result, metrics, final IFC
  path when compiled, and links or paths to the source trace sidecars.
- Dataset expansion must preserve license status, source provenance, sidecar
  losses, and Phase 3 scene-family splits.
- Fine-tuning is selected only if measured prompt-only, conditional repair, and
  optional RAG baselines justify it.
- All conversation-specific work happens in the C-drive `multiagent-design`
  worktree; the E-drive working tree is not edited.

**Status:** Complete - verified 2026-06-21

## Phase 6.1: Live Mimo Multi-agent Pipeline (INSERTED)

**Goal:** Replace the Phase 6 fake-provider acceptance claim with an observable,
Chinese-first, real-Mimo multi-agent pipeline that reaches validated BIM JSON
2.0 or an explicit canonical Draft, compiles accepted Formal output to IFC2X3,
and records exact provider evidence without supervisor-authored semantic facts.

**Requirements:** LIVE-01, LIVE-02, LIVE-03, LIVE-04, LIVE-05, LIVE-06, OBS-02

**Depends on:** Phase 6

**Canonical refs:**

- `.planning/phases/06.1-live-mimo-multiagent-pipeline/06.1-SPEC.md`
- `.planning/phases/06.1-live-mimo-multiagent-pipeline/06.1-CONTEXT.md`
- `.planning/phases/06.1-live-mimo-multiagent-pipeline/06.1-AI-SPEC.md`
- `.planning/phases/06.1-live-mimo-multiagent-pipeline/06.1-RESEARCH.md`
- `.planning/phases/06.1-live-mimo-multiagent-pipeline/06.1-VALIDATION.md`

**Explicit boundary:** Every acceptance run calls the configured Mimo Anthropic
API for the Design Brief Agent, BIM JSON Generator, and Audit Agent. Repair also
uses Mimo when deterministic feedback makes repair eligible. Fake/file
providers remain available only for isolated unit tests and replay; their output
cannot support a live quality, completion, or deployment claim. The Observer is
not a semantic agent and may never delete ambiguity, add facts, or reinterpret
user intent to force a run through a gate.

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `06.1-00-PLAN.md` - Real Mimo envelope, streaming, and trace contract

**Wave 1** *(verified on Wave 0 exact response provenance)*

- [x] `06.1-01-PLAN.md` - Dynamic Design Brief Agent and clarification ownership

**Wave 2** *(verified on Wave 1 readiness contract)*

- [x] `06.1-02-PLAN.md` - Real Chinese multi-turn orchestration

**Wave 3** *(verified on Wave 2 clarified Design Brief)*

- [x] `06.1-03-PLAN.md` - Formal/Draft Generator contracts and output routing

**Wave 4** *(verified on Wave 3 terminal generation route)*

- [x] `06.1-04-PLAN.md` - Conditional Mimo repair without supervisor mutation

**Wave 5** *(verified on Wave 4 terminal generation route)*

- [x] `06.1-05-PLAN.md` - Real Mimo Audit and generated review report

**Wave 6** *(blocked on final IFC acceptance gates)*

- [x] `06.1-06-PLAN.md` - Live acceptance matrix, IFC artifact, and final review

**Acceptance artifacts:**

- `dataset/processed/agent-demo/phase6.1-mimo-live/output.ifc`
- `dataset/processed/agent-demo/phase6.1-mimo-live/report.md`
- A trace bundle containing original Chinese input, conversation turns,
  Design Brief prompt/request/raw response/parsed output, Generator evidence,
  validation and geometry feedback, conditional repair evidence, Audit
  evidence, provider `id`/`model`/`stop_reason`/`usage`, event stream, metrics,
  and secret-scan result.
- Live matrix sidecars also cover non-IFC terminal outcomes: `unknown-answer`
  must stop at canonical Draft after the user says a required fact is unknown,
  and `invalid-contract` replay must block as `unknown_contract` while staying
  excluded from live-quality metrics.

**Status:** Complete - verified with real Mimo and final IFC gates 2026-06-23

## Phase 6.2: Interactive CLI with OpenAI-Compatible Mimo Agent Orchestration (INSERTED)

**Goal:** Turn the Phase 6.1 scripted-answer live workflow into a Chinese-first
interactive CLI where the user types the request and clarification answers,
while the system persists role-isolated Mimo evidence, deterministic gates,
generated report, and a final IFC2X3 artifact.

**Requirements:** CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-07

**Depends on:** Phase 6.1

**Canonical refs:**

- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-SPEC.md`
- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-CONTEXT.md`
- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-AI-SPEC.md`
- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-RESEARCH.md`
- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-VALIDATION.md`
- `.planning/phases/06.2-interactive-cli-with-openai-compatible-mimo-agent-orchestration/06.2-PLAN-OUTLINE.md`
- `docs/reference/mimo-openai-api.md`

**Explicit boundary:** Phase 6.2 prioritizes the local CLI clarification
experience over public API/service work. It may use OpenAI Agents SDK only if
Wave 0 proves compatibility with Mimo Chat Completions and preserves required
trace evidence. Otherwise the native text2IFC orchestrator plus OpenAI Python
SDK provider remains the implementation path. Fake/file/replay providers remain
unit-test tools and cannot satisfy live CLI acceptance.

**Final acceptance artifacts:**

- `dataset/processed/agent-demo/phase6.2-interactive-cli/sessions.sqlite`
- `dataset/processed/agent-demo/phase6.2-interactive-cli/final-acceptance.json`
  naming the accepted `session_id` and `session_hash`
- `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/output.ifc`
- `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/report.md`
- `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/session-export.json`
- Large-object artifacts linked from the session DB as needed.

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `06.2-00-PLAN.md` - OpenAI Agents SDK research and OpenAI-compatible
  Mimo compatibility checkpoint

**Wave 1** *(blocked on Wave 0 provider/framework decision)*

- [x] `06.2-01-PLAN.md` - Interactive CLI session shell, shared DB, and
  query/resume/export interface

**Wave 2** *(blocked on Wave 1 durable session shell)*

- [x] `06.2-02-PLAN.md` - Interactive Design Brief clarification loop

**Wave 3** *(blocked on Wave 2 ready Design Brief or canonical Draft routing)*

- [x] `06.2-03-PLAN.md` - BIM JSON generation and deterministic IFC gates

**Wave 4** *(blocked on Wave 3 terminal generation and gate state)*

- [x] `06.2-04-PLAN.md` - Audit, conditional repair, and generated report
  integration

**Wave 5** *(blocked on Wave 4 generated report integration)*

- [x] `06.2-05-PLAN.md` - Interactive acceptance matrix and final
  Codex-as-user CLI IFC demo

**Wave 6** *(blocked on Wave 5 final artifact bundle)*

- [x] `06.2-06-PLAN.md` - Final verification, security review, and roadmap
  state update

**Cross-cutting constraints:**

- All Phase 6.2 work happens in the C-drive `multiagent-design` worktree; the
  E-drive working tree is not edited.
- The CLI may support scripted stdin for deterministic tests, but the scripted
  path must exercise the same code path as a human terminal session.
- The shared SQLite session DB is the primary evidence container for Phase 6.2
  CLI runs. Each run receives a stable `session_id` and `session_hash`;
  artifact files are linked payloads or exported review bundles.
- Session query, resume, and export commands are part of the Phase 6.2 product
  surface, not optional debug helpers.
- Final acceptance requires a real-time UAT in which Codex acts as the user and
  Mimo acts as the Agent provider. Scripted stdin is regression support, not the
  highest acceptance evidence.
- Real-provider claims require real Mimo response IDs, model, finish reason,
  usage, raw output, prompt ID/hash, parsed output, and evidence-class labels.
- A truncated OpenAI-compatible response (`finish_reason: length`) blocks
  semantic acceptance.
- The model layer outputs Design Brief, BIM JSON 2.0, canonical Draft, repair
  output, or Audit only; raw IFC/STEP and low-level IFC helper objects remain
  forbidden.
- Formal BIM JSON 2.0 validation gates IFC compilation; Draft and blocked
  outcomes write reports but no IFC.
- Every CLI run must generate `report.md` from session DB records and linked
  artifacts so the user can
  review original input, transcript, prompts, raw outputs, parsed outputs,
  gate feedback, route, metrics, Audit, and final artifact paths in one file.
- OpenAI Agents SDK adoption is conditional on Wave 0 evidence; a rejected SDK
  does not block the native OpenAI SDK provider path.

**Status:** Complete - verified 2026-06-26 with accepted live IFC session
`0fe9f14742b5c5d7`

## Phase 6.2-fix: Real-time REPL CLI UAT Correction (INSERTED)

**Goal:** Correct the Phase 6.2 acceptance gap by delivering a true
Chinese-first terminal REPL where the user types a request, sees each
Mimo-authored clarification question before answering, and receives a validated
IFC2X3 artifact plus a DB-backed review report.

**Requirements:** CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-07, CLI-08,
CLI-09, AGENT-05, REPAIR-01, OBS-01

**Depends on:** Phase 6.2

**Canonical refs:**

- `.planning/phases/06.2-fix-real-time-repl-cli-uat/06.2-fix-SPEC.md`
- `.planning/phases/06.2-fix-real-time-repl-cli-uat/06.2-fix-PLAN-OUTLINE.md`

**Explicit boundary:** This phase does not replace the Phase 6.2 backend
pipeline, provider path, session DB, query/export commands, Generator, Audit,
or compiler. It fixes the user-facing acceptance boundary and the trust gates
around accepted IFC output. Scripted stdin, prewritten answer files, fake
providers, and replay evidence remain regression tools only and cannot satisfy
final Phase 6.2-fix acceptance. After UAT defect 003, generated-IFC gate
feedback must reach decisive Audit before acceptance, and confirmed geometry
failures must route to bounded repair/generation or explicit blocking. After
UAT defect 004, Formal acceptance must also prove Design-Brief semantic
coverage: geometry expectations for supported rectangular rooms derive from
user facts rather than candidate wall placements alone, and unsupported
explicit facts remain Draft/blocked unless the user waives them. After UAT
defect 005, parseable invalid Formal Generator output must enter bounded
repair/regeneration when diagnostics are actionable instead of blocking only
because no validated `candidate.json` exists.

**Final acceptance artifacts:**

- `dataset/processed/agent-demo/phase6.2-fix-repl/sessions.sqlite`
- `dataset/processed/agent-demo/phase6.2-fix-repl/final-acceptance.json`
- `dataset/processed/agent-demo/phase6.2-fix-repl/runs/<session_hash>/output.ifc`
- `dataset/processed/agent-demo/phase6.2-fix-repl/runs/<session_hash>/report.md`
- `dataset/processed/agent-demo/phase6.2-fix-repl/runs/<session_hash>/session-export.json`

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `06.2-fix-00-PLAN.md` - Failure reproduction and REPL acceptance contract

**Wave 1** *(blocked on Wave 0 RED tests)*

- [x] `06.2-fix-01-PLAN.md` - Chinese REPL entrypoint and stepwise Design
  Brief loop

**Wave 2** *(blocked on Wave 1 REPL interaction)*

- [x] `06.2-fix-02-PLAN.md` - REPL-to-IFC route, report evidence, and strict
  verifier

**Wave 3** *(blocked on Wave 2 verifier and report gates)*

- [ ] `06.2-fix-03-PLAN.md` - Real Mimo REPL UAT, final verification, and
  documentation closure

**Wave 4** *(inserted after Wave 3 UAT defect 003)*

- [x] `06.2-fix-04-PLAN.md` - Geometry feedback to Audit and bounded repair
  loop

**Wave 5** *(inserted after Wave 4 live UAT review defect 004)*

- [x] `06.2-fix-05-PLAN.md` - Semantic fidelity gate and BIM JSON capability
  contract

**Wave 6** *(inserted after Wave 5 final UAT defect 005)*

- [x] `06.2-fix-06-PLAN.md` - Invalid Formal recovery loop and Design Brief
  gate normalization

**Cross-cutting constraints:**

- Final accepted evidence must be `interaction_mode: "human_repl_live"` and
  `input_source: "terminal"`.
- The REPL must print/persist Mimo's assistant question before reading the
  user's answer.
- Scripted stdin, file input, fake providers, and replay evidence cannot
  satisfy final acceptance even if they produce valid IFC.
- Regression tests may use fake providers and scripted IO, but they must be
  labelled as regression evidence only.
- Formal BIM JSON 2.0 validation still gates IFC compilation.
- Generated-IFC compile, reopen, and geometry feedback must be available to
  decisive Audit before final acceptance.
- Audit may classify failed deterministic gates but cannot override them.
- True candidate geometry failures route to bounded repair/generation; gate
  disputes block for human/developer review.
- Supported rectangular-room semantic geometry expectations derive from the
  Design Brief and explicit user facts, not only from candidate wall boxes.
- Every explicit user fact must be represented, compiler-generated,
  unsupported/Draft, waived by the user, or blocked as unknown capability
  before Formal acceptance.
- Custom property text preservation cannot count as faithful IFC semantic
  support.
- Draft, quit, and blocked outcomes write trace/report artifacts but no IFC.
- All work remains in the C-drive `multiagent-design` worktree; the E-drive
  working tree is not edited.

**Status:** Waves 0-2 implemented and automatically verified 2026-06-26.
Wave 3 real UAT found defects 001 and 002 that were fixed, then exposed UAT
defect 003: Audit accepted before final geometry feedback existed. Wave 4 is
implemented and automatically verified: generated-IFC gate feedback now reaches
Audit before acceptance, Audit override attempts block, and Audit `revise` can
route true geometry failures to bounded repair and a second gate/Audit pass.
Follow-up live session `d462b95089755d47` proved the real REPL can generate a
viewable IFC, but review exposed defect 004: candidate-derived geometry
expectations can be circular, and unsupported explicit facts such as inward
door opening can be silently lost. Wave 5 is now planned to add semantic
capability and coverage gates before final Phase 6.2-fix acceptance. Wave 5
implementation and automated verification are complete: semantic geometry,
semantic capability, semantic coverage, report, Audit evidence, and verifier
gates are implemented. Final UAT then exposed defect 005: parseable invalid
Formal Generator output was not treated as a repair source, so repair blocked
with `previous_candidate=None`. Wave 6 is implemented and automatically
verified: parseable invalid Formal output can now enter bounded repair when
diagnostics are actionable, repair route evidence records the invalid Formal
source, and Design Brief outside-boundary wording is normalized for semantic
geometry gates. Final Phase 6.2-fix acceptance still requires a fresh real
human-terminal Mimo REPL run after Wave 6.

## Phase 6.3: Gate-Audit Fusion, Dynamic Routing, and Compact Trace (INSERTED)

**Goal:** Add scalable complex-building reliability to the live text2IFC
pipeline by fusing deterministic gates with dynamic Audit reasoning, routing
failures back to the correct stage, and reducing default trace artifacts enough
to speed up normal generation runs without losing auditability.

**Requirements:** GEN-03, GATE-01, GATE-02, GATE-03, ROUTE-01, TRACE-02,
AGENT-04, AGENT-05, REPAIR-01, OBS-01

**Depends on:** Phase 6.2-fix

**Canonical refs:**

- `.planning/phases/06.3-gate-audit-fusion-dynamic-routing-and-compact-trace/06.3-SPEC.md`
- `.planning/phases/06.3-gate-audit-fusion-dynamic-routing-and-compact-trace/06.3-PLAN-OUTLINE.md`

**Explicit boundary:** Phase 6.3 is not Phase 7 and not a BIM JSON schema
redesign. It improves the current live REPL pipeline so complex multi-storey
requests can be dynamically audited, safely blocked, and routed to Design
Brief, Generator, local repair, Draft, or gate-dispute review. The phase may
add sidecars such as `expected-facts.json`, `gate-summary.json`,
`route-decision.json`, and `trace-manifest.json`, but JSON Schema remains the
single BIM JSON structural truth. Single-room and two-room demos are smoke
regressions only; the primary target is complex multi-storey no-false-accept
behavior and accurate routing. Compact trace exists to speed normal generation
and reduce review noise while preserving debug/full trace on demand.

**Plans:** 7 plans in 7 waves

**Wave 0**

- [x] `06.3-00-PLAN.md` - Complex multi-storey failure fixture and
  no-false-accept baseline

**Wave 1** *(blocked on Wave 0 fixture baseline)*

- [x] `06.3-01-PLAN.md` - Gate-Audit evidence bundle and applicability states

**Wave 2** *(blocked on Wave 1 shared evidence bundle)*

- [x] `06.3-02-PLAN.md` - Dynamic expected facts from Design Brief

**Wave 3** *(blocked on Wave 2 expected facts)*

- [x] `06.3-03-PLAN.md` - Dynamic completeness, containment, and opening/fill
  gates

**Wave 4** *(blocked on Wave 3 dynamic gates)*

- [x] `06.3-04-PLAN.md` - Route decisions and bounded stage back-routing

**Wave 5** *(blocked on Wave 4 route decisions)*

- [x] `06.3-05-PLAN.md` - Compact trace levels and artifact write reduction

**Wave 6** *(blocked on Wave 5 compact trace)*

- [x] `06.3-06-PLAN.md` - Complex-building matrix, final verification, and
  documentation closure

**Cross-cutting constraints:**

- Gate and Audit form one review system: gates provide deterministic evidence,
  Audit provides dynamic classification, and failed applicable gates cannot be
  accepted by Audit wording.
- Every nontrivial gate must declare applicability, basis, and source evidence.
- Expected facts derive from Design Brief and transcript evidence, not
  hard-coded floor, room, wall, door, or window counts.
- Non-two-storey coverage must exercise expected-fact extraction, dynamic
  gates, and route decisions; extraction-only coverage is not enough.
- Gate summary, Audit input, route decision, report, and trace manifest must
  bind to the same candidate through matching evidence hashes.
- Stage routes must distinguish Design Brief revision, Generator regeneration,
  local repair, Draft/clarification, gate dispute, and blocked failure.
- Back-routing is bounded and observable; stalled or non-improving loops block
  with evidence.
- Compact trace is the default to reduce normal run file writes and latency;
  debug/full trace remains available for provider and prompt audit. Compact
  non-accept routes must still preserve or link recoverable failure evidence.
- Phase 6.3 may add orchestration sidecars but does not silently change BIM
  JSON 2.0 schema or add a second BIM JSON model.
- All work remains in the C-drive `multiagent-design` worktree; the E-drive
  working tree is not edited.

**Status:** Complete - verified 2026-07-02. Phase 6.3 closes the reliability
architecture for complex-building no-false-accept, dynamic Gate/Audit routing,
hash-bound evidence, and compact trace. The complex two-storey matrix case is
currently an honest blocked route, not a claimed accepted live IFC.

## Phase 6.4: Feedback Routing Loop MVP and Live DeepSeek Matrix (INSERTED)

**Goal:** Turn the current mostly linear text2IFC workflow into a
feedback-capable loop by normalizing validation, compiler, gate, Audit,
provider, and runtime failures into structured Issues, aggregating them into
RouteDecision v2, recording bounded feedback rounds, producing matrix
artifacts, and proving the result with deterministic TDD plus real DeepSeek
live workflow evidence.

**Requirements:** GEN-02, GEN-03, GATE-01, ROUTE-01, TRACE-02, AGENT-04,
AGENT-05, REPAIR-01, OBS-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-08

**Depends on:** Phase 6.3

**Canonical refs:**

- `.planning/phases/06.4-feedback-routing-loop-mvp-and-live-deepseek-matrix/06.4-SPEC.md`
- `.planning/phases/06.4-feedback-routing-loop-mvp-and-live-deepseek-matrix/06.4-PLAN-OUTLINE.md`

**Explicit boundary:** Phase 6.4 prioritizes the feedback loop mechanism over
making one complex two-storey prompt pass. It does not introduce RAG,
fine-tuning, deployment changes, large BIM JSON schema redesign, or
case-specific production fixes. Deterministic TDD/regression tests must pass
before real DeepSeek live tests. Live acceptance requires real provider
evidence and cannot be satisfied by fake/file/replay providers, prewritten
`answers.json`, or exact scripted clarification transcripts.

**Plans:** 9 plans in 9 waves

**Wave 0**

- [x] `06.4-00-PLAN.md` - Issue and RouteDecision v2 contracts

**Wave 1** *(blocked on Wave 0 contracts)*

- [x] `06.4-01-PLAN.md` - Failure source Issue normalization

**Wave 2** *(blocked on Wave 1 normalizers)*

- [x] `06.4-02-PLAN.md` - Bounded feedback round controller

**Wave 3** *(blocked on Wave 2 feedback rounds)*

- [x] `06.4-03-PLAN.md` - Matrix artifacts and report integration

**Wave 4** *(blocked on Wave 3 matrix/report artifacts)*

- [x] `06.4-04-PLAN.md` - Adaptive CLI and live UAT harness

**Wave 5** *(blocked on Wave 4 live UAT harness)*

- [x] `06.4-05-PLAN.md` - Real DeepSeek live matrix and final verification

**Wave 6** *(supplemental verification; blocked on Wave 5 live evidence)*

- [x] `06.4-06-PLAN.md` - Supplemental live chain coverage evidence

**Wave 7** *(manual-IFC bugfix; blocked on Wave 6 evidence)*

- [x] `06.4-07-PLAN.md` - Geometry truth, stair frame, and Gate/Audit redesign

**Wave 8** *(bounded orchestration stabilization; blocked on Wave 7)*

- [x] `06.4-08-PLAN.md` - Gate-authoritative bounded regeneration and live closure

**Cross-cutting constraints:**

- New machine-readable workflow fields, JSON keys, enum values, issue types,
  route names, structured logs, and tests use English control vocabulary.
- Chinese raw user input is preserved as source text; Chinese may appear in
  transcripts, reports, or optional `message_zh`, but not as control keys.
- JSON Schema remains the single BIM JSON structural truth.
- Every terminal non-accept run with a session directory writes
  `issues.json`, `route-decision.json`, `feedback-rounds.json`,
  `case-result.json`, and `report.md`.
- Feedback loops are bounded to `max_feedback_rounds = 2` by default. Early
  non-improvement requires unchanged structured issue evidence, not merely an
  unchanged issue count.
- DeepSeek secrets, headers, private base URLs, and token values never appear
  in prompts, traces, reports, commits, or final answers.
- `finish_reason=length` or equivalent provider truncation blocks acceptance.
- Real DeepSeek live acceptance happens only after deterministic TDD and matrix
  tests pass.

**Status:** Supplemental Waves 7 and 8 complete and verified 2026-07-11. The
final real DeepSeek session `5a19ce5b34bce809` executed two Generator
regenerations, passed the complete deterministic Gate summary and Audit, and
produced a reopened IFC2X3 artifact. Complete regression passed 678 tests.
Manual visual IFC review remains a separate human acceptance activity.

**Prior verified scope:** Phase 6.4 has normalized
Issues, RouteDecision v2, bounded feedback rounds, generated matrix/report
artifacts, adaptive live-UAT guardrails, a real DeepSeek JSON smoke, a real
DeepSeek accepted IFC workflow, a real DeepSeek non-accept Draft route, a
supplemental live-chain coverage report proving 8 / 8 required workflow links,
a chain-completeness report proving the required deterministic route matrix
with explicit route boundaries, a route-level live UAT supplement covering all
defined Phase 6.4 routes, and zero secret findings in generated Phase 6.4
artifacts.
