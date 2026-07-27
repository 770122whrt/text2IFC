---
phase: 11-wall-opening-and-door-operations
plan: "01"
status: complete
completed: "2026-07-28"
commits: [035468bd, e892c85a, 107074d2]
---

# Plan 11-01 Summary

Implemented the additive Phase 11 public contracts and bounded operation prompt
routing.

## Delivered

- RepairIntent/body 0.5 with per-operation `routing_intent`.
- Semantic Manifest 0.3 and Bound ChangeSet 0.4 with
  `door_occurrence`, without modifying historical schema files.
- Deterministic generated-Type template identity, formal-attribute projection
  and SHA-256 derivation.
- Prompt Profile 0.1 plus five checked-in profiles and eight Door sentinel
  few-shots.
- One-call Stage 1 routing/extraction using compact profile projections.
- Stage 2 selected-profile union with hashes, byte count and token estimate.
- Production `RepairAPI` default upgraded to RepairIntent 0.5.

## Verification

- 60 focused tests passed.
- `python -m compileall -q src tests` passed.
- `git diff --check` passed.
- Captured Provider tests prove one Stage 1 call and exclusion of unused
  profiles/few-shots from Stage 2.

## Deviations

None. Door and Opening profiles are reserved but remain non-executable until
their operation definitions are registered by Plan 11-03.
