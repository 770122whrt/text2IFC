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

**Goal:** Preserve material/type fidelity, complex source geometry, supported
connection topology, and broader product classes while reporting every
unsupported loss.

**Requirements:** GEO-03, GEO-04, GEO-05, IFC-06

**Depends on:** Phase 2.5

**Status:** Deferred

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

- [ ] `05-06-PLAN.md` - Final verification, summary, security review, and
  roadmap/state update

**Cross-cutting constraints:**

- Chinese-first interaction with 1-3 user-facing questions per turn.
- No silent defaults when required facts are unknown.
- Draft state is explicit and never compiled.
- Formal BIM JSON 2.0 validation gates IFC compilation.
- Fake/file providers are deterministic; live Mimo smoke is optional and
  secret-safe.
- The final phase gate is a generated, reopenable IFC file.

**Status:** Planned - ready to execute

## Phase 6: Data Expansion, Fine-tuning, and Deployment

**Goal:** Expand approved training data, compare fine-tuning with the baseline,
select the deployable approach, and package the full text2IFC service.

**Requirements:** MODEL-01, MODEL-02, DEPLOY-01

**Depends on:** Phase 3, Phase 4, Phase 5

**Status:** Deferred
