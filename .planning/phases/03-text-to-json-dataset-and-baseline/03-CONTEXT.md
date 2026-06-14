# Phase 3: Text-to-JSON Dataset and Baseline - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning
**Source:** Phase 3 user discussion plus Phase 2.5 handoff

<domain>
## Phase Boundary

Phase 3 turns the Phase 2.5 IFC2X3 semantic graph foundation into a measured
Text-to-JSON baseline. It does not fine-tune a production model and does not
build the multi-turn clarification Agent. The primary product is a trustworthy
dataset/evaluation loop:

Natural Language -> formal BIM JSON 2.0 -> validation -> IFC2X3 compilation.

The IFC-to-BIM-JSON path is offline label construction. Runtime inference
stays Natural Language -> BIM JSON 2.0 -> IFC compiler.
</domain>

<spec_lock>
## Locked Requirements

The requirements, boundaries, and acceptance criteria in `03-SPEC.md` are
locked. Planning must not weaken the split-by-scene-family rule, the
no-fabrication rule, the formal-versus-Draft separation, or the requirement
that the baseline output BIM JSON rather than raw IFC STEP text.
</spec_lock>

<decisions>
## Implementation Decisions

### Dataset and split policy

- **D-01:** BIMNet is the primary authorized Phase 3 source. It may be used
  locally for extraction, dataset construction, baseline evaluation, and local
  model training according to `dataset/manifests/bimnet-ifc2x3.jsonl`.
- **D-02:** Legacy `dataset/ifc/train` and `dataset/ifc/test` folders are
  source organization only. They are not model splits.
- **D-03:** Split assignment is by `scene_family`, not file path. A family
  cannot appear in more than one split.
- **D-04:** The split manifest is produced before any text generation,
  augmentation, baseline run, or fine-tuning export.
- **D-05:** buildingSMART IFC4/IFC4X3 samples remain a separate cross-schema
  and relationship fixture track, not BIMNet training records.

### Formal targets and Draft handling

- **D-06:** All 25 current BIMNet extraction outputs are Drafts because the
  source contains explicit losses beyond the Phase 2.5 generation profile.
- **D-07:** Phase 3 may construct a formal gold target from a Draft
  `partial_document` only when that supported-scope document validates as
  formal BIM JSON 2.0.
- **D-08:** Promoting a supported-scope partial document to a formal target is
  not a claim of full IFC fidelity. The source losses stay in a sidecar tied to
  the target by file ID, source hash, and scene family.
- **D-09:** Missing materials, type relationships, connection topology,
  arbitrary geometry, unsupported properties, or source-specific facts are
  never invented for a formal target.
- **D-10:** Draft records may be exported as future clarification examples, but
  the Phase 3 baseline evaluates formal targets unless an experiment declares a
  non-formal target kind explicitly.

### Text pair policy

- **D-11:** Text is generated from formal BIM JSON 2.0 targets and sidecar
  provenance, not from unsupported source IFC facts.
- **D-12:** Every text/JSON pair records source file ID, source SHA-256, scene
  family, split, target path, text style, generation template, and review
  status.
- **D-13:** Generated text may mention only facts present in the target JSON,
  or clearly state that omitted source fidelity is outside the current target
  when producing a Draft/clarification record.
- **D-14:** Pair manifests must be deterministic and drift-checkable.

### Structured-output baseline

- **D-15:** The model layer outputs formal BIM JSON 2.0. It does not output
  `.ifc`, STEP text, `IfcCartesianPoint`, `IfcDirection`, `IfcOwnerHistory`,
  STEP line IDs, or compiler bookkeeping.
- **D-16:** The baseline runner is provider-agnostic. Tests use a deterministic
  fake provider; optional live providers require explicit configuration.
- **D-17:** A prediction is not accepted until JSON parsing, schema validation,
  semantic validation, and formal/Draft target-kind checks pass.
- **D-18:** Raw provider responses and metadata are stored separately from
  parsed predictions to keep evaluation reproducible and debuggable.

### Evaluation and next-phase routing

- **D-19:** Evaluation reports invalid JSON and invalid BIM JSON as first-class
  failures before comparing semantic fields.
- **D-20:** Evaluation includes document validity, class identity, entity
  counts, properties, relationships, placement, geometry, IFC compilation, and
  reopened IFC checks.
- **D-21:** Metrics must be split-aware. Train metrics cannot be used to claim
  validation or test performance.
- **D-22:** RAG is an experiment after baseline error analysis, not a Phase 3
  correctness dependency.
- **D-23:** Fine-tuning is deferred until the dataset and evaluation harness
  are stable and baseline results exist.
- **D-24:** Runtime missing-data questions and multi-turn state are Phase 5.
  Phase 3 may only produce labeled clarification targets and error categories.

### the agent's Discretion

- Exact split ratios, provided there is a validation and test split and family
  leakage is impossible.
