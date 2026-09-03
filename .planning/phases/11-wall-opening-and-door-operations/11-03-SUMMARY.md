---
phase: 11-wall-opening-and-door-operations
plan: "03"
status: complete
completed: 2026-07-28
commits:
  - 00ac362e
  - 8a4f10a9
  - cde06232
---

# Phase 11 Plan 03 Summary

## Delivered

- Extracted the wall-local footprint, collision, deterministic identity,
  placement, Opening, void and containment primitives into
  `operations/hosted_opening.py`; the existing Window operation now reuses
  that module.
- Registered `add_opening_to_wall`. It creates one `IfcOpeningElement` and one
  `IfcRelVoidsElement`, with no filling, Window, Door, Type or SpaceBoundary.
- Registered `add_door_with_opening_to_wall` and
  `fill_existing_opening_with_door`.
- Added deterministic `IfcDoor` placement, dimensions, fill topology, Storey
  containment and `IfcDoorStyle` binding.
- Generalized bound Type creation to a registered factory. Existing
  `IfcDoorStyle` is reused without changing its formal attributes or
  representation maps; generated styles require a digest-valid compiler
  template.
- Changed semantic assignment dispatch to use each operation's registered
  scope-to-role metadata.
- Added one shared `hosted_opening` audit conflict domain, so Window, Door and
  opening-only footprints are checked against each other.

## Verification

- Shared hosted-opening, Opening, Door, Window, audit and transaction suite:
  `29 passed` in the focused implementation run.
- Expanded Plan 03 regression run: `20 passed`; after updating the historical
  unregistered-operation fixture and cross-family evidence envelope:
  `11 passed`.
- Real LargeBuilding IFC2X3 application:
  - generated-Type Door path publishes and reopens;
  - surviving-Opening path keeps the original Opening/void and reuses the
    selected DoorStyle;
  - generated template tampering publishes no IFC;
  - cross-family overlap is rejected before mutation.

## Notes

- The generated Door representation is intentionally a deterministic,
  simplified type-owned mapped panel. Frame, hardware and material facts are
  not invented.
- Detailed independent L1/L2 and family-neutral occurrence fidelity remain in
  Plan 11-04.
