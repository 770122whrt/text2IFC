---
phase: 03-text-to-json-dataset-and-baseline
plan: 01
subsystem: scene-family-split
tags: [text2json, bimnet, provenance, split, leakage]
requires:
  - phase-02.5-all-25-bimnet-audit
provides:
  - Deterministic BIMNet scene-family train/validation/test split
  - Authorization and provenance gate for Phase 3 dataset builders
  - Drift-checkable split CLI
affects:
  - phase-03-text-to-json-gold-set
  - phase-03-text-pair-generation
key-files:
  created:
    - dataset/splits/bimnet-scene-splits.json
    - dataset/processed/text2json/README.md
    - scripts/text2json/build_splits.py
    - tests/text2json/test_split_manifest.py
  modified:
    - src/text2ifc_text/__init__.py
    - src/text2ifc_text/splits.py
requirements-addressed:
  - TEXT-01
requirements-completed: []
completed: 2026-06-14
---

# Phase 3 Plan 01 Summary

**The Phase 3 BIMNet split boundary is now deterministic, provenance-linked,
and checked before any text generation, augmentation, baseline run, or
fine-tuning export.**

## Accomplishments

- Added `text2ifc_text.splits` with BIMNet manifest loading, scene-family
  loading, authorization/provenance checks, deterministic family assignment,
  leakage validation, and deterministic JSON rendering.
- Added `scripts/text2json/build_splits.py` with `--write` and `--check`.
- Wrote `dataset/splits/bimnet-scene-splits.json` using policy
  `scene-family-shuffle-70-15-15-v1`, seed `20260614`, and date `2026-06-14`.
- Documented Phase 3 generated artifact locations and the local-use/no
  redistribution boundary in `dataset/processed/text2json/README.md`.
- Preserved the rule that legacy `dataset/ifc/train` and `dataset/ifc/test`
  are source folders only, not model splits.

## Split Evidence

| Split | Scene families | File IDs |
|---|---:|---:|
| train | 13 | 17 |
| validation | 3 | 5 |
| test | 3 | 3 |
| total | 19 | 25 |

Validation families are `i5n`, `vt2`, and `zsn`. Test families are `1px`,
`b6b`, and `vvo`. No scene family appears in more than one split.

## Authorization Gate Cases

The RED tests mutate one source manifest record at a time and prove the split
builder rejects:

- missing `dataset-construction`;
- missing `local-model-training`;
- `training_eligible: false`;
- missing or malformed `sha256`;
- `declared_schema` other than `IFC2X3`.

## TDD Commits

1. RED split/provenance behavior - `687cebe`
2. GREEN split builder, CLI, README, and manifest - `9576753`

## Verification

- Focused split tests: `8 passed in 0.33s`.
- Split drift check: `python scripts/text2json/build_splits.py --check`
  returned `status: ok`.
- Repository regression: `256 passed in 355.57s`.

## Next Wave

Proceed to `03-02-PLAN.md`: Draft triage and formal supported-scope gold set.
That wave must consume `dataset/splits/bimnet-scene-splits.json` and keep all
source losses in sidecars before any text/JSON pair generation.
