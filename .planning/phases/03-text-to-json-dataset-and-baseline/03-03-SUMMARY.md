---
phase: 03-text-to-json-dataset-and-baseline
plan: 03
subsystem: text-json-pair-generation
tags: [text2json, pairs, dataset, provenance, deterministic]
requires:
  - phase-03-supported-scope-projection
provides:
  - Deterministic Text-to-BIM-JSON pair records
  - Split-aware pair manifest
  - Drift-checkable pair generation CLI
affects:
  - phase-03-evaluation-harness
  - phase-03-structured-output-baseline
key-files:
  created:
    - dataset/processed/text2json/pair-manifest.json
    - dataset/processed/text2json/pairs/
    - scripts/text2json/build_pairs.py
    - tests/text2json/test_pair_generation.py
  modified:
    - src/text2ifc_text/__init__.py
    - src/text2ifc_text/pairs.py
requirements-addressed:
  - TEXT-01
requirements-completed: []
completed: 2026-06-14
---

# Phase 3 Plan 03 Summary

**The first split-aware Text-to-BIM-JSON dataset now exists: 100 deterministic
records generated from 25 formal BIM JSON 2.0 targets.**

## Accomplishments

- Added `text2ifc_text.pairs` for formal target loading, validation, fact
  extraction, deterministic text rendering, pair IDs, manifesting, and drift
  checks.
- Added `scripts/text2json/build_pairs.py` with `--write` and `--check`.
- Generated JSONL pair files under `dataset/processed/text2json/pairs/`.
- Generated `dataset/processed/text2json/pair-manifest.json`.
- Enforced that pair text reads formal target facts only and does not mention
  sidecar-only loss categories as formal facts.

## Pair Counts

| Split | Records |
|---|---:|
| train | 68 |
| validation | 20 |
| test | 12 |
| total | 100 |

| Text style | Records |
|---|---:|
| concise | 25 |
| enumerated | 25 |
| spatial | 25 |
| property_focused | 25 |

All pair records have `target_kind: formal` and `review_status: generated`.

## TDD Commits

1. RED pair behavior - `faeec4a`
2. GREEN pair builder, CLI, and artifacts - `9dac1de`

## Verification

- Pair focused tests: `3 passed in 26.44s`.
- Pair drift check: `python scripts/text2json/build_pairs.py --check`
  returned `status: ok`.
- Text-to-JSON focused tests: `19 passed in 34.46s`.
- Repository regression: `267 passed in 412.88s`.

## Next Wave

Proceed to `03-04-PLAN.md`: provider-independent evaluation harness. The
evaluator should consume prediction files and pair/gold metadata; it must not
call a model provider.
