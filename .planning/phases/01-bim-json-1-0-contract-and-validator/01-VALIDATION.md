---
phase: 1
slug: bim-json-1-0-contract-and-validator
status: implementation_complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-11
---

# Phase 1 - Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| **Framework** | pytest 7.4.4 |
| **Config file** | `pyproject.toml` created in Plan 01 |
| **Quick run command** | `python -m pytest tests/contract -q` |
| **Full suite command** | `python -m pytest tests -q` |
| **Estimated runtime** | Quick < 10 seconds; full < 40 seconds |

## Sampling Rate

- After every RED commit: run the plan-specific test and confirm a behavioral
  failure.
- After every GREEN or REFACTOR commit: run the plan-specific test and
  `python -m pytest tests/contract -q`.
- After every wave: run `python -m pytest tests -q`.
- Before `$gsd-verify-work`: the full suite must be green.
- Maximum expected feedback latency: 40 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure behavior | Test type | Automated command | File exists | Status |
|---|---:|---:|---|---|---|---|---|---|---|
| 01-01 | 01 | 1 | JSON-01..04 | T-01-01, T-01-02 | Bounded local-only validation | unit/CLI | `python -m pytest tests/contract/test_schema_validation.py -q` | yes | green |
| 01-02 | 02 | 2 | JSON-02, JSON-03 | T-01-01 | Stable semantic errors | unit | `python -m pytest tests/contract/test_semantic_validation.py -q` | yes | green |
| 01-03 | 03 | 3 | JSON-05 | T-01-03, T-01-04 | No overwrite or silent loss | integration | `python -m pytest tests/contract/test_migration.py -q` | yes | green |
| 01-04 | 04 | 2 | DOC-01, DOC-02 | T-01-02 | Local deterministic docs | unit | `python -m pytest tests/contract/test_reference.py -q` | yes | green |

## Wave 0 Requirements

- [x] `pyproject.toml` configures `src` and `.deps/python312` on pytest's path.
- [x] `tests/contract/fixtures/complete.json` covers every supported family.
- [x] All contract test modules were created before their GREEN steps.

## Manual-Only Verifications

All Phase 1 behaviors have automated verification.

## Validation Sign-Off

- [x] Every plan has a plan-specific automated command.
- [x] No three consecutive implementation steps lack automated feedback.
- [x] Wave 0 establishes missing package and fixture infrastructure.
- [x] No watch-mode command is used.
- [x] Expected feedback latency is below 40 seconds.
- [x] `nyquist_compliant: true` is set.

**Approval:** planned 2026-06-11
