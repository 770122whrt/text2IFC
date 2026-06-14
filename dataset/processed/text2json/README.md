# Phase 3 Text-to-JSON Artifacts

This directory contains generated local artifacts for the Phase 3
Natural Language -> BIM JSON 2.0 baseline.

## Boundaries

- BIMNet records are user-authorized for local extraction, dataset
  construction, baseline evaluation, and local model training.
- The repository does not infer redistribution rights for BIMNet source IFC or
  derived training data.
- Train, validation, and test assignment is controlled by
  `dataset/splits/bimnet-scene-splits.json` and grouped by Matterport
  `scene_family` before any text generation.
- Formal targets, Draft clarification records, pairs, predictions, and metrics
  are generated in later Phase 3 waves under this directory.

## Planned Layout

- `formal-gold/`: supported-scope formal BIM JSON 2.0 targets.
- `sidecars/`: source provenance and explicit omitted/loss facts.
- `pairs/`: split-aware Text-to-JSON JSONL records.
- `predictions/`: parsed model outputs accepted by the baseline runner.
- `baseline-runs/`: raw provider responses, diagnostics, and run reports.
- `evaluations/`: metrics JSON and markdown evaluation reports.
