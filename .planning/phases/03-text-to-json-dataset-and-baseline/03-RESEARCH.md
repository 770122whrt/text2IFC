# Phase 3: Text-to-JSON Dataset and Baseline - Research

**Created:** 2026-06-14
**Status:** Planning research complete

## Research Question

What must be true to plan Phase 3 well enough that execution can build a
trustworthy Text-to-BIM-JSON dataset, structured-output baseline, evaluation
harness, and first E2E demo without leaking data or fabricating IFC facts?

## Current Technical Baseline

- BIM JSON 2.0 formal schema exists at `schemas/bim-json/2.0/schema.json`.
- Draft Envelope schema exists at `schemas/bim-json/draft/1.0/schema.json`.
- Formal semantic validation exists in `src/text2ifc_contract/validation_v2.py`.
- Draft validation exists in `src/text2ifc_contract/draft.py`.
- IFC2X3 extraction exists in `src/text2ifc_extractor/`.
- BIM JSON to IFC compilation exists in `src/text2ifc_compiler/`.
- All 25 authorized BIMNet IFC2X3 files are present locally and audited.
- 19 scene families are recorded in
  `dataset/processed/bim-json-2.0/scene-families.json`.
- All 25 extraction outputs are Drafts with zero `missing_fact_count` but
  explicit losses beyond the current generation profile.
- Existing split folders leak scene families and cannot be used as model
  splits.

## Data Construction Findings

### Split first

Text generation must happen after scene-family split assignment. If we generate
multiple text variants before splitting, near-duplicate descriptions of the
same source building can leak across train/validation/test.

Required split invariant:

```text
for every scene_family:
  count(distinct split) == 1

for every file_id:
  appears exactly once in the split manifest
```

### Formal target policy

The key Phase 3 complication is that all BIMNet outputs are Drafts. The correct
first target is not to fabricate full IFC fidelity. The correct target is:

```text
Draft partial_document
  -> validate as formal BIM JSON 2.0
  -> write as supported-scope formal gold target
  -> keep original losses in a sidecar
```

This produces a model target for the Phase 2.5 generation profile while
preserving the fact that the source IFC contains unsupported material, type,
connection, and complex-geometry information.

### Sidecar provenance

Every formal target derived from a Draft should have a sidecar with:

- source file ID
- source SHA-256
- source IFC path
- scene family
- split
- original Draft status
- loss counts and detailed losses
- extraction inventory
- target construction policy

The formal target is what the model learns to emit. The sidecar is what keeps
the label honest.

## Text Pair Strategy

Text should be generated from formal targets with deterministic templates
before any learned paraphrasing. The first useful variants are:

1. Concise building summary.
2. Enumerated object list with IFC class names.
3. Spatial description with storeys, spaces, and placements.
4. Property-focused description with selected property sets.
5. Relationship-focused description for openings and fillings when present.

Each pair should be a JSONL record:

```json
{
  "record_id": "...",
  "target_kind": "formal",
  "input_text": "...",
  "target_json_path": "...",
  "split": "train",
  "scene_family": "...",
  "source_file_id": "...",
  "source_sha256": "...",
  "text_style": "spatial",
  "template_id": "spatial-v1",
  "review_status": "generated"
}
```

## Structured-Output Baseline Research

A Phase 3 baseline should be provider-agnostic because model/provider choice is
not yet a stable product decision. The runner should own:

- prompt construction
- provider adapter invocation
- raw response storage
- JSON extraction/parsing
- formal BIM JSON validation
- diagnostic output
- prediction manifest writing

The evaluator should not call the model. It should consume prediction files
only. This separation lets us compare prompt-only, RAG, fine-tuned, and fake
provider outputs using the same metrics.

Recommended baseline modes:

- `fake`: deterministic provider for tests and CI.
- `file`: read precomputed provider responses for offline reproduction.
- `live`: optional provider adapter requiring explicit credentials.

## Evaluation Architecture

Evaluation should report early-stage validity failures before semantic scores.
This avoids a misleading partial score for outputs that are not legal BIM JSON.

Metric groups:

- Document: parse success, schema validity, semantic validity.
- Collection: entity count error, relationship count error, class distribution.
- Entity: `ifc_class` accuracy, ID matching, GlobalId preservation where used.
- Property: property-set precision/recall/F1 and typed value equality.
- Relationship: relation class and endpoint accuracy.
- Placement: origin distance and axis/ref_direction angular tolerance.
- Geometry: profile kind, dimensions, depth, direction, local position.
- Compiler: compile success, reopen success, IFC validation issue count.

The first matching strategy can use stable IDs for generated formal targets.
Later evaluation can add fuzzy matching if natural-language targets become less
ID-prescriptive.

## Validation Architecture

Phase 3 verification should sample the full data path:

1. Split manifest covers all files and rejects leakage.
2. Gold-set builder validates formal targets and sidecars.
3. Pair builder proves no generated text crosses split boundaries.
4. Baseline fake provider proves output validation and diagnostic behavior.
5. Evaluator computes fixture metrics with known expected values.
6. E2E demo compiles and reopens at least one prediction.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Scene-family leakage | Split by `scene_family` before text generation and test leakage directly |
| Drafts mislabeled as full-fidelity Formal | Use supported-scope target policy plus sidecar losses |
| Model/provider lock-in | Provider adapter boundary plus fake/file modes |
| Evaluation hides invalid outputs | Validity metrics precede semantic metrics |
| Generated text includes unsupported source facts | Text builder reads formal target facts, not raw IFC facts |
| Credentials block CI | Live provider is optional; tests use fake/file providers |
| Small dataset overclaims model quality | Phase 3 reports baseline evidence and recommends expansion before fine-tuning |

## Planning Implication

Phase 3 should be executed in this order:

1. Split and provenance gate.
2. Draft triage and formal supported-scope gold set.
3. Text/JSON pair generation.
4. Evaluation harness.
5. Structured-output baseline.
6. First E2E demo and decision report.

This order keeps model work downstream of data truth and keeps evaluation ready
before claiming baseline quality.
