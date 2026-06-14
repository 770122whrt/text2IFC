# 03-06 Summary: E2E Demo and Phase 3 Decision Report

## Status

Complete and verified on 2026-06-14.

## Commits

- RED: `f1d5bcf test(03-06): add failing e2e demo tests`
- GREEN: `8cba218 feat(03-06): implement text2json e2e demo`
- Stabilization: `0cfcb83 fix(03-06): stabilize e2e verification checks`

## Delivered

- Added `scripts/text2json/run_e2e_demo.py`.
- Added deterministic E2E artifacts under
  `dataset/processed/text2json/e2e-demo/`.
- Added `docs/architecture/phase-3-summary.md`.
- Added `docs/architecture/text2json-rag-finetune-decision.md`.

## Demo

Command:

```powershell
python scripts/text2json/run_e2e_demo.py --check
```

Result:

| field | value |
| --- | --- |
| record_id | `bimnet-ifc2x3-i5n:spatial:09fcea3d6d138620` |
| split | validation |
| source_file_id | `bimnet-ifc2x3-i5n` |
| text_style | spatial |
| validation stage | ok |
| compile/reopen | success |

Artifacts:

- `dataset/processed/text2json/e2e-demo/input.txt`
- `dataset/processed/text2json/e2e-demo/prediction.json`
- `dataset/processed/text2json/e2e-demo/diagnostics.json`
- `dataset/processed/text2json/e2e-demo/metrics.json`
- `dataset/processed/text2json/e2e-demo/output.ifc`
- `dataset/processed/text2json/e2e-demo/report.md`

## Verification

Passed:

```powershell
python -m pytest tests/text2json -q
python scripts/text2json/build_splits.py --check
python scripts/text2json/build_gold_set.py --check
python scripts/text2json/build_pairs.py --check
python scripts/text2json/evaluate.py --check-fixtures
python scripts/text2json/run_e2e_demo.py --check
python -m compileall -q src scripts
python scripts/ifc_knowledge/check_registry.py
python scripts/ifc_pipeline_v2/audit_bimnet.py --check-accounting
python -m pytest tests -q
```

Observed outputs:

| command | result |
| --- | --- |
| `python -m pytest tests/text2json -q` | 33 passed |
| `build_splits.py --check` | 19 families / 25 files, status ok |
| `build_gold_set.py --check` | 25 formal, 0 draft, status ok |
| `build_pairs.py --check` | 100 pairs, status ok |
| `evaluate.py --check-fixtures` | parse 0.75, schema 0.50, semantic 0.25 |
| `run_e2e_demo.py --check` | success true |
| `compileall` | passed |
| `check_registry.py` | IFC2X3 registry verified |
| `audit_bimnet.py --check-accounting` | 25 files, status ok |
| `python -m pytest tests -q` | 281 passed in 430.43s |

## Requirement Coverage

| requirement | status |
| --- | --- |
| TEXT-01 | covered by split/gold/pair artifacts |
| TEXT-02 | covered by structured-output baseline |
| TEXT-03 | covered by evaluation harness and reports |
| E2E-01 | covered by E2E demo |

## Code Review and Security Notes

- Code review found a check-command regression: package-level imports pulled in
  evaluator/baseline modules and made split checks depend on `ifcopenshell`.
  Fixed in `0cfcb83` by keeping `text2ifc_text.__init__` lightweight.
- E2E check initially rewrote the tracked IFC artifact on every run because
  IFC serialization is not byte-stable. Fixed in `0cfcb83` by compiling to a
  temporary check file when a committed demo IFC already exists.
- Secret scan found no live credentials. Hits for `raw IFC`, `STEP text`,
  `IfcCartesianPoint`, `IfcDirection`, and `IfcOwnerHistory` are prompt
  prohibitions, tests, documentation, or compiler internals.
- No network access or live provider credentials are required for Phase 3
  verification.
- Split leakage check remains scene-family based before text generation,
  baseline, or fine-tune export.

## Decision

RAG, fine-tuning, and the multi-turn Agent remain deferred until a real
provider/file-replay baseline produces measured errors. The fake provider is a
pipeline smoke oracle, not model-quality evidence.

Recommended next default: plan Phase 5 multi-turn clarification Agent if the
project wants to handle missing facts in user natural language. Run a real
file/live provider baseline first if model-quality measurement is the immediate
priority.
