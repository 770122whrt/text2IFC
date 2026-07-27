# Phase 11: Wall Opening and Door Operations - Context

**Status:** Design decisions confirmed
**Date:** 2026-07-28
**Canonical contract:** [11-SPEC.md](11-SPEC.md)

## Why this phase exists

Phases 7 through 10.5 proved one production path for Window repair:
bounded target and Type evidence, partial intent and clarification, one atomic
ChangeSet, deterministic IfcOpenShell application, L1/L2/occurrence fidelity,
and scalable full-model preservation. Phase 11 must prove that these are
operation-family capabilities rather than Window-specific code.

Door is the next family because its host topology matches Window while its
Type semantics are materially richer. IFC2X3 Door behavior spans
`IfcDoorStyle.OperationType`, `IfcDoorPanelProperties`,
`IfcDoorLiningProperties`, mapped geometry, placement orientation and
occurrence-direct properties. The phase also needs an opening-only operation
and a path for a surviving empty Opening.

## Confirmed decisions

1. Phase 11 registers three geometry operations:
   `add_opening_to_wall`, `add_door_with_opening_to_wall`, and
   `fill_existing_opening_with_door`. Existing Door scalar properties continue
   to use the generic `set_occurrence_properties` operation.
2. Door width/height language is clarified only when its meaning is ambiguous.
   Explicit door-opening, clear-passage, leaf or rough-opening wording is
   preserved. No conversion to IFC overall dimensions is invented.
3. Left/right swing requires a viewpoint. A reliable explicitly reused
   `IfcDoorStyle` supplies its own formal operation; otherwise missing or
   viewpoint-ambiguous swing information is clarified. A user may explicitly
   accept `NOTDEFINED`.
4. Explicit Type reuse means reuse the exact `IfcDoorStyle` unchanged. Name is
   a lookup label, not formal operation authority. The system does not derive a
   corrected copy of a semantically incomplete Type.
5. Without Type reuse, the compiler creates a dedicated correct system Type.
   Generated styles are limited to `SINGLE_SWING_LEFT`,
   `SINGLE_SWING_RIGHT`, and explicitly accepted `NOTDEFINED`. Complex styles
   may be reused but are not generated in the first release.
6. A Type size or mapped-geometry conflict is clarified; no existing
   representation is silently scaled, including a `Sizeable=TRUE` Type in the
   first release.
7. Space may resolve the target and viewpoint, but Phase 11 does not author
   `IfcRelSpaceBoundary`. Door containment remains at
   `IfcBuildingStorey`, consistent with the sampled models.
8. User-facing Door positions support distance from a named wall end to the
   opening center, distance from a named wall end to the nearest opening edge,
   wall midpoint, or an existing Opening. Project-coordinate placement is out
   of scope. Grid is a target selector unless formal grid geometry is
   explicitly supported later.
9. “Reuse Type/appearance” authorizes only Type reuse. Copying occurrence
   Psets/quantities requires explicit wording about properties, parameters,
   complete configuration or named facts. Context and unique identity facts
   are always recomputed or omitted.
10. Missing optional material, transom, threshold, casing, glazing, rating,
    hardware or custom properties are not generated and do not trigger
    clarification. A requested supported fact is authored and validated; a
    requested unsupported feature is rejected by deterministic capability
    code, never improvised by an LLM.
11. Ordinary generated doors do not require the user to supply manufacturing
    dimensions for frame and leaf. A versioned deterministic visual template
    produces repeatable simplified geometry without promoting its internal
    display parameters to user-authorized semantic facts. Explicit construction
    detail becomes binding only when supplied and supported.
12. Stage 1 performs lightweight family/action classification inside each
    RepairIntent operation using a new routing field. After Stage 1, the
    runtime selects only the relevant operation contracts and few-shots for
    clarification, resolution and Stage 2. There is no extra classification
    Provider call.
13. Replacement, deletion, repositioning and resizing of an existing filled
    Door are deferred. An already-filled Opening cannot be filled again.
14. Acceptance includes single full-bundle repair, surviving-Opening repair,
    generated Type, five-Door atomicity, mixed Window/Door atomicity,
    AdvancedProject preservation and real DeepSeek complete/clarified paths.

## Evidence observed before design

The design was checked against four IFC2X3 models:

| Model | Doors | DoorStyles | Formal operation evidence | Door containment |
|---|---:|---:|---|---|
| LargeBuilding | 18 | 3 | right swing and double-door operation values | 18/18 in storey |
| vvo | 26 | 23 | left, right, double and `NOTDEFINED` | 26/26 in storey |
| AdvancedProject | 126 | 14 | all formal values `NOTDEFINED`; some names mention handedness | 126/126 in storey |
| px4 | 12 | 10 | mainly right swing plus `NOTDEFINED` | 12/12 in storey |

All sampled Doors fill an Opening which voids a host, all have a bound Type,
and none is directly referenced by an `IfcRelSpaceBoundary`. These observations
are benchmark evidence, not universal IFC assumptions.

## Deferred horizon

- complex generated double, sliding, folding, revolving and rolling doors;
- exact manufacturer geometry and hardware;
- derived or authored space boundaries;
- project-coordinate and formal grid-intersection placement;
- existing Door replacement/deletion/repositioning/resizing;
- curved, segmented and free-form walls;
- L3 GUID, STEP, representation-node and byte-level exactness.
