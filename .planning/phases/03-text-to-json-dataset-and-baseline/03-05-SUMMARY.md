# 03-05 Summary: Structured-output Text-to-JSON Baseline

## Status

Complete on 2026-06-14.

## Commits

- RED: `aaf46e4 test(03-05): add failing structured baseline tests`
- GREEN: `d06693f feat(03-05): implement structured text2json baseline`

## Delivered

- Added `prompts/text2json/structured-output-v1.md` as the baseline prompt
  contract.
- Added `src/text2ifc_text/baseline.py` with:
  - provider protocol
  - deterministic `FakeProvider`
  - replayable `FileProvider`
  - prompt construction
  - formal BIM JSON 2.0 parse/schema/semantic acceptance gates
  - Draft Envelope rejection for formal baseline records
  - separate raw response, raw metadata, parsed prediction, and diagnostics
    storage
  - optional evaluation harness invocation
- Added `scripts/text2json/run_baseline.py` with:
  - `--provider fake|file`
  - `--pairs`
  - `--split`
  - `--output-dir`
  - `--responses`
  - `--evaluate`
- Added validation fake baseline artifacts:
  - `dataset/processed/text2json/baseline-runs/`
  - `dataset/processed/text2json/predictions/fake-validation.jsonl`

## Prompt Boundary

The prompt explicitly requires:

- `schema_version: "bim-json/2.0"`
- `ifc_schema: "IFC2X3"`
- one JSON object only

The prompt explicitly forbids:

- raw IFC
- STEP text
- `.ifc files`
- `IfcCartesianPoint`
- `IfcDirection`
- `IfcOwnerHistory`
- low-level compiler implementation objects

## Baseline Run

Command:

```powershell
python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate
```

Result:

| metric | value |
| --- | ---: |
| provider mode | fake target-echo smoke |
| record_count | 20 |
| accepted_count | 20 |
| invalid_count | 0 |
| parse_success_rate | 1.00 |
| schema_valid_rate | 1.00 |
| semantic_valid_rate | 1.00 |
| ifc_class_accuracy | 1.00 |
| property_f1 | 1.00 |
| relationship_endpoint_accuracy | 1.00 |
| geometry_exact_accuracy | 1.00 |

## Important Interpretation

The fake provider is an oracle smoke mode that echoes formal gold targets. Its
1.00 metrics prove the baseline storage/evaluation loop works; they are not a
claim about a real language model's Text-to-JSON quality.

Real provider or file-replay outputs must use the same runner and evaluator
before any model-quality conclusion.

## Verification

Passed:

```powershell
python -m pytest tests/text2json/test_structured_output_baseline.py -q
python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate
python -m pytest tests/text2json -q
python -m compileall -q src scripts
python -m pytest tests -q
```

Full regression result: `276 passed in 425.96s`.

## Next

Proceed to Phase 3 Wave 6 (`03-06-PLAN.md`): end-to-end demo, Phase 3
summary, and RAG/fine-tune decision report.
