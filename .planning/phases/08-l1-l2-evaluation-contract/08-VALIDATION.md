---
phase: 8
slug: l1-l2-evaluation-contract
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-19
---

# Phase 8 - Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest through Python 3.12 virtual environment |
| Config file | `pyproject.toml` |
| Quick run command | `.venv\Scripts\python -m pytest tests\ifc_repair\test_evaluation_contract.py tests\ifc_repair\test_evaluation_policy.py tests\ifc_repair\test_l1_evaluator.py -q` |
| Full suite command | `.venv\Scripts\python -m pytest tests\ifc_repair -q` |
| Estimated runtime | focused under 30 seconds; full repair suite under 5 minutes |

## Sampling Rate

- After every RED/GREEN/REFACTOR commit: run the plan's focused test file.
- After every plan: run all completed Phase 8 focused files.
- After every wave: run existing compare/audit/offline workflow regressions.
- Before verification: run all `tests/ifc_repair`, compileall, schema checks,
  privacy canary scan, and `git diff --check`.
- Maximum focused feedback latency: 30 seconds.

## Per-Task Verification Map

| Task | Plan | Wave | Requirements | Threat | Secure behavior | Automated command |
|---|---:|---:|---|---|---|---|
| Contract/status RED-GREEN | 01 | 1 | VAL-01, VAL-03 | T-08-01 | Unknown facts cannot pass | `pytest tests/ifc_repair/test_evaluation_contract.py -q` |
| L2 policy/evidence RED-GREEN | 02 | 2 | VAL-02, VAL-05 | T-08-02 | No unauthorized semantic inference | `pytest tests/ifc_repair/test_evaluation_policy.py -q` |
| L1 scope/preservation RED-GREEN | 03 | 3 | VAL-01 | T-08-03 | Applicator self-report cannot authorize drift | `pytest tests/ifc_repair/test_l1_evaluator.py -q` |
| Benchmark/privacy RED-GREEN | 04 | 4 | VAL-04, VAL-05 | T-08-04 | Gold canary absent from public/Provider artifacts | `pytest tests/ifc_repair/test_benchmark_evaluation.py -q` |
| LargeBuilding acceptance | 04 | 4 | VAL-01..05 | T-08-04 | L1 cannot conceal L2 failure | `pytest tests/ifc_repair/test_phase8_large_building.py -q` |

## Wave 0 Requirements

Existing pytest, jsonschema, IfcOpenShell, `tmp_path`, LargeBuilding fixture,
mutation helper, and offline deterministic Provider cover the phase. Test files
are created in each plan's RED task; no dependency installation is required.

## Manual-Only Verifications

None. All Phase 8 acceptance behavior, including privacy leakage detection, is
deterministically automated.

## Validation Sign-Off

- [x] Every task has an automated focused command.
- [x] Sampling continuity has no three-task gap.
- [x] Existing infrastructure covers all Wave 0 needs.
- [x] No watch-mode commands.
- [x] Focused feedback target is under 30 seconds.
- [x] `nyquist_compliant: true` is set.

**Approval:** approved 2026-07-19
