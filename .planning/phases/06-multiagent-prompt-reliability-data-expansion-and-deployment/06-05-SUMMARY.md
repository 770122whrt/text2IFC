# 06-05 Summary: Data Expansion and Model Decision

**Completed:** 2026-06-21
**Plan:** `06-05-PLAN.md`
**Status:** Complete

## Objective

Build a license-aware, provenance-linked, scene-family-safe Phase 6 data
manifest, then select the next model path from measured project evidence
instead of assuming that RAG or fine-tuning is required.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `69935a2` | Added failing license, provenance, sidecar, and split gates |
| RED | `0d2c84d` | Required deterministic manifest write and drift detection |
| GREEN | `cba91bc` | Implemented and generated the split-safe training manifest |
| Documentation | `b5a533c` | Recorded the evidence-based Phase 6 model decision |

## Implemented

- `src/text2ifc_dataset/phase6_manifest.py` joins the authorized source
  manifest, scene-family split manifest, formal gold manifest, split-specific
  text pairs, and loss sidecars.
- Every record carries source and target hashes, scene family, split, license
  status, approved and eligible uses, formal-target path, loss-sidecar path,
  loss counts, template identity, style, and review status.
- Formal targets are revalidated through `validate_v2_document`.
- Hash drift, missing license evidence, missing sidecars, duplicate IDs,
  scene-family leakage, count drift, and train/evaluation eligibility mistakes
  block the manifest.
- `scripts/dataset/build_phase6_training_manifest.py --write/--check` provides
  deterministic generation and drift checking.
- `docs/architecture/phase-6-model-decision.md` compares prompt-only,
  conditional repair, optional RAG, and fine-tuning using current metrics and
  data quality.

## Manifest Evidence

`dataset/processed/phase6/training-manifest.json` records:

| Metric | Value |
|---|---:|
| Authorized source IFCs | 25 |
| Scene families | 19 |
| Formal targets | 25 |
| Pair records | 100 |
| Train records | 68 |
| Validation records | 20 |
| Test records | 12 |
| Training-eligible records | 68 |

Validation and test records are evaluation-only. All 100 pairs have
`review_status: generated`. Although 39 inputs contain CJK characters from
source object names, their instruction templates remain English-first, so the
set is not treated as a reviewed Chinese-first training corpus.

## Model Decision

- Deploy the traceable prompt-only multi-agent path with deterministic gates.
- Keep repair as a conditional generator mode, not a mandatory separate Agent.
- Do not enable RAG until a real held-out benchmark shows recurring IFC2X3
  knowledge-retrieval failures.
- Do not fine-tune yet. The current 68 training records are too small,
  template-generated, and not human-reviewed; no Phase 6 real-provider
  validation/test benchmark exists.
- Treat all current Phase 6 experiment metrics as fake-provider orchestration
  evidence, not live model accuracy.

## Verification

- `python -m pytest tests/dataset/test_phase6_training_manifest.py -q`:
  6 passed.
- `python scripts/dataset/build_phase6_training_manifest.py --check`: passed
  with 100 records and 68 training-eligible records.
- `python -m compileall src/text2ifc_dataset scripts/dataset -q`: passed.
- `git diff --check`: passed before commits.
- Required model-decision headings and evidence labels were checked.

## Requirement Coverage

- **MODEL-01:** The model choice is based on durable Wave 4 metrics and explicit
  evidence limits.
- **MODEL-02:** Fine-tuning is deferred with measurable trigger conditions.
- **TEXT-01:** Text/target records remain provenance-linked and split-safe.

## Deviations from Plan

- The plan referenced
  `dataset/processed/text2json/pairs.jsonl`, which does not exist. The
  implementation reads the repository's actual split-specific files under
  `dataset/processed/text2json/pairs/`.
- Target validation initially repeated expensive work for the four text styles
  attached to each target. A path, modification-time, and size keyed cache
  preserves validation behavior while reducing the focused test runtime.
- No additional external data was imported. Existing authorized data was
  expanded into a stricter training/evaluation manifest without changing its
  license scope.

## Self-Check: PASSED

The manifest, drift check, tests, model decision, and evidence boundaries meet
the Wave 5 acceptance criteria.

## Next

Proceed to `06-06-PLAN.md`: package the selected prompt-only multi-agent path
as a repeatable service demo and run final Phase 6 verification.
