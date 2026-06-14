# Phase 3: Text-to-JSON Dataset and Baseline - Specification

**Created:** 2026-06-14
**Ambiguity score:** 0.11 (gate: <= 0.20)
**Requirements:** 10 locked

## Goal

Create a leak-free, provenance-linked Text-to-BIM-JSON dataset from authorized
IFC2X3 sources, run a structured-output Text-to-JSON baseline against formal
BIM JSON 2.0 targets, evaluate it with deterministic metrics, and demonstrate
one validated Natural Language -> BIM JSON 2.0 -> IFC2X3 loop.

## Background

Phase 2.5 established BIM JSON 2.0, the Draft Envelope, official IFC2X3
knowledge registries, deterministic IFC extraction, and a compiler profile for
the initial BIMNet architectural subset. The handoff is intentionally not a
training-ready dataset yet. All 25 authorized BIMNet source files currently
extract as Drafts because the source IFC contains explicit material, type,
connection, property-value, and complex-geometry losses beyond the Phase 2.5
formal generation profile.

Phase 3 therefore starts with dataset construction rather than model tuning.
It must split the 19 Matterport scene families before any text generation,
derive formal training targets only inside the supported generation profile,
preserve every omitted source fact in sidecar provenance, and keep
clarification/missing-data behavior as future Phase 5 work.

## Requirements

1. **Scene-family split manifest**: Assign train, validation, and test splits
   by Matterport scene family before text generation or augmentation.
   - Current: `dataset/processed/bim-json-2.0/scene-families.json` lists 19
     scene families but has `split_assignment: null`; legacy file folders leak
     `7y3`, `e9z`, and `px4` across train/test.
   - Target: A deterministic split manifest assigns each scene family and
     derived file ID to exactly one split, records the seed and policy, and
     rejects any file-level leakage.
   - Acceptance: A test proves no `scene_family` appears in more than one
     split and the manifest covers all 25 BIMNet file IDs exactly once.

2. **Training eligibility and provenance gate**: Use only records whose
   authorization permits local dataset construction and model training.
   - Current: `dataset/manifests/bimnet-ifc2x3.jsonl` records approved local
     uses, source hashes, schema, and training eligibility, but no Text-to-JSON
     dataset gate consumes it.
   - Target: Dataset builders reject missing hashes, non-IFC2X3 records,
     disabled `training_eligible`, or absent approved uses before producing
     text pairs.
   - Acceptance: Negative tests mutate one manifest record at a time and prove
     the builder refuses unsafe or unauthorized records with field-level
     diagnostics.

3. **Draft triage report**: Classify every Phase 2.5 Draft into explicit
   training usability buckets without discarding loss information.
   - Current: `extraction-audit.json` reports all 25 files as Drafts and
     aggregates 8,280 explicit losses, but Phase 3 has no per-record target
     policy.
   - Target: A triage artifact records for each source file whether the
     supported-scope partial document can become a formal gold target, which
     losses are kept only as sidecar provenance, and which records remain
     clarification or fidelity material.
   - Acceptance: A repeatable command writes a triage JSON whose counts match
     the extraction audit and whose unsupported/loss categories are preserved.

4. **Formal gold-set construction**: Build formal BIM JSON 2.0 targets only
   from source facts already represented by the Phase 2.5 generation profile.
   - Current: The extractor can return a Draft Envelope, but no Phase 3 path
     promotes compiler-ready supported-scope targets into a training gold set.
   - Target: A gold-set builder extracts the Draft `partial_document` when it
     passes formal BIM JSON 2.0 validation, writes it as a formal target, and
     writes a sidecar that keeps the original losses and source provenance.
   - Acceptance: The builder never invents materials, type reuse, connection
     topology, arbitrary BRep/tessellation, or user intent; every formal target
     validates with `validate_v2_document` and every omitted source fact remains
     listed in a sidecar.

5. **Text/JSON pair generation**: Generate provenance-linked natural-language
   prompts from formal gold targets.
   - Current: Legacy description scripts write free-form summaries from older
     IFC parsing, but they are not tied to BIM JSON 2.0, splits, or provenance.
   - Target: The pair builder produces JSONL records with `input_text`,
     `target_json_path`, `split`, `scene_family`, `source_file_id`, text style,
     source hash, and review status. Text variants include concise,
     enumerated, spatial, and property-focused forms.
   - Acceptance: Every pair references an existing formal target in the same
     split; no validation/test text is generated from train families; generated
     text contains no facts absent from the target JSON or sidecar.

