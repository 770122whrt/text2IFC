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
- [ ] `02-03-PLAN.md` - Selected property and predefined-type fidelity

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] `02-04-PLAN.md` - Verifier proof, CLI, complete acceptance, and docs

**Cross-cutting constraints:**

- BIM JSON 1.0 validation runs before any IFC output path is touched.
- Tests inspect serialized and reopened IFC instead of compiler bookkeeping.
- Output replacement occurs only after in-memory and reopened verification.
- Every behavior follows a recorded RED-GREEN TDD cycle.

**Status:** Planned - ready to execute

## Phase 3: Text-to-JSON Dataset and Baseline

**Goal:** Build provenance-linked text/JSON pairs, establish a structured-output
Text-to-JSON baseline, evaluate it, and demonstrate the first end-to-end
Text-to-JSON-to-IFC request.

**Requirements:** TEXT-01, TEXT-02, TEXT-03, E2E-01

**Depends on:** Phase 1, Phase 2

**Status:** Deferred

## Phase 4: High-fidelity IFC Round Trip

**Goal:** Preserve precise placement, orientation, materials, openings, filling
relationships, and supported topology, while reporting every unsupported loss.

**Requirements:** GEO-01, GEO-02, GEO-03, GEO-04

**Depends on:** Phase 2

**Status:** Deferred

## Phase 5: Multi-turn Clarification Agent

**Goal:** Turn incomplete natural-language requests into valid BIM JSON through
targeted follow-up questions and persistent conversation state.

**Requirements:** AGENT-01, AGENT-02, AGENT-03

**Depends on:** Phase 1, Phase 3

**Status:** Deferred

## Phase 6: Data Expansion, Fine-tuning, and Deployment

**Goal:** Expand approved training data, compare fine-tuning with the baseline,
select the deployable approach, and package the full text2IFC service.

**Requirements:** MODEL-01, MODEL-02, DEPLOY-01

**Depends on:** Phase 3, Phase 4, Phase 5

**Status:** Deferred