- Exact Python module names for text dataset, baseline, and evaluation code.
- Exact prompt wording for the baseline, provided it requests formal BIM JSON
  2.0 and forbids raw IFC/STEP output.
- Exact metric serialization format, provided it is machine-readable and
  includes a markdown report.
</decisions>

<specifics>
## Specific Ideas

- Recommended split shape for 19 families: deterministic approximately
  70/15/15 by family count with a fixed seed, then inspect entity/loss
  distribution to avoid a meaningless validation/test split.
- The first formal gold set can be a supported-scope projection of BIMNet
  Drafts. It must carry a sidecar loss ledger so Phase 4 can later close
  fidelity gaps without rewriting the target history.
- The first baseline should have two modes:
  - `fake` or `fixture` mode for deterministic tests and CI.
  - optional live provider mode for an actual model run when credentials are
    available.
- The evaluation harness should be provider-independent. It should compare
  prediction files to gold files, not call a model.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Locked Phase 3 behavior

- `.planning/phases/03-text-to-json-dataset-and-baseline/03-SPEC.md` - locked
  requirements, boundaries, and pass/fail acceptance criteria.
- `.planning/REQUIREMENTS.md` - TEXT-01, TEXT-02, TEXT-03, and E2E-01.
- `.planning/ROADMAP.md` - phase dependency and later-phase boundaries.
- `.planning/STATE.md` - current state, risks, and active decisions.

### Phase 2.5 foundation

- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-SPEC.md` -
  formal/Draft, no-fabrication, capability, placement, and compiler rules.
- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-CONTEXT.md` -
  locked semantic graph and IFC-class boundary decisions.
- `.planning/phases/02.5-bim-json-2.0-ifc-semantic-graph/02.5-06-SUMMARY.md`
  - all-25 BIMNet handoff and extraction evidence.
- `docs/reference/bim-json-2.0.md` - generated Formal and Draft reference.
- `docs/reference/ifc2x3-generation-profile.md` - supported compiler profile.

### Dataset inputs

- `dataset/manifests/bimnet-ifc2x3.jsonl` - source hashes, authorization,
  scene families, and approved uses.
- `dataset/processed/bim-json-2.0/scene-families.json` - 19 scene families.
- `dataset/processed/bim-json-2.0/extraction-audit.json` - all-25 Draft and
  loss accounting.
- `dataset/sources/CATALOG.md` - source catalog.

### Existing implementation

- `schemas/bim-json/2.0/schema.json` - formal BIM JSON 2.0 structural truth.
- `schemas/bim-json/draft/1.0/schema.json` - Draft Envelope structural truth.
- `src/text2ifc_contract/validation_v2.py` - formal semantic validation.
- `src/text2ifc_contract/draft.py` - Draft validation.
- `src/text2ifc_extractor/` - IFC2X3 extraction into formal/Draft payloads.
- `src/text2ifc_compiler/` - BIM JSON to IFC compiler and verification.
- `scripts/ifc_pipeline_v2/audit_bimnet.py` - all-25 audit and manifest
  generation pattern.
- `scripts/bim_json/compile_ifc.py` - existing compiler CLI boundary.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `text2ifc_contract.validation_v2.validate_v2_document` returns stable
  field-level diagnostics for formal BIM JSON 2.0.
- `text2ifc_contract.draft.validate_draft` validates Draft Envelopes and
  addressable loss/missing-fact paths.
- `text2ifc_extractor.extract_ifc2x3` returns `document` or `draft`, losses,
  source hash, and represented-plus-reported inventories.
- `text2ifc_compiler.compile_document` already rejects Draft Envelopes and
  atomically writes reopenable IFC for valid formal documents.
- Existing tests use `pytest` with `.deps/python312` on the Python path.

### Integration Points

- New dataset code should live under a clearly named text package, such as
  `src/text2ifc_text/`, and new CLIs under `scripts/text2json/`.
- Generated dataset artifacts should live under `dataset/processed/text2json/`
  and split manifests under `dataset/splits/`.
- Prediction and metric artifacts should be generated under
  `dataset/processed/text2json/predictions/` and
  `dataset/processed/text2json/evaluations/`.
- Tests should live under `tests/text2json/` and should not require network
  access or live model credentials.
</code_context>

<deferred>
## Deferred Ideas

- Add retrieval over IFC class/property documentation if baseline errors show
  class/property lookup weakness.
- Fine-tune only after evaluation shows the baseline ceiling and the dataset is
  large enough or expanded with license-reviewed sources.
- Build the multi-turn clarification Agent after Draft/clarification examples
  and missing-fact policies stabilize.
- Extend formal targets toward full IFC fidelity after Phase 4 adds materials,
  type reuse, topology, and complex geometry.
</deferred>

---

*Phase: 03-text-to-json-dataset-and-baseline*
*Context gathered: 2026-06-14*