6. **Draft and clarification records stay separate**: Preserve incomplete or
   unsupported source information for future Agent training without mixing it
   into the formal baseline target set.
   - Current: Draft Envelopes already contain `missing_facts`, `losses`, and
     `clarification_targets`, but Phase 3 has no dataset partition for them.
   - Target: Phase 3 may create a separate Draft training/enrichment manifest,
     but the structured-output baseline evaluates only formal BIM JSON 2.0
     targets unless an experiment explicitly declares a Draft target kind.
   - Acceptance: Dataset manifests distinguish `target_kind: formal` from
     `target_kind: draft_clarification`, and baseline evaluation refuses to
     score Draft records as formal predictions.

7. **Structured-output baseline**: Provide a reproducible baseline that
   converts natural language into formal BIM JSON 2.0 without generating raw
   IFC STEP text.
   - Current: No Text-to-JSON model runner or provider boundary exists.
   - Target: The baseline runner has a provider-agnostic interface, constrains
     output to BIM JSON 2.0, validates every prediction, stores raw response
     metadata separately from parsed JSON, and supports a deterministic fake
     provider for tests plus optional real provider adapters.
   - Acceptance: Baseline tests use a deterministic provider to prove valid
     predictions are accepted, invalid JSON/schema/semantic outputs are
     rejected with diagnostics, and no `.ifc` or STEP text is produced by the
     model layer.

8. **Evaluation harness**: Score predictions against gold targets with
   document, collection, field, placement, geometry, relationship, property,
   and IFC compilation metrics.
   - Current: Validation and compiler tests exist, but no Text-to-JSON
     evaluation command compares predictions to gold JSON.
   - Target: An evaluator reads a split manifest, gold targets, and prediction
     files, then writes machine-readable metrics plus a markdown error report.
   - Acceptance: Fixture tests prove metric calculations for parse success,
     schema validity, semantic validity, class accuracy, entity-count error,
     property F1, relationship endpoint accuracy, placement tolerance, geometry
     tolerance, IFC compile success, and reopened IFC success.

9. **First end-to-end spatial demo**: Demonstrate one complete request through
   the validated pipeline.
   - Current: JSON-to-IFC and IFC extraction are validated separately; no
     natural-language request enters the BIM JSON 2.0 compiler path.
   - Target: A demo command runs one approved sample from text to predicted
     BIM JSON, validation, IFC compilation, reopened IFC verification, and a
     final report.
   - Acceptance: The demo writes the input text, predicted JSON, diagnostics,
     output IFC, and reopened verification result; if the baseline prediction
     is incomplete, the command fails explicitly rather than filling values.

10. **RAG, fine-tuning, and Agent decision report**: Use baseline evidence to
    decide the next modeling work instead of assuming RAG or fine-tuning.
    - Current: The roadmap names later RAG/fine-tuning/Agent directions, but
      no metric-backed decision gate exists.
    - Target: Phase 3 produces a decision report that compares no-RAG baseline
      failures with candidate retrieval or fine-tuning needs, and identifies
      which errors belong to Phase 5 multi-turn clarification.
    - Acceptance: The report maps observed errors to at least schema/class,
      property, relationship, placement, geometry, missing-fact, and provider
      categories, and recommends whether Phase 4, Phase 5, or Phase 6 should
      handle each category.

## Boundaries

**In scope:**

- BIMNet IFC2X3 scene-family split and dataset manifests
- Training eligibility checks from the local authorization manifest
- Draft triage and formal supported-scope gold-set construction
- Text/JSON pair generation from formal BIM JSON 2.0 targets
- Separate Draft/clarification records for future work
- Provider-agnostic structured-output baseline runner
- Deterministic evaluation harness and metric reports
- One Natural Language -> BIM JSON 2.0 -> IFC2X3 demo
- Metric-backed recommendation for RAG, fine-tuning, and Agent phases

**Out of scope:**

- Fine-tuning a production model - Phase 6 compares and trains models after
  the dataset/evaluation contract is stable.
