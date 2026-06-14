# 03-04 Summary: Provider-independent Evaluation Harness

## Status

Complete on 2026-06-14.

## Commits

- RED: `ed7719a test(03-04): add failing evaluation harness tests`
- GREEN: `bcd6c12 feat(03-04): implement text2json evaluation harness`

## Delivered

- Added `src/text2ifc_text/evaluation.py` as the provider-independent
  Text-to-BIM-JSON evaluator.
- Added `scripts/text2json/evaluate.py` with:
  - `--pairs`
  - `--predictions`
  - `--output-dir`
  - `--split`
  - `--compile`
  - `--check-fixtures`
- Added deterministic fixture outputs in
  `dataset/processed/text2json/evaluation-fixtures/`:
  - `metrics.json`
  - `records.json`
  - `error-buckets.json`
  - `report.md`
- Ignored generated `compiled/*.ifc` fixture compiler outputs while preserving
  the fixture directory contract.

## Metric Families

The evaluator reports invalid outputs before semantic scoring:

- JSON parse validity
- BIM JSON 2.0 schema validity
- BIM JSON 2.0 semantic validity
- IFC class accuracy by stable entity ID
- Entity and relationship count error
- Property precision, recall, and F1 over property-set/property/value triples
- Relationship endpoint accuracy
- Placement origin max error in millimetres
- Placement axis and ref-direction max angular error
- Geometry exact accuracy over supported representation signatures
- Compile and reopen success rates
- Split/source/stage/code error buckets

## Fixture Result

Command:

```powershell
python scripts/text2json/evaluate.py --check-fixtures
```

Result:

| metric | value |
| --- | ---: |
| record_count | 4 |
| parse_success_rate | 0.75 |
| schema_valid_rate | 0.50 |
| semantic_valid_rate | 0.25 |
| compile_checked_record_count | 1 |
| compile_success_rate | 1.00 |
| reopen_success_rate | 1.00 |

Expected fixture error buckets:

| stage | code | count |
| --- | --- | ---: |
| parse | JSON_DECODE_ERROR | 1 |
| schema | REQUIRED_FIELD | 1 |
| semantic | CLASS_NOT_GENERATABLE | 1 |

## Verification

Passed:

```powershell
python -m pytest tests/text2json/test_evaluation_harness.py -q
python scripts/text2json/evaluate.py --check-fixtures
python -m pytest tests/text2json -q
python -m pytest tests -q
```

Full regression result: `271 passed in 420.50s`.

The first full regression attempt used a 5-minute timeout and was interrupted
without failure output; the rerun used a longer timeout and passed.

## Notes

- Invalid JSON and invalid BIM JSON are counted in validity metrics but are
  not semantically scored.
- Compiler checks run only for semantically valid predictions.
- Evaluation is split-aware and rejects unknown split names.
- The evaluator consumes BIM JSON 2.0 targets and prediction JSON only; it does
  not call any model provider.

## Next

Proceed to Phase 3 Wave 5 (`03-05-PLAN.md`): structured-output Text-to-JSON
baseline using this evaluator before making any baseline quality claim.
