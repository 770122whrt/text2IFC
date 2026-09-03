---
phase: 11-wall-opening-and-door-operations
plan: "02"
status: complete
completed: "2026-07-28"
commits: [1600292d, 32668860, 13091209]
---

# Plan 11-02 Summary

Implemented IFC Index 0.4 and deterministic Door execution-fact resolution.

## Delivered

- Active index/indexer upgraded to 0.4; 0.3 remains stale and rebuild-only.
- First-class `IfcOpeningElement` records with host, filling state, Storey,
  measured dimensions and Wall-local position.
- Invalid/unmeasurable Openings remain diagnostic and non-editable.
- `IfcDoorStyle` formal attributes and bounded representation summaries are
  persisted through SQLite.
- Pure Door dimension, position, viewpoint, operation and exact-Type policy.
- Registry resolution hooks can canonicalize parameters before Stage 2.
- Space boundary and geometry-side evidence can establish observation side;
  unresolved or same-side Spaces clarify.

## Verification

- 81 focused tests passed.
- LargeBuilding indexes all 60 Openings; measured valid records retain exact
  host/fill/storey evidence.
- DoorStyle formal values match direct reopened IFC values.
- `python -m compileall -q src tests` and `git diff --check` passed.

## Key fail-closed results

- Generic dimension meaning, ambiguous Wall-end measurement and incomplete
  viewpoint clarify together.
- Clear-passage/leaf/rough-opening values are never converted silently.
- Project coordinates, complex generated Door styles, filled Openings and
  existing-Door mutation requests stop before Stage 2.
