---
phase: 10-window-l2-semantic-fidelity-closure
plan: 04
status: complete
completed: 2026-07-21
commits:
  - 26c5e81d
---

# Plan 10-04 Summary

Bound Window semantic assignments are now authored inside the existing atomic
IFC transaction. The operation-neutral dispatcher writes typed occurrence
attributes, Psets, BaseQuantities, and operation-scoped Material and
Classification relationships while reusing only manifest-authorized resources.
Type-owned facts remain inherited through the formal Type relationship.

Window application binds the exact authorized Prototype Type, records every
new semantic relationship for L1 allowed-effect accounting, and fails closed on
missing resources, relationship mismatches, or missing IFC2X3 OwnerHistory.
Actual L2 evidence is independently extracted after serialization/reopen; it is
not taken from applicator self-report.

Verification: 77 focused transaction, authoring, audit, benchmark, policy, and
orchestrator tests passed. The LargeBuilding offline public-API repair also
passed with L1 and L2 both `passed` and a successful IFC artifact published.