- Runtime multi-turn questioning - Phase 5 owns conversation state and
  targeted clarification.
- High-fidelity materials, type reuse, connections, arbitrary BReps,
  tessellation, and full topology - Phase 4 owns fidelity expansion.
- IFC4 or IFC4X3 output - Phase 3 remains an IFC2X3 text-to-formal-json
  baseline stage.
- Raw STEP generation by an LLM - BIM JSON remains the model contract and IFC
  is compiler output.
- Using buildingSMART IFC4/IFC4X3 samples as BIMNet training records - they
  remain a separate cross-schema fixture/evaluation track.
- Fabricating missing source or user facts - every absent fact is rejected,
  carried as Draft/sidecar loss, or deferred to clarification.

## Constraints

- JSON Schema Draft 2020-12 remains the only BIM JSON structural truth.
- Formal targets must pass `validate_v2_document` before they enter the
  baseline training/evaluation set.
- Dataset splits are grouped by `scene_family` before text generation.
- BIMNet data is local-authorized; manifests must not imply redistribution
  rights.
- Baseline provider adapters must be replaceable and testable without network
  access or secrets.
- Evaluation must not hide invalid outputs behind partial scoring.
- Every implementation behavior follows RED/GREEN/REFACTOR TDD where the
  behavior has defined inputs and outputs.

## Acceptance Criteria

- [ ] A scene-family split manifest covers all 25 BIMNet file IDs exactly once
      and rejects family leakage.
- [ ] Dataset builders refuse records without approved local training and
      dataset-construction uses.
- [ ] Draft triage preserves all 25 source statuses, loss counts, and sidecar
      provenance.
- [ ] Formal gold targets validate as BIM JSON 2.0 and every omitted source
      fact is retained outside the target.
- [ ] Text/JSON pairs are generated only after split assignment and reference
      same-split formal targets.
- [ ] Draft/clarification records are labeled separately and cannot be scored
      as formal baseline predictions.
- [ ] The structured-output baseline stores parsed predictions, raw metadata,
      and validation diagnostics without writing raw IFC text.
- [ ] The evaluation harness writes machine-readable metrics and a markdown
      report for fixture and baseline predictions.
- [ ] At least one spatial natural-language request completes the validator,
      compiler, and reopened-IFC checks.
- [ ] Phase 3 summary recommends next RAG, fine-tuning, and Agent steps from
      observed metrics, not assumptions.

## Ambiguity Report

| Dimension | Score | Min | Status | Notes |
|---|---:|---:|---|---|
| Goal Clarity | 0.94 | 0.75 | Met | Dataset, baseline, evaluator, and E2E demo are measurable |
| Boundary Clarity | 0.91 | 0.70 | Met | Fine-tuning, multi-turn Agent, and fidelity are deferred |
| Constraint Clarity | 0.88 | 0.65 | Met | Split, provenance, no fabrication, provider, and TDD rules are explicit |
| Acceptance Criteria | 0.84 | 0.70 | Met | Ten pass/fail criteria map to TEXT-01/02/03 and E2E-01 |
| **Ambiguity** | **0.11** | **<= 0.20** | **Met** | Ready for planning |

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|---|---|---|---|
| 1 | Researcher | What exists after Phase 2.5? | BIM JSON 2.0, Drafts, extraction audit, scene families, compiler path exist |
| 2 | Simplifier | What is the smallest useful Phase 3? | Build clean data, no-RAG structured baseline, evaluator, one E2E demo |
| 3 | Boundary Keeper | Should model output low-level IFC entities? | No. It outputs semantic BIM JSON 2.0; compiler emits low-level IFC objects |
| 4 | Failure Analyst | What invalidates a training set? | Scene-family leakage, fabricated facts, Drafts scored as Formal, hidden invalid predictions |
| 5 | Seed Closer | Does Phase 3 include Agent follow-up questions? | Only Draft/clarification data labels; runtime multi-turn Agent is Phase 5 |
| 6 | Seed Closer | Does Phase 3 require RAG? | No. RAG is a decision after the baseline error report |

---

*Phase: 03-text-to-json-dataset-and-baseline*
*Spec created: 2026-06-14*
*Next step: execute Phase 3 plans in wave order*
