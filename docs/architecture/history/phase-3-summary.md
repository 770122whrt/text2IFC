# Phase 3 Summary: Text-to-JSON Dataset and Baseline

**Date:** 2026-06-14

Phase 3 built the first reproducible Text-to-BIM-JSON loop:

Natural language -> formal BIM JSON 2.0 -> IFC2X3.

The phase used authorized BIMNet IFC2X3 sources, kept dataset splits
scene-family-safe, retained omitted IFC source facts in sidecars, and added a
provider-independent evaluation harness before any baseline quality claim.

## Dataset Split

The split manifest is `dataset/splits/bimnet-scene-splits.json`.

| split | scene families | files |
| --- | ---: | ---: |
| train | 13 | 17 |
| validation | 3 | 5 |
| test | 3 | 3 |
| total | 19 | 25 |

The split is grouped by Matterport scene family before text generation,
augmentation, baseline runs, or fine-tune export.

## Gold Targets

The gold manifest is
`dataset/processed/text2json/gold-set-manifest.json`.

| target kind | count |
| --- | ---: |
| formal | 25 |
| draft_clarification | 0 |
| total | 25 |

All 25 formal targets pass `validate_v2_document`. Unsupported or omitted
source IFC facts remain in per-record sidecars under
`dataset/processed/text2json/sidecars/`.

The supported-scope projection produced 5,325 recorded projection omissions.
This is intentional: Phase 3 trains and evaluates only the formal generation
profile while Phase 4 owns higher-fidelity IFC recovery.

## Text/JSON Pairs

The pair manifest is `dataset/processed/text2json/pair-manifest.json`.

| split | records |
| --- | ---: |
| train | 68 |
| validation | 20 |
| test | 12 |
| total | 100 |

| text style | records |
| --- | ---: |
| concise | 25 |
| enumerated | 25 |
| property_focused | 25 |
| spatial | 25 |

Every pair targets formal BIM JSON 2.0. Draft and clarification data remain
separate and are not scored as formal predictions.

## Baseline

The structured-output prompt is
`prompts/text2json/structured-output-v1.md`.

The runner is `scripts/text2json/run_baseline.py`.

The validation smoke run used the deterministic fake target-echo provider:

```powershell
python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate
```

| metric | value |
| --- | ---: |
| record_count | 20 |
| accepted_count | 20 |
| invalid_count | 0 |
| parse_success_rate | 1.00 |
| schema_valid_rate | 1.00 |
| semantic_valid_rate | 1.00 |
| ifc_class_accuracy | 1.00 |
| property_f1 | 1.00 |
| geometry_exact_accuracy | 1.00 |

The fake provider is an oracle smoke mode. These metrics prove the storage,
validation, and evaluation loop works; they are not a real model-quality claim.

Baseline artifacts:

- `dataset/processed/text2json/baseline-runs/`
- `dataset/processed/text2json/predictions/fake-validation.jsonl`

## Evaluation Harness

The evaluator is `scripts/text2json/evaluate.py` and
`src/text2ifc_text/evaluation.py`.

It reports:

- JSON parse validity
- BIM JSON 2.0 schema validity
- BIM JSON 2.0 semantic validity
- class, entity, property, relationship, placement, and geometry metrics
- compile/reopen metrics when compiler checks are enabled
- split/source/stage/code error buckets

Invalid JSON and invalid BIM JSON are counted as failures before semantic
scoring.

## E2E Demo

The demo command is:

```powershell
python scripts/text2json/run_e2e_demo.py --check
```

Selected sample:

- Record: `bimnet-ifc2x3-i5n:spatial:09fcea3d6d138620`
- Split: validation
- Source file: `bimnet-ifc2x3-i5n`
- Text style: spatial

Demo artifacts:

- `dataset/processed/text2json/e2e-demo/input.txt`
- `dataset/processed/text2json/e2e-demo/prediction.json`
- `dataset/processed/text2json/e2e-demo/diagnostics.json`
- `dataset/processed/text2json/e2e-demo/metrics.json`
- `dataset/processed/text2json/e2e-demo/output.ifc`
- `dataset/processed/text2json/e2e-demo/report.md`

The prediction validates as formal BIM JSON 2.0 and compiles to reopened
IFC2X3 with no compiler issues.

## Requirement Coverage

| requirement | evidence |
| --- | --- |
| TEXT-01 | Scene-family split, 25 formal targets, 100 provenance-linked pairs |
| TEXT-02 | Structured-output prompt and fake/file baseline runner |
| TEXT-03 | Provider-independent evaluator and baseline/e2e metrics |
| E2E-01 | `run_e2e_demo.py --check` writes valid BIM JSON and IFC2X3 |

## Open Risks

- The fake provider is only a deterministic smoke path. A real model or file
  replay run is still needed for model-quality measurement.
- The 25-source dataset is small for fine-tuning and should not be treated as
  sufficient by itself.
- Supported-scope projection deliberately omits material/type/topology and
  complex geometry facts; Phase 4 owns high-fidelity IFC recovery.
- Missing facts in free-form user requests still require Phase 5 multi-turn
  clarification rather than silent defaults.
