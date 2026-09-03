---
phase: 07
slug: ifc-retrieval-index-and-target-resolution
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-19
---

# Phase 7 - Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest through Python 3.12 virtual environment |
| Config file | `pyproject.toml` |
| Quick run command | `.venv\Scripts\python -m pytest tests/ifc_repair/test_index_store.py tests/ifc_repair/test_indexer.py tests/ifc_repair/test_target_query.py tests/ifc_repair/test_target_context.py -q` |
| Full run command | `.venv\Scripts\python -m pytest tests/ifc_repair -q` |
| Static command | `.venv\Scripts\python -m compileall -q src/text2ifc_ifc_repair scripts/ifc_repair` |
| Estimated runtime | focused under 60 seconds; full repair suite under 5 minutes |

## Sampling Rate

- After every RED edit: run the focused new test and confirm the intended
  assertion fails because behavior is absent.
- After every GREEN edit: rerun the focused file and relevant existing repair
  tests.
- After each plan: run all Phase 7 focused tests.
- Before completion: run `tests/ifc_repair`, compileall, LargeBuilding CLI
  smoke, schema validation, and `git diff --check`.
- Max expected focused feedback latency: 60 seconds.

## Per-Task Verification Map

| Task | Plan | Wave | Requirements | Threat | Test command |
|---|---:|---:|---|---|---|
| Contracts and SQLite lifecycle | 01 | 1 | TGT-01, TGT-03 | T-07-01, T-07-02 | `pytest tests/ifc_repair/test_index_store.py -q` |
| IFC extraction and diagnostics | 02 | 2 | TGT-01, TGT-02 | T-07-03 | `pytest tests/ifc_repair/test_indexer.py -q` |
| Query/ranking/ambiguity | 03 | 3 | TGT-02, TGT-03, TGT-04 | T-07-04 | `pytest tests/ifc_repair/test_target_query.py -q` |
| Context, CLI, LargeBuilding | 04 | 4 | TGT-05 | T-07-05 | `pytest tests/ifc_repair/test_target_context.py tests/ifc_repair/test_index_cli.py tests/ifc_repair/test_large_building_retrieval.py -q` |

## Wave 0 Requirements

Existing pytest, IfcOpenShell, jsonschema, `tmp_path`, and the frozen
LargeBuilding fixture cover the phase. No new test dependency is required.

## Manual-Only Verifications

None. Phase 7 is Provider-independent and all acceptance behavior is
automatable. Human review is limited to reading the generated evidence report.

## Security and Integrity Checks

- T-07-01: all SQL statements bind user/IFC values as parameters.
- T-07-02: failed builds never replace an existing valid database.
- T-07-03: malformed/duplicate identity cannot become an authorized target.
- T-07-04: conflicts and ambiguity cannot be converted to resolved status.
- T-07-05: raw IFC, full properties, and private ground truth do not enter the
  bounded public context.

## Validation Sign-Off

- [x] Every task has an automated focused test.
- [x] Sampling continuity has no untested behavior task.
- [x] No watch-mode commands.
- [x] Full repair regressions protect the existing Window chain.
- [x] `nyquist_compliant: true` is set.

**Approval:** approved 2026-07-19
