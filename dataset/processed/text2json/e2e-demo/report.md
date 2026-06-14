# Phase 3 E2E Demo Report

- Success: True
- Record ID: bimnet-ifc2x3-i5n:spatial:09fcea3d6d138620
- Split: validation
- Source file ID: bimnet-ifc2x3-i5n
- Text style: spatial
- Output directory: E:\code for project\bimnet\dataset\processed\text2json\e2e-demo

## Reproduce

```powershell
python scripts/text2json/run_e2e_demo.py --check
python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate
python scripts/text2json/evaluate.py --check-fixtures
```

## Validation

- Stage: ok
- Issue count: 0

## Compilation

- Attempted: True
- Success: True
