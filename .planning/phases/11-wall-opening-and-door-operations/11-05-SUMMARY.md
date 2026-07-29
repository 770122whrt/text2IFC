---
phase: 11-wall-opening-and-door-operations
plan: "05"
status: blocked_external
completed: false
updated: 2026-07-29
commits:
  - 29daa793
---

# Phase 11 Plan 05 Progress

## Completed

- Added deterministic `remove_door_and_opening` and
  `remove_door_preserve_opening` damage modes. Reports include Door name,
  GlobalId, Type GlobalId/name, formal OperationType and exact damage scope.
- Added an offline acceptance runner and frozen tests.
- LargeBuilding exact-Type, surviving-Opening repair passed IFC reopen, L1,
  L2 and global preservation.
- vvo exact-Type, surviving-Opening repair passed the same gates. The source
  Door's occurrence Storey conflicts with its host Wall; the repaired Door
  correctly follows the host Wall instead of reproducing that error.
- Added a single-write five-Door damage fixture and a five-operation atomic
  ChangeSet. Injected duplicate-target failure publishes no IFC.
- Added a two-Door/two-Window mixed ChangeSet; all four operations pass
  independent L1/L2 and publish one IFC.
- Strengthened the mixed proof so its user request and RepairIntent contain no
  IFC GlobalIds. Window walls and retained Door openings resolve from names,
  storeys and wall-local measurements before the program binds internal GUIDs.
  Exact Type reuse is name-based; duplicate DoorStyle names are narrowed by
  the explicitly requested formal OperationType and still fail closed if more
  than one candidate remains.
- Added a controlled generated-DoorStyle LargeBuilding case and an
  AdvancedProject full-scope case. AdvancedProject cold request-to-publication
  is 140.805 seconds and warm evaluation is 50.037 seconds.
- Independently curated six offline Door/mixed Proof cases. The complete
  success collection validates 11 cases, 30 operations, 137 hashed files and
  33 IFC reopens.
- Full IFC repair regression: 643 passed, 1 skipped.
- Added a real no-fallback DeepSeek runner for complete, clarification and
  unsupported-complex-Door cases.
- Provider configuration checks as ready with 65,536 input and completion
  guards and redacted secrets.

## External blocker

The authorized live command was rejected by the Codex execution quota before
the process or Provider started. The tool reported that usage is exhausted and
suggested retrying after 2026-08-03 10:34.

Actual evidence:

- Stage 1 calls: 0
- Stage 2 calls: 0
- synthetic fallback: false
- Provider result: not executed

This is not recorded as a DeepSeek failure or success.

## Remaining

- Diagnose the 2026-07-29 AdvancedProject cold performance regression. Two
  reruns passed functional/L1/L2/preservation gates but measured 225.665 s and
  226.164 s against the frozen 180 s cold deadline; warm runs remained below
  80 s. Do not raise the deadline to hide this regression.
- Run `scripts/ifc_repair/run_phase11_live_uat.py --live` when execution quota
  is available.
- Independently validate and curate only actual successful live artifacts.
- Mark OPS-01/OPS-02 and Phase 11 complete and create the final checkpoint.
