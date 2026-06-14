---
phase: 03-text-to-json-dataset-and-baseline
plan: 02
subsystem: draft-triage-and-gold-set
tags: [text2json, bimnet, draft, sidecar, provenance]
requires:
  - phase-03-scene-family-split
provides:
  - All-25 Draft triage joined to scene-family splits
  - Gold-set manifest with explicit formal versus draft_clarification labels
  - Loss-preserving sidecars for every authorized BIMNet source file
affects:
  - phase-03-text-pair-generation
  - phase-04-high-fidelity-ifc-round-trip
  - phase-05-clarification-agent
key-files:
  created:
    - dataset/processed/text2json/draft-triage.json
    - dataset/processed/text2json/gold-set-manifest.json
    - dataset/processed/text2json/sidecars/
    - scripts/text2json/build_gold_set.py
    - tests/text2json/test_gold_set.py
  modified:
    - src/text2ifc_text/__init__.py
    - src/text2ifc_text/gold.py
requirements-addressed:
  - TEXT-01
requirements-completed: []
completed: 2026-06-14
---

# Phase 3 Plan 02 Summary

**All 25 BIMNet IFC2X3 records are triaged and provenance-linked, but none can
yet become formal gold targets without an additional supported-scope projection
or an upstream fidelity expansion.**

## Accomplishments

- Added `text2ifc_text.gold` for Draft triage, formal-target promotion checks,
  sidecar construction, deterministic artifact rendering, and drift checks.
- Added `scripts/text2json/build_gold_set.py` with `--write` and `--check`.
- Wrote `draft-triage.json`, `gold-set-manifest.json`, and 25 sidecars grouped
  by the Phase 3 scene-family split.
- Preserved every original Draft loss in sidecars and kept Draft records
  separate from formal baseline records.
- Proved with tests that a Draft `partial_document` promotes only when
  `validate_v2_document` returns zero issues; invalid partials remain
  `draft_clarification` and are not written under `formal-gold`.

## Dataset Evidence

| Target kind | Count |
|---|---:|
| formal | 0 |
| draft_clarification | 25 |
| total | 25 |

| Split | Formal | Draft clarification | Total |
|---|---:|---:|---:|
| train | 0 | 17 | 17 |
| validation | 0 | 5 | 5 |
| test | 0 | 3 | 3 |

The triage preserves `file_count == 25`, `status_counts.draft == 25`, and
aggregate `loss_count == 8280`.

## Validation-Issue Evidence

The 25 Draft `partial_document` payloads fail formal validation with these
issue counts:

| Issue code | Count |
|---|---:|
| CLASS_NOT_GENERATABLE | 6 |
| INVALID_IFC_ATTRIBUTE_TYPE | 50 |
| INVALID_PROPERTY_TYPE | 72 |
| MISSING_REPRESENTATION | 1263 |
| WALL_STANDARD_CASE_REQUIRES_RECTANGLE | 1528 |

This means Phase 3 cannot honestly generate formal Text/JSON pairs from the
current artifacts. Moving forward requires a product/data-policy decision:

1. Insert a supported-scope projection step that removes only invalid formal
   facts, records every omission in sidecars, and validates the projected
   target before text generation.
2. Defer pair generation until Phase 4 expands extractor/compiler fidelity
   enough for Draft partials to validate directly.

## TDD Commits

1. RED Draft triage and gold-set behavior - `b186531`
2. GREEN triage, sidecars, CLI, and artifacts - `f201553`

## Verification

- Focused gold-set tests: `5 passed in 0.99s`.
- Text-to-JSON focused tests: `13 passed in 1.14s`.
- Gold-set drift check: `python scripts/text2json/build_gold_set.py --check`
  returned `status: ok`.
- Repository regression: `261 passed in 228.63s`.

## Next Decision

Wave 3 (`03-03-PLAN.md`) depends on formal targets. Because formal target
count is currently zero, the next executable step is to resolve whether Phase 3
may add a loss-recording supported-scope projection before pair generation.
