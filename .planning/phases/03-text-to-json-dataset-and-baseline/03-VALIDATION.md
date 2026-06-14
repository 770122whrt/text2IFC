# Phase 3: Text-to-JSON Dataset and Baseline - Validation Strategy

**Created:** 2026-06-14
**Status:** Ready for execution

## Validation Objective

Prove that Phase 3 creates a leak-free formal Text-to-BIM-JSON dataset,
evaluates structured-output predictions reproducibly, and demonstrates one
validated Natural Language -> BIM JSON 2.0 -> IFC2X3 loop without fabricating
missing facts.

## Nyquist Dimensions

| Dimension | Minimum coverage |
|---|---|
| Scene-family split | All 19 families, all 25 file IDs, no family in more than one split |
| Authorization gate | Positive authorized record plus negative missing-use, disabled-training, missing-hash, and schema-mismatch records |
| Draft triage | All 25 audited records and aggregate loss counts preserved |
| Formal target construction | Valid formal target, invalid partial document, sidecar loss preservation |
| Text pairs | At least two text styles and two splits, with no cross-split references |
| Baseline validation | Valid JSON, invalid JSON, schema-invalid JSON, semantic-invalid JSON, Draft-as-formal rejection |
| Evaluation metrics | Perfect prediction, invalid prediction, count mismatch, class mismatch, placement mismatch, compile failure |
| E2E | At least one spatial sample that compiles and reopens, plus one explicit failure path |

## Required Verification Commands

Focused commands:

```bash
python -m pytest tests/text2json -q
python scripts/text2json/build_splits.py --check
python scripts/text2json/build_gold_set.py --check
python scripts/text2json/build_pairs.py --check
python scripts/text2json/evaluate.py --check-fixtures
python scripts/text2json/run_e2e_demo.py --check
```

Regression commands:

```bash
python -m pytest tests -q
python -m compileall -q src scripts
python scripts/ifc_pipeline_v2/audit_bimnet.py --check-accounting
python scripts/ifc_knowledge/check_registry.py
```

## Pass/Fail Gates

- **Pre-flight gate:** Required Phase 2.5 source artifacts exist and parse.
- **Revision gate:** Each plan's RED/GREEN behavior passes focused tests before
  dependent plans start.
- **Coverage gate:** TEXT-01, TEXT-02, TEXT-03, and E2E-01 are each covered by
  at least one passing plan summary.
- **Integrity gate:** Generated dataset and evaluation artifacts are
  deterministic under `--check`.
- **Completion gate:** Final Phase 3 verification report shows no open
  requirement gaps, no scene-family leakage, and no Draft scored as Formal.

## Manual Review Points

Manual review is required only if:

- a split ratio change affects validation or test representativeness;
- live provider credentials are required for a real model run;
- a Draft cannot be converted into a supported-scope formal target without a
  product decision;
- the baseline error report suggests adding RAG before the no-RAG baseline is
  measured.
